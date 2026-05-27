#!/bin/bash
# 明鉴框架 — SessionStart 自动化健康检查
# 每次会话开始时自动运行
# 解决: "执行率自监控本身不被监控"——递归监控通过外部触发打破

HEALTH_FILE=".claude/tracking/root-risks-status.json"
FRAMEWORK_DIR=".claude"
WARN_DAYS=7
CRITICAL_DAYS=14

echo "[明鉴] SessionStart 健康检查..."

# 1. 追踪文件是否存在？
if [ ! -f "$HEALTH_FILE" ]; then
  echo "[明鉴] ⚠️ CRITICAL: 追踪文件缺失——框架可能从未被执行"
  echo "[明鉴] 行动: 立即检查框架状态"
fi

# 2. 追踪文件最后更新时间
if [ -f "$HEALTH_FILE" ]; then
  LAST_UPDATE=$(stat -c "%Y" "$HEALTH_FILE" 2>/dev/null || echo 0)
  NOW=$(date +%s)
  DAYS_SINCE=$(( (NOW - LAST_UPDATE) / 86400 ))

  if [ "$DAYS_SINCE" -gt "$CRITICAL_DAYS" ]; then
    echo "[明鉴] 🔴 CRITICAL: 追踪文件${DAYS_SINCE}天未更新——框架可能已废弃"
  elif [ "$DAYS_SINCE" -gt "$WARN_DAYS" ]; then
    echo "[明鉴] 🟡 WARNING: 追踪文件${DAYS_SINCE}天未更新——检查执行状态"
  else
    echo "[明鉴] 🟢 健康: 追踪文件${DAYS_SINCE}天前更新"
  fi
fi

# 3. 框架文件git状态——是否有未追踪的修改？
UNTRACKED=$(git ls-files --others --exclude-standard "$FRAMEWORK_DIR/"*.md 2>/dev/null | wc -l)
if [ "$UNTRACKED" -gt 0 ]; then
  echo "[明鉴] 🟡 WARNING: ${UNTRACKED}个未追踪的框架文件变更"
fi

# 4. CLAUDE.md是否引用了已废弃的检查机制？
if grep -q "self_check.py 41" CLAUDE.md 2>/dev/null; then
  echo "[明鉴] 🔴 CRITICAL: CLAUDE.md仍引用已归档的self_check.py——需要更新"
fi
if grep -q "四层进化防御" CLAUDE.md 2>/dev/null; then
  echo "[明鉴] 🔴 CRITICAL: CLAUDE.md仍包含旧'四层进化防御'——需要更新"
fi

# 5. 模块文件是否存在？
for mod in "framework-v2-minimal.md" "deepdig-framework-v3.2.md" "INSPECTION-REPORT.md" "INSPECTION-MINGJIAN-FRAMEWORK.md"; do
  if [ ! -f "$FRAMEWORK_DIR/$mod" ]; then
    echo "[明鉴] 🔴 CRITICAL: 模块缺失: $mod"
  fi
done

# 6. "无告警也是告警"——写入时间戳文件证明Hook曾运行
HOOK_LOG=".claude/tracking/.last-health-check"
mkdir -p "$(dirname "$HOOK_LOG")"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) HEALTH_CHECK_PASSED" > "$HOOK_LOG"
echo "[明鉴] 健康检查时间戳已写入: $HOOK_LOG"

echo "[明鉴] 健康检查完毕"
