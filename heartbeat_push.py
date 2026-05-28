"""明鉴看门狗心跳推送 — 防止 GitHub 60天不活跃暂停 Scheduled Workflows

每日通过 GitHub API 推送看门狗健康状态，保持仓库活跃。
Token 来源优先级: GITHUB_TOKEN 环境变量 > git credential fill

用法:
  python heartbeat_push.py          # 推送健康状态
  python heartbeat_push.py --dry-run  # 仅显示将推送的内容
"""
import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from base64 import b64encode

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
HEALTH_FILE = os.path.join(REPO_ROOT, ".claude", "tracking", "watchdog-health.json")
HEARTBEAT_LOG = os.path.join(REPO_ROOT, ".claude", "tracking", "heartbeat.log")

GITHUB_OWNER = "X510959783"
GITHUB_REPO = "gas-station"
GITHUB_PATH = ".claude/tracking/watchdog-health.json"


def get_token() -> str | None:
    """获取 GitHub Token"""
    # 优先级 1: 环境变量
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token

    # 优先级 2: git credential fill
    try:
        proc = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True, text=True, timeout=10,
        )
        for line in proc.stdout.split("\n"):
            if line.startswith("password="):
                return line.split("=", 1)[1]
    except Exception:
        pass

    return None


def push_heartbeat(dry_run: bool = False) -> bool:
    """推送心跳到 GitHub"""
    token = get_token()
    if not token:
        print("[heartbeat] 无法获取 GitHub Token, 跳过推送", flush=True)
        _log("SKIP: no token")
        return False

    # 读取健康状态
    health_data = {}
    if os.path.exists(HEALTH_FILE):
        with open(HEALTH_FILE, encoding="utf-8") as f:
            health_data = json.load(f)

    health_data["_heartbeat"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    content_bytes = json.dumps(health_data, ensure_ascii=False, indent=2).encode("utf-8")
    content_b64 = b64encode(content_bytes).decode()

    if dry_run:
        print("[heartbeat dry-run] 将推送:")
        print(json.dumps(health_data, ensure_ascii=False, indent=2))
        return True

    import urllib.request
    import urllib.error

    # 获取当前文件 SHA (如果存在)
    sha = None
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "MingJian-Heartbeat/1.0")

    try:
        with urllib.request.urlopen(req) as resp:
            existing = json.loads(resp.read())
            sha = existing.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"[heartbeat] 获取文件 SHA 失败: {e.code}", flush=True)
            _log(f"ERROR: SHA fetch {e.code}")
            return False

    # PUT 更新
    body = {
        "message": "心跳: 看门狗健康状态更新",
        "content": content_b64,
        "branch": "master",
    }
    if sha:
        body["sha"] = sha

    put_req = urllib.request.Request(url, method="PUT")
    put_req.add_header("Authorization", f"token {token}")
    put_req.add_header("Accept", "application/vnd.github+json")
    put_req.add_header("X-GitHub-Api-Version", "2022-11-28")
    put_req.add_header("Content-Type", "application/json")
    put_req.add_header("User-Agent", "MingJian-Heartbeat/1.0")
    put_data = json.dumps(body).encode("utf-8")

    try:
        with urllib.request.urlopen(put_req, data=put_data) as resp:
            if resp.status in (200, 201):
                print(f"[heartbeat] 推送成功 ({resp.status})", flush=True)
                _log("OK")
                return True
            else:
                print(f"[heartbeat] 推送失败: {resp.status}", flush=True)
                _log(f"ERROR: PUT {resp.status}")
                return False
    except urllib.error.HTTPError as e:
        print(f"[heartbeat] 推送失败: {e.code} - {e.reason}", flush=True)
        _log(f"ERROR: {e.code}")
        return False


def _log(msg: str):
    """写入心跳日志"""
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(HEARTBEAT_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        pass


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    ok = push_heartbeat(dry_run=dry_run)
    sys.exit(0 if ok else 1)
