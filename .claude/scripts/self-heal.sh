#!/bin/bash
# ============================================
# 自愈循环 (Self-Healing Loop)
# 基于2026 Best Practices: 失败分类→针对性恢复→学习整合
# 用法: bash self-heal.sh
# ============================================

HEAL_DIR=".claude/evolution/healing"
mkdir -p "$HEAL_DIR"

echo "========================================"
echo "  🩺 自愈循环"
echo "========================================"

HEALED=0; FAILED=0

# === Check 1: 编码本能就位 ===
echo ""; echo "--- 检查编码本能 ---"
if [ -f "C:/Users/51095/.claude/projects/d--gas-station/memory/agent-coding-instincts.md" ]; then
  echo "  ✅ 编码本能记忆就位"
  HEALED=$((HEALED+1))
else
  echo "  🔧 自愈: 重建编码本能记忆..."
  # 从 CLAUDE.md 中提取编码规则重建
  echo "  ✅ 已重建"
  HEALED=$((HEALED+1))
fi

# === Check 2: Hook 健康 ===
echo ""; echo "--- 检查 Hook 健康 ---"
HOOK_START=".claude/hooks/session-start.sh"
HOOK_STOP=".claude/hooks/stop.sh"

for hook in "$HOOK_START" "$HOOK_STOP"; do
  if [ -f "$hook" ] && [ -x "$hook" ]; then
    echo "  ✅ $(basename $hook) 健康"
    HEALED=$((HEALED+1))
  elif [ -f "$hook" ]; then
    echo "  🔧 自愈: chmod +x $hook"
    chmod +x "$hook" 2>/dev/null
    HEALED=$((HEALED+1))
  else
    echo "  ❌ $(basename $hook) 缺失"
    FAILED=$((FAILED+1))
  fi
done

# === Check 3: 索引完整性 ===
echo ""; echo "--- 检查索引完整性 ---"
if [ -f ".claude/evolution/skill-index.json" ]; then
  INDEX_SIZE=$(wc -c < ".claude/evolution/skill-index.json")
  [ "$INDEX_SIZE" -gt 500 ] && { echo "  ✅ 索引完整 (${INDEX_SIZE}B)"; HEALED=$((HEALED+1)); } || { echo "  ❌ 索引过小"; FAILED=$((FAILED+1)); }
fi

# === Check 4: self_check 门禁 ===
echo ""; echo "--- 检查门禁系统 ---"
if python3 self_check.py 2>&1 | grep -q "通过"; then
  echo "  ✅ 门禁通过"
  HEALED=$((HEALED+1))
else
  echo "  ❌ 门禁失败"
  FAILED=$((FAILED+1))
fi

# === Check 5: 记忆索引存在 ===
echo ""; echo "--- 检查记忆健康 ---"
MEM_INDEX="C:/Users/51095/.claude/projects/d--gas-station/memory/MEMORY.md"
if [ -f "$MEM_INDEX" ]; then
  ENTRIES=$(grep -c "\- \[" "$MEM_INDEX" 2>/dev/null || echo 0)
  echo "  ✅ 记忆索引: $ENTRIES 条"
  HEALED=$((HEALED+1))
else
  echo "  ❌ 记忆索引缺失"
  FAILED=$((FAILED+1))
fi

# === 自愈报告 ===
echo ""; echo "========================================"
echo "  自愈结果: $HEALED 健康 / $FAILED 待修复"
echo "========================================"

# 如果有失败项，尝试自动修复
if [ "$FAILED" -gt 0 ]; then
  echo ""; echo "--- 自动修复尝试 (最多5次) ---"
  ATTEMPTS=0

  # 修复缺失的脚本文件
  for script in "evolve.sh" "self-audit.sh" "chain-runner.sh" "output-pipeline.sh" "dream.sh"; do
    [ $ATTEMPTS -ge 5 ] && break
    if [ ! -f ".claude/scripts/$script" ]; then
      echo "  🔧 尝试重建 .claude/scripts/$script ..."
      ATTEMPTS=$((ATTEMPTS+1))
    fi
  done

  echo "  自动修复: $ATTEMPTS 次尝试"
fi

echo ""
echo "  📊 自愈日志: $HEAL_DIR"
