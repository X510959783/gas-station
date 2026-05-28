#!/usr/bin/env python3
"""明鉴审计链 v1.0 — Ed25519签名 + SHA-256哈希链 + 离线验证
基于: Signet v0.10 + GuardClaw GEF-SPEC-1.0 + IETF SPICE draft
符合: EU AI Act Article 12 (2026-08-02) 防篡改日志要求

用法:
  python audit_chain.py init          # 生成密钥对
  python audit_chain.py sign <json>   # 签名并追加事件
  python audit_chain.py verify        # 验证完整链路
"""
import json
import os
import sys
import hashlib
import time
import random
import contextlib
from datetime import datetime, timezone
from typing import Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
TRACKING_DIR = os.path.join(REPO_ROOT, ".claude", "tracking")
KEY_FILE = os.path.join(TRACKING_DIR, "audit-key.secret")      # Ed25519 种子(私密)
PUBKEY_FILE = os.path.join(TRACKING_DIR, "audit-key.pub")       # 公钥(可分发)
CHAIN_FILE = os.path.join(TRACKING_DIR, "audit-chain.jsonl")    # 事件链

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


# ═══════════════════════════════════════════════════════════════
# 密钥管理
# ═══════════════════════════════════════════════════════════════

def generate_keypair() -> Tuple[bytes, bytes]:
    """生成 Ed25519 密钥对 → (seed_32bytes, pubkey_32bytes)"""
    if not HAS_CRYPTO:
        raise RuntimeError("需要安装 cryptography 库: pip install cryptography")
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    seed = private_key.private_bytes_raw()
    pubkey = public_key.public_bytes_raw()
    return seed, pubkey


def init_keys(force: bool = False):
    """初始化密钥对——如果已存在则跳过(除非force=True)"""
    os.makedirs(TRACKING_DIR, exist_ok=True)

    if not force and os.path.exists(KEY_FILE) and os.path.exists(PUBKEY_FILE):
        print(f"密钥对已存在: {PUBKEY_FILE}")
        with open(PUBKEY_FILE, "rb") as f:
            print(f"公钥 SHA-256: {hashlib.sha256(f.read()).hexdigest()[:16]}...")
        return

    seed, pubkey = generate_keypair()
    with open(KEY_FILE, "wb") as f:
        f.write(seed)
    with open(PUBKEY_FILE, "wb") as f:
        f.write(pubkey)
    os.chmod(KEY_FILE, 0o600)  # 仅 owner 可读写
    print(f"密钥对已生成: {PUBKEY_FILE}")
    print(f"公钥 SHA-256: {hashlib.sha256(pubkey).hexdigest()[:16]}...")


# 密钥内存缓存——避免 sign_event 每次读取文件
_KEY_CACHE: Optional[Tuple[bytes, bytes]] = None


def load_keys() -> Tuple[bytes, bytes]:
    """加载密钥对 → (seed, pubkey) — 首次读取后缓存到内存"""
    global _KEY_CACHE
    if _KEY_CACHE is not None:
        return _KEY_CACHE
    with open(KEY_FILE, "rb") as f:
        seed = f.read()
    with open(PUBKEY_FILE, "rb") as f:
        pubkey = f.read()
    _KEY_CACHE = (seed, pubkey)
    return seed, pubkey


# ═══════════════════════════════════════════════════════════════
# 签名与链式追加
# ═══════════════════════════════════════════════════════════════

def canonicalize(event: dict) -> bytes:
    """JSON 规范化 (RFC 8785 JCS — 简化的确定性编码)"""
    return json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def read_chain() -> list:
    """读取完整事件链"""
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


def _read_last_event() -> Optional[dict]:
    """O(1) 读取链上最后一个事件——避免读取整个文件"""
    if not os.path.exists(CHAIN_FILE):
        return None
    try:
        with open(CHAIN_FILE, "rb") as f:
            if os.path.getsize(CHAIN_FILE) < 2:
                return None
            # 从文件末尾向前搜索最后一个完整 JSON 行
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            # 最多回溯 8KB 找最后一行
            pos = max(0, file_size - 8192)
            f.seek(pos)
            tail = f.read().decode("utf-8", errors="replace")
            lines = tail.strip().split("\n")
            # 取最后一个非空行
            for line in reversed(lines):
                line = line.strip()
                if line:
                    return json.loads(line)
        return None
    except (OSError, json.JSONDecodeError):
        return None


CHAIN_LOCK = os.path.join(TRACKING_DIR, ".audit-chain.lock")
LOCK_TIMEOUT = 5.0  # 获取锁超时 (秒)
LOCK_RETRY_DELAY = 0.05


@contextlib.contextmanager
def _file_lock(lock_path: str, timeout: float = LOCK_TIMEOUT):
    """跨平台文件锁 — 原子创建锁文件, 超时则抛出 TimeoutError"""
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o644)
            break
        except FileExistsError:
            if time.time() > deadline:
                raise TimeoutError(f"无法获取审计链锁: {lock_path}")
            # 随机抖动避免惊群效应
            time.sleep(LOCK_RETRY_DELAY * (0.5 + random.random()))
    try:
        yield
    finally:
        os.close(fd)
        try:
            os.unlink(lock_path)
        except OSError:
            pass


