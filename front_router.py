"""明鉴 Front Router v2.0 — 三级智能路由
端口: 8765

路由策略 (月预算 ¥1,450):
  L1 简单 (~40%): DeepSeek V4-Flash (¥1/M in, ¥2/M out) — 文件读取/补全/缓存命中
  L2 中等 (~50%): DeepSeek V4-Pro  (¥3/M in, ¥6/M out) — 调试/重构/标准编码
  L3 复杂 (~10%): Claude Sonnet 4.6 (¥18/M in, ¥89/M out) — 架构/多文件/视觉/交叉验证

协议支持:
  - Anthropic 原生: DeepSeek / 七牛云Claude (直连, 无翻译损耗)
  - OpenAI 翻译: SkyClaw / Cerebras / Groq (Anthropic↔OpenAI 双向翻译)
"""
import json
import os
import re
import time
import hmac
import asyncio
import contextlib
import hashlib
import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import StreamingResponse, Response, JSONResponse
from starlette.routing import Route

# === 审计链集成 (模块级别导入, 避免每请求重复) ===
try:
    from audit_chain import sign_event as _audit_sign_event
except ImportError:
    _audit_sign_event = None

def _try_audit_log(event_type: str, data: dict):
    """非阻塞审计日志——失败不影响主流程"""
    if _audit_sign_event is None:
        return
    try:
        _audit_sign_event(event_type, data, signer="front-router")
    except Exception:
        pass

# === 配置文件 ===
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "providers.json")

# === 供应商注册表 ===
PROVIDER_REGISTRY = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/anthropic",
        "protocol": "anthropic",
        "auth_header": None,
        "timeout": 300,
        "strip_headers": True,
        "strip_body_fields": True,
        "filter_sse": True,
    },
    "deepseek-flash": {
        "name": "DeepSeek Flash",
        "base_url": "https://api.deepseek.com/anthropic",
        "protocol": "anthropic",
        "auth_header": None,
        "timeout": 120,
        "strip_headers": True,
        "strip_body_fields": True,
        "filter_sse": True,
        "force_model": "deepseek-v4-flash",  # 强制覆盖模型名
    },
    "qiniu-claude": {
        "name": "七牛云 Claude Sonnet 4.6",
        "base_url": "https://api.qnaigc.com",
        "protocol": "anthropic",
        "auth_header": "x-api-key",  # 非 None → 独立密钥型, 需要 api_key
        "api_key": None,        # 从 providers.json 读取
        "timeout": 120,
        "strip_headers": True,
        "strip_body_fields": False,
        "filter_sse": False,
        "force_model": "claude-sonnet-4-6",
    },
    "skyclaw": {
        "name": "SkyClaw",
        "base_url": "https://api.apifree.ai/agent/v1/chat/completions",
        "protocol": "openai",
        "api_key": None,  # 从环境变量 SKYCLAW_API_KEY 加载
        "default_model": "skywork-ai/skyclaw-v1-lite",
        "timeout": 300,
        "streaming": False,
    },
    "cerebras": {
        "name": "Cerebras",
        "base_url": "https://api.cerebras.ai/v1/chat/completions",
        "protocol": "openai",
        "api_key": None,
        "default_model": "qwen-3-235b",
        "timeout": 300,
        "streaming": False,
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "protocol": "openai",
        "api_key": None,
        "default_model": "gpt-oss-120b",
        "timeout": 300,
        "streaming": False,
    },
}

# === 三级路由配置 ===
# 每级: {"primary": 首选供应商, "fallbacks": [备用供应商列表]}
# 预算分配: L1~40% | L2~50% | L3~10%
TIERED_ROUTING = {
    "simple": {
        "primary": "deepseek-flash",
        "fallbacks": ["deepseek"],
        "budget_pct": 40,
    },
    "medium": {
        "primary": "deepseek",
        "fallbacks": ["deepseek-flash", "qiniu-claude"],
        "budget_pct": 50,
    },
    "complex": {
        "primary": "qiniu-claude",
        "fallbacks": ["deepseek", "skyclaw"],
        "budget_pct": 10,
    },
}

