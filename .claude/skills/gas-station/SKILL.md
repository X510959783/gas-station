---
name: gas-station
description: 园中园燃气后端开发技能，自动加载项目架构、约定和已知陷阱
---

# 园中园燃气后端开发技能

> 自动加载项目上下文：架构、约定、已知陷阱

---

## 架构概览

```
server/
├── app.js              ← Express 入口，中间件链 + 路由挂载
├── config/
│   ├── env.js          ← 环境变量统一管理 + JWT 密钥
│   └── db.js           ← mysql2 连接池（参数化查询）
├── middleware/
│   ├── auth.js         ← JWT 鉴权（authRequired / adminRequired）
│   ├── validate.js     ← Zod v4 校验（issues 不是 errors）
│   ├── requestId.js    ← 请求追踪 ID
│   └── opLog.js        ← 操作日志
├── routes/
│   ├── auth.js         ← 微信登录/注册/个人资料
│   ├── orders.js       ← 订单 CRUD（BOLA 已防护）
│   ├── coupons.js      ← 优惠券（available/my/receive）
│   ├── products.js     ← 商品
│   ├── feedback.js     ← 用户反馈
│   ├── sms.js          ← 短信验证码
│   ├── stations.js     ← 站点
│   └── admin/          ← 管理后台子路由（全部 adminRequired）
├── utils/
│   ├── logger.js       ← logger(tag) 工厂 + 静态方法
│   ├── response.js     ← serverError() 统一错误响应
│   └── scheduler.js    ← 预警定时任务
└── tests/
    ├── api/            ← API 测试（supertest + mock）
    ├── security/       ← 安全回归测试
    └── __mocks__/      ← Jest mock（DB/Auth/Logger/UUID）
```

## 关键约定

1. **SQL 查询只用参数化**（`pool.query('... WHERE id = ?', [id])`），ESLint 规则禁止拼接
2. **JWT 密钥从 `config/env.js` 统一获取**，不再在 auth.js 中重复生成
3. **logger 支持两种用法**：`logger.info(msg)`（无 tag）或 `logger('tag').info(msg)`（有 tag）
4. **Zod v4** 用 `result.error.issues` 不是 `errors`
5. **validate 中间件**对 `undefined` body 返回 400（Zod object schema 拒绝 undefined）
6. **测试环境** rateLimit + scheduler + listen 全部跳过
7. **mock auth** 接受所有 `Bearer *` token（测试用，不校验 JWT 签名）

## 已知陷阱

- **不要加正则安全中间件** — 参数化查询是唯一可靠防御，正则黑名单误拦截正常业务输入
- **Windows Scheduled Task 不可靠** — Gateway 用 `Start-Process -WindowStyle Hidden`
- **mock-DB 必须区分查询类型** — SELECT 返回行数据，INSERT 返回 insertHeader
- **logger.js 和其 mock 必须接口一致** — 两边都有静态方法 `logger.info()` 和工厂方法 `logger('tag')`
- **DB 连接池 queueLimit 不能是 0** — 改为 50，防止队列耗尽内存

## 测试命令

```bash
npx jest                          # 全量运行
npx jest tests/api/auth.test.js   # 单个文件
npx jest --testNamePattern='wx-login'  # 按名称过滤
```

---

## Agent 团队模式（分析流水线）

足彩分析任务采用 **Producer-Reviewer 模式**：

```
Producer（数据解析 + L1/L2 分析）
  → Reviewer（验证门禁 + 框架一致性 + 输出完整性）
    → Calibrator（赛后校准 + 框架进化）
```

### 质量门（每次分析必经）

1. **数据门**：竞彩官方在列表中、公司数合理（≥10）、关键字段完整
2. **一致性门**：self_check.py 41 项全部通过 → 使用 **verification-gate** 确保真实运行
3. **输出门**：8 段式输出（赛事背景→关键数据→六维评分→L1决策→L2走势→截止前后→主任行为→进化提示）
4. **逻辑门**：使用 **logical-fallacy-detector** 自检分析中是否存在因果谬误/预设谬误

### 并行分析模式

多场比赛分析时使用 **Fan-out/Fan-in**：
1. 每场比赛派发独立子 Agent 并行分析
2. 全部完成后主 Agent 汇总对比
3. 跨场次统计：胜率、skip 率、D6 信号分布
4. 使用 **scientific-critical-thinking** 评估统计显著性

### 能力强化 Skill 映射

> 以下 16 个 skill 全部通过安全审查，分两组：通用能力（9 个）+ 足彩分析（7 个）

#### 通用能力强化（9 个）

