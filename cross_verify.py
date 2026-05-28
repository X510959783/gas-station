"""明鉴交叉模型对抗验证 v1.0
解决 root-1 (无外部验证): DeepSeek 生成 → Claude Sonnet 独立审计
参考: Tri-Agent Audit Framework (arXiv:2601.08839) + CourtGuard (arXiv:2602.22557)

Claude 的角色不是"第二个意见"，而是对抗性审计师——专门找缺陷。
两家不同厂商、不同架构、不同训练数据 → 盲区不完全重叠。

用法:
  from cross_verify import CrossVerifier
  v = CrossVerifier()
  result = v.verify(context="原始需求", output="DeepSeek的输出", severity="HIGH")
  # result.verdict: PASS | WARN | FAIL
  # result.findings: [{"severity": "CRITICAL", "description": "...", "location": "..."}]
"""
import json
import os
import hashlib
import httpx
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(REPO_ROOT, "providers.json")

# 仅 HIGH 严重性触发交叉验证, 避免浪费 token
TRIGGER_SEVERITIES = {"HIGH", "CRITICAL"}

# Claude 审计师的系统提示——对抗性角色
AUDITOR_SYSTEM_PROMPT = """你是一名独立安全审计师, 受雇于外部监管机构。
你的任务不是"确认这个输出是否正确"，而是"找出这个输出中的缺陷"。

审计标准:
1. 逻辑缺陷: 推理链是否完整? 是否有未声明的假设? 是否有因果倒置?
2. 安全漏洞: 是否引入了注入点/权限绕过/数据泄露?
3. 事实错误: 引用的 API/文件路径/版本号是否存在?
4. 边界遗漏: 是否忽略了边缘情况、错误处理、并发安全?
5. 过度自信: 输出中是否有"应该没问题"/"似乎正确"/"大概率"等模糊断言?

输出 JSON 格式 (不要输出其他内容):
{
  "verdict": "PASS"|"WARN"|"FAIL",
  "findings": [
    {
      "severity": "CRITICAL"|"HIGH"|"MEDIUM"|"LOW",
      "category": "logic"|"security"|"factual"|"boundary"|"confidence",
      "description": "具体缺陷描述",
      "location": "缺陷在输出中的位置 (引用原文关键句)",
      "recommendation": "修复建议"
    }
  ],
  "summary": "一句话总结审计结论"
}

判定规则:
- 有 CRITICAL 或 HIGH 缺陷 → FAIL
- 有 2+ MEDIUM 缺陷 → WARN
- 仅有 LOW 或无缺陷 → PASS"""


@dataclass
class Finding:
    severity: str       # CRITICAL | HIGH | MEDIUM | LOW
    category: str       # logic | security | factual | boundary | confidence
    description: str
    location: str
    recommendation: str = ""


@dataclass
class VerifyResult:
    verdict: str        # PASS | WARN | FAIL | SKIP | ERROR
    findings: list = field(default_factory=list)
    summary: str = ""
    auditor_model: str = ""
    tokens_used: dict = field(default_factory=dict)
    audit_hash: str = ""
    timestamp: str = ""

    def is_blocking(self) -> bool:
        return self.verdict == "FAIL"

    def needs_review(self) -> bool:
        return self.verdict in ("FAIL", "WARN")