# === 任务复杂度检测配置 ===
# 简单任务关键词 → L1 Flash 足够 (中英双语) — 预编译提升性能
_SIMPLE_PATTERN_STRS = [
    r"\b(read|list|show|cat|type|display|view)\s+.*file",
    r"\bwhat\s+is\b",
    r"\bhow\s+(do|to|can|should)\b",
    r"\b(find|search|locate|grep)\b",
    r"\bexplain\s+(this|the|what|how)\b",
    r"\b(convert|format|translate)\b",
    r"\b(generate|create)\s+(a|an|simple|basic)\s+(commit|message|readme|comment|doc)",
    r"\b(add|write)\s+(a|an)\s+(unit|test|simple)\s+test",
    r"\b(fix|resolve)\s+(typo|spelling|formatting|lint|style)\b",
    r"\b(summarize|summary|tldr|recap)\b",
    # 中文简单任务
    r"(查看|显示|列出|读一下|帮我看|找一下|搜索)",
    r"(怎么写|怎么用|是什么意思|解释一下)",
    r"(翻译|转换|格式化)",
    r"(生成|创建).{0,5}(commit|readme|注释|文档|测试)",
    r"(修正|修复).{0,5}(拼写|格式|typo|lint)",
    r"(总结|概括|摘要)",
]
SIMPLE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _SIMPLE_PATTERN_STRS]

# 复杂任务关键词 → L3 Sonnet 值得 (中英双语) — 预编译提升性能
_COMPLEX_PATTERN_STRS = [
    r"\b(architect|architecture|design\s+system|system\s+design)\b",
    r"\b(refactor|restructure|reorganize|migrate|overhaul)\s+(the|entire|whole|all)\b",
    r"\b(multi[- ]file|multi[- ]service|multi[- ]module|cross[- ]cutting)\b",
    r"\b(security|vulnerability|injection|exploit|auth[a-z]*\s+bypass)\b",
    r"\b(performance|optimize|optimization|profiling|bottleneck)\s+(critical|severe|major)\b",
    r"\b(concurrency|race[- ]condition|deadlock|thread[- ]safe)\b",
    r"\b(debug|diagnose|troubleshoot|investigate)\s+(complex|difficult|strange|weird|mysterious)\b",
    r"\b(design|implement|build|create)\s+(a|the|new)\s+(system|service|api|pipeline|framework|platform)\b",
    r"\b(image|picture|screenshot|photo|diagram|chart|graph|ui|visual)\b",
    r"\b(review|audit)\s+(full|complete|comprehensive|entire|whole)\s+(codebase|project|system)\b",
    r"\b(production|deploy|release|rollout)\b.*\b(safe|safety|risk|critical|breaking)\b",
    r"\b(cross[- ]validat|second[- ]opinion|independent[- ]review|verify.*correct)\b",
    # 中文复杂任务
    r"(架构|系统设计|重构|迁移|全面.{0,10}(改|修|重写|翻新))",
    r"(安全|漏洞|注入|权限|认证.{0,10}(绕过|缺陷|加固|方案))",
    r"(性能.{0,10}(优化|瓶颈|分析)|并发|死锁|竞态)",
    r"(跨.{0,10}(文件|服务|模块|系统)|多.{0,10}(文件|服务|模块))",
    r"(设计|实现|构建|搭建).{0,10}(系统|服务|API|框架|平台|管道)",
    r"(图片|截图|图表|照片|UI|界面|视觉)",
    r"(审查|审计|检查|复查).{0,10}(全面|完整|代码|系统|项目|安全|架构)",
    r"(生产|上线|部署|发布).{0,10}(安全|风险|关键|破坏|回滚)",
    r"(交叉验证|第二意见|独立审计|验证.*正确性|不同模型)",
    # 中文单关键词强信号 (独立出现即触发复杂路由)
    r"(安全审计|安全架构|安全审查|渗透测试|威胁建模)",
    r"(大规模重构|全栈|端到端|零信任|纵深防御)",
    r"(密码学|加密算法|数字签名|哈希链|密钥管理)",
    r"(状态机|有限状态|工作流引擎|事件溯源)",
]
COMPLEX_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _COMPLEX_PATTERN_STRS]

