#!/bin/bash
# ============================================
# Dreaming 梦境引擎
# 基于 Anthropic Dreaming (May 2026) + OpenCLAW Nightly Pipeline
# 用法: bash dream.sh [--auto]
# ============================================

set -e
MEMORY_ROOT="C:/Users/51095/.claude/projects/d--gas-station/memory"
DREAM_LOG=".claude/evolution/dream-log.jsonl"
mkdir -p ".claude/evolution"

echo "========================================"
echo "  🧠 Dreaming 梦境引擎"
echo "========================================"

# === Phase 1: SCAN (正则提取纠正信号) ===
echo ""; echo "--- Phase 1: 扫描纠正信号 ---"

SIGNALS=0
declare -A CORRECTIONS

scan_signals() {
  # 扫描 evolution/learnings/ 中的教训
  for f in .claude/evolution/learnings/*.md; do
    [ -f "$f" ] || continue
    content=$(cat "$f" 2>/dev/null)

    # 纠正信号模式 (OpenCLAW-inspired)
    patterns=(
      "用户指出"
      "纠正"
      "错了"
      "不应该"
      "禁止"
      "必须"
      "不再重复"
      "关键教训"
      "根因"
      "缺陷"
    )

    for pattern in "${patterns[@]}"; do
      if echo "$content" | grep -q "$pattern"; then
        SIGNALS=$((SIGNALS + 1))
        break
      fi
    done
  done

  echo "  📊 扫描到 $SIGNALS 个纠正信号 (来自 $(ls .claude/evolution/learnings/*.md 2>/dev/null | wc -l) 条教训)"
}

scan_signals

# === Phase 2: MERGE (合并去重) ===
echo ""; echo "--- Phase 2: 合并去重 ---"

MERGED=0
merge_memories() {
  # 检查是否有重叠主题的记忆文件
  local files=$(ls "$MEMORY_ROOT/"*.md 2>/dev/null | grep -v MEMORY.md)

  for f in $files; do
    basename_f=$(basename "$f" .md)
    # 检查是否有相似名称的文件(如 feedback_no_guessing vs feedback_certain_answers)
    # 这里做简单的关键词重叠检测
    for g in $files; do
      [ "$f" = "$g" ] && continue
      basename_g=$(basename "$g" .md)

      # 如果两个文件名共享至少2个关键词，标记为候选合并
      common=$(echo "$basename_f $basename_g" | tr '_' ' ' | tr ' ' '\n' | sort | uniq -d | wc -l)
      if [ "$common" -ge 2 ]; then
        echo "  🔗 候选合并: $basename_f ↔ $basename_g (共同词: $common)"
        MERGED=$((MERGED + 1))
      fi
    done
  done

  echo "  📝 发现 $MERGED 组候选合并"
}

merge_memories

# === Phase 3: STALE (清理过期) ===
echo ""; echo "--- Phase 3: 过期检测 ---"

STALE=0
check_stale() {
  local cutoff=$(date -d "30 days ago" +%s 2>/dev/null || echo 0)

  for f in "$MEMORY_ROOT/"*.md; do
    [ -f "$f" ] || continue
    # 检查是否有日期引用
    if grep -q "202[56]-" "$f" 2>/dev/null; then
      dates=$(grep -oP "202[56]-\d{2}-\d{2}" "$f" 2>/dev/null | sort -u)
      latest=$(echo "$dates" | tail -1)
      if [ -n "$latest" ] && [ "$cutoff" != "0" ]; then
        latest_ts=$(date -d "$latest" +%s 2>/dev/null || echo 0)
        if [ "$latest_ts" -lt "$cutoff" ] && [ "$latest_ts" != "0" ]; then
          echo "  ⚠️  可能过期: $(basename $f) (最新日期: $latest)"
          STALE=$((STALE + 1))
        fi
      fi
    fi
  done

  echo "  📅 检测到 $STALE 条可能过期的记忆"
}

check_stale

# === Phase 4: PATTERN (模式发现) ===
echo ""; echo "--- Phase 4: 模式发现 ---"

PATTERNS=0
discover_patterns() {
  # 从所有教训中提取共同主题
  local themes=()

  for f in .claude/evolution/learnings/*.md; do
    [ -f "$f" ] || continue
    content=$(cat "$f" 2>/dev/null)

    # 检测常见模式
    [[ "$content" =~ 验证 ]] && themes+=("verification:需要强验证机制") && PATTERNS=$((PATTERNS + 1))
    [[ "$content" =~ 记忆 ]] && themes+=("memory:记忆管理需改进") && PATTERNS=$((PATTERNS + 1))
    [[ "$content" =~ 上下文 ]] && themes+=("context:上下文压力管理") && PATTERNS=$((PATTERNS + 1))
    [[ "$content" =~ skill ]] && themes+=("skill:skill发现/安装/审查") && PATTERNS=$((PATTERNS + 1))
  done

  # 去重并展示
  echo "  🔍 发现的模式:"
  printf '%s\n' "${themes[@]}" | sort -u | head -10 | while read line; do
    echo "    - $line"
  done
}

discover_patterns

# === Phase 5: REPORT (梦境报告) ===
echo ""; echo "--- Phase 5: 梦境报告 ---"

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
REPORT=".claude/evolution/dream-report-$(date +%Y-%m-%d).md"

cat > "$REPORT" << EOF
# Dream Report $(date +%Y-%m-%d)

- **时间**: $TIMESTAMP
- **纠正信号**: $SIGNALS 个
- **候选合并**: $MERGED 组
- **可能过期**: $STALE 条
- **发现模式**: $PATTERNS 个

## 建议动作
EOF

# 自动建议
[ $SIGNALS -gt 0 ] && echo "- [ ] 审查 $SIGNALS 个纠正信号，考虑升级为规则" >> "$REPORT"
[ $MERGED -gt 0 ] && echo "- [ ] 合并 $MERGED 组重叠记忆" >> "$REPORT"
[ $STALE -gt 0 ] && echo "- [ ] 清理 $STALE 条过期记忆" >> "$REPORT"

echo ""
echo "  📄 报告已保存: $REPORT"

# 记录到梦境日志
echo "{\"timestamp\":\"$TIMESTAMP\",\"signals\":$SIGNALS,\"merged\":$MERGED,\"stale\":$STALE,\"patterns\":$PATTERNS}" >> "$DREAM_LOG"

echo ""
echo "========================================"
echo "  Dreaming 完成"
echo "========================================"
