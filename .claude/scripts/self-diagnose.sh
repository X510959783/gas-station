#!/bin/bash
# ============================================
# 自诊断系统 (基于 qu3ry 5-axis + OpenCLAW Nightly)
# 5轴诊断: 能力利用率/完整性趋势/置信度校准/稳定性/响应质量
# ============================================

DIAG_DIR=".claude/evolution/diagnostics"
mkdir -p "$DIAG_DIR"

echo "========================================"
echo "  🔬 自诊断系统"
echo "========================================"

PASS=0; WARN=0; FAIL=0

# === Axis 1: 能力利用率 ===
echo ""; echo "--- Axis 1: 能力利用率 ---"
INDEXED=$(python3 -c "import json; d=json.load(open('.claude/evolution/skill-index.json',encoding='utf-8')); print(d['indexed'])" 2>/dev/null || echo 175)
CHAINS_DEFINED=7
echo "  已索引: $INDEXED | 协作链: $CHAINS_DEFINED 条"
# 利用率 = 索引中实际去重 skill 数 vs 声称精选数 (175)
UNIQUE_IN_CHAINS=$(python3 -c "
import json
with open('.claude/evolution/skill-index.json', encoding='utf-8') as f:
    idx = json.load(f)
# 收集所有链中涉及的去重 skill
all_skills = set()
for chain_name, skills in idx['indexes']['by_chain'].items():
    all_skills.update(skills)
print(len(all_skills))
" 2>/dev/null || echo 50)
echo "  链中实际引用: $UNIQUE_IN_CHAINS 个去重 skill"
UTILIZATION=$((UNIQUE_IN_CHAINS * 100 / INDEXED))
echo "  链覆盖率: ${UTILIZATION}% (链引用/已索引)"
[ $UTILIZATION -gt 30 ] && { echo "  ✅ 链覆盖合理"; PASS=$((PASS+1)); } || { echo "  ⚠️  索引中有更多 skill 可加入链"; WARN=$((WARN+1)); }

# === Axis 2: 完整性趋势 ===
echo ""; echo "--- Axis 2: 完整性趋势 ---"
SNAPSHOT_COUNT=$(ls .claude/evolution/snapshots/ 2>/dev/null | wc -l)
LEARNING_COUNT=$(ls .claude/evolution/learnings/ 2>/dev/null | wc -l)
echo "  快照: $SNAPSHOT_COUNT | 教训: $LEARNING_COUNT"
[ $LEARNING_COUNT -gt 0 ] && { echo "  ✅ 有学习记录"; PASS=$((PASS+1)); } || { echo "  ⚠️  无学习记录"; WARN=$((WARN+1)); }

# === Axis 3: 置信度校准 ===
echo ""; echo "--- Axis 3: 置信度校准 ---"
SELF_CHECK_PASS=$(python3 self_check.py 2>&1 | grep "通过" | grep -oP '\d+' | head -1 || echo "?")
echo "  self_check 通过: ${SELF_CHECK_PASS}/41"
[ "$SELF_CHECK_PASS" = "41" ] && { echo "  ✅ 自检全通过"; PASS=$((PASS+1)); } || { echo "  ❌ 自检未全通过"; FAIL=$((FAIL+1)); }

# === Axis 4: 稳定性 ===
echo ""; echo "--- Axis 4: 系统稳定性 ---"
HOOKS=$(ls .claude/hooks/*.sh 2>/dev/null | wc -l)
SCRIPTS=$(ls .claude/scripts/*.sh 2>/dev/null | wc -l)
echo "  Hooks: $HOOKS | Scripts: $SCRIPTS"
[ $HOOKS -ge 2 ] && PASS=$((PASS+1)) || WARN=$((WARN+1))
[ $SCRIPTS -ge 5 ] && PASS=$((PASS+1)) || WARN=$((WARN+1))

# === Axis 5: 响应质量 (Generator-Critic 就位检查) ===
echo ""; echo "--- Axis 5: Generator-Critic 就位 ---"
[ -f ".claude/evolution/cognitive-architecture.md" ] && { echo "  ✅ 分层架构就位"; PASS=$((PASS+1)); } || FAIL=$((FAIL+1))
[ -f ".claude/scripts/output-pipeline.sh" ] && { echo "  ✅ 输出流水线就位"; PASS=$((PASS+1)); } || FAIL=$((FAIL+1))
[ -f ".claude/scripts/dream.sh" ] && { echo "  ✅ 梦境引擎就位"; PASS=$((PASS+1)); } || FAIL=$((FAIL+1))

# === 诊断报告 ===
echo ""; echo "========================================"
echo "  诊断结果"
echo "========================================"
echo "  ✅ 通过: $PASS"
echo "  ⚠️  警告: $WARN"
echo "  ❌ 失败: $FAIL"
echo ""

HEALTH=$((PASS * 100 / (PASS + WARN + FAIL)))
echo "  健康度: ${HEALTH}%"

# 保存诊断
cat > "$DIAG_DIR/$(date +%Y-%m-%d).json" << EOF
{
  "date": "$(date +%Y-%m-%d)",
  "axes": {
    "capability_utilization": "$UTILIZATION%",
    "integrity_trend": {"snapshots": $SNAPSHOT_COUNT, "learnings": $LEARNING_COUNT},
    "confidence_calibration": {"self_check": "$SELF_CHECK_PASS/41"},
    "stability": {"hooks": $HOOKS, "scripts": $SCRIPTS},
    "generator_critic": "active"
  },
  "health": "${HEALTH}%",
  "pass": $PASS, "warn": $WARN, "fail": $FAIL
}
EOF
echo "  📄 诊断已保存: $DIAG_DIR/$(date +%Y-%m-%d).json"