# 其他预编译正则 (classify_complexity 中使用)
_FILE_PATH_PATTERN = re.compile(r'[^\s"]+\.(py|js|ts|go|rs|yaml|json|toml|md)')
_BULK_FIX_PATTERN = re.compile(r'(全面|所有|剩余|全部|一切|每个).{0,10}(解决|修复|处理|改造|重写|迁移|审查)')

# === DeepSeek 专用: 需要剥离的 headers/body 字段 ===
STRIP_HEADERS = {"anthropic-beta", "host"}
STRIP_BODY_FIELDS = {"tool_choice"}

limits = httpx.Limits(max_connections=50, max_keepalive_connections=20, keepalive_expiry=60)
timeout = httpx.Timeout(connect=10, read=300, write=30, pool=5)

# === 安全配置 ===
MAX_BODY_SIZE = 5 * 1024 * 1024  # 5MB 请求体上限
FRONT_ROUTER_AUTH_KEY = os.environ.get("FRONT_ROUTER_AUTH_KEY", "")  # 空=不启用认证

# SSRF 防护: 上游 URL 必须匹配的基础域名白名单
ALLOWED_UPSTREAM_DOMAINS = {
    "api.deepseek.com",
    "api.qnaigc.com",
    "api.apifree.ai",
    "api.cerebras.ai",
    "api.groq.com",
}

# 速率限制: 简单的基于IP的令牌桶 (内存)
_rate_limit_buckets: dict = {}  # ip -> {"tokens": float, "last_refill": float}
RATE_LIMIT_RPS = 10.0          # 每秒允许请求数
RATE_LIMIT_BURST = 30          # 突发容量
_rate_limit_cleanup = 0.0       # 上次清理时间戳


# ═══════════════════════════════════════════════════════════════
# 任务复杂度检测
# ═══════════════════════════════════════════════════════════════

def classify_complexity(anth_body: dict) -> str:
    """分析 Anthropic 请求体, 返回 "simple" / "medium" / "complex"

    检测维度:
      1. 消息数量 (历史轮次)
      2. 工具定义数量
      3. system prompt 长度
      4. 内容中是否包含图片
      5. 最后一条用户消息匹配简单/复杂模式
    """
    messages = anth_body.get("messages", [])
    tools = anth_body.get("tools", [])
    system = anth_body.get("system", "")

    # 维度1: 消息数
    msg_count = len(messages)

    # 维度2: 工具数
    tool_count = len(tools) if isinstance(tools, list) else 0

    # 维度3: system prompt 长度
    if isinstance(system, list):
        system_len = sum(len(s.get("text", "")) for s in system if isinstance(s, dict))
    elif isinstance(system, str):
        system_len = len(system)
    else:
        system_len = 0

    # 维度4: 图片检测
    has_image = False
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "image":
                    has_image = True
                    break
        if has_image:
            break

    # 维度5: 最后一条用户消息的文本
    last_user_text = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                last_user_text = content
            elif isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(block.get("text", ""))
                last_user_text = " ".join(parts)
            break

    # 图片 → 直接 L3 (DeepSeek 不支持图片)
    if has_image:
        return "complex"

    # 匹配简单模式 (预编译正则)
    simple_score = 0
    for pattern in SIMPLE_PATTERNS:
        if pattern.search(last_user_text):
            simple_score += 1

    # 匹配复杂模式 (预编译正则)
    complex_score = 0
    for pattern in COMPLEX_PATTERNS:
        if pattern.search(last_user_text):
            complex_score += 2  # 复杂模式权重更高

    # 启发式加权
    if msg_count > 15:
        complex_score += 3
    elif msg_count > 8:
        complex_score += 1
    elif msg_count <= 2:
        simple_score += 2

    if tool_count > 20:
        complex_score += 3
    elif tool_count > 10:
        complex_score += 1
    elif tool_count == 0:
        simple_score += 1

    if system_len > 5000:
        complex_score += 2
    elif system_len > 2000:
        complex_score += 1
    elif system_len < 500:
        simple_score += 1

    # 附加检测: 消息长度 (长消息通常包含复杂指令)
    if len(last_user_text) > 3000:
        complex_score += 2
    elif len(last_user_text) > 1500:
        complex_score += 1

    # 附加检测: 多文件路径 (如 "src/a.py + tests/b.py + config/c.json") — 预编译
    file_path_count = len(_FILE_PATH_PATTERN.findall(last_user_text))
    if file_path_count >= 5:
        complex_score += 2
    elif file_path_count >= 3:
        complex_score += 1

    # 附加检测: "全面/所有/剩余/全部" + 动作动词 = 批量操作 — 预编译
    if _BULK_FIX_PATTERN.search(last_user_text):
        complex_score += 2

    if complex_score >= 3:
        return "complex"
    elif complex_score >= 1 or simple_score < 2:
        return "medium"
    else:
        return "simple"


