#!/usr/bin/env python3
"""明鉴外部看门狗 v1.0 — 独立于执行者的第二台机器验证

设计原则:
  - 零密钥依赖: 仅使用公钥验证签名, 不需要私钥
  - 独立运行: 可在 GitHub Actions / 免费云VM / cron-job.org 任意环境运行
  - 验证不签名: 外部看门狗只读验证, 不写入审计链

与 mingjian_watchdog.py 的分工:
  - mingjian_watchdog.py: 本地第一层监控 (同机特权分离)
  - watchdog_external.py: 外部第二层验证 (真正的独立机器)

用法:
  python watchdog_external.py --ci          # CI 模式, JSON 输出
  python watchdog_external.py --json        # 人类可读 + JSON 摘要
  python watchdog_external.py --check-recent 2  # 检查最近2小时是否有活动
"""
import json
import os
import sys
import hashlib
from datetime import datetime, timezone
from typing import Optional

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
TRACKING_DIR = os.path.join(REPO_ROOT, ".claude", "tracking")
CHAIN_FILE = os.path.join(TRACKING_DIR, "audit-chain.jsonl")
PUBKEY_FILE = os.path.join(TRACKING_DIR, "audit-key.pub")
SNAPSHOT_FILE = os.path.join(TRACKING_DIR, "watchdog-snapshot.json")
HEALTH_FILE = os.path.join(TRACKING_DIR, "watchdog-health.json")
ROOT_RISKS = os.path.join(TRACKING_DIR, "root-risks-status.json")
INTEGRITY_MANIFEST = os.path.join(TRACKING_DIR, "integrity-manifest.json")

# 启动时自完整性验证的模块列表 (微软 Agent Governance Toolkit v1.1.0 标准)
# 这些模块在 watchdog 启动时被哈希并与已知良好清单核对
# 如果任一模块被篡改, watchdog 拒绝运行
SELF_INTEGRITY_MODULES = [
    "watchdog_external.py",
    "mingjian_watchdog.py",
    "audit_chain.py",
    "cross_verify.py",
]

# 框架文件基线
FRAMEWORK_FILES = [
    ".claude/framework-v2-minimal.md",
    ".claude/deepdig-framework-v3.2.md",
    ".claude/INSPECTION-MINGJIAN-FRAMEWORK.md",
    ".claude/INSPECTION-REPORT.md",
    "cross_verify.py",
    "audit_chain.py",
    "front_router.py",
    "mingjian_watchdog.py",
    "watchdog_external.py",
]

# Ed25519 签名验证 (纯 Python 实现, 零外部依赖)
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def load_pubkey() -> Optional[bytes]:
    """加载 Ed25519 公钥 (外部看门狗只需要公钥)"""
    if not os.path.exists(PUBKEY_FILE):
        return None
    with open(PUBKEY_FILE, "rb") as f:
        return f.read()