| 分析阶段 | 触发 Skill | 作用 |
|----------|-----------|------|
| 数据解析 | **logic-lens** | 检查解析代码的边界条件、空值处理、类型安全 |
| 六维评分 | **logical-fallacy-detector** | 自检推理中是否有因果简化、预设偏差 |
| 赛后校准 | **scientific-critical-thinking** | 评估预测 vs 实际是否有统计显著性 |
| 框架升级 | **debugging-strategies** | 系统化定位框架缺陷根因 |
| bug 修复 | **phase-gated-debugging** | 5 阶段协议，根源确认前禁止修改代码 |
| 声称完成前 | **verification-gate** | 只读验证：检查声明是否真实、边缘是否遗漏 |
| 会话持久化 | **memory-extractor** | 自动提取分析经验→4 类型 memory |
| 上下文压力 | **structured-context-compressor** | 9 段式无损压缩，保留关键决策 |
| 跨场次回顾 | **mesh-memory** | 语义搜索历史分析，发现跨场次模式 |

#### 足彩分析强化（16 个）

| 分析阶段 | 触发 Skill | 作用 |
|----------|-----------|------|
| 新数据接入 | **exploratory-data-analysis** | 200+ 格式检测、数据质量六维评估、异常值诊断 |
| 赔率信号验证 | **statistical-analysis** | 检验选择→效应量→贝叶斯框架，判断信号是否真实 |
| 策略回测 | **quant-analyst** + **backtesting-frameworks** | 事件驱动回测、避免前视/幸存偏差、样本外验证 |
| 赔率走势预测 | **timesfm-forecasting** | Google TimesFM 零样本时间序列，无需训练 |
| 球队舆情分析 | **sentiment-scoring** | 规则+上下文校正（反讽/比较/条件句） |
| 新模式发现 | **hypothesis-generation** | 观察→可检验假设→预测，7 项质量准则过滤 |
| 外部分析评估 | **research-critique** | 论据-声明对齐，识别真正削弱贡献的局限 |
| 预测失败归因 | **rca-methodology** | 5 Whys→鱼骨图→故障树，追到框架参数根因 |
| 仓位决策 | **risk-manager** | Kelly 准则、R-multiple、对冲策略、压力测试 |
| 风险评估 | **risk-metrics-calculation** | VaR/CVaR/Sharpe/Sortino/最大回撤 |
| 数据采集加固 | **web-scraping** | 多策略降级（requests→trafilatura→Playwright隐身） |
| 科学图表 | **matplotlib-scientific-plotting** | 出版级图表，全线元素控制，PDF/SVG 导出 |
| 统计可视化 | **seaborn-statistical-plots** | DataFrame 原生，自动分组/CI/回归拟合/热力图 |
| 图表选择 | **chart-selector** | 比较/趋势/分布/关系/构成 5 维决策树 |
| 结果汇总报告 | **data-storytelling** | 原始数据→叙事驱动的洞察 |
| 网页采集增强 | **firecrawl**（已有） | 搜索引擎级爬取，JS 渲染 |

#### 自身能力强化（14 个）

| 场景 | 触发 Skill | 作用 |
|------|-----------|------|
| 写新代码 | **clean-code** | Uncle Bob：命名/函数/SOLID/代码味道 |
| 代码审查 | **code-review-excellence** | 建设性反馈、严重性分级、知识共享 |
| 代码重构 | **refactoring-catalog** | Fowler 模式、代码味道→重构映射 |
| 安全编码 | **security-review** + **security-best-practices** + **vulnerability-patterns** | OWASP 清单、语言特定安全、CWE Top 25 |
| 架构决策 | **architecture-decision-records** + **architecture-patterns** | ADR 记录、Clean/Hexagonal/DDD 模式 |
| 长会话 | **context-compression** + **context-degradation** | 锚定迭代摘要、退化模式诊断+缓解 |
| 大型任务 | **swarm-coordinator** | 分解→分配→合成→验证，多 Agent 协调 |
| 测试设计 | **test-design-patterns** | 等价类/边界值/状态转换/配对测试 |
| bug 修复 | **test-first-bugs** | 复现→失败测试→子Agent修复→回归 |
| 概念解释 | **explain-like-socrates** | 苏格拉底式对话，引导式教学 |

#### 足彩数据工程与建模（7 个）

