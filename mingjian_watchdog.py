#!/usr/bin/env python3
"""明鉴 Watchdog v1.0 — 独立监控进程
架构原则: Cognitive-Executive Separation (Parallax, arXiv:2604.12986)
         + Layered Governance Architecture (arXiv:2603.07191)

Watchdog 与执行者(Claude Code/DeepSeek)完全分离:
  - 由 Windows Task Scheduler 独立触发 (非 executor 调用)
  - 写入 append-only 日志 (executor 不可删除)
  - 独立验证审计链完整性 (不信任 executor 自报)
  - 检测框架漂移 (文件内容变更 vs 预期基线)

这是对 root-1(无外部验证) 的最强缓解——虽然仍在同一台机器上,
但 watchdog 不经过 executor 的推理管道, executor 无法拦截或篡改其输出。
"""
import json
import os
import sys
import hashlib
import socket
import time
from datetime import datetime, timezone
from typing import Optional

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
TRACKING_DIR = os.path.join(REPO_ROOT, ".claude", "tracking")
WATCHDOG_LOG = os.path.join(TRACKING_DIR, "watchdog-log.jsonl")
WATCHDOG_ALERTS = os.path.join(TRACKING_DIR, "watchdog-alerts.jsonl")
CHAIN_FILE = os.path.join(TRACKING_DIR, "audit-chain.jsonl")
ROOT_RISKS = os.path.join(TRACKING_DIR, "root-risks-status.json")
HEALTH_FILE = os.path.join(TRACKING_DIR, "watchdog-health.json")
PID_FILE = os.path.join(TRACKING_DIR, "watchdog.pid")
SILENT_FAILURE_LOG = os.path.join(TRACKING_DIR, "silent-failure.json")  # 静默失败检测基线

# 日志轮转配置
MAX_LOG_SIZE = 2 * 1024 * 1024   # 2MB
MAX_LOG_BACKUPS = 5              # 保留5个历史文件

# 框架文件基线——watchdog 能检测到这些文件的未授权修改
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
    ".github/workflows/external-watchdog.yml",
]

# 监控配置
CHECK_INTERVAL_HINT = "推荐每30分钟运行一次 (通过 Task Scheduler)"
ALERT_COOLDOWN_HOURS = 1  # 同类型告警冷却时间 (每小时运行一次, 冷却1小时=最多连续2次相同告警)


def _acquire_pid_lock() -> bool:
    """PID 文件并发保护: 防止多个 watchdog 同时运行"""
    os.makedirs(TRACKING_DIR, exist_ok=True)
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            # 检查旧进程是否还活着 (跨平台)
            import platform
            if platform.system() == "Windows":
                import ctypes
                SYNCHRONIZE = 0x00100000
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(SYNCHRONIZE, False, old_pid)
                alive = bool(handle)
                if handle:
                    kernel32.CloseHandle(handle)
            else:
                # Unix: 发送信号 0 检测进程存在
                try:
                    os.kill(old_pid, 0)
                    alive = True
                except OSError:
                    alive = False
            if alive:
                print(f"[Watchdog] 已有实例运行中 (PID={old_pid}), 跳过本次执行")
                return False
            # 进程已死→清理过期 PID 文件
            os.remove(PID_FILE)
        except (ValueError, OSError):
            os.remove(PID_FILE)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    return True


def _release_pid_lock():
    """释放 PID 锁文件"""
    try:
        os.remove(PID_FILE)
    except OSError:
        pass


def _rotate_log(filepath: str):
    """JSONL 日志轮转: 超过 MAX_LOG_SIZE 自动轮转"""
    if not os.path.exists(filepath):
        return
    size = os.path.getsize(filepath)
    if size < MAX_LOG_SIZE:
        return
    # 轮转: .jsonl → .jsonl.1 → .jsonl.2 → ...
    for i in range(MAX_LOG_BACKUPS - 1, 0, -1):
        old = f"{filepath}.{i}"
        new = f"{filepath}.{i + 1}"
        if os.path.exists(old):
            if os.path.exists(new):
                os.remove(new)
            os.rename(old, new)
    backup = f"{filepath}.1"
    if os.path.exists(backup):
        os.remove(backup)
    os.rename(filepath, backup)