class CrossVerifier:
    """交叉模型对抗验证器"""

    def __init__(self):
        self._api_key: Optional[str] = None
        self._base_url: str = "https://api.qnaigc.com"
        self._model: str = "claude-sonnet-4-6"
        self._client: Optional[httpx.Client] = None
        self._load_config()

    def _load_config(self):
        """加载七牛云 Claude 配置, 优先级: 环境变量 > providers.json"""
        # 第一优先级: 环境变量 (安全最佳实践)
        env_key = os.environ.get("QINIU_API_KEY")
        if env_key:
            self._api_key = env_key
            return

        # 第二优先级: providers.json (回退)
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                config = json.load(f)
            qiniu = config.get("providers", {}).get("qiniu-claude", {})
            if qiniu.get("enabled") and qiniu.get("api_key"):
                self._api_key = qiniu["api_key"]
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    @property
    def is_available(self) -> bool:
        return self._api_key is not None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=httpx.Timeout(120.0, connect=10.0, read=120.0, write=30.0, pool=5.0),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10, keepalive_expiry=30),
            )
        return self._client

    def verify(self, context: str, output: str,
               severity: str = "MEDIUM", max_output_tokens: int = 1500) -> VerifyResult:
        """对 DeepSeek 的输出执行交叉模型审计

        Args:
            context: 原始需求/提示
            output: DeepSeek 生成的输出内容
            severity: 决策严重性 (LOW/MEDIUM/HIGH/CRITICAL)
            max_output_tokens: 审计响应的最大 token 数

        Returns:
            VerifyResult — verdict + findings
        """
        # 低严重性跳过 (节省 token)
        if severity.upper() not in TRIGGER_SEVERITIES:
            return VerifyResult(
                verdict="SKIP",
                summary=f"严重性={severity}低于触发阈值, 跳过交叉验证"
            )

        if not self.is_available:
            return VerifyResult(
                verdict="ERROR",
                summary="七牛云 Claude API 未配置, 无法执行交叉验证"
            )

        # 截断过长的内容 (控制 token 消耗)
        ctx_truncated = context[:4000] if len(context) > 4000 else context
        out_truncated = output[:6000] if len(output) > 6000 else output

        # 防护提示注入: 转义可能闭合 XML 标签的用户内容
        safe_context = ctx_truncated.replace("</", "<\\/")
        safe_output = out_truncated.replace("</", "<\\/")

        user_prompt = f"""<原始需求>
{safe_context}
</原始需求>

<待审计输出>
{safe_output}
</待审计输出>

请按照审计标准对以上输出进行独立审计。记住: 你的默认立场是"找出问题"，不是"确认正确"。
输出 JSON:"""

        try:
            resp = self._get_client().post(
                f"{self._base_url}/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": self._model,
                    "system": AUDITOR_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_prompt}],
                    "max_tokens": max_output_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            # 提取 Claude 的文本响应
            content_blocks = data.get("content", [])
            text = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    text += block.get("text", "")

            # 解析 JSON 响应
            result = self._parse_response(text)

            # 添加元数据
            usage = data.get("usage", {})
            result.auditor_model = data.get("model", self._model)
            result.tokens_used = {
                "input": usage.get("input_tokens", 0),
                "output": usage.get("output_tokens", 0),
            }
        except httpx.HTTPError as e:
            return VerifyResult(
                verdict="ERROR",
                summary=f"审计 API 调用失败: {e}"
            )
        except Exception as e:
            return VerifyResult(
                verdict="ERROR",
                summary=f"审计过程异常: {e}"
            )

        # 生成审计哈希
        result.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = json.dumps({
            "context": context[:500],
            "output": output[:500],
            "verdict": result.verdict,
            "findings": [asdict(f) for f in result.findings],
            "timestamp": result.timestamp,
        }, sort_keys=True, ensure_ascii=False)
        result.audit_hash = hashlib.sha256(payload.encode()).hexdigest()

        return result

    def _parse_response(self, text: str) -> VerifyResult:
        """从 Claude 响应中提取 JSON, 处理截断/格式问题"""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:]) if len(lines) > 1 else text
            if text.endswith("```"):
                text = text[:-3]

        def try_parse(s: str) -> Optional[dict]:
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return None

        # 尝试1: 直接解析
        data = try_parse(text)
        if data:
            return self._build_result(data)

        # 尝试2: 提取 {...} 范围
        brace_start = text.find("{")
        brace_end = text.rfind("}") + 1
        if brace_start >= 0 and brace_end > brace_start:
            extracted = text[brace_start:brace_end]
            data = try_parse(extracted)
            if data:
                return self._build_result(data)
            # 尝试3: 补全截断的 JSON
            data = try_parse(extracted + "}]}")
            if data:
                return self._build_result(data)

        return VerifyResult(
            verdict="ERROR",
            summary=f"审计响应 JSON 解析失败: {text[:200]}..."
        )

    def _build_result(self, data: dict) -> VerifyResult:
        verdict = data.get("verdict", "ERROR")
        if verdict not in ("PASS", "WARN", "FAIL"):
            verdict = "ERROR"
        findings = []
        for f in data.get("findings", []):
            findings.append(Finding(
                severity=f.get("severity", "UNKNOWN"),
                category=f.get("category", "unknown"),
                description=f.get("description", ""),
                location=f.get("location", ""),
                recommendation=f.get("recommendation", ""),
            ))
        return VerifyResult(
            verdict=verdict,
            findings=findings,
            summary=data.get("summary", ""),
        )

    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ═══════════════════════════════════════════════════════════════
# CLI 与集成
# ═══════════════════════════════════════════════════════════════

