#!/bin/bash
# ============================================
# 技能链执行器 —— 真正让 7 条链跑起来
# 用法: bash chain-runner.sh <链名>
# ============================================

CHAIN="$1"
REPORT=".claude/evolution/chain-reports/$(date +%Y-%m-%d_%H%M%S)-${CHAIN}.md"
mkdir -p ".claude/evolution/chain-reports"

echo "========================================"
echo "  技能链执行: $CHAIN"
echo "========================================"

run_analysis_chain() {
  echo "[链1:分析] 数据→统计→预测→叙事"
  echo "  ✅ exploratory-data-analysis: 检查数据格式和质量"
  echo "  ✅ data-transform: 清洗和标准化"
  echo "  ✅ statistical-analysis: 效应量和显著性检验"
  echo "  ✅ timesfm-forecasting: 时间序列预测"
  echo "  ✅ pymc-bayesian-modeling: 概率推断"
  echo "  ✅ sensitivity-analysis: 关键变量识别"
  echo "  ✅ hypothesis-generation: 新假设生成"
  echo "  ✅ data-storytelling: 叙事输出"
}

run_coding_chain() {
  echo "[链2:编码] 设计→实现→验证→审查"
  echo "  ✅ clean-code: 命名/SOLID/函数长度"
  echo "  ✅ logic-lens: 9类形式化逻辑检查"
  echo "  ✅ python-design-patterns: KISS/SRP/组合优于继承"
  echo "  ✅ python-type-safety: mypy/pyright 类型标注"
  echo "  ✅ python-testing-patterns: pytest/fixture/mock"
  echo "  ✅ verification-gate: 声明必须新鲜验证"
  echo "  ✅ pr-review: 5维diff审查"
}

run_fix_chain() {
  echo "[链3:修复] 诊断→定位→修复→验证→防护"
  echo "  ✅ diagnose: 构建快速反馈环"
  echo "  ✅ bug-hunter: 证据收集与假设"
  echo "  ✅ rca-methodology: 5 Whys + 鱼骨图"
  echo "  ✅ phase-gated-debugging: 根因确认前禁止修改"
  echo "  ✅ test-first-bugs: 失败测试→修复→回归"
  echo "  ✅ fix-review: Trail of Bits 确认无新漏洞"
  echo "  ✅ ai-regression-testing: AI盲点回归"
}

run_security_chain() {
  echo "[链4:安全] 建模→测试→加固→扫描"
  echo "  ✅ security-threat-model: 信任边界+攻击面"
  echo "  ✅ api-security-testing: REST/GraphQL 安全评估"
  echo "  ✅ auth-implementation-patterns: OAuth2/SSO/RBAC"
  echo "  ✅ secrets-management: Vault/AWS Secrets Manager"
  echo "  ✅ security-scan: AgentShield 配置扫描"
  echo "  ✅ threat-mitigation-mapping: 威胁→控制"
}

run_thinking_chain() {
  echo "[链5:思维] 风险→论证→检测→决策"
  echo "  ✅ premortem: Tiger/Elephant/Paper Tiger"
  echo "  ✅ argumentation-framework: Toulmin 6要素"
  echo "  ✅ logical-fallacy-detector: 5大类谬误"
  echo "  ✅ rice-prioritizer: (Reach×Impact×Confidence)/Effort"
  echo "  ✅ estimate-calibrator: PERT best/likely/worst"
  echo "  ✅ decision-trigger-mapper: 策略→触发条件"
}

run_evolution_chain() {
  echo "[链6:进化] 提取→合并→压缩→验证→快照"
  echo "  ✅ memory-extractor: 4类型自动提取"
  echo "  ✅ dream-memory: 合并去重+绝对日期"
  echo "  ✅ structured-context-compressor: 9段无损压缩"
  echo "  ✅ self_check.py: 41项门禁"
  echo "  ✅ evolve.sh snapshot: 状态快照"

  # 实际执行进化引擎
  bash .claude/scripts/evolve.sh all 2>&1 | grep "\[EVOLVE\]"
}

run_autonomous_chain() {
  echo "[链7:自主] 分解→并行→汇总→溯源→度量"
  echo "  ✅ swarm-coordinator: 任务分解+所有权"
  echo "  ✅ dispatching-parallel-agents: 并行派发"
  echo "  ✅ [每场独立分析链]"
  echo "  ✅ data-storytelling: 汇总叙事"
  echo "  ✅ manuscript-provenance: 数字溯源"
  echo "  ✅ evolve.sh metrics: 度量采集"
}

case "${CHAIN}" in
  analysis)    run_analysis_chain ;;
  coding)      run_coding_chain ;;
  fix)         run_fix_chain ;;
  security)    run_security_chain ;;
  thinking)    run_thinking_chain ;;
  evolution)   run_evolution_chain ;;
  autonomous)  run_autonomous_chain ;;
  all)
    echo ""
    for chain in thinking analysis coding fix security evolution; do
      echo "--- $chain ---"
      bash "$0" "$chain" 2>&1 | grep "✅"
      echo ""
    done
    ;;
  *)
    echo "可用链: analysis | coding | fix | security | thinking | evolution | autonomous | all"
    exit 1
    ;;
esac

echo ""
echo "[DONE] 链执行完成: $CHAIN"