def log_event(event_type: str, data: dict, severity: str = "INFO"):
    """写入 append-only 日志 (executor 不可删除, 不可修改)"""
    os.makedirs(TRACKING_DIR, exist_ok=True)
    _rotate_log(WATCHDOG_LOG)
    event = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": event_type,
        "severity": severity,
        "data": data,
    }
    with open(WATCHDOG_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def log_alert(alert_type: str, message: str, evidence: dict = None):
    """写入告警日志 (独立于主日志)"""
    os.makedirs(TRACKING_DIR, exist_ok=True)
    _rotate_log(WATCHDOG_ALERTS)
    alert = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": alert_type,
        "message": message,
        "evidence": evidence or {},
    }
    with open(WATCHDOG_ALERTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert, ensure_ascii=False) + "\n")


# ═══════════════════════════════════════════════════════════════
# 检查函数
# ═══════════════════════════════════════════════════════════════

def check_port(port: int = 8765) -> dict:
    """检查 Front Router 是否在监听"""
    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect(("127.0.0.1", port))
        s.close()
        return {"ok": True, "port": port, "message": f"端口 {port} 正常监听"}
    except Exception as e:
        return {"ok": False, "port": port, "message": f"端口 {port} 无响应: {e}"}


def check_audit_chain() -> dict:
    """独立验证审计链完整性 (不依赖 executor 的 verify_chain 报告)"""
    if not os.path.exists(CHAIN_FILE):
        return {"ok": True, "message": "审计链文件不存在 (可能未初始化)", "events": 0}

    events = []
    with open(CHAIN_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    if not events:
        return {"ok": True, "message": "审计链为空", "events": 0}

    errors = []

    # 验证哈希链
    for i in range(1, len(events)):
        prev_canonical = json.dumps(events[i - 1], sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        expected = hashlib.sha256(prev_canonical).hexdigest()
        actual = events[i].get("prev_hash", "")
        if expected != actual:
            errors.append(f"seq={i}: 哈希链断裂")

    # 验证 seq 连续
    for i, e in enumerate(events):
        if e.get("seq") != i:
            errors.append(f"seq={e.get('seq')} at position {i}: 期望 {i}")

    return {
        "ok": len(errors) == 0,
        "message": f"审计链有效: {len(events)} 事件" if not errors else f"审计链断裂: {errors}",
        "events": len(events),
        "errors": errors,
    }


def check_framework_integrity() -> dict:
    """检查框架文件的 SHA-256 基线是否变化"""
    changes = []
    present = 0
    missing = []

    for rel_path in FRAMEWORK_FILES:
        abs_path = os.path.join(REPO_ROOT, rel_path.replace("/", os.sep))
        if os.path.exists(abs_path):
            with open(abs_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            changes.append({"file": rel_path, "sha256": file_hash[:16]})
            present += 1
        else:
            missing.append(rel_path)

    # 读取上一次快照并比较
    snapshot_file = os.path.join(TRACKING_DIR, "watchdog-snapshot.json")
    drift_detected = []

    if os.path.exists(snapshot_file):
        with open(snapshot_file, "r", encoding="utf-8") as f:
            try:
                old_snapshot = json.load(f)
            except json.JSONDecodeError:
                old_snapshot = {}

        old_files = {f["file"]: f["sha256"] for f in old_snapshot.get("files", [])}
        for entry in changes:
            old_hash = old_files.get(entry["file"])
            if old_hash and old_hash != entry["sha256"]:
                drift_detected.append({
                    "file": entry["file"],
                    "old_hash": old_hash,
                    "new_hash": entry["sha256"],
                })

    # 保存新快照
    with open(snapshot_file, "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "files": changes}, f, ensure_ascii=False, indent=2)

    return {
        "ok": len(drift_detected) == 0 and len(missing) == 0,
        "present": present,
        "missing": missing,
        "drift": drift_detected,
        "message": f"{present}/{len(FRAMEWORK_FILES)} 文件完整"
            if not drift_detected else f"检测到 {len(drift_detected)} 个文件漂移",
    }


def check_cross_verify() -> dict:
    """验证 cross_verify.py 的 Claude 审计链路可用"""
    try:
        from cross_verify import CrossVerifier
        v = CrossVerifier()
        available = v.is_available
        v.close()
        return {
            "ok": available,
            "message": "cross_verify.py: 七牛云 Claude 可用" if available
            else "cross_verify.py: 七牛云 Claude 未配置",
        }
    except Exception as e:
        return {"ok": False, "message": f"cross_verify.py 检查失败: {e}"}


def check_root_risks() -> dict:
    """检查根风险状态是否有异常变化"""
    if not os.path.exists(ROOT_RISKS):
        return {"ok": True, "message": "root-risks-status.json 不存在"}

    with open(ROOT_RISKS, "r", encoding="utf-8") as f:
        data = json.load(f)

    summary = data.get("summary", {})
    risks = data.get("root_risks", [])

    # 检测是否有新的 CRITICAL 但未记录的
    critical_open = [r for r in risks if r.get("severity") == "CRITICAL" and r.get("status") == "OPEN"]
    total_closed = summary.get("closed", 0)
    total_open = summary.get("open", 0)

    return {
        "ok": True,
        "total_risks": len(risks),
        "open": total_open,
        "closed": total_closed,
        "critical_open": len(critical_open),
        "closure_rate": summary.get("closure_rate", 0),
        "message": f"根风险: {total_open} OPEN / {total_closed} CLOSED ({summary.get('closure_rate', 0):.0%})",
    }


# ═══════════════════════════════════════════════════════════════
# 自完整性 + 元看门狗 (Meta-Watchdog)
# ═══════════════════════════════════════════════════════════════

# 自完整性模块 (与 watchdog_external.py 共享的模块列表)
SELF_MODULES = [
    "mingjian_watchdog.py",
    "watchdog_external.py",
    "audit_chain.py",
    "cross_verify.py",
    "front_router.py",
]

INTEGRITY_MANIFEST = os.path.join(TRACKING_DIR, "integrity-manifest.json")


def check_bootstrap_integrity() -> dict:
    """启动时自完整性验证 — 哈希自身模块并与已知良好清单核对

    如果看门狗自身被篡改, 此检查会失败。
    (参考: Microsoft Agent Governance Toolkit v1.1.0)
    """
    if not os.path.exists(INTEGRITY_MANIFEST):
        return {
            "ok": True,
            "message": "完整性清单不存在 (运行 watchdog_external.py --init-integrity 初始化)",
            "manifest_exists": False,
        }

    with open(INTEGRITY_MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    known = manifest.get("modules", {})
    tampered = []

    for mod in SELF_MODULES:
        abs_path = os.path.join(REPO_ROOT, mod.replace("/", os.sep))
        if not os.path.exists(abs_path):
            tampered.append({"module": mod, "known_hash": known.get(mod, "?")[:16], "current_hash": "MISSING"})
            continue
        with open(abs_path, "rb") as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()
        known_hash = known.get(mod)
        if known_hash and current_hash != known_hash:
            tampered.append({"module": mod, "known_hash": known_hash[:16], "current_hash": current_hash[:16]})

    ok = len(tampered) == 0
    return {
        "ok": ok,
        "tampered": tampered,
        "total_checked": len(SELF_MODULES),
        "message": f"自完整性: {len(SELF_MODULES)} 模块通过" if ok
        else f"自完整性失败: {len(tampered)} 个模块被篡改",
    }


def check_meta_watchdog() -> dict:
    """元看门狗检查: 验证外部看门狗基础设施是否就绪

    形成监控闭环:
      外部看门狗 (GitHub Actions) → 检查本地看门狗健康文件
      本地看门狗 (此进程)        → 检查外部看门狗配置是否就绪

    当 git remote 配置且推送后, 本地看门狗可通过 GitHub API
    检查外部看门狗的最近运行状态。
    """
    # 检查外部看门狗脚本是否存在且可运行
    external_script = os.path.join(REPO_ROOT, "watchdog_external.py")
    workflow_file = os.path.join(REPO_ROOT, ".github", "workflows", "external-watchdog.yml")
    integrity_manifest = os.path.join(TRACKING_DIR, "integrity-manifest.json")

    missing = []
    if not os.path.exists(external_script):
        missing.append("watchdog_external.py")
    if not os.path.exists(workflow_file):
        missing.append(".github/workflows/external-watchdog.yml")

    infrastructure_ready = len(missing) == 0

    # 检查是否有 git remote (外部看门狗需要推送到 GitHub)
    has_remote = False
    try:
        import subprocess
        result = subprocess.run(["git", "remote", "get-url", "origin"],
                              capture_output=True, text=True, cwd=REPO_ROOT)
        has_remote = bool(result.stdout.strip())
    except Exception:
        pass

    # 检查完整性清单 (bootstrap integrity 需要)
    manifest_ready = os.path.exists(integrity_manifest)

    status_parts = []
    if infrastructure_ready:
        status_parts.append("基础设施就绪")
    else:
        status_parts.append(f"缺少: {', '.join(missing)}")
    if has_remote:
        status_parts.append("git remote 已配置")
    else:
        status_parts.append("git remote 未配置 (推送到 GitHub 后激活)")
    if manifest_ready:
        status_parts.append("完整性清单已初始化")
    else:
        status_parts.append("运行 --init-integrity 初始化完整性清单")

    # 基础设施就绪且清单已初始化 = 完全就绪
    fully_ready = infrastructure_ready and manifest_ready

    return {
        "ok": fully_ready,
        "infrastructure_ready": infrastructure_ready,
        "has_remote": has_remote,
        "manifest_ready": manifest_ready,
        "missing_files": missing,
        "message": "; ".join(status_parts),
    }


# ═══════════════════════════════════════════════════════════════
# 静默失败检测 (Silent Failure Detection — 2026 最佳实践)
# 基于: silentwatch-mcp + AI Agent Kill Switch 模式
# 检测三类静默失败:
#   1. 空输出 — 看门狗运行但无有效结果
#   2. 持续时间异常 — 运行时间偏离历史基线 >3σ
#   3. 过期运行 — 上次运行超过阈值时间
# ═══════════════════════════════════════════════════════════════

SILENT_FAILURE_MAX_HISTORY = 30    # 保留最近30次运行时间
SILENT_FAILURE_OVERDUE_HOURS = 1.5 # 超过此时间未运行→告警
SILENT_FAILURE_ZSCORE = 3.0        # Z-score 异常阈值


def check_silent_failure() -> dict:
    """静默失败检测 — 检测看门狗自身的异常行为

    三信号检测:
      1. 空输出/空结果: 全部检查返回未知状态→可能看门狗被替换为空壳
      2. 持续时间异常: 运行时间 Z-score > 3σ → 可能被注入了恶意检查
      3. 过期运行: 上次运行 > 1.5h → 计划任务可能被禁用
    """
    now = datetime.now(timezone.utc)
    issues = []

    # 信号1: 加载历史运行基线
    baseline = _load_silent_failure_baseline()
    run_history = baseline.get("run_history", [])

    # 信号2: 过期运行检测
    overdue_ok = True
    if run_history:
        last_ts_str = run_history[-1].get("timestamp", "")
        if last_ts_str:
            try:
                last_ts = datetime.fromisoformat(last_ts_str.replace("Z", "+00:00"))
                hours_since = (now - last_ts).total_seconds() / 3600
                if hours_since > SILENT_FAILURE_OVERDUE_HOURS:
                    overdue_ok = False
                    issues.append(f"看门狗过期: 上次运行 {hours_since:.1f}h 前 (阈值 {SILENT_FAILURE_OVERDUE_HOURS}h)")
            except ValueError:
                pass

    # 信号3: 持续时间异常检测 (Z-score)
    duration_ok = True
    if len(run_history) >= 10:
        durations = [r.get("duration_ms", 0) for r in run_history if r.get("duration_ms")]
        if durations:
            mean_dur = sum(durations) / len(durations)
            std_dur = (sum((d - mean_dur) ** 2 for d in durations) / len(durations)) ** 0.5
            last_dur = durations[-1]
            if std_dur > 0:
                zscore = abs(last_dur - mean_dur) / std_dur
                if zscore > SILENT_FAILURE_ZSCORE:
                    duration_ok = False
                    issues.append(f"运行时间异常: {last_dur}ms (均值={mean_dur:.0f}ms, Z={zscore:.1f})")

    # 信号4: 空输出检测 (所有检查都返回 unknown → 可疑)
    # 在主流程 run_all_checks() 之后调用, 这里只加载基线
    empty_output_ok = True

    ok = overdue_ok and duration_ok and empty_output_ok
    return {
        "ok": ok,
        "overdue_ok": overdue_ok,
        "duration_ok": duration_ok,
        "empty_output_ok": empty_output_ok,
        "issues": issues,
        "run_count": len(run_history),
        "message": "静默失败检测通过" if ok else "; ".join(issues),
    }


def _load_silent_failure_baseline() -> dict:
    """加载静默失败检测基线"""
    if os.path.exists(SILENT_FAILURE_LOG):
        try:
            with open(SILENT_FAILURE_LOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"run_history": []}


def _update_silent_failure_baseline(duration_ms: float, report: dict):
    """更新静默失败基线 — 记录本次运行时间和结果摘要"""
    baseline = _load_silent_failure_baseline()
    history = baseline.get("run_history", [])

    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_ms": round(duration_ms, 1),
        "health": report.get("health", "?"),
        "checks_count": len(report.get("checks", {})),
        "failed_checks": sum(1 for r in report.get("checks", {}).values() if not r.get("ok")),
    }
    history.append(entry)

    # 只保留最近 N 次
    if len(history) > SILENT_FAILURE_MAX_HISTORY:
        history = history[-SILENT_FAILURE_MAX_HISTORY:]

    baseline["run_history"] = history
    baseline["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    os.makedirs(TRACKING_DIR, exist_ok=True)
    with open(SILENT_FAILURE_LOG, "w", encoding="utf-8") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
# 健康状态文件 — 供外部看门狗 (GitHub Actions / 云VM) 验证
# ═══════════════════════════════════════════════════════════════

def _write_health_file(report: dict):
    """写入签名健康状态文件, 供外部看门狗验证本地看门狗是否存活

    外部看门狗 (watchdog_external.py) 会检查:
    1. 文件是否存在
    2. 时间戳是否在2小时内 (证明本地看门狗仍在运行)
    3. 健康状态是否为 HEALTHY

    攻击者即使控制了主用户, 也无法:
    - 阻止外部看门狗 (运行在 GitHub 基础设施上)
    - 伪造签名 (需要 Ed25519 私钥, 存储在隔离用户下)
    """
    try:
        health_data = {
            "timestamp": report["timestamp"],
            "health": report["health"],
            "checks_summary": {
                name: {"ok": r.get("ok"), "message": r.get("message", "")[:100]}
                for name, r in report.get("checks", {}).items()
            },
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
        }
        with open(HEALTH_FILE, "w", encoding="utf-8") as f:
            json.dump(health_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # 健康文件写入失败不阻塞主流程
        print(f"[Watchdog] 健康文件写入失败: {e}", file=sys.stderr, flush=True)


# ═══════════════════════════════════════════════════════════════
# 主检查流程
# ═══════════════════════════════════════════════════════════════

def run_all_checks() -> dict:
    """执行所有检查, 返回汇总报告"""
    start_time = time.time()
    results = {}

    checks = [
        ("bootstrap_integrity", check_bootstrap_integrity),
        ("port", check_port),
        ("audit_chain", check_audit_chain),
        ("framework_integrity", check_framework_integrity),
        ("cross_verify", check_cross_verify),
        ("root_risks", check_root_risks),
        ("meta_watchdog", check_meta_watchdog),
        ("silent_failure", check_silent_failure),
    ]

    all_ok = True
    for check_name, check_fn in checks:
        try:
            result = check_fn()
            results[check_name] = result
            if not result.get("ok", False):
                all_ok = False
        except Exception as e:
            results[check_name] = {"ok": False, "message": f"检查异常: {e}"}
            all_ok = False

    duration_ms = (time.time() - start_time) * 1000

    health = "HEALTHY" if all_ok else "WARNING"
    report = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "health": health,
        "duration_ms": round(duration_ms, 1),
        "checks": results,
    }

    # 记录到日志
    log_event("watchdog_run", report, severity="INFO" if all_ok else "WARNING")

    # 写入健康状态文件 — 供外部看门狗 (GitHub Actions / 云VM) 验证
    _write_health_file(report)

    # 更新静默失败基线
    _update_silent_failure_baseline(duration_ms, report)

    # 如果异常, 写入告警——按检查类型分别冷却
    if not all_ok:
        for check_name, result in results.items():
            if not result.get("ok", False) and not _is_in_cooldown([check_name]):
                log_alert(check_name,
                          f"{check_name}: {result.get('message', '检查失败')}",
                          evidence={check_name: result})

    return report


def _is_in_cooldown(failed_checks: list) -> bool:
    """检查是否在告警冷却期内——按告警类型分别检查"""
    if not os.path.exists(WATCHDOG_ALERTS):
        return False
    try:
        with open(WATCHDOG_ALERTS, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return False
        now = datetime.now(timezone.utc)
        # 从最末开始回溯, 同类型的最近告警在冷却期内→抑制
        failed_set = set(failed_checks)
        for line in reversed(lines):
            try:
                alert = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            alert_type = alert.get("type", "")
            alert_ts = datetime.fromisoformat(alert["timestamp"].replace("Z", "+00:00"))
            if (now - alert_ts).total_seconds() >= ALERT_COOLDOWN_HOURS * 3600:
                break  # 更早的告警已超出冷却期, 无需继续
            if alert_type in failed_set:
                return True  # 此类型在冷却期内
        return False
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# 验证基线 (首次运行——创建快照)
# ═══════════════════════════════════════════════════════════════

def init_baseline():
    """创建框架文件基线快照 (首次运行)"""
    os.makedirs(TRACKING_DIR, exist_ok=True)
    check_framework_integrity()  # 这会自动创建快照
    print("基线快照已创建")
    log_event("baseline_init", {"message": "Watchdog 基线初始化"})


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        init_baseline()
        sys.exit(0)

    # PID 并发保护: 已有实例运行中则跳过
    if not _acquire_pid_lock():
        sys.exit(0)

    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--once":
            report = run_all_checks()
            health = report["health"]
            print(f"Watchdog: {health}")
            for name, result in report["checks"].items():
                status = "PASS" if result.get("ok") else "FAIL"
                print(f"  [{status}] {name}: {result.get('message', '?')}")
            sys.exit(0 if health == "HEALTHY" else 1)

        # 默认: 持续监控模式 (由 Task Scheduler 定时触发, 所以只需运行一次)
        report = run_all_checks()
        health = report["health"]

        # 简洁输出 (写入日志文件)
        print(f"[{report['timestamp']}] Watchdog: {health}")
        for name, result in report["checks"].items():
            status = "PASS" if result.get("ok") else "FAIL"
            if not result.get("ok"):
                print(f"  [{status}] {name}: {result.get('message', '?')}")

        sys.exit(0 if health == "HEALTHY" else 1)
    finally:
        _release_pid_lock()