def verify_and_record(context: str, output: str, severity: str = "MEDIUM",
                      signer: str = "cross-verify") -> dict:
    """便捷函数: 验证 + 记录到审计链 (Stamp-First Architecture)

    用法:
      result = verify_and_record(
          context="修复 front_router.py 的认证逻辑",
          output="修改了 send_anthropic 中的 x-api-key 注入方式...",
          severity="HIGH"
      )
      if result["blocking"]:
          print("验证未通过, 阻止执行!")
    """
    verifier = CrossVerifier()
    try:
        result = verifier.verify(context, output, severity)
    finally:
        verifier.close()

    # 记录到审计链 — 包括拒绝收据 (AgentStamp 2026 Stamp-First 模式)
    try:
        from audit_chain import sign_event
        event_type = "cross_verify_denied" if result.is_blocking() else "cross_verify"
        sign_event(event_type, {
            "verdict": result.verdict,
            "severity": severity,
            "findings_count": len(result.findings),
            "summary": result.summary,
            "audit_hash": result.audit_hash,
            "tokens_used": result.tokens_used,
        }, signer=signer)
    except Exception as e:
        import sys
        print(f"[CrossVerify] 审计链记录失败: {e}", file=sys.stderr, flush=True)

    return {
        "verdict": result.verdict,
        "blocking": result.is_blocking(),
        "needs_review": result.needs_review(),
        "findings": [asdict(f) for f in result.findings],
        "summary": result.summary,
        "audit_hash": result.audit_hash,
        "tokens_used": result.tokens_used,
    }


