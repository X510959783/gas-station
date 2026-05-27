#!/bin/bash
# 明鉴框架 — SessionStart 自动化健康检查 v1.1
# 修复: 相对路径→绝对路径, stat兼容性, git缺失处理, 编码安全

# === 确定repo根目录（解决Bug1: 相对路径） ===
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT" || { echo "[明鉴] FATAL: 无法进入仓库根目录"; exit 1; }

HEALTH_FILE=".claude/tracking/root-risks-status.json"
FRAMEWORK_DIR=".claude"
WARN_DAYS=7
CRITICAL_DAYS=14

echo "[明鉴] SessionStart 健康检查... (repo: $REPO_ROOT)"

# === 0. 自检——Hook本身是否完好？ ===
if [ ! -f ".claude/hooks/mingjian-health-check.sh" ]; then
  echo "[明鉴] FATAL: Hook脚本自身缺失——L1防线已失效"
fi

# === 1. 追踪文件是否存在？ ===
if [ ! -f "$HEALTH_FILE" ]; then
  echo "[明鉴] CRITICAL: 追踪文件缺失——框架可能从未被执行"
fi

# === 2. 追踪文件最后更新时间（解决Bug2: stat兼容性） ===
if [ -f "$HEALTH_FILE" ]; then
  # GNU stat (Linux/Windows-MSYS2): stat -c %Y
  # BSD stat (macOS): stat -f %m
  if stat -c "%Y" "$HEALTH_FILE" 2>/dev/null; then
    LAST_UPDATE=$(stat -c "%Y" "$HEALTH_FILE" 2>/dev/null)
  elif stat -f "%m" "$HEALTH_FILE" 2>/dev/null; then
    LAST_UPDATE=$(stat -f "%m" "$HEALTH_FILE" 2>/dev/null)
  else
    LAST_UPDATE=0
  fi

  if [ "$LAST_UPDATE" != "0" ]; then
    NOW=$(date +%s 2>/dev/null || echo 0)
    if [ "$NOW" != "0" ]; then
      DAYS_SINCE=$(( (NOW - LAST_UPDATE) / 86400 ))
      if [ "$DAYS_SINCE" -gt "$CRITICAL_DAYS" ]; then
        echo "[明鉴] CRITICAL: 追踪文件${DAYS_SINCE}天未更新"
      elif [ "$DAYS_SINCE" -gt "$WARN_DAYS" ]; then
        echo "[明鉴] WARNING: 追踪文件${DAYS_SINCE}天未更新"
      else
        echo "[明鉴] HEALTHY: 追踪文件${DAYS_SINCE}天前更新"
      fi
    fi
  fi
fi

# === 3. 框架文件git状态（解决Bug3: git缺失处理） ===
if command -v git >/dev/null 2>&1; then
  UNTRACKED=$(git ls-files --others --exclude-standard "$FRAMEWORK_DIR/"*.md 2>/dev/null | wc -l)
  if [ "$UNTRACKED" -gt 0 ]; then
    echo "[明鉴] WARNING: ${UNTRACKED}个未追踪的框架文件变更"
  fi
else
  echo "[明鉴] WARNING: git不可用——跳过git状态检查"
fi

# === 4. CLAUDE.md引用检查 ===
if [ -f "CLAUDE.md" ]; then
  if grep -q "self_check.py 41" CLAUDE.md 2>/dev/null; then
    echo "[明鉴] CRITICAL: CLAUDE.md引用已归档的self_check.py"
  fi
  if grep -q "四层进化防御" CLAUDE.md 2>/dev/null; then
    echo "[明鉴] CRITICAL: CLAUDE.md含旧四层进化防御"
  fi
fi

# === 5. 模块文件完整性 ===
for mod in "framework-v2-minimal.md" "deepdig-framework-v3.2.md" "INSPECTION-REPORT.md" "INSPECTION-MINGJIAN-FRAMEWORK.md"; do
  if [ ! -f "$FRAMEWORK_DIR/$mod" ]; then
    echo "[明鉴] CRITICAL: 模块缺失: $mod"
  fi
done

# === 6. 写入时间戳（证明Hook曾运行） ===
HOOK_LOG=".claude/tracking/.last-health-check"
mkdir -p "$(dirname "$HOOK_LOG")" 2>/dev/null
date -u +"%Y-%m-%dT%H:%M:%SZ" > "$HOOK_LOG" 2>/dev/null || \
  date +"%Y-%m-%dT%H:%M:%SZ" > "$HOOK_LOG" 2>/dev/null || \
  echo "TIMESTAMP_UNAVAILABLE" > "$HOOK_LOG"
echo "[明鉴] 健康检查时间戳: $(cat "$HOOK_LOG")"

echo "[明鉴] 健康检查完毕"