def read_chain() -> list:
    """读取完整审计链"""
    if not os.path.exists(CHAIN_FILE):
        return []
    events = []
    with open(CHAIN_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def canonicalize(event: dict) -> bytes:
    """JSON 规范化 (与 audit_chain.py 一致)"""
    return json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


# ═══════════════════════════════════════════════════════════════
# 启动时自完整性验证 (Bootstrap Integrity — 微软 AgentGov v1.1.0)
# ═══════════════════════════════════════════════════════════════

def compute_module_hashes() -> dict:
    """计算所有自完整性模块的 SHA-256 哈希"""
    hashes = {}
    for rel_path in SELF_INTEGRITY_MODULES:
        abs_path = os.path.join(REPO_ROOT, rel_path.replace("/", os.sep))
        if os.path.exists(abs_path):
            with open(abs_path, "rb") as f:
                hashes[rel_path] = hashlib.sha256(f.read()).hexdigest()
        else:
            hashes[rel_path] = None
    return hashes


def load_integrity_manifest() -> Optional[dict]:
    """加载已知良好的完整性清单"""
    if not os.path.exists(INTEGRITY_MANIFEST):
        return None
    with open(INTEGRITY_MANIFEST, "r", encoding="utf-8") as f:
        return json.load(f)


def save_integrity_manifest():
    """保存当前模块哈希为已知良好的完整性清单 (首次运行或手动更新)"""
    manifest = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "modules": compute_module_hashes(),
    }
    os.makedirs(TRACKING_DIR, exist_ok=True)
    with open(INTEGRITY_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest


def check_bootstrap_integrity() -> dict:
    """启动时自完整性验证 — 哈希自身模块并与已知良好清单核对

    如果 watchdog 自身被篡改, 此检查会失败。
    供应链攻击在 watchdog 执行任何策略评估之前就被检测到。
    (参考: Microsoft Agent Governance Toolkit v1.1.0)
    """
    manifest = load_integrity_manifest()
    if manifest is None:
        return {
            "ok": True,
            "message": "完整性清单不存在 (运行 --init-integrity 初始化)",
            "manifest_exists": False,
        }

    current = compute_module_hashes()
    known = manifest.get("modules", {})
    tampered = []
    missing = []
    new_modules = []

    for module, current_hash in current.items():
        known_hash = known.get(module)
        if current_hash is None:
            missing.append(module)
        elif known_hash is None:
            new_modules.append(module)
        elif current_hash != known_hash:
            tampered.append({
                "module": module,
                "known_hash": known_hash[:16],
                "current_hash": current_hash[:16] if current_hash else "MISSING",
            })

    ok = len(tampered) == 0 and len(missing) == 0
    return {
        "ok": ok,
        "tampered": tampered,
        "missing": missing,
        "new_modules": new_modules,
        "total_checked": len(current),
        "manifest_ts": manifest.get("timestamp", ""),
        "message": f"自完整性验证通过: {len(current)} 模块"
        if ok else f"检测到 {len(tampered)} 个模块被篡改, {len(missing)} 个模块缺失",
    }


def check_audit_chain_integrity() -> dict:
    """验证审计链哈希链 + Ed25519 签名 (外部独立验证)"""
    chain = read_chain()
    if not chain:
        return {"ok": True, "events": 0, "message": "审计链为空 (可能是新项目)"}

    errors = []
    pubkey = load_pubkey()

    for i, event in enumerate(chain):
        seq = event.get("seq", -1)
        if seq != i:
            errors.append(f"seq={seq} at pos={i}: 期望 {i}")

        if i > 0:
            prev_canon = canonicalize(chain[i - 1])
            expected_prev = hashlib.sha256(prev_canon).hexdigest()
            actual_prev = event.get("prev_hash", "")
            if expected_prev != actual_prev:
                errors.append(f"seq={i}: 哈希链断裂")

        if HAS_CRYPTO and pubkey:
            sig_hex = event.get("sig")
            pubkey_hex = event.get("pubkey")
            if sig_hex and pubkey_hex:
                try:
                    event_for_verify = {k: v for k, v in event.items() if k not in ("sig", "pubkey")}
                    event_bytes = canonicalize(event_for_verify)
                    pk = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubkey_hex))
                    pk.verify(bytes.fromhex(sig_hex), event_bytes)
                except Exception as e:
                    errors.append(f"seq={i}: 签名无效 ({e})")

    ok = len(errors) == 0
    return {
        "ok": ok,
        "events": len(chain),
        "errors": errors,
        "first_event_ts": chain[0].get("timestamp", "") if chain else "",
        "last_event_ts": chain[-1].get("timestamp", "") if chain else "",
        "message": f"审计链有效: {len(chain)} 事件" if ok else f"审计链断裂: {len(errors)} 处错误",
        "crypto_available": HAS_CRYPTO,
        "pubkey_available": pubkey is not None,
    }


def check_recent_activity(hours: float = 2.0) -> dict:
    """检查最近 N 小时内是否有审计事件"""
    chain = read_chain()
    if not chain:
        return {"ok": False, "message": "审计链为空, 无近期活动", "hours_threshold": hours}

    last_ts_str = chain[-1].get("timestamp", "")
    if not last_ts_str:
        return {"ok": False, "message": "最后一个事件无时间戳", "hours_threshold": hours}

    try:
        last_ts = datetime.fromisoformat(last_ts_str.replace("Z", "+00:00"))
    except ValueError:
        return {"ok": False, "message": f"时间戳解析失败: {last_ts_str}", "hours_threshold": hours}

    now = datetime.now(timezone.utc)
    delta = now - last_ts
    hours_since = delta.total_seconds() / 3600

    ok = hours_since <= hours
    return {
        "ok": ok,
        "hours_since_last_event": round(hours_since, 2),
        "hours_threshold": hours,
        "last_event_ts": last_ts_str,
        "message": f"最近活动: {hours_since:.1f}小时前 (阈值={hours}h)" if ok
        else f"无近期活动: {hours_since:.1f}小时前 > {hours}h 阈值",
    }