# ═══════════════════════════════════════════════════════════════
# 配置加载
# ═══════════════════════════════════════════════════════════════

# 环境变量 → 供应商密钥映射 (优先于 providers.json)
ENV_KEY_MAP = {
    "qiniu-claude": "QINIU_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "groq": "GROQ_API_KEY",
    "skyclaw": "SKYCLAW_API_KEY",
}


def load_provider_keys():
    """加载第三方 API 密钥, 优先级: 环境变量 > providers.json"""
    # 第一优先级: 环境变量 (安全最佳实践)
    for provider_name, env_var in ENV_KEY_MAP.items():
        if provider_name in PROVIDER_REGISTRY:
            env_val = os.environ.get(env_var)
            if env_val:
                PROVIDER_REGISTRY[provider_name]["api_key"] = env_val
                print(f"[FrontRouter] [OK] {provider_name} 密钥来自环境变量 {env_var}", flush=True)

    # 第二优先级: providers.json (回退, 向后兼容)
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            config = json.load(f)
        for name, cfg in config.get("providers", {}).items():
            if name in PROVIDER_REGISTRY and cfg.get("enabled") and cfg.get("api_key"):
                # 不覆盖环境变量已设置的值
                if not PROVIDER_REGISTRY[name].get("api_key"):
                    PROVIDER_REGISTRY[name]["api_key"] = cfg["api_key"]
                    print(f"[FrontRouter] [WARN] {name} 密钥来自 providers.json (建议改用环境变量 {ENV_KEY_MAP.get(name, '?')})", flush=True)
    except (FileNotFoundError, json.JSONDecodeError):
        pass


# ═══════════════════════════════════════════════════════════════
# 请求/响应处理
# ═══════════════════════════════════════════════════════════════

def get_tiered_chain(anth_body: dict) -> list:
    """根据请求复杂度获取三级路由链——只返回可用的供应商

    anthropic 协议的供应商分两种:
      - 透传型 (auth_header=None): 转发客户端的 x-api-key → DeepSeek
      - 独立密钥型 (有 api_key): 使用自己的 key → 七牛云 Claude
    openai 协议的供应商必须有 api_key
    """
    tier = classify_complexity(anth_body)
    routing = TIERED_ROUTING[tier]
    chain = []

    all_names = [routing["primary"]] + routing["fallbacks"]
    seen = set()
    for name in all_names:
        if name in seen:
            continue
        seen.add(name)
        provider = PROVIDER_REGISTRY.get(name)
        if provider is None:
            continue
        if provider["protocol"] == "anthropic":
            # 透传型: 总是可用 (客户端自带 key)
            if provider.get("auth_header") is None:
                chain.append((name, provider, tier))
            # 独立密钥型: 需要配置 api_key
            elif provider.get("api_key"):
                chain.append((name, provider, tier))
        elif provider.get("api_key"):
            chain.append((name, provider, tier))

    return chain


