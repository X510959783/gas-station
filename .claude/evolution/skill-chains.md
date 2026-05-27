# 技能协作链

> 不是单独使用某个 skill，而是让它们形成协作流水线。

## 链 1: 分析链（足彩分析核心）

```
exploratory-data-analysis     ← 新数据接入：格式检测+质量评估
  → data-transform            ← 清洗+归一化
  → statistical-analysis      ← 信号验证：效应量+贝叶斯
    → timesfm-forecasting     ← 赔率走势预测
    → pymc-bayesian-modeling  ← 概率推断
      → sensitivity-analysis  ← 关键变量敏感度
        → hypothesis-generation ← 新假设→预测
          → data-storytelling  ← 叙事输出
```

## 链 2: 编码链（写代码时自动触发）

```
clean-code                    ← 命名/SOLID
  → logic-lens                ← 9类形式化检查
    → python-design-patterns  ← 架构模式
      → python-type-safety    ← 类型标注
        → python-testing-patterns ← 测试
          → verification-gate ← 验证门
            → pr-review       ← 最终审查
```

## 链 3: 修复链（bug 出现时自动触发）

```
diagnose                      ← 快速反馈环构建
  → bug-hunter                ← 证据收集
    → rca-methodology         ← 5 Whys 根因
      → phase-gated-debugging ← 根因确认前禁止修改
        → test-first-bugs     ← 失败测试→修复
          → fix-review        ← 确认修复不引入新bug
            → ai-regression-testing ← 回归防护
```

## 链 4: 安全链（安全敏感代码时自动触发）

```
security-threat-model         ← 信任边界+攻击面
  → api-security-testing      ← API 安全测试
    → auth-implementation-patterns ← 认证实现
      → secrets-management    ← 密钥管理
        → security-scan       ← AgentShield 扫描
          → threat-mitigation-mapping ← 威胁→控制
```

## 链 5: 思维链（做决策/选择方案时自动触发）

```
premortem                     ← Tiger/Elephant 风险→失败逆向
  → argumentation-framework   ← Toulmin 论证
    → logical-fallacy-detector ← 谬误自检
      → rice-prioritizer      ← RICE 优先级
        → estimate-calibrator ← PERT 三点估算
          → decision-trigger-mapper ← 触发条件映射
```

## 链 6: 进化链（发现新知识/被纠正时自动触发）

```
memory-extractor              ← 4类型提取(user/feedback/project/reference)
  → dream-memory              ← 合并去重+绝对日期
    → structured-context-compressor ← 9段压缩
      → self_check.py         ← 最终门禁
        → evolve.sh snapshot  ← 快照记录
```

## 链 7: 自主分析链（批量比赛分析）

```
swarm-coordinator             ← 分解→分配→合成
  → dispatching-parallel-agents ← 并行派发
    → [每场: 链1 分析链]     ← 独立分析
      → data-storytelling     ← 汇总叙事
        → manuscript-provenance ← 数字溯源
          → evolve.sh metrics ← 度量记录
```

## 激活规则

- 链内从前到后顺序执行，上游输出=下游输入
- 任何一环 FAIL → 停止后续，标记问题
- 链间可以嵌套（链1 内部可以调用链3 修复数据问题）
- 所有链最终汇聚到进化链（链6）持久化经验
