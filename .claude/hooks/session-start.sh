#!/bin/bash
# SessionStart Hook — 每次会话开始时自动执行进化引擎
# 被 Claude Code 在会话启动时调用

EVOLVE_LOG=".claude/evolution/session-log.jsonl"

echo "[EVOLVE-HOOK] SessionStart 触发..."

# 战前检查
python3 self_check.py 2>&1 | tail -1

# 记录会话开始
echo "{\"event\":\"session_start\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >> "$EVOLVE_LOG"

# 静默采集上次会话后是否有未处理的学习
PENDING=$(ls .claude/evolution/learnings/ 2>/dev/null | wc -l)
if [ "$PENDING" -gt 0 ]; then
  echo "[EVOLVE-HOOK] 📝 $PENDING 条待处理的教训"
fi

echo "[EVOLVE-HOOK] 就绪"