def filter_headers(headers: dict) -> dict:
    """DeepSeek 路径: 剥离不合规的 headers"""
    result = {}
    for k, v in headers.items():
        lower = k.lower()
        if lower in STRIP_HEADERS:
            continue
        if lower.startswith("anthropic-") and lower != "anthropic-version":
            continue
        if lower in ("content-length", "transfer-encoding", "connection"):
            continue
        result[k] = v
    return result


def deepseek_filter_body(raw_body: bytes) -> bytes:
    """DeepSeek 路径: 移除 tool_choice + 禁用 thinking"""
    try:
        body = json.loads(raw_body)
        for field in STRIP_BODY_FIELDS:
            body.pop(field, None)
        body["thinking"] = {"type": "disabled"}
        return json.dumps(body).encode()
    except (json.JSONDecodeError, KeyError):
        return raw_body


# ═══════════════════════════════════════════════════════════════
# Anthropic ↔ OpenAI 双向翻译
# ═══════════════════════════════════════════════════════════════

def anth_to_openai(anth_body: dict) -> dict:
    """Anthropic Messages → OpenAI Chat Completions"""
    openai_body = {
        "model": anth_body["model"],
        "messages": [],
        "reasoning_effort": "none",
    }

    system = anth_body.get("system", "")
    if isinstance(system, list):
        system = "\n".join(
            s.get("text", "") for s in system
            if isinstance(s, dict) and s.get("type") == "text"
        )
    if system:
        openai_body["messages"].append({"role": "system", "content": system})

    for msg in anth_body.get("messages", []):
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if isinstance(content, list):
            parts = []
            for block in content:
                if not isinstance(block, dict):
                    continue
                t = block.get("type", "")
                if t == "text":
                    parts.append(block.get("text", ""))
                elif t == "tool_use":
                    parts.append(
                        f"[调用工具 {block.get('name', '')}："
                        f"{json.dumps(block.get('input', {}), ensure_ascii=False)}]"
                    )
                elif t == "tool_result":
                    parts.append(block.get("content", ""))
            content = "\n".join(parts)

        if content:
            openai_body["messages"].append({"role": role, "content": content})

    if "max_tokens" in anth_body:
        openai_body["max_tokens"] = anth_body["max_tokens"]

    return openai_body


def openai_to_anth(openai_body: dict, model: str) -> dict:
    """OpenAI Chat Completions → Anthropic Messages"""
    choice = openai_body.get("choices", [{}])[0]
    message = choice.get("message", {})
    content_text = message.get("content") or ""

    finish_reason = choice.get("finish_reason", "stop")
    stop_map = {"stop": "end_turn", "length": "max_tokens", "tool_calls": "tool_use"}
    usage = openai_body.get("usage", {})

    return {
        "id": openai_body.get("id", "msg_000"),
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": content_text}],
        "stop_reason": stop_map.get(finish_reason, "end_turn"),
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }


# ═══════════════════════════════════════════════════════════════
# SSE 流式处理
# ═══════════════════════════════════════════════════════════════

async def filter_thinking_sse(response):
    """从 SSE 流中剥离 thinking/redacted_thinking 块事件"""
    thinking_indices: set = set()
    buffer = b""
    current_event = b""
    has_sse_events = False

    async for chunk in response.aiter_bytes():
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            current_event += line + b"\n"
            has_sse_events = True

            if line == b"":
                event_bytes = current_event
                current_event = b""
                event_text = event_bytes.decode("utf-8", errors="replace")
                skip = False

                for ev_line in event_text.split("\n"):
                    if ev_line.startswith("data: "):
                        try:
                            data = json.loads(ev_line[6:])
                            t = data.get("type", "")
                            idx = data.get("index")

                            if t == "content_block_start":
                                cb = data.get("content_block", {})
                                if cb.get("type") in ("thinking", "redacted_thinking"):
                                    thinking_indices.add(idx)
                                    skip = True
                            elif idx is not None and idx in thinking_indices:
                                skip = True
                                if t == "content_block_stop":
                                    thinking_indices.discard(idx)
                        except (json.JSONDecodeError, KeyError):
                            pass
                        break

                if not skip:
                    yield event_bytes

    if current_event:
        yield current_event

    if buffer:
        if not has_sse_events:
            yield buffer
        elif current_event:
            pass
        else:
            yield buffer