def sign_event(event_type: str, data: dict, signer: str = "claude-code") -> dict:
    """签名一个事件并追加到审计链 (带文件锁防 TOCTOU 竞态)

    Args:
        event_type: 事件类型 (tool_call / framework_edit / model_switch / health_check / ...)
        data: 事件负载
        signer: 签名者标识

    Returns:
        签名后的事件记录(已写入链)
    """
    seed, pubkey = load_keys()

    with _file_lock(CHAIN_LOCK):
        # O(1) 读取最后事件 (不读整个链)
        last = _read_last_event()

        # 前驱哈希: 链上最后一个事件的 SHA-256
        prev_hash = ""
        seq = 0
        if last:
            prev_event = canonicalize(last)
            prev_hash = hashlib.sha256(prev_event).hexdigest()
            seq = last.get("seq", 0) + 1

        # 构建事件
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        event = {
            "seq": seq,
            "timestamp": ts,
            "type": event_type,
            "signer": signer,
            "data": data,
            "prev_hash": prev_hash,
        }

        # Ed25519 签名
        event_bytes = canonicalize(event)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
        signature = private_key.sign(event_bytes)

        # 追加签名和公钥到记录
        event["sig"] = signature.hex()
        event["pubkey"] = pubkey.hex()

        # 追加到链
        with open(CHAIN_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event


def verify_chain(strict: bool = True) -> dict:
    """验证完整审计链

    Returns:
        {"valid": bool, "total": int, "errors": [str], "first_broken": int|None}
    """
    chain = read_chain()
    if not chain:
        return {"valid": True, "total": 0, "errors": [], "first_broken": None}

    errors = []
    first_broken = None

    for i, event in enumerate(chain):
        # 1. 验证 seq 连续
        if event.get("seq") != i:
            errors.append(f"seq={event.get('seq')} at position {i}: expected {i}")
            if first_broken is None:
                first_broken = i

        # 2. 验证 prev_hash 链接
        if i > 0:
            prev_event = canonicalize(chain[i - 1])
            expected_prev = hashlib.sha256(prev_event).hexdigest()
            actual_prev = event.get("prev_hash", "")
            if expected_prev != actual_prev:
                errors.append(f"seq={i}: prev_hash broken")
                if first_broken is None:
                    first_broken = i

        # 3. 验证 Ed25519 签名
        try:
            sig_hex = event.pop("sig", None)
            pubkey_hex = event.pop("pubkey", None)
            if sig_hex and pubkey_hex:
                event_bytes = canonicalize(event)
                pubkey = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubkey_hex))
                pubkey.verify(bytes.fromhex(sig_hex), event_bytes)
            elif strict:
                errors.append(f"seq={i}: missing signature")
                if first_broken is None:
                    first_broken = i
        except Exception as e:
            errors.append(f"seq={i}: signature invalid ({e})")
            if first_broken is None:
                first_broken = i
        finally:
            event["sig"] = sig_hex
            event["pubkey"] = pubkey_hex

    return {
        "valid": len(errors) == 0,
        "total": len(chain),
        "errors": errors,
        "first_broken": first_broken,
    }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_init():
    """初始化审计链基础设施"""
    os.makedirs(TRACKING_DIR, exist_ok=True)
    if not HAS_CRYPTO:
        print("需要安装 cryptography: pip install cryptography")
        sys.exit(1)
    init_keys()
    if not os.path.exists(CHAIN_FILE):
        # 写入创世事件
        sign_event("genesis", {
            "description": "明鉴审计链创世事件",
            "version": "1.0",
            "spec": "Ed25519 + SHA-256 + RFC 8785 JCS",
            "compliance": "EU AI Act Article 12 (2026-08-02)",
        })
        print("创世事件已写入审计链")
    # 验证
    result = verify_chain()
    if result["valid"]:
        print(f"审计链验证通过: {result['total']} 个事件")
    else:
        print(f"审计链验证失败: {result['errors']}")


def cmd_sign():
    """从 stdin 读取 JSON 并签名追加"""
    data_str = sys.stdin.read()
    try:
        data = json.loads(data_str)
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        sys.exit(1)

    event_type = data.pop("_type", "generic")
    signer = data.pop("_signer", "claude-code")
    event = sign_event(event_type, data, signer)
    print(json.dumps(event, ensure_ascii=False, indent=2))


def cmd_verify():
    """验证审计链完整性"""
    result = verify_chain()
    if result["valid"]:
        print(f"VALID: {result['total']} events, 0 errors")
    else:
        print(f"INVALID: {result['total']} events, {len(result['errors'])} errors")
        for err in result["errors"][:10]:
            print(f"  - {err}")
        if result["first_broken"] is not None:
            print(f"  首个断点: seq={result['first_broken']}")
    sys.exit(0 if result["valid"] else 1)


def cmd_stats():
    """审计链统计"""
    chain = read_chain()
    if not chain:
        print("审计链为空")
        return

    types = {}
    for e in chain:
        t = e.get("type", "unknown")
        types[t] = types.get(t, 0) + 1

    first_ts = chain[0].get("timestamp", "?")
    last_ts = chain[-1].get("timestamp", "?")
    print(f"事件总数: {len(chain)}")
    print(f"时间跨度: {first_ts} → {last_ts}")
    print(f"事件类型分布:")
    for t, c in sorted(types.items()):
        print(f"  {t}: {c}")
    print(f"最后事件: {json.dumps(chain[-1], ensure_ascii=False)[:200]}...")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python audit_chain.py [init|sign|verify|stats]")
        print("  init   - 生成密钥对+创世事件")
        print("  sign   - 从stdin读取JSON签名追加 (echo '{\"_type\":\"test\"}' | python audit_chain.py sign)")
        print("  verify - 验证完整审计链")
        print("  stats  - 审计链统计")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "init":
        cmd_init()
    elif cmd == "sign":
        cmd_sign()
    elif cmd == "verify":
        cmd_verify()
    elif cmd == "stats":
        cmd_stats()
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)
