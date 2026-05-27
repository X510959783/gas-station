#!/bin/bash
# ============================================
# 自主进化执行引擎
# 每次会话关键节点自动触发
# ============================================

set -e
EVOLVE_DIR=".claude/evolution"
mkdir -p "$EVOLVE_DIR/snapshots" "$EVOLVE_DIR/metrics" "$EVOLVE_DIR/learnings"

# === 阶段 1: 战前检查 (PRE-FLIGHT) ===
preflight() {
  echo "[EVOLVE] PRE-FLIGHT 检查..."

  # 1.1 验证环境
  python3 self_check.py 2>&1 | tail -3

  # 1.2 检查是否有未处理的 issue
  OPEN_ISSUES=$(grep -c "进行中" issues-tracker.md 2>/dev/null || echo "0")
  if [ "$OPEN_ISSUES" -gt 0 ]; then
    echo "  ⚠️  $OPEN_ISSUES 条未解决问题"
  fi

  # 1.3 检查记忆索引完整性
  if [ -f "C:/Users/51095/.claude/projects/d--gas-station/memory/MEMORY.md" ]; then
    MEM_COUNT=$(grep -c "\- \[" "C:/Users/51095/.claude/projects/d--gas-station/memory/MEMORY.md" 2>/dev/null || echo "0")
    echo "  📝 记忆索引: $MEM_COUNT 条"
  fi

  echo "[EVOLVE] PRE-FLIGHT 完成"
}

# === 阶段 2: 行为快照 (SNAPSHOT) ===
snapshot() {
  TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
  SNAP="$EVOLVE_DIR/snapshots/$TIMESTAMP.md"

  echo "# 进化快照 $TIMESTAMP" > "$SNAP"
  echo "" >> "$SNAP"
  echo "## 当前状态" >> "$SNAP"
  echo "- Skill 总数: $(ls .claude/skills/ 2>/dev/null | grep -v 'everything-claude-code\|skills-lock.json' | wc -l)" >> "$SNAP"
  echo "- Agent 总数: $(ls .claude/agents/ 2>/dev/null | wc -l)" >> "$SNAP"
  echo "- Memory 数: $(ls 'C:/Users/51095/.claude/projects/d--gas-station/memory/'*.md 2>/dev/null | wc -l)" >> "$SNAP"
  echo "- 数据库场次: $(python3 -c "import json; d=json.load(open('match-db.json')); print(len(d.get('matches',[])))" 2>/dev/null || echo "?")" >> "$SNAP"

  echo "[EVOLVE] 快照已保存: $SNAP"
}

# === 阶段 3: 学到的教训 (LEARN) ===
learn() {
  local lesson="$1"
  local category="${2:-feedback}"
  TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)

  LEARN_FILE="$EVOLVE_DIR/learnings/$TIMESTAMP.md"
  echo "---" > "$LEARN_FILE"
  echo "date: $(date +%Y-%m-%d)" >> "$LEARN_FILE"
  echo "category: $category" >> "$LEARN_FILE"
  echo "---" >> "$LEARN_FILE"
  echo "" >> "$LEARN_FILE"
  echo "$lesson" >> "$LEARN_FILE"

  echo "[EVOLVE] 教训已记录: $LEARN_FILE"
}

# === 阶段 4: 进化度量 (METRICS) ===
metrics() {
  METRIC_FILE="$EVOLVE_DIR/metrics/$(date +%Y-%m-%d).json"

  # 统计今天的通过/失败
  SELF_CHECK_PASS=$(python3 self_check.py 2>&1 | grep "通过" | grep -oP '\d+' | head -1)

  cat > "$METRIC_FILE" << EOF
{
  "date": "$(date +%Y-%m-%d)",
  "timestamp": "$(date +%Y-%m-%dT%H:%M:%S)",
  "self_check_passes": $SELF_CHECK_PASS,
  "skills_total": $(ls .claude/skills/ 2>/dev/null | grep -v 'everything-claude-code\|skills-lock.json' | wc -l),
  "memories_total": $(ls 'C:/Users/51095/.claude/projects/d--gas-station/memory/'*.md 2>/dev/null | wc -l)
}
EOF
  echo "[EVOLVE] 度量已记录: $METRIC_FILE"
}

# === 主入口 ===
case "${1:-preflight}" in
  preflight) preflight ;;
  snapshot)  snapshot ;;
  learn)     learn "$2" "$3" ;;
  metrics)   metrics ;;
  all)       preflight && snapshot && metrics ;;
  *)         echo "用法: evolve.sh {preflight|snapshot|learn|metrics|all}" ;;
esac