# ═══════════════════════════════════════════════════════════════
# 供应商请求发送
# ═══════════════════════════════════════════════════════════════

def prepare_anth_request(provider: dict, raw_body: bytes, request_headers: dict) -> tuple:
    """准备 Anthropic 协议请求——根据供应商特性处理 headers 和 body

    DeepSeek (透传型): 剥离 headers + 移除 tool_choice + 禁用 thinking, 转发客户端 x-api-key
    Claude (独立密钥型): 仅剥离 headers, 保留 thinking, 替换为供应商自己的 api_key
    """
    forward_headers = filter_headers(request_headers) if provider.get("strip_headers") else dict(request_headers)
    for h in ("content-length", "transfer-encoding", "connection"):
        forward_headers.pop(h, None)

    # 鉴权处理: 独立密钥型供应商替换 x-api-key
    own_key = provider.get("api_key")
    if own_key:
        forward_headers["x-api-key"] = own_key

    forward_body = raw_body
    if provider.get("strip_body_fields"):
        forward_body = deepseek_filter_body(raw_body)

    if provider.get("force_model"):
        try:
            body = json.loads(forward_body)
            body["model"] = provider["force_model"]
            forward_body = json.dumps(body).encode()
        except (json.JSONDecodeError, KeyError):
            pass

    return forward_body, forward_headers


async def send_anthropic(client, provider: dict, target_url: str,
                         raw_body: bytes, request_headers: dict):
    """发送原生 Anthropic 协议请求"""
    # SSRF 校验: 确保构造的 URL 域名在白名单内
    if not _validate_upstream_url(target_url):
        raise ValueError(f"SSRF blocked: upstream URL not in whitelist ({target_url})")

    forward_body, forward_headers = prepare_anth_request(provider, raw_body, request_headers)

    resp = await client.request(
        "POST", target_url,
        content=forward_body,
        headers=forward_headers,
    )

    resp_headers = {}
    for k, v in resp.headers.items():
        lower = k.lower()
        if lower not in ("content-length", "transfer-encoding", "connection", "keep-alive"):
            resp_headers[k] = v

    if provider.get("filter_sse"):
        body_iter = filter_thinking_sse(resp)
    else:
        body_iter = resp.aiter_bytes()

    return StreamingResponse(
        body_iter,
        status_code=resp.status_code,
        headers=resp_headers,
    )


async def send_openai(client, provider: dict, anth_body: dict, model: str):
    """发送 OpenAI 协议请求——翻译 Anthropic→OpenAI, 发送, 翻译回 Anthropic"""
    target_url = provider["base_url"]
    if not _validate_upstream_url(target_url):
        raise ValueError(f"SSRF blocked: upstream URL not in whitelist ({target_url})")

    openai_body = anth_to_openai(anth_body)
    # 使用供应商的默认模型名（或保留原始模型名）
    if provider.get("default_model"):
        openai_body["model"] = provider["default_model"]

    forward_body = json.dumps(openai_body).encode()
    forward_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {provider['api_key']}",
    }

    resp = await client.request(
        "POST", provider["base_url"],
        content=forward_body,
        headers=forward_headers,
    )

    if resp.status_code == 200:
        openai_resp = json.loads(await resp.aread())
        anth_resp = openai_to_anth(openai_resp, model)
        return Response(
            json.dumps(anth_resp, ensure_ascii=False).encode(),
            status_code=200,
            media_type="application/json",
        )
    else:
        # 非 200 → 返回错误给上层回退逻辑
        error_body = await resp.aread()
        raise httpx.HTTPStatusError(
            f"{provider['name']} returned {resp.status_code}",
            request=resp.request,
            response=resp,
        )


# ═══════════════════════════════════════════════════════════════
# 核心代理 + 回退链
# ═══════════════════════════════════════════════════════════════