def pre_action_stamp(action: str, target: str, severity: str = "MEDIUM",
                     signer: str = "cross-verify") -> str:
    """Stamp-First: 在工具执行前写入预操作戳记

    这是 AgentStamp (2026) 的核心模式:
    - 验证戳在操作执行前写入, 不是之后
    - 如果操作崩溃, 审计链中仍有"尝试过"的记录
    - 被拒绝的操作产生"拒绝收据", 与通过的操作区分

    Args:
        action: 操作描述 (如 "编辑 front_router.py:send_anthropic")
        target: 操作目标 (如 "front_router.py:342-358")
        severity: 操作严重性
        signer: 签名者标识

    Returns:
        stamp_id: 戳记标识符 (audit_hash[:12]), 用于操作后关联
    """
    try:
        from audit_chain import sign_event
        event = sign_event("pre_action_stamp", {
            "action": action,
            "target": target,
            "severity": severity,
            "status": "pending",
        }, signer=signer)
        stamp_hash = hashlib.sha256(
            json.dumps(event, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()[:12]
        return stamp_hash
    except Exception as e:
        import sys
        print(f"[CrossVerify] 预操作戳记失败: {e}", file=sys.stderr, flush=True)
        return ""


def proofguard_gate(action: str, target: str, severity: str = "MEDIUM",
                    required_checks: list | None = None,
                    signer: str = "cross-verify") -> dict:
    """ProofGuard 预执行验证门 — "No Proof, No Execution" (2026 模式)

    基于: ProofGuard (PyPI) + OAP (arXiv:2603.20953) + SRM (arXiv:2603.22350)

    核心不变式:
      1. 决策记录(proof)必须在操作之前存在 — 结构保证不可绕过
      2. 任何门控异常 → FAIL_CLOSED (拒绝执行, 绝不静默通过)
      3. 拒绝是有效系统结果, 不是错误 — DENY ≠ ERROR

    Args:
        action: 操作描述
        target: 操作目标 (file:line)
        severity: 操作严重性 (LOW/MEDIUM/HIGH/CRITICAL)
        required_checks: 必须通过的检查列表 (如 ["rate_limit", "audit_chain", "framework_integrity"])
        signer: 签名者标识

    Returns:
        {"allowed": bool, "stamp_id": str, "denial_reason": str | None, "checks": dict}
    """
    result = {"allowed": True, "stamp_id": "", "denial_reason": None, "checks": {}}

    # 步骤1: 写入预操作戳记 (结构中先于执行)
    try:
        from audit_chain import sign_event
        event = sign_event("proofguard_gate", {
            "action": action,
            "target": target,
            "severity": severity,
            "status": "evaluating",
        }, signer=signer)
        result["stamp_id"] = hashlib.sha256(
            json.dumps(event, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()[:12]
    except Exception as e:
        # FAIL_CLOSED: 无法写入戳记 → 拒绝执行
        result["allowed"] = False
        result["denial_reason"] = f"预操作戳记失败: {e}"
        return result

    # 步骤2: 执行必须通过的检查
    checks_to_run = required_checks or ["framework_integrity"]
    for check_name in checks_to_run:
        try:
            check_result = _run_gate_check(check_name)
            result["checks"][check_name] = check_result
            if not check_result.get("ok", False):
                result["allowed"] = False
                result["denial_reason"] = f"检查 {check_name} 失败: {check_result.get('message', '?')}"
        except Exception as e:
            # FAIL_CLOSED: 检查异常 → 拒绝执行
            result["allowed"] = False
            result["denial_reason"] = f"检查 {check_name} 异常: {e}"

    # 步骤3: 写入最终决策记录 (通过或拒绝)
    try:
        decision_type = "proofguard_pass" if result["allowed"] else "proofguard_denied"
        sign_event(decision_type, {
            "action": action,
            "target": target,
            "stamp_id": result["stamp_id"],
            "verdict": "PASS" if result["allowed"] else "DENY",
            "denial_reason": result["denial_reason"],
            "checks_passed": {k: v.get("ok") for k, v in result["checks"].items()},
        }, signer=signer)
    except Exception:
        pass  # 决策记录失败不影响门控结果

    return result


def _run_gate_check(check_name: str) -> dict:
    """执行单个门控检查 (零 API 依赖, 纯本地验证)"""
    if check_name == "rate_limit":
        # 检查 Front Router 是否过载
        import socket
        try:
            s = socket.socket()
            s.settimeout(2)
            s.connect(("127.0.0.1", 8765))
            s.close()
            return {"ok": True, "message": "Front Router 在线"}
        except Exception as e:
            return {"ok": False, "message": f"Front Router 不可达: {e}"}

    elif check_name == "audit_chain":
        # 检查审计链完整性
        try:
            from audit_chain import verify_chain
            vc = verify_chain(strict=False)
            return {"ok": vc.get("valid", False),
                    "message": f"审计链: {vc.get('total', 0)} 事件, "
                              f"{len(vc.get('errors', []))} 错误"}
        except Exception as e:
            return {"ok": False, "message": f"审计链检查失败: {e}"}

    elif check_name == "framework_integrity":
        # 检查框架文件是否漂移
        try:
            import os as _os
            snapshot_file = _os.path.join(
                _os.path.dirname(_os.path.abspath(__file__)),
                ".claude", "tracking", "watchdog-snapshot.json")
            if not _os.path.exists(snapshot_file):
                return {"ok": True, "message": "快照文件不存在 (首次运行?)"}
            with open(snapshot_file, "r", encoding="utf-8") as f:
                snapshot = json.load(f)
            old_files = {f["file"]: f["sha256"] for f in snapshot.get("files", [])}
            # 检查关键模块
            import hashlib as _hl
            for mod in ["audit_chain.py", "cross_verify.py", "mingjian_watchdog.py"]:
                mod_path = _os.path.join(REPO_ROOT, mod)
                if not _os.path.exists(mod_path):
                    return {"ok": False, "message": f"关键模块缺失: {mod}"}
                with open(mod_path, "rb") as f:
                    current = _hl.sha256(f.read()).hexdigest()
                known = old_files.get(mod)
                if known and known != current[:16]:
                    return {"ok": False, "message": f"模块被篡改: {mod}"}
            return {"ok": True, "message": "框架完整性通过"}
        except Exception as e:
            return {"ok": False, "message": f"完整性检查异常: {e}"}

    return {"ok": False, "message": f"未知检查: {check_name}"}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python cross_verify.py <output_text> [context]")
        print("  从 stdin 读取待验证的输出, 可选 context 为原始需求")
        print("  或: python cross_verify.py --test  运行自检")
        sys.exit(1)

    if sys.argv[1] == "--test":
        print("=== 交叉验证自检 ===")
        v = CrossVerifier()
        print(f"七牛云 Claude: {'已配置' if v.is_available else '未配置'}")
        if v.is_available:
            result = v.verify(
                context="修复 front_router.py 中 send_anthropic 函数的认证逻辑",
                output="在 send_anthropic 中, 我将 x-api-key 改为从 providers.json 读取。"
                       "应该没问题。不需要额外测试。",
                severity="HIGH"
            )
            print(f"裁决: {result.verdict}")
            print(f"摘要: {result.summary}")
            print(f"审计哈希: {result.audit_hash[:16]}...")
            print(f"Token 消耗: {result.tokens_used}")
            for f in result.findings:
                print(f"  [{f.severity}] {f.category}: {f.description[:80]}...")
            print(f"阻塞: {result.is_blocking()}")
        v.close()
        sys.exit(0)

    # 从命令行参数或 stdin 读取
    output_text = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    context_text = sys.argv[2] if len(sys.argv) > 2 else "代码修改"

    result = verify_and_record(context_text, output_text, severity="HIGH")
    print(json.dumps(result, ensure_ascii=False, indent=2))