def check_framework_integrity() -> dict:
    """验证框架文件 SHA-256 vs 已提交基线 (不需要密钥)"""
    present = []
    missing = []
    drift_detected = []

    # 读取基线快照
    snapshot = {}
    if os.path.exists(SNAPSHOT_FILE):
        with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
            try:
                snapshot = json.load(f)
            except json.JSONDecodeError:
                pass

    old_files = {f["file"]: f["sha256"] for f in snapshot.get("files", [])}

    for rel_path in FRAMEWORK_FILES:
        abs_path = os.path.join(REPO_ROOT, rel_path.replace("/", os.sep))
        if os.path.exists(abs_path):
            with open(abs_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            present.append({"file": rel_path, "sha256": file_hash[:16]})
            old_hash = old_files.get(rel_path)
            if old_hash and old_hash != file_hash[:16]:
                drift_detected.append({
                    "file": rel_path,
                    "baseline": old_hash,
                    "current": file_hash[:16],
                })
        else:
            missing.append(rel_path)

    ok = len(drift_detected) == 0 and len(missing) == 0
    return {
        "ok": ok,
        "present": len(present),
        "total": len(FRAMEWORK_FILES),
        "missing": missing,
        "drift": drift_detected,
        "message": f"框架完整: {len(present)}/{len(FRAMEWORK_FILES)} 文件"
        if ok else f"异常: {len(missing)} 缺失, {len(drift_detected)} 漂移",
    }


def check_health_file() -> dict:
    """验证本地看门狗健康状态文件的时效性"""
    if not os.path.exists(HEALTH_FILE):
        return {"ok": False, "message": "健康状态文件不存在 (本地看门狗可能未运行)"}

    try:
        with open(HEALTH_FILE, "r", encoding="utf-8") as f:
            health = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return {"ok": False, "message": f"健康文件读取失败: {e}"}

    ts_str = health.get("timestamp", "")
    if not ts_str:
        return {"ok": False, "message": "健康文件无时间戳"}

    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        return {"ok": False, "message": f"健康文件时间戳无效: {ts_str}"}

    now = datetime.now(timezone.utc)
    hours_since = (now - ts).total_seconds() / 3600

    # 告警阈值: 最近2小时内必须有本地看门狗运行
    ok = hours_since <= 2.0
    return {
        "ok": ok,
        "hours_since": round(hours_since, 2),
        "health_status": health.get("health", "UNKNOWN"),
        "last_watchdog_run": ts_str,
        "message": f"本地看门狗健康: {health.get('health')} ({hours_since:.1f}h前)"
        if ok else f"本地看门狗过期: {hours_since:.1f}h前 > 2h阈值",
    }


def check_root_risks_closure() -> dict:
    """检查根风险关闭率"""
    if not os.path.exists(ROOT_RISKS):
        return {"ok": True, "message": "根风险文件不存在", "closure_rate": None}

    with open(ROOT_RISKS, "r", encoding="utf-8") as f:
        data = json.load(f)

    summary = data.get("summary", {})
    total_open = summary.get("open", 0)
    total_closed = summary.get("closed", 0)
    closure_rate = summary.get("closure_rate", 0)

    # 告警: 打开的风险数 > 5
    ok = total_open <= 5
    return {
        "ok": ok,
        "open": total_open,
        "closed": total_closed,
        "closure_rate": closure_rate,
        "message": f"根风险: {total_open} OPEN / {total_closed} CLOSED ({closure_rate:.0%})"
        if ok else f"打开的风险过多: {total_open} > 5",
    }


def run_all_checks(hours_threshold: float = 2.0) -> dict:
    """执行所有外部验证"""
    # 首先执行自完整性验证 (必须在其他检查之前)
    bootstrap = check_bootstrap_integrity()

    checks = {
        "bootstrap_integrity": bootstrap,
        "audit_chain": check_audit_chain_integrity(),
        "recent_activity": check_recent_activity(hours_threshold),
        "framework_integrity": check_framework_integrity(),
        "health_file": check_health_file(),
        "root_risks": check_root_risks_closure(),
    }

    all_ok = all(v.get("ok", False) for v in checks.values())
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "health": "HEALTHY" if all_ok else "WARNING",
        "watchdog_type": "external",
        "runner": os.environ.get("GITHUB_RUN_ID", socket.gethostname() if "socket" in dir() else "unknown"),
        "checks": checks,
    }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import socket  # noqa: E402

    if "--ci" in sys.argv:
        # CI 模式: JSON 一行输出
        report = run_all_checks()
        print(json.dumps(report, ensure_ascii=False))
        sys.exit(0 if report["health"] == "HEALTHY" else 1)

    if "--json" in sys.argv:
        report = run_all_checks()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(0 if report["health"] == "HEALTHY" else 1)

    if "--check-recent" in sys.argv:
        hours = float(sys.argv[sys.argv.index("--check-recent") + 1]) if len(sys.argv) > sys.argv.index("--check-recent") + 1 else 2.0
        result = check_recent_activity(hours)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["ok"] else 1)

    if "--init-integrity" in sys.argv:
        manifest = save_integrity_manifest()
        print(f"完整性清单已初始化: {len(manifest['modules'])} 个模块")
        for m, h in manifest["modules"].items():
            print(f"  {m}: {h[:16]}...")
        sys.exit(0)

    # 默认: 人类可读输出
    report = run_all_checks()
    print(f"[{report['timestamp']}] 外部看门狗: {report['health']}")
    print(f"  运行者: {report['runner']}")
    for name, result in report["checks"].items():
        status = "PASS" if result.get("ok") else "FAIL"
        print(f"  [{status}] {name}: {result.get('message', '?')}")
        if not result.get("ok"):
            errors = result.get("errors", [])
            for err in errors[:5]:
                print(f"    - {err}")
            drift = result.get("drift", [])
            for d in drift:
                print(f"    DRIFT: {d['file']} ({d['baseline']} → {d['current']})")

    sys.exit(0 if report["health"] == "HEALTHY" else 1)