async def get_or_create_client():
    """创建或返回全局 httpx 客户端"""
    if not hasattr(app.state, "client") or app.state.client is None:
        app.state.client = httpx.AsyncClient(
            limits=limits, timeout=timeout, follow_redirects=False
        )
    return app.state.client


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    load_provider_keys()
    app.state.client = httpx.AsyncClient(
        limits=limits, timeout=timeout, follow_redirects=False
    )
    loaded = [n for n, p in PROVIDER_REGISTRY.items() if p.get("api_key") or p["protocol"] == "anthropic"]
    print(f"[FrontRouter] 已加载供应商: {', '.join(loaded)}")
    yield
    if app.state.client:
        await app.state.client.aclose()


def _validate_upstream_url(url: str) -> bool:
    """SSRF 防护: 验证上游 URL 的域名在白名单内"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.hostname in ALLOWED_UPSTREAM_DOMAINS
    except Exception:
        return False


def _check_rate_limit(ip: str) -> bool:
    """令牌桶速率限制, 返回 True=放行, False=限流"""
    global _rate_limit_cleanup
    now = time.time()

    # 每60秒清理一次过期条目
    if now - _rate_limit_cleanup > 60:
        stale = [k for k, v in _rate_limit_buckets.items() if now - v["last_refill"] > 120]
        for k in stale:
            del _rate_limit_buckets[k]
        _rate_limit_cleanup = now

    bucket = _rate_limit_buckets.get(ip)
    if bucket is None:
        bucket = {"tokens": RATE_LIMIT_BURST, "last_refill": now}
        _rate_limit_buckets[ip] = bucket

    elapsed = now - bucket["last_refill"]
    bucket["tokens"] = min(RATE_LIMIT_BURST, bucket["tokens"] + elapsed * RATE_LIMIT_RPS)
    bucket["last_refill"] = now

    if bucket["tokens"] >= 1.0:
        bucket["tokens"] -= 1.0
        return True
    return False


async def proxy(request: Request):
    # === 安全门1: 认证检查 (可选, 通过 FRONT_ROUTER_AUTH_KEY 启用) ===
    if FRONT_ROUTER_AUTH_KEY:
        auth_header = request.headers.get("x-api-key", "") or request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            auth_header = auth_header[7:]
        if not hmac.compare_digest(auth_header, FRONT_ROUTER_AUTH_KEY):
            return JSONResponse(
                {"error": {"type": "authentication_error", "message": "invalid or missing api key"}},
                status_code=401,
            )

    # === 安全门2: 速率限制 ===
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not _check_rate_limit(client_ip):
        return JSONResponse(
            {"error": {"type": "rate_limit_error", "message": "too many requests"}},
            status_code=429,
            headers={"Retry-After": "1"},
        )

    # === 安全门3: 请求体大小限制 ===
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_BODY_SIZE:
                return JSONResponse(
                    {"error": {"type": "invalid_request_error", "message": f"body too large, max {MAX_BODY_SIZE // 1048576}MB"}},
                    status_code=413,
                )
        except (ValueError, TypeError):
            pass  # 无效的 content-length, 由实际 body 大小检查兜底

    path = request.url.path
    method = request.method

    # === 安全门4: 路径穿越检测 (所有请求方法) ===
    if ".." in path or "//" in path:
        return JSONResponse(
            {"error": {"type": "invalid_request_error", "message": "invalid path"}},
            status_code=400,
        )

    raw_body = await request.body()

    # 二次检查: 实际读取的body大小
    if len(raw_body) > MAX_BODY_SIZE:
        return JSONResponse(
            {"error": {"type": "invalid_request_error", "message": f"body too large, max {MAX_BODY_SIZE // 1048576}MB"}},
            status_code=413,
        )

    # 非 POST 请求→直接走 DeepSeek Flash (便宜)
    if method != "POST":
        client = await get_or_create_client()
        forward_headers = filter_headers(dict(request.headers))
        try:
            upstream_resp = await client.request(
                method, f"https://api.deepseek.com/anthropic{path}",
                content=raw_body, headers=forward_headers,
            )
            return StreamingResponse(
                upstream_resp.aiter_bytes(),
                status_code=upstream_resp.status_code,
                headers={k: v for k, v in upstream_resp.headers.items()
                        if k.lower() not in ("content-length", "transfer-encoding", "connection")},
            )
        except httpx.ConnectError:
            return Response(
                b'{"error":{"type":"api_error","message":"upstream unreachable"}}',
                status_code=502, media_type="application/json",
            )

    # POST 请求: 解析 body → 复杂度检测 → 三级路由
    try:
        body = json.loads(raw_body)
    except (json.JSONDecodeError, KeyError):
        body = {"model": "", "messages": []}

    chain = get_tiered_chain(body)
    if not chain:
        return Response(
            b'{"error":{"type":"api_error","message":"no available provider"}}',
            status_code=502, media_type="application/json",
        )

    model = body.get("model", "?")
    tier = chain[0][2]  # 第一个供应商的 tier
    tier_label = {"simple": "[L1]", "medium": "[L2]", "complex": "[L3]"}
    print(f"[FrontRouter] {tier_label.get(tier, '[?]')} {tier.upper()} -> "
          f"model={model} chain={[n for n,_,_ in chain]}", flush=True)

    # 记录审计事件 (路由决策)
    _try_audit_log("route_decision", {
        "tier": tier,
        "model": model,
        "chain": [n for n, _, _ in chain],
        "msg_count": len(body.get("messages", [])),
        "tool_count": len(body.get("tools", [])),
    })

    client = await get_or_create_client()
    last_error = None
    primary_name = chain[0][0]  # 路由链的首选供应商
    used_fallback = False

    for provider_name, provider, _ in chain:
        try:
            if provider_name != primary_name:
                used_fallback = True
                # 记录回退事件
                _try_audit_log("provider_fallback", {
                    "tier": tier,
                    "primary": primary_name,
                    "fallback": provider_name,
                    "reason": str(last_error) if last_error else "unknown",
                })

            if provider["protocol"] == "anthropic":
                target_url = f"{provider['base_url']}{path}"
                resp = await send_anthropic(
                    client, provider, target_url, raw_body, dict(request.headers)
                )
                if used_fallback:
                    resp.headers["X-Front-Router-Fallback"] = "true"
                    resp.headers["X-Front-Router-Primary"] = primary_name
                    resp.headers["X-Front-Router-Actual"] = provider_name
                    print(f"[FrontRouter] [WARN] 回退模式: {primary_name}->{provider_name}", flush=True)
                return resp
            else:
                resp = await send_openai(client, provider, body, model)
                if used_fallback:
                    resp.headers["X-Front-Router-Fallback"] = "true"
                    resp.headers["X-Front-Router-Primary"] = primary_name
                    resp.headers["X-Front-Router-Actual"] = provider_name
                    print(f"[FrontRouter] [WARN] 回退模式: {primary_name}->{provider_name}", flush=True)
                return resp

        except (httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPStatusError,
                httpx.RemoteProtocolError, httpx.PoolTimeout) as e:
            last_error = e
            print(f"[FrontRouter] {provider_name} 失败→回退: {e}", flush=True)
            continue
        except Exception as e:
            last_error = e
            print(f"[FrontRouter] {provider_name} 异常→回退: {e}", flush=True)
            continue

    # 所有供应商都失败
    error_type = "all_providers_failed"
    error_msg = f"tried {len(chain)} provider(s): {[n for n, _, _ in chain]}"
    if isinstance(last_error, httpx.ConnectError):
        error_type, error_msg = "upstream_unreachable", str(last_error)
    elif isinstance(last_error, httpx.ReadTimeout):
        error_type, error_msg = "upstream_timeout", str(last_error)

    return Response(
        json.dumps({"error": {"type": error_type, "message": error_msg}}).encode(),
        status_code=502, media_type="application/json",
    )


app = Starlette(lifespan=lifespan, routes=[
    Route("/{path:path}", proxy, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]),
])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info", limit_max_requests=10000)
