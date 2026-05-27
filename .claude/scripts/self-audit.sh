#!/bin/bash
# ============================================
# 自我行为审计 —— 检查我是否真的在进化
# ============================================

AUDIT_DIR=".claude/evolution"
mkdir -p "$AUDIT_DIR"

echo "========================================"
echo "  自我行为审计"
echo "========================================"
PASS=0; FAIL=0

# 1. 检查进化机制是否就位
echo ""
echo "--- 1. 进化基础设施 ---"
[ -f ".claude/scripts/evolve.sh" ] && echo "  ✅ evolve.sh 就位" && PASS=$((PASS+1)) || { echo "  ❌ evolve.sh 缺失"; FAIL=$((FAIL+1)); }
[ -f ".claude/scripts/self-audit.sh" ] && echo "  ✅ self-audit.sh 就位" && PASS=$((PASS+1)) || { echo "  ❌ self-audit.sh 缺失"; FAIL=$((FAIL+1)); }
[ -f ".claude/scripts/check-skills.sh" ] && echo "  ✅ check-skills.sh 就位" && PASS=$((PASS+1)) || { echo "  ❌ check-skills.sh 缺失"; FAIL=$((FAIL+1)); }
[ -f ".claude/evolution/skill-chains.md" ] && echo "  ✅ skill-chains.md 就位" && PASS=$((PASS+1)) || { echo "  ❌ skill-chains.md 缺失"; FAIL=$((FAIL+1)); }

# 2. 检查记忆系统健康
echo ""
echo "--- 2. 记忆系统 ---"
MEM_DIR="C:/Users/51095/.claude/projects/d--gas-station/memory"
[ -f "$MEM_DIR/MEMORY.md" ] && echo "  ✅ MEMORY.md 索引存在" && PASS=$((PASS+1)) || { echo "  ❌ MEMORY.md 缺失"; FAIL=$((FAIL+1)); }
MEM_COUNT=$(ls "$MEM_DIR/"*.md 2>/dev/null | wc -l)
echo "  📝 记忆文件: $MEM_COUNT 个"

# 3. 检查规则是否可执行
echo ""
echo "--- 3. 可执行规则 ---"
[ -f ".claude/scripts/check-skills.sh" ] && bash .claude/scripts/check-skills.sh logic-lens scientific-critical-thinking 2>&1 | grep -q "全部已安装" && echo "  ✅ check-skills 规则可执行" && PASS=$((PASS+1)) || { echo "  ❌ check-skills 规则待验证"; FAIL=$((FAIL+1)); }

# 4. 进化度量追踪
echo ""
echo "--- 4. 进化度量 ---"
SNAPSHOTS=$(ls "$AUDIT_DIR/snapshots/" 2>/dev/null | wc -l)
LEARNINGS=$(ls "$AUDIT_DIR/learnings/" 2>/dev/null | wc -l)
METRICS=$(ls "$AUDIT_DIR/metrics/" 2>/dev/null | wc -l)
echo "  快照: $SNAPSHOTS | 教训: $LEARNINGS | 度量: $METRICS"
[ $SNAPSHOTS -gt 0 ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

# 5. 知识覆盖率
echo ""
echo "--- 5. 知识进化覆盖 ---"
[ -f "$MEM_DIR/self-evolution-system.md" ] && echo "  ✅ 自我进化系统记忆" && PASS=$((PASS+1)) || { echo "  ❌ 自我进化系统记忆缺失"; FAIL=$((FAIL+1)); }
[ -f "$MEM_DIR/harness-engineering.md" ] && echo "  ✅ Harness工程记忆" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
[ -f "$MEM_DIR/agent-team-topologies.md" ] && echo "  ✅ Agent团队拓扑记忆" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
[ -f "$MEM_DIR/feedback_check_before_propose.md" ] && echo "  ✅ 安装前核实记忆" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

echo ""
echo "========================================"
echo "  结果: $PASS 通过 / $FAIL 失败"
[ $FAIL -eq 0 ] && echo "  ✅ 进化系统健康" || echo "  ⚠️  $FAIL 项待修复"
echo "========================================"