| 分析阶段 | 触发 Skill | 作用 |
|----------|-----------|------|
| 原始数据清洗 | **data-transform** | pandas/numpy 清洗/归一化/缺失值/合并 |
| 数据管道自动化 | **data-engineer** | Spark/dbt/Airflow 管道架构、数据治理 |
| 赔率特征构建 | **feature-engineering-cookbook** | 缩放/分箱/编码/时间序列特征/特征重要性 |
| 预测模型选择 | **model-selection-guide** | XGBoost/LightGBM/Prophet 选择矩阵 |
| ML 建模 | **scikit-learn** | 分类/回归/聚类/管道完整工作流 |
| 赔率概率推断 | **pymc-bayesian-modeling** | MCMC/NUTS/层次模型/后验检查/模型比较 |
| 策略 A/B 对比 | **ab-test-setup** | 假设门→指标门→执行门，统计功效验证 |

#### 编程能力强化（21 个）

| 技术栈 | 触发 Skill |
|--------|-----------|
| Python 设计 | **python-design-patterns** + **python-anti-patterns** |
| Python 风格 | **python-code-style** + **python-type-safety** |
| Python 健壮 | **python-error-handling** + **python-resource-management** |
| Python 结构 | **python-project-structure** + **python-configuration** |
| Python 性能 | **python-performance-optimization** + **async-python-patterns** |
| Python 测试 | **python-testing-patterns** |
| Python 运维 | **python-observability** |
| Bash | **bash-defensive-patterns** + **bash-scripting** |
| Node.js | **nodejs-backend-patterns** + **javascript-testing-patterns** |
| API | **api-design-principles** + **rest-api-conventions** |
| SQL | **sql-optimization-patterns** |
| Git | **git-hooks-automation** |
| Docker | **docker-patterns** |

## 技能协作链（7 条）

> 激活方式：场景匹配→自动按链顺序执行→上游输出=下游输入→任何一环 FAIL 停止后续。

| 链名 | 触发场景 | 协作流程 |
|------|----------|----------|
| 分析链 | 足彩分析 | EDA→清洗→统计→时序→贝叶斯→敏感性→假设→叙事 |
| 编码链 | 写代码 | CleanCode→LogicLens→设计模式→类型安全→测试→验证门→PR |
| 修复链 | bug | Diagnose→BugHunter→RCA→PhaseGated→TestFirst→FixReview→回归 |
| 安全链 | 安全审计 | 威胁建模→API测试→认证→密钥→扫描→缓解 |
| 思维链 | 做决策 | Premortem→论证→谬误检测→优先级→估算→触发映射 |
| 进化链 | 发现/纠正 | MemoryExtractor→DreamMemory→压缩→self_check→快照 |
| 自主链 | 批量分析 | Swarm→并行派发→分析链→叙事→溯源→度量 |

## 自主进化机制

### 会话生命周期

```
会话开始 → bash .claude/scripts/evolve.sh all (preflight+snapshot+metrics)
  → 加载进化基因 (CLAUDE.md + MEMORY.md + skill-chains.md)
    → 执行任务 (7链自动匹配)
      → 被纠正 → bash .claude/scripts/evolve.sh learn "教训"
        → 发现模式 → memory-extractor → memory 文件
          → 会话结束 → dream-memory 合并去重
```

### 赛后校准循环

```
分析 → 比赛结束 → 对比预测 vs 实际 → 记录偏差 → 调整框架参数
```

- D6 |gap|>0.20 阈值：等待更多数据验证
- D5 K>1.1 阈值：已从行业标准确认
- 每 5 场比赛做一次框架审计

### 记忆积累

- 每场比赛存入 match-db.json（含 D1-D6 各项得分 + 决策 + 实际结果）
- 赛后学到的新模式写入 memory（使用两步保存不变式）
- 框架参数调整记录到 calibration.md

### 知识进化触发条件

- 连续 3 场相同模式的预测错误 → 审查对应维度
- 新联赛/新盘口类型出现 → 评估是否需要适配
- 发现新的可靠信号 → 提案加入框架

## 安全要求（后端特有）

- SQL 只用参数化查询，ESLint 强制
- JWT 密钥统一从 config/env.js 获取
- 测试环境跳过 rateLimit + scheduler + listen
- DB 连接池 queueLimit: 50（不能为 0）
- 不做正则安全中间件（参数化是唯一可靠防御）

## 自主执行模式

批量分析时使用 autonomous-skill（feiskyer/claude-code-settings）：
- Headless 模式：`bash scripts/run-session.sh "分析挪超第X轮" --max-sessions 10`
- Hook 模式：Stop hook 自动续接会话
- 完成后自动运行 self_check.py 验证

长期进化使用 ContinuousClaudeV4.7 流水线：
- assess → plan → premortem → prepare → execute → validate → evolve
