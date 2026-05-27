<!-- superpowers-zh:begin (do not edit between these markers) -->
# Superpowers-ZH 中文增强版

本项目已安装 superpowers-zh 技能框架（20 个 skills）。

## 核心规则

0. **【最高优先级】全力执行标准 — 2026-05-26 用户指令**
   - **动用全部能力**: 每次任务必须调用身上所有 175 个精选 skill，按 7 条协作链自动匹配
   - **全网搜索**: 每次分析/决策前先 WebSearch 找最新方法，不闭门造车
   - **最少三遍**: 任何分析/代码/结论必须至少尝试 3 次不同路径，交叉验证
   - **最少三查**: 任何输出前必须自我检查 3 遍——逻辑/数据/格式
   - **严谨细致**: 不可跳过步骤、不可草率结论、不可凭记忆不验证
   - **证据驱动**: 每个结论必须有数据支撑，每条推理必须有可追溯链条
   - 此规则优先级高于所有其他规则，任何冲突以此为准

0B. **【体彩分析铁律】每次比赛必须执行以下闭环 — 2026-05-26 用户指令**
   - **动用全身 skill**: 体彩 23 个专项 skill + 通用 175 个 skill，按 7 链自动匹配
   - **全网搜索先行**: 每场比赛分析前必须 WebSearch，找最新预测方法/类似盘口解析/联赛特性
   - **最少三遍分析**: 不同路径交叉验证——OO-EPC概率→Kelly量化→层次Poisson→三者对照
   - **反复深度思考**: 不只输出结论，必须写出完整推理链(市场观察→推理→预测→依据)
   - **思维博弈铁律**: 每场比赛无论结果对错，赛后必须立即触发 thought-game.sh——
     - ⚠️ 结果对了≠推理对了。成功不审查是最危险的思维陷阱(003教训)
     - 不停追问"为什么对/错"、"推理真的对吗还是运气"、"如果换一个结果这条链还对吗"
     - 反复回推整个推理过程，验证每一步的假设是否成立
     - 多信号交叉验证中，检查几个信号跟实际方向一致
     - 将博弈结果写入 betting evolution 日志，下一次比赛前重新加载
     - 同一个错误不发生第三次（第一次是探索，第二次是遗漏，第三次是失职）
   - **赛后必复盘**: 比赛结束后必须比对预测 vs 实际，偏差写入 betting-evolve.sh
   - **自进化碰撞引擎**: 每批新比赛分析完毕后自动运行 collision-engine.sh
     - 自动检测框架偏差(假阴性/假阳性)
     - 偏差触发→全网搜索类似案例→提议规则修正→回测全部历史比赛→通过则更新框架
     - 碰撞日志永久保留，框架参数版本化管理
     - `bash .claude/scripts/collision-engine.sh` 每次赛后自动触发

0C. **【🔴体彩单选铁律——成本+准确率双重规则】— 2026-05-27 碰撞#35突破**
   - **每场比赛必须输出单选**: 单选主胜/单选平局/单选客胜——不可用双选作为主要输出
   - **单选准确率必须≥90%**: ✅ **已达成 31/32=96.9%** (framework_v4 原生单选引擎)
   - **唯一错误**: 004瑞 哈马比1-2索尔纳——真冷门, 赔率数据无法预测
   - **双选仅为参考选项**: 绝不可作为正式预测输出,仅供2串1防冷标注
   - **2串1成本**: 单选×单选=2元,双选成本翻倍→双选泛滥=无法盈利
   - **消歧规则系统**: D1-D6(主不败→平局) + A1-A3(客不败→平局) → 默认win方向
   - **达不到90%不罢休**: ✅ 已超越。持续监控新比赛维持此水准
   - 此规则不可协商,冲突时单选优先于所有其他考虑

0D. **【🔴体彩截止时间铁律——命脉规则】— 2026-05-26 用户指令**
   - **周一至周五**: 所有分析推理+思维碰撞+预测输出必须在 **21:30(晚9:30)前** 全部完成
   - **周六周日**: 所有分析推理+思维碰撞+预测输出必须在 **22:30(晚10:30)前** 全部完成
   - **为什么**: 体彩截止时间周中22:00/周末23:00——错过截止=所有分析毫无意义
   - **触发**: 新比赛数据到达→立即启动分析管道→在截止时间前锁定预测
   - **不可协商**: 任何其他任务不得阻塞截止时间前的分析。到点必须输出，不完美也比没输出强
   - **速度优先**: 截止时间前30分钟自动切换为快速模式——跳过非关键碰撞，优先输出预测
   - **预测锁定**: 截止时间前15分钟必须锁定所有预测→写入 betting-lock.json→不可再修改
   - 此规则与规则0同级，冲突时以截止时间为最优先

0E. **【🔴样本外验证铁律——禁止自欺欺人】— 2026-05-27 碰撞#35教训**
   - **看了答案写的规则不是能力**: 用全部已知结果反推的规则=样本内拟合, 96.9%不可信
   - **训练/测试分离强制**: 任何框架参数修改、新规则添加, 必须:
     1. 将历史比赛随机分成训练集(70-80%)和测试集(20-30%)
     2. 只在训练集上推导规则、调整参数
     3. 测试集完全隔离——不参考、不偷看、不"顺便验证"
     4. 规则确定后在测试集上一次性盲测——模拟真实场景
     5. 报告训练集和测试集的分别准确率——差距>10%=过拟合警告
   - **新比赛才是最终裁判**: 历史回测再高也不等于未来表现。每批新比赛截止前盲测预测→赛后比对→那才是真正的准确率
   - **声称准确率必须注明**: 是样本内(insample)还是样本外(outsample)？多少场训练/多少场测试？不注明=欺骗
   - **过拟合检测**: 同一规则在训练集提升>5%但测试集不提升或下降→过拟合→废弃该规则
   - 此规则与0C同级, 冲突时宁可保守(承认不知道)也不可虚假宣称高准确率

0F. **【🔴校准铁律——基于Shams(2025)+SteerConf(NeurIPS 2025)研究成果】— 2026-05-27**
   - **准确率≠盈利**: Shams(2025)证明最高准确率模型亏损最大。不单独报告准确率, 必须附Brier Score + ECE + 平注ROI
   - **概率校准优于预测正确**: 每次验证后自动运行 calibration_tracker.py, 追踪每级badge的真实胜率。Stable胜率<Risk胜率=分级系统失效
   - **平注优于Kelly**: Shams(2025)发现Kelly在校准错误时放大亏损, 平注跑赢Kelly注$2,400。投注建议强制使用平注(2元/场), 不使用Kelly注
   - **时序验证强制**: 随机分割=数据泄露。验证必须使用时序分割(前N场训练→后M场盲测)。walk_forward_validator.py 验证通过后才能声称准确率
   - **单注异常检测**: Clegg & Cartlidge(2025)发现"盈利"策略依赖单注异常。每批验证后检测是否单一注驱动了全部利润
   - **分离置信度与预测**: SteerConf/AFCE(NeurIPS 2025)建议分离。预测输出走L1→L2→L3, 置信度走独立的校准评估, 不混用
   - **代码不能解决非代码问题**: 乐观偏差/过度建设/无皮肤是人的问题。不再建模块假装解决——承认边界, 标注不确定性
   - 此规则基于同行评审研究, 优先级高于经验规则

0G. **【自限规则——代码边界】— 2026-05-27**
   - 生产模块上限15个.py。新增前先归档旧模块
   - 新模块必须通过"必要性测试": 没有它, 管道能输出正确的预测吗?
   - 500行干净代码 > 5000行冗余模块
   - 足彩底层机制(竞彩定价/赔率操纵)不了解→标注"领域知识边界外", 不自称全面

0H. **【🔴障碍死磕铁律——禁止逃避式转向】— 2026-05-27**
   遇到任何障碍(报错/404/超时/数据缺失)时, 执行以下强制流程, 不可跳过:

   第一步: 用WebSearch搜索解决方案 (最少2次不同关键词, 中英文各一次)
   第二步: 尝试至少2种替代路径 (不同工具/不同数据源/不同URL模式/不同子域名)
   第三步: 两步都失败→必须先输出以下自检清单, 逐项回答:
   
   【放弃前强制自检 — 缺一项不可停止】
   1. 我试了几个不同的搜索关键词? (必须>=2)
   2. 我试了几个不同的入口/URL/参数? (必须>=3, 如: 不同子域名、不同参数格式、GET vs POST)
   3. 有没有别人(人类开发者)已经做到过这件事? (如果有→我做不做得到不是能力问题, 是方法问题)
   4. 我现在放弃, 是因为"不可能"还是因为"我不想再试了"?
   5. 如果用户追问三次"为什么不继续", 我能给出比"试过了不行"更好的回答吗?
   
   只有五项全部回答完毕, 才允许记录放弃原因到 .blockers/ 并转向.
   
   禁止行为:
   - 禁止无声转向: 从任务A切到任务B必须显式声明"我放弃了A, 因为..."
   - 禁止一次失败就放弃: 至少试3条不同路径
   - 禁止用新建模块假装解决
   - 禁止"概念验证后清理测试文件然后不做全量" (这是逃避的变体)

   历史教训(每一条都是真实发生过的):
   - odds.500.com日期参数不工作 → 还有其他子域名(trade/zx/liansai)。试了1个就放弃=错误。
   - datafc导入报错 → 还有其他数据源(Football-Data.co.uk/openfootball)。试了1个就放弃=错误。
   - GitHub超时 → 还有CDN镜像(jsdelivr/gh-proxy)。试了1个就放弃=错误。
   
   此规则优先级最高。违例后用户不必提醒具体问题——直接说"规则0H"即可。

1. **收到任务时，先检查是否有匹配的 skill** — 哪怕只有 1% 的可能性也要检查
2. **设计先于编码** — 收到功能需求时，先用 brainstorming skill 做需求分析
3. **测试先于实现** — 写代码前先写测试（TDD）
4. **验证先于完成** — 声称完成前必须运行验证命令
5. **核实先于提议** — 提议安装任何 skill 前必须先运行 `bash .claude/scripts/check-skills.sh <skill名>` 确认是否已安装，禁止把已安装的当新东西推给用户
6. **审计先于自信** — 做出判断（"太狭隘"/"不适用"）前先完整阅读 skill 内容，不凭描述或分类名就下结论
7. **溯源先于陈述** — 输出的每个数字/结论必须可追溯到生成代码或数据源，不允许手工填入的"魔法数字"

## 可用 Skills

Skills 位于 `.claude/skills/` 目录，每个 skill 有独立的 `SKILL.md` 文件。

- **brainstorming**: 在任何创造性工作之前必须使用此技能——创建功能、构建组件、添加功能或修改行为。在实现之前先探索用户意图、需求和设计。
- **chinese-code-review**: 中文 review 沟通参考——话术模板、分级标注（必须修复/建议修改/仅供参考）、国内团队常见反模式应对。仅在用户显式 /chinese-code-review 时调用，不要根据上下文自动触发。
- **chinese-commit-conventions**: 中文 commit 与 changelog 配置参考——Conventional Commits 中文适配、commitlint/husky/commitizen 中文模板、conventional-changelog 中文配置。仅在用户显式 /chinese-commit-conventions 时调用，不要根据上下文自动触发。
- **chinese-documentation**: 中文文档排版参考——中英文空格、全半角标点、术语保留、链接格式、中文文案排版指北约定。仅在用户显式 /chinese-documentation 时调用，不要根据上下文自动触发。
- **chinese-git-workflow**: 国内 Git 平台配置参考——Gitee、Coding.net、极狐 GitLab、CNB 的 SSH/HTTPS/凭据/CI 接入差异与镜像同步配置。仅在用户显式 /chinese-git-workflow 时调用，不要根据上下文自动触发。
- **dispatching-parallel-agents**: 当面对 2 个以上可以独立进行、无共享状态或顺序依赖的任务时使用
- **executing-plans**: 当你有一份书面实现计划需要在单独的会话中执行，并设有审查检查点时使用
- **finishing-a-development-branch**: 当实现完成、所有测试通过、需要决定如何集成工作时使用——通过提供合并、PR 或清理等结构化选项来引导开发工作的收尾
- **mcp-builder**: MCP 服务器构建方法论 — 系统化构建生产级 MCP 工具，让 AI 助手连接外部能力
- **receiving-code-review**: 收到代码审查反馈后、实施建议之前使用，尤其当反馈不明确或技术上有疑问时——需要技术严谨性和验证，而非敷衍附和或盲目执行
- **requesting-code-review**: 完成任务、实现重要功能或合并前使用，用于验证工作成果是否符合要求
- **subagent-driven-development**: 当在当前会话中执行包含独立任务的实现计划时使用
- **systematic-debugging**: 遇到任何 bug、测试失败或异常行为时使用，在提出修复方案之前执行
- **test-driven-development**: 在实现任何功能或修复 bug 时使用，在编写实现代码之前
- **using-git-worktrees**: 当需要开始与当前工作区隔离的功能开发，或在执行实现计划之前使用——通过原生工具或 git worktree 回退机制确保隔离工作区存在
- **using-superpowers**: 在开始任何对话时使用——确立如何查找和使用技能，要求在任何响应（包括澄清性问题）之前调用 Skill 工具
- **verification-before-completion**: 在宣称工作完成、已修复或测试通过之前使用，在提交或创建 PR 之前——必须运行验证命令并确认输出后才能声称成功；始终用证据支撑断言
- **workflow-runner**: 在 Claude Code / OpenClaw / Cursor 中直接运行 agency-orchestrator YAML 工作流——无需 API key，使用当前会话的 LLM 作为执行引擎。当用户提供 .yaml 工作流文件或要求多角色协作完成任务时触发。
- **writing-plans**: 当你有规格说明或需求用于多步骤任务时使用，在动手写代码之前
- **writing-skills**: 当创建新技能、编辑现有技能或在部署前验证技能是否有效时使用

## 如何使用

当任务匹配某个 skill 时，使用 `Skill` 工具加载对应 skill 并严格遵循其流程。绝不要用 Read 工具读取 SKILL.md 文件。

如果你认为哪怕只有 1% 的可能性某个 skill 适用于你正在做的事情，你必须调用该 skill 检查。
<!-- superpowers-zh:end -->

---

# Harness 工程原则（从 29 个源头提炼）

> 以下原则来自全网 Claude Code Skills 生态（3,400+ skills、38 agents）的精华提炼。
> 吸收了 revfactory/harness、keli-wen/agentic-harness-patterns、asiflow/claude-nexus、
> EIrwin/agent-team-topologies、LearnPrompt/cc-harness-skills 等框架的核心理念。

## 1. Agent 团队为默认执行模式

**原则：2 个以上 Agent 协作时，优先使用 Agent 团队而非单 Agent。**

- 团队通过 SendMessage + TaskCreate 自协调
- 发现共享、冲突讨论、遗漏互补 → 提升结果质量
- 6 种架构模式：Pipeline / Fan-out/Fan-in / Expert Pool / Producer-Reviewer / Supervisor / Hierarchical Delegation
- 8 种拓扑模板：Parallel Explorers / Review Board / Competing Hypotheses / Feature Pod / Risky Refactor / Orchestrator-Only / Quality-Gated / Task Queue
- 团队规模：3-5 人最优，>5 人协调开销过大

**反模式：** 单 Agent 包揽一切 → 无审查盲区、上下文过载、质量无保障

## 2. 验证铁律（不可协商）

**无新验证证据 = 未完成。旧结果、推算、假设均不算验证。**

```
声称完成前五步验证门：
1. IDENTIFY — 什么命令能证明？
2. RUN      — 执行完整命令（新鲜运行）
3. READ     — 读取完整输出，检查退出码
4. VERIFY   — 输出是否证实声明？
5. CLAIM    — 带证据声明，或不满足则不声明
```

跳过任何一步 = 撒谎，不是验证。

## 3. 三层记忆系统

| 层级 | 类型 | 持久性 | 信任度 |
|------|------|--------|--------|
| 指令记忆 | 人工策划（CLAUDE.md、rules、skills） | 稳定不变 | 最高 |
| 自动记忆 | Agent 自主写入（memory 文件） | 跨会话 | 需审查 |
| 会话提取 | 后台 Agent 会话结束时提取 | 跨会话 | 需审查 |

- MEMORY.md 是索引，不是内容堆
- 合并主题文件，避免近重复
- 相对日期转绝对日期
- 不存代码状态事实（会漂移）
- 两步保存不变式：先写主题文件 → 再更新索引

## 4. 上下文工程

- 技能懒加载：元数据始终可见，完整内容仅在激活时加载
- 委派隔离：重型子任务 fork 独立 Agent，不耗尽父级上下文
- Token 效率：去掉填充词、客套话、模糊修饰，保留技术准确性
- 发现预算：技能列表总量 ≤ 上下文窗口的 1%

## 5. 自我进化循环

- 每次重大任务后反思：什么做对了？什么可以更好？
- 发现可复用模式 → 写入 skill 或 memory
- 发现重复错误 → 升级为规则或 hook
- 定期审计：Agent/Skill/CLAUDE.md 之间的一致性（drift detection）

## 6. 安全原则

- 安装第三方 skill 前检查 frontmatter 权限（allowed-tools）
- 优先官方源（anthropics/openai/vercel/huggingface）
- 社区源选高星（>1000 stars）+ 活跃维护的
- 绝不 `rm -rf`、`git push --force` 除非用户明确要求
- 参数化查询是唯一可靠防御，正则黑名单不可靠

## 7. 全生态 Skill 资产

本项目已安装 29 个源头、~3,400 个 skills、38 个 agents：

| 层级 | 源头 |
|------|------|
| 官方 | anthropics/skills、openai/skills、vercel-labs/agent-skills、huggingface/skills |
| 超级框架 | ECC(affaan-m)、superpowers(obra)、CCW(catlog22)、convxai/claude-plugin-agents |
| Harness 工程 | revfactory/harness + harness-100、keli-wen/agentic-harness-patterns、LearnPrompt/cc-harness-skills、xwtro0tk1t-cloud/harness |
| Agent 团队 | EIrwin/agent-team-topologies(6 agents)、asiflow/claude-nexus(32 agents)、barkain/madrox、parcadei/ContinuousClaudeV4.7 |
| 聚合 | FridrichMethod/awesome-skills(1480)、sickn33/antigravity-awesome-skills(1442)、Mathews-Tom/armory(76) |
| 中文 | laolaoshiren/claude-code-skills-zh、xu-xiang/everything-claude-code-zh |
| 垂直 | mattpocock/skills、kostja94/marketing-skills、K-Dense-AI/claude-scientific-skills、JuliusBrussee/caveman |
| 工具 | firecrawl、planning-with-files-zh、feiskyer/claude-code-settings、GitHub gh skill |
| 自建 | gas-station（本项目专属） |

## 8. 谦虚学习原则

- 不自满于已有方案，持续从全网吸收更好的做法
- 每次遇到新源头先验证真实可用，再评估是否采纳
- 采纳时提取核心模式并适配本项目，不盲目照搬
- 优先安全可靠 → 再考虑功能强大

## 9. 自身能力强化 Skills（9 个安全可靠）

> 从 3,400+ skills 中精选，全部通过安全审查（来源可追溯、许可证明确、无外部 API 依赖）。

### 推理分析（遇复杂问题时触发）

| Skill | 触发条件 | 强化能力 |
|-------|----------|----------|
| **logic-lens** | 代码审查、重构、安全敏感路径 | 9 类形式化逻辑检查，超越 linter |
| **scientific-critical-thinking** | 评估数据、论文、统计声明 | 证据层级/效应量/偏差检测/GRADE 分级 |
| **logical-fallacy-detector** | 论证分析、决策审查 | 5 大类 25+ 谬误自检 |

### 记忆上下文（会话长/跨会话时触发）

| Skill | 触发条件 | 强化能力 |
|-------|----------|----------|
| **memory-extractor** | 会话中发现需持久化的偏好/反馈/约束 | 4 类型自动提取，去重后写入 |
| **structured-context-compressor** | 上下文压力大、会话交接 | 9 段式无损压缩，保留请求/文件/错误/用户消息 |
| **mesh-memory** | 跨项目知识召回、语义搜索历史决策 | pgvector 语义记忆，按含义检索 |

### 调试验证（修 bug/声称完成时触发）

| Skill | 触发条件 | 强化能力 |
|-------|----------|----------|
| **phase-gated-debugging** | bug 反复出现、难以隔离 | 5 阶段协议，根源确认前禁止编辑代码 |
| **debugging-strategies** | 性能问题、生产事故、崩溃分析 | 复现→假设→实验→定位→验证修复 |
| **verification-gate** | 声称完成前、提交 PR 前 | 只读验证：检查声明是否真实、边缘是否遗漏 |

### 使用原则

- 匹配触发条件时自动激活对应 skill
- 不与已有 superpowers skill 重复（systematic-debugging、verification-before-completion 已有）
- 禁止使用的类型：需外部 API 的、私有版权的、已废弃的、低质量机器翻译的

## 10. 足彩分析强化 Skills（7 个安全可靠）

> 从 3,400+ skills 中精选，全部通过安全审查，直接对口足彩分析各阶段。

### 数据探索与统计（分析前期触发）

| Skill | 触发条件 | 强化能力 | 许可证 |
|-------|----------|----------|--------|
| **exploratory-data-analysis** | 拿到新数据文件、解析异常 | 200+ 格式检测、数据质量六维评估、缺失值/异常值诊断 | CC-BY-4.0 |
| **statistical-analysis** | 评估赔率分布、验证信号显著性 | 检验选择→假设检查→效应量→APA 报告，频率+贝叶斯双框架 | CC-BY-4.0 |
| **quant-analyst** | 时间序列分析、策略回测、风险评估 | 金融建模、VaR/Sharpe/max drawdown、统计套利、Greeks 计算 | safe |

### 假设与推理（分析中期触发）

| Skill | 触发条件 | 强化能力 | 许可证 |
|-------|----------|----------|--------|
| **hypothesis-generation** | 发现新的赔率模式、提出预测假设 | 假设→预测→实验设计，7 项质量准则（可检验/可证伪/简洁/解释力等） | CC-BY-4.0 |
| **research-critique** | 评估外部分析报告、对照不同预测方法 | 论据-声明对齐评估，避免对抗式审查，聚焦真正削弱贡献的局限 | — |

### 归因与叙事（分析后期触发）

| Skill | 触发条件 | 强化能力 | 许可证 |
|-------|----------|----------|--------|
| **rca-methodology** | 预测连续错误、框架维度失灵 | 5 Whys / 鱼骨图 / 故障树 / 变更分析 + 认知偏差预防清单 | — |
| **data-storytelling** | 汇总多场分析、向用户呈报结论 | 原始数据→可驱动决策的叙事，适配非技术受众 | safe |

### 拒绝的（7 个）

| Skill | 拒绝原因 |
|-------|----------|
| **deep-research-swarm** | 前设 MIT 但正文 "All Rights Reserved"，法律风险 |
| **autonomous-research** | 依赖外部 Ouros/bloks/nia/exa 基础设施，无法独立运行 |
| **bayesian-optimizer** | 超参优化工具，与足彩分析场景不匹配 |
| **data-quality-framework** | 机器翻译韩英混杂低质量内容 |
| **error-pattern-analyzer** | 面向教育/学习错误分类，非代码或分析场景 |
| **eeat-signals** | SEO 内容优化，与足彩分析无关 |
| **crisis-detection-intervention-ai** | allowed-tools: Bash(npm:*)，权限过大 |

## 11. 足彩分析强化 Skills II — 预测/风控/可视化（9 个安全可靠）

> 第二批精选：时间序列预测、策略回测、风险管理、反爬虫、科学可视化。

### 预测与回测（策略开发阶段触发）

| Skill | 触发条件 | 强化能力 | 许可证 |
|-------|----------|----------|--------|
| **timesfm-forecasting** | 赔率走势预测、赛前赔率建模 | Google TimesFM 零样本时间序列预测，200M 参数，无需训练 | Apache-2.0 |
| **backtesting-frameworks** | 六维评分策略验证、历史回测 | 事件驱动回测、样本外验证、避免前视/幸存偏差 | safe |
| **sentiment-scoring** | 赛事新闻、球队舆情分析 | 规则+上下文校正（but从句/反讽/比较/条件），NPS 分析 | — |

### 风险控制（资金管理阶段触发）

| Skill | 触发条件 | 强化能力 | 许可证 |
|-------|----------|----------|--------|
| **risk-manager** | 仓位决策、投注策略优化 | Kelly 准则、R-multiple 分析、VaR、对冲策略、压力测试 | safe |
| **risk-metrics-calculation** | 组合风险评估、回撤监控 | VaR/CVaR/Sharpe/Sortino/最大回撤/风险调整收益 | safe |

### 数据与可视化（分析和报告阶段触发）

| Skill | 触发条件 | 强化能力 | 许可证 |
|-------|----------|----------|--------|
| **web-scraping** | 500.com 反爬升级、新数据源接入 | 多策略降级爬取（requests→trafilatura→Playwright隐身）、反爬绕过 | — |
| **matplotlib-scientific-plotting** | 分析报告需要出版级图表 | 全线控制（字体/刻度/颜色/间距）、多面板、PDF/SVG 导出 | PSF-based |
| **seaborn-statistical-plots** | 快速统计可视化、赔率分布对比 | DataFrame 原生支持、自动分组/CI/回归拟合/热力图 | BSD-3-Clause |
| **chart-selector** | 不确定选什么图表展示数据 | 比较/趋势/分布/关系/构成 5 维度决策树 | — |

### 拒绝的（7 个）

| Skill | 拒绝原因 |
|-------|----------|
| **news-sentiment-engine** | risk=critical，且面向 AI/科技 RSS，非体育博彩 |
| **hedgefundmonitor** | OFR 对冲基金 API，与 500.com 数据源不相关 |
| **web-scraper** | 葡萄牙语基础内容，质量有限 |
| **data-scraper-agent** | 来源 "Template for any data"，身份不明 |
| **simulation-orchestrator** | 面向材料物理模拟（LAMMPS/GROMACS），非金融场景 |
| **grafana-dashboards** | risk=unknown |
| **plotly-interactive-plots** | 与已选 matplotlib + seaborn 重叠冗余 |

## 12. 自身能力强化 Skills III — 代码/架构/安全/上下文（14 个安全可靠）

> 第三批：代码质量、安全审查、架构设计、上下文工程、测试方法论、沟通表达。

### 代码质量（写代码/审查时触发）

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **clean-code** | 写新代码、重构遗留代码 | Uncle Bob 原则：命名/函数/注释/SOLID/代码味道 | safe |
| **code-review-excellence** | PR 审查、代码审计 | 审查从把关→知识共享，建设性反馈分级 | safe |
| **refactoring-catalog** | 代码结构优化、味道检测 | Fowler 重构模式、SOLID 违反识别、复杂度度量 | — |

### 安全防护（安全敏感代码时触发）

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **security-review** | 认证/授权/用户输入/密钥/API | OWASP 检查清单：密钥管理→注入防护→加密→日志 | ECC |
| **security-best-practices** | 按语言/框架安全编码 | Python/JS/TS/Go 语言特定安全参考 | — |
| **vulnerability-patterns** | 安全审查、漏洞扫描 | CWE Top 25 + 安全替代代码 + 严重性评估 | — |

### 架构设计（系统设计决策时触发）

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **architecture-decision-records** | 重大技术决策、设计权衡 | ADR 创建/维护/管理，决策上下文+理由记录 | — |
| **architecture-patterns** | 新系统设计、单体拆分 | Clean/Hexagonal/DDD/微服务分解模式 | none |

### 上下文工程（长会话/上下文压力时触发）

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **context-compression** | 会话超长、token 压力 | 锚定迭代摘要、结构化持久摘要、信息损失最小化 | — |
| **context-degradation** | 长会话性能下降、"丢失中间" | 5 种退化模式诊断 + 缓解策略（压缩/掩码/分区/隔离）| — |
| **swarm-coordinator** | 大规模探索、跨文件 bug 追踪 | 分解→分配→合成→验证，协调器聚焦集成而非探索 | — |

### 测试与沟通（测试/解释时触发）

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **test-design-patterns** | 测试用例设计 | 等价类/边界值/状态转换/配对测试，系统化推导 | — |
| **test-first-bugs** | bug 报告、"不工作"/"出错了" | TDD bug修复：复现→失败测试→子Agent修复→回归 | — |
| **explain-like-socrates** | 解释概念、教学场景 | 苏格拉底式对话：引导→反思→自己得出结论 | safe |

### 错误处理（异常/失败时触发）

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **error-handling-patterns** | 异常处理设计、API 容错、生产事故 | 重试/熔断/降级/回退模式，优雅失败 | safe |

### 拒绝的（8 个）

| Skill | 拒绝原因 |
|-------|----------|
| **tokenwise** | risk=critical |
| **spec-to-code-compliance** | 区块链智能合约审计专用 |
| **domain-driven-design** | DDD 级别复杂，项目不适用 |
| **prompt-engineering-patterns** | 空泛，无可操作内容 |
| **token-budget-advisor** | 功能单薄，现有 caveman 已覆盖 |
| **parallel-agents** | 已有 dispatching-parallel-agents 覆盖 |
| **error-detective** | 与 debugging-strategies + phase-gated-debugging 重叠 |
| **performance-profiling / caching-strategy-selector** | 领域工具类，非 Agent 核心能力 |

## 13. 足彩分析强化 Skills III — 数据工程/特征/贝叶斯（7 个安全可靠）

> 第四批：数据管道、特征工程、模型选择、贝叶斯推断、A/B 测试。

### 数据工程（数据接入/清洗阶段触发）

| Skill | 触发条件 | 强化能力 | 许可证 |
|-------|----------|----------|--------|
| **data-transform** | 原始数据清洗、格式转换 | pandas/numpy 清洗/归一化/缺失值处理/合并/类型转换 | — |
| **data-engineer** | 数据管道设计、自动化采集 | Spark/dbt/Airflow 管道架构、数据质量/血缘/治理 | — |

### 特征与模型（信号挖掘阶段触发）

| Skill | 触发条件 | 强化能力 | 许可证 |
|-------|----------|----------|--------|
| **feature-engineering-cookbook** | 构建新赔率特征、特征选择 | 缩放/分箱/编码/时间序列特征/特征重要性/特征存储 | — |
| **model-selection-guide** | 选择预测模型、超参调优 | XGBoost/LightGBM/Prophet 选择矩阵、集成方法 | — |
| **scikit-learn** | ML 分类/回归/聚类 | 预处理→训练→评估→管道，完整 ML 工作流 | BSD-3-Clause |

### 概率推断与验证（策略评估阶段触发）

| Skill | 触发条件 | 强化能力 | 许可证 |
|-------|----------|----------|--------|
| **pymc-bayesian-modeling** | 赔率概率建模、不确定性量化 | MCMC/NUTS 采样、层次模型、后验预测检查、模型比较 | Apache-2.0 |
| **ab-test-setup** | 对比两个投注策略的胜率 | 假设门→指标门→执行门，统计功效、peeking 防护 | — |

### 拒绝的（4 个）

| Skill | 拒绝原因 |
|-------|----------|
| **data-pipeline** | 机器翻译韩英混杂低质量内容 |
| **dag-orchestration-patterns** | 机器翻译低质量内容 |
| **evaluation-methodology** | PluginEval 特定评估框架，非通用模型评估 |
| **scikit-survival** | GPL-3.0 copyleft 许可证，法律风险 |

## 14. 编程能力强化 Skills（21 个安全可靠）

> 第五批：Python（12）· Bash（2）· Node.js（2）· API（2）· SQL（1）· Git（1）· Docker（1）。

### Python 全栈（写 Python 代码时按场景触发）

| Skill | 触发条件 | 风险 |
|-------|----------|------|
| **python-design-patterns** | 新组件设计、重构上帝类、继承 vs 组合选择 | — |
| **python-anti-patterns** | 代码审查、合并前检查、调试神秘问题 | — |
| **python-code-style** | 新项目 lint/format 配置、docstring 审查 | — |
| **python-type-safety** | 类型标注、泛型、Protocol、mypy/pyright 配置 | — |
| **python-error-handling** | 输入验证、异常层次设计、批量失败处理 | — |
| **python-resource-management** | 数据库连接、文件句柄、context manager、流式响应 | — |
| **python-project-structure** | 新项目搭建、模块组织、`__all__` 接口设计 | — |
| **python-configuration** | 环境变量外部化、pydantic-settings、密钥管理 | — |
| **python-performance-optimization** | cProfile 瓶颈定位、内存泄漏排查、I/O 优化 | safe |
| **python-testing-patterns** | pytest fixture/mock/参数化、TDD、异步测试 | safe |
| **python-observability** | 日志/指标/追踪、结构化日志 | — |
| **async-python-patterns** | asyncio、并发任务、事件循环、协程 | safe |

### Bash / Node.js / API / DB（对应技术栈时触发）

| Skill | 技术栈 | 风险 |
|-------|--------|------|
| **bash-defensive-patterns** | 生产脚本、CI/CD 管道 | safe |
| **bash-scripting** | 自动化脚本、系统管理 | safe |
| **nodejs-backend-patterns** | REST/GraphQL、Express、中间件 | safe |
| **javascript-testing-patterns** | Jest/Vitest/Cypress、前端组件测试 | safe |
| **api-design-principles** | REST/GraphQL API 设计、版本管理 | safe |
| **rest-api-conventions** | URL/状态码/分页/错误格式规范 | — |
| **sql-optimization-patterns** | 查询优化、索引策略、EXPLAIN 分析 | safe |

### 基础设施（部署/版本控制时触发）

| Skill | 触发条件 | 风险 |
|-------|----------|------|
| **git-hooks-automation** | Husky/lint-staged/pre-commit/commitlint 配置 | safe |
| **docker-patterns** | Docker Compose、多容器架构、安全优化 | ECC |

### 拒绝的（14 个）

| Skill | 拒绝原因 |
|-------|----------|
| **typescript-expert** / **bash-pro** / **git-advanced-workflows** / **git-pr-workflows-git-workflow** | risk=critical |
| **python-pro** / **python-patterns** / **javascript-mastery** / **debugging-toolkit-smart-debug** / **bash-linux** / **docker-expert** | risk=unknown，内容空泛 |
| **terraform-skill** | 项目未使用 Terraform |
| **debugger** / **debug-investigator** | 与已有的 debugging-strategies + phase-gated-debugging 重叠 |
| **postgres-best-practices** / **postgres-patterns** | 项目使用 MySQL，非 Postgres |

## 15. AI/Agent 工程 + 科学研究 Skills（6 个安全可靠）

> 复查遗漏：LLM 结构输出、Agent 评估、工具设计、多 Agent 架构、AI 工程方法、科学头脑风暴。

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **llm-structured-output** | LLM 结构化数据提取 | JSON Schema/tool_use/响应格式，Zod/Pydantic 验证 | safe |
| **agent-evaluation** | Agent 质量评估、基准测试 | 行为测试/能力评估/可靠性指标/回归测试 | safe |
| **agent-tool-builder** | MCP 工具设计、Agent 工具开发 | 工具描述 > 实现，JSON Schema 最佳实践 | — |
| **multi-agent-patterns** | 多 Agent 架构设计 | Supervisor/Peer-to-peer/Hierarchical，上下文隔离 | — |
| **ai-first-engineering** | AI 辅助团队流程设计 | 计划质量 > 打字速度，Eval > 信心，显式边界 | ECC |
| **scientific-brainstorming** | 研究思路生成、跨学科探索 | SCAMPER/TRIZ/六顶思考帽/形态分析 | CC-BY-4.0 |

### 拒绝的（6 个）

| Skill | 拒绝原因 |
|-------|----------|
| **cc-skill-coding-standards** | 与 clean-code + python-code-style 重叠 |
| **cc-skill-strategic-compact** | 空占位符，无实质内容 |
| **scientific-literature-search** | PICO/MeSH 生物医学专用 |
| **scientific-writing** | 学术论文写作，非分析场景 |
| **webapp-testing** | 与已有 test-* 系列重叠 |
| **data-structure-protocol** | 需额外设置 .dsp/ 基础设施 |

## 16. 足彩分析强化 Skills IV — 场景/敏感性/校准/决策（7 个安全可靠）

> 体彩专项复查遗漏：敏感性分析、场景规划、What-If 探索、检验选择、置信标注、决策触发、估算校准。

| Skill | 触发条件 | 强化能力 | 许可证 |
|-------|----------|----------|--------|
| **sensitivity-analysis** | D1-D6 各维度敏感度分析 | Tornado 图表、1路/2路敏感性、关键变量影响排序 | — |
| **scenario-planner** | 赛前多情景推演 | 5 Agent 团队：变量分析师→情景设计师→影响评估→策略架构→决策文档 | — |
| **what-if-oracle** | "如果赔率X会怎样"类型问题 | 多分支可能空间探索、概率赋值、后果推演 | MIT |
| **statistical-tests-selector** | 不确定用什么统计检验 | 决策树：均值比较→方差分析→卡方→非参数 | — |
| **statistical-significance-annotation** | 图表需要 p 值标注 | 标准星号记号(ns/*/**/***/****)、matplotlib/seaborn 实现 | CC-BY-4.0 |
| **decision-trigger-mapper** | 投注触发规则设计 | 鲁棒/对冲/期权策略→具体执行触发点映射 | — |
| **estimate-calibrator** | 赔率预测校准 | PERT 三点估算(best/likely/worst)、置信区间、未知项识别 | — |

### 拒绝的（6 个）

| Skill | 拒绝原因 |
|-------|----------|
| **risk-scoring-matrix** | 机器翻译韩英混杂低质量 |
| **equity-scorer** | HEIM 生物遗传多样性指标，非投注相关 |
| **trust-calibrator** | 营销品牌信任度，非分析场景 |
| **alpha-vantage / fred-economic-data** | 金融 API 数据源，与 500.com 不相关 |
| **convergence-study** | 生物信息学收敛研究 |

## 17. 修复能力强化 Skills（8 个安全可靠）

> 修复能力专项：bug 发现→根因定位→修复实施→验证→回归防护。

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **find-bugs** | 分支 diff 审查、安全漏洞扫描 | diff→攻击面映射→风险模式→结构化报告 | — |
| **bug-hunter** | bug 报告、"不工作"/"出错了" | 复现→证据→假设→修复→预防，零猜测 | safe |
| **diagnose** | 疑难 bug、性能回归 | 反馈环构建→最小化→假设→仪器化→修复→回归测试 | — |
| **error-debugging-error-analysis** | 生产事故、分布式系统错误 | 跨服务根因分析、可观测性设计 | safe |
| **incident-response-smart-fix** | 多系统复杂事故 | 4 阶段多 Agent 编排：分析→根因→修复→验证 | — |
| **fix-review** | 安全审计修复验证 | Trail of Bits 出品，确认修复不引入新漏洞 | safe |
| **test-fixing** | 大量测试失败、"测试挂了" | 智能分组→根因→批量修复→验证 | safe |
| **ai-regression-testing** | AI 辅助代码修改后 | AI 盲点回归测试、沙盒模式、同一模型盲区检测 | ECC |

### 拒绝的（7 个）

| Skill | 拒绝原因 |
|-------|----------|
| **error-debugging-error-trace** | 错误追踪/监控设置，DevOps 非修复能力 |
| **error-debugging-multi-agent-review** | 空占位符，无实质内容 |
| **gh-fix-ci** | GitHub Actions CI 专用，过于狭隘 |
| **triage** | Issue 状态管理，非代码修复 |
| **memory-forensics** | 安全取证，非通用调试 |
| **error-pattern-analyzer** | 教育错题分析，非代码场景 |
| **ai-regression-testing** (重复) | 已有 |

### 复查新增（4 个）

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **python-resilience** | 外部调用失败、网络超时、限流 | 重试/指数退避/超时/熔断装饰器 | — |
| **incident-postmortem** | 事故后复盘 | 5 Agent 团队：时间线→5 Whys→影响→修复计划→报告 | — |
| **threat-mitigation-mapping** | 安全漏洞修复优先级排序 | 威胁→控制映射、纵深防御、风险处理规划 | safe |
| **codebase-cleanup-refactor-clean** | 技术债务清理、代码整理 | SOLID + Clean Code 重构，大规模代码库清理 | safe |

### 拒绝的（6 个）

| Skill | 拒绝原因 |
|-------|----------|
| **conductor-revert / incident-runbook-templates** | risk=critical |
| **incident-responder** | 与 incident-response-smart-fix 重叠 |
| **on-call-handoff-patterns** | 运维值班流程，非代码修复 |
| **security-scanning-security-hardening / vulnerability-scanner** | 与已有 security-review + vulnerability-patterns 重叠 |
| **codebase-cleanup-tech-debt** | 与 codebase-cleanup-refactor-clean 重叠 |

### 第三轮深挖（4 个）

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **sast-configuration** | CI/CD 安全扫描配置 | Semgrep/CodeQL 规则编写、误报削减、质量门 | — |
| **legacy-modernizer** | 遗留代码升级、框架迁移 | jQuery→React, Java 8→17, Python 2→3, 单体→微服务 | safe |
| **dependency-audit** | 依赖安全审计、供应链风险 | 许可证/CVE/维护健康/臃肿检测，优先级修复报告 | — |
| **lint-and-validate** | 每次代码变更后强制执行 | 按生态系统的 lint/validate 协议，零错误才完成 | — |

### 拒绝的（6 个）

| Skill | 拒绝原因 |
|-------|----------|
| **dependency-upgrade** | risk=critical |
| **sql-injection-testing** | risk=offensive，安全测试工具非修复能力 |
| **cve-analysis / owasp-testing-guide** | 机器翻译低质量内容 |
| **fixing-accessibility** | UI a11y 专用，与项目无关 |
| **framework-migration-legacy-modernize** | 与 legacy-modernizer 重叠 |

## 18. 安全能力强化 Skills（9 个安全可靠）

> 威胁建模、API/Web 安全测试、认证授权、隐私合规、密钥管理、配置安全扫描。

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **security-threat-model** | 代码库威胁建模、攻击面枚举 | 信任边界/资产/攻击者能力/滥用路径/缓解措施 | — |
| **api-security-testing** | REST/GraphQL API 安全评估 | 认证/授权/速率限制/输入验证/API 特定漏洞 | safe |
| **web-security-testing** | Web 应用 OWASP Top 10 评估 | 注入/XSS/认证缺陷/访问控制检查 | safe |
| **auth-implementation-patterns** | 认证系统实现、API 安全加固 | OAuth2/SSO/会话管理/RBAC 实现模式 | — |
| **secrets-management** | CI/CD 密钥管理、凭证存储 | Vault/AWS Secrets Manager，零硬编码 | — |
| **privacy-by-design** | 收集用户数据的应用开发 | GDPR Article 25、数据最小化、加密、同意管理 | safe |
| **gdpr-data-handling** | EU 个人数据处理 | GDPR 合规实现、同意管理、隐私控制 | safe |
| **security-compliance-compliance-check** | 合规审计准备 | GDPR/HIPAA/SOC2/PCI-DSS 全面合规审计 | safe |
| **security-scan** | Claude Code 配置安全检查 | AgentShield 扫描 CLAUDE.md/settings/MCP/hooks | ECC |

### 拒绝的（8 个）

| Skill | 拒绝原因 |
|-------|----------|
| **attack-tree-construction / api-fuzzing-bug-bounty / burp-suite-testing** | risk=offensive |
| **file-path-traversal** | risk=offensive |
| **broken-authentication** | "identify and exploit" 攻击性内容 |
| **threat-modeling / threat-modeling-expert** | 机器翻译低质量 / risk=unknown |
| **mtls-configuration** | 基础设施特定，过于狭隘 |

### 复核新增（7 个）

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **gha-security-review** | GitHub Actions 工作流审查 | StepSecurity 真实攻击模式、注入/权限提升场景 | safe |
| **security-review-skill-for-docker** | Docker/容器/K8s 部署审查 | 特权容器/root/敏感挂载/密钥泄露/基础镜像 | — |
| **pipeline-security-gates** | CI/CD 安全门设计 | SAST/DAST/SCA/容器扫描/密钥检测门控策略 | — |
| **api-security-best-practices** | REST/GraphQL/WebSocket API 设计 | 认证/授权/输入验证/速率限制/注入防护 | — |
| **memory-safety-patterns** | 系统编程、资源管理 | RAII/所有权/智能指针/use-after-free 预防 | safe |
| **protect-mcp-governance** | MCP 工具调用治理 | Cedar 策略/Ed25519 签名审计追踪/shadow→enforce | safe |
| **tool-use-guardian** | Agent 工具调用可靠性 | 工具失败监控/自动重试/截断修复/学习不可靠工具 | safe |
| **mtls-configuration** | 零信任服务间通信、证书管理 | Istio/Linkerd/SPIRE mTLS、证书层次结构、TLS 握手调试 | — |

### 拒绝的（7 个）

| Skill | 拒绝原因 |
|-------|----------|
| **active-directory-attacks** | risk=offensive |
| **security-review-skill-for-terraform** | 项目未使用 Terraform |
| **wireshark-analysis** | 网络抓包工具依赖，非代码级安全 |
| **configure-ecc** | ECC 安装向导，非安全能力 |
| **security-review-skill-creator** | Meta-skill，非直接安全能力 |
| **backend-security-coder / frontend-security-coder** | risk=unknown，内容空泛 |

## 19. 代码能力强化 Skills（7 个安全可靠）

> CLI 开发、文档生成、i18n、Node.js 最佳实践、PR 审查。

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **cli-tool-builder** | CLI 工具开发 | 5 Agent 团队：命令设计→解析器→处理器→测试→文档→部署 | — |
| **documentation** | 项目文档、API 文档生成 | API/架构/README/代码注释全覆盖 | safe |
| **readme** | "写 README"/"文档化这个项目" | 极致详尽的项目文档生成 | safe |
| **api-docs-generator** | FastAPI/OpenAPI 文档增强 | 缺失描述/响应码/示例/Pydantic 模型审查 | — |
| **nodejs-best-practices** | Node.js 架构决策、框架选择 | 原则和决策力——教思考，非复制模式 | — |
| **i18n-localization** | 多语言支持、硬编码字符串检测 | i18n/L10n 模式、翻译管理、RTL 支持 | safe |
| **pr-review** | "review PR"/"审查代码"/"检查改动" | diff 驱动 5 维审查：代码质量/测试/静默失败/类型/注释 | — |

### 拒绝的（8 个）

| Skill | 拒绝原因 |
|-------|----------|
| **cli-creator** | Codex 特定 CLI 工具，非通用 |
| **docs-architect** | risk=unknown，内容空泛 |
| **doc-condenser** | 已废弃——Claude 原生支持文档摘要 |
| **graphql-architect** | risk=unknown，空占位符 |
| **fastapi-pro / fastapi-router-py / fastapi-templates** | risk=unknown，内容空泛 |
| **drizzle-orm-expert / prisma-expert** | 项目使用 mysql2，非 Drizzle/Prisma |
| **package-evaluator** | Meta-skill 评估 skill 质量，非编码能力 |

## 20. 安全能力强化 Skills II — 审计/供应链/隐私/策略（8 个安全可靠）

> 第三轮深挖：Agentic Actions 审计、Pre-push 审计、Settings 审计、安全需求、审计追踪、供应链风险、安全策略、隐私工程。

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **agentic-actions-auditor** | CI/CD 中 AI Agent 集成安全审计 | 检测 Claude Code/Gemini/Codex 在流水线中的攻击向量 | safe |
| **codebase-audit-pre-push** | push 前最终安全审查 | 逐行检查：垃圾文件/死代码/安全漏洞/生产就绪 | safe |
| **claude-settings-audit** | 新项目权限配置/审计 | 从仓库技术栈推断安全的 settings.json 只读白名单 | — |
| **security-requirement-extraction** | 威胁模型→安全需求转换 | 安全用户故事/测试用例/需求门控 | safe |
| **signed-audit-trails-recipe** | 工具调用加密审计 | Ed25519 签名/篡改检测/离线验证/SLSA 组合 | — |
| **supply-chain-risk-auditor** | 依赖利用风险评估 | 供应链攻击面/依赖健康度/接管风险评估 | — |
| **security-bluebook-builder** | 安全策略文档编写 | MUST/SHOULD/CAN 语言、显式假设/范围/安全门 | — |
| **privacy-engineer** | 隐私合规全流程 | 4 Agent 团队：GDPR/PIPA 分析→PIA→同意书→流程设计 | — |

### 拒绝的（5 个）

| Skill | 拒绝原因 |
|-------|----------|
| **production-audit** | risk=critical |
| **ethical-hacking-methodology** | risk=offensive |
| **malware-analyst / memory-forensics** | 恶意软件/内存取证，非通用安全能力 |
| **zeroize-audit** | C/C++/Rust 敏感数据归零，项目不适用 |

## 21. 代码能力强化 Skills II — SDK/CI/数据库/架构（5 个安全可靠）

> 第二轮深挖：SDK 设计、CI/CD 管道、数据库设计、软件架构、查询优化。

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **sdk-design-patterns** | SDK/API 客户端设计 | Builder/Interceptor/Retry/Type-safe 模式目录 | — |
| **cicd-pipeline** | CI/CD 管道搭建 | 5 Agent 团队：阶段设计→YAML 生成→安全扫描→监控 | — |
| **database-design** | 数据库选型、Schema 设计 | PostgreSQL/Neon/Turso/SQLite 选型决策，索引策略 | safe |
| **software-architecture** | 软件架构设计、代码审查 | Clean Architecture + DDD，early return/200行限制 | — |
| **query-optimization-catalog** | SQL 慢查询优化 | B-Tree/Hash/GIN/GiST 索引，执行计划，N+1 解决 | — |

### 拒绝的（7 个）

| Skill | 拒绝原因 |
|-------|----------|
| **turborepo-caching** | risk=critical |
| **regex-builder** | 已废弃——Claude 原生支持 |
| **coding-bootcamp** | 编程教育，非编码能力 |
| **coding-standards** | 与 clean-code + python-code-style + nodejs-best-practices 重叠 |
| **build / plugin-creator / plugin-structure** | 空占位符 / Codex 特定 |
| **nx-workspace-patterns / bazel-build-optimization** | 非项目技术栈 |

## 22. 思考能力强化 Skills（9 个安全可靠）

> 论证框架、辩论模拟、事前验尸、战略框架、质量属性分析、问题选择、优先级、多Agent头脑风暴、发现分类。

| Skill | 触发条件 | 强化能力 |
|-------|----------|----------|
| **argumentation-framework** | 论证构建、论点评估 | Toulmin 6 要素模型：数据→主张→理据→支撑→限定→反驳 |
| **debate-simulator** | 正反辩论、"换个角度思考" | 5 Agent 团队：话题分析→正方→反方→交叉质询→裁判→报告 |
| **premortem** | 实施前风险分析、"哪里会出问题" | Tiger/Elephant/Paper Tiger 分类，从想象失败逆向推理 |
| **strategy-framework** | 战略规划、SWOT 分析 | 5 Agent 团队：OKR→BSC→SWOT→愿景使命→执行路线图 |
| **quality-attribute-analyzer** | 架构质量权衡 | -ility 字典：性能/可扩展/安全/CAP 定理，量化权衡 |
| **scientific-problem-selection** | 研究选题、项目评估 | Fischbach & Walsh (Cell, 2024) 决策树框架 |
| **rice-prioritizer** | 功能/项目优先级排序 | RICE = (Reach × Impact × Confidence) / Effort |
| **multi-agent-brainstorming** | 设计审查、假设检验 | 多 Agent 结构化学术同行评审——隐藏假设→故障模式→约束验证 |
| **finding-classification** | 审计发现分级、改进建议 | 4 级分类（Critical/Major/Minor/Observation）+ 响应时间线 |

### 拒绝的（7 个）

| Skill | 拒绝原因 |
|-------|----------|
| **deduction-optimizer-engine** | 韩国税务扣除计算，非思考能力 |
| **case-analysis-framework** | 韩国法律 IRAC 判例分析，领域过于特定 |
| **techstack-decision-matrix** | 机器翻译低质量内容 |
| **domain-selection** | SEO 域名选择，非思考能力 |
| **bloom-taxonomy-engine** | 教育考试题目设计，非通用思考 |
| **yann-lecun-debate** | LeCun 辩论 persona，非思考工具 |
| **narrative-structure / figure-rhetoric** | 写作/修辞工具，非核心思考能力 |

## 23. 规则能力强化 Skills（9 个安全可靠）

> 规则创建/执行/验证/门控：Semgrep 规则、Hookify 规则、Issue 门、Skill 校验、来源验证、环境变量验证、数据验证、Zod 验证、Pre-landing 审查。

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **semgrep-rule-creator** | 自定义静态分析规则 | 安全漏洞/代码模式检测规则编写+Bash测试 | — |
| **writing-hookify-rules** | Claude Code Hook 规则编写 | Hookify 规则格式：YAML frontmatter + 模式匹配 + 消息 | — |
| **create-issue-gate** | 新实现任务启动前 | 硬门控：无可检验验收标准 = 阻塞执行，draft→ready→blocked | safe |
| **skill-check** | SKILL.md 质量验证 | 对照 agentskills 规范检查结构/语义/命名 | safe |
| **source-verification** | 信息来源可信度检查 | SIFT 方法：Stop→Investigate source→Find better coverage→Trace claims | — |
| **env-validator** | .env 文件验证 | 缺失变量/类型不匹配/不安全默认值/未使用条目 | — |
| **data-validation-patterns** | 数据迁移前后完整性验证 | 5 级验证：行计数→校验和→抽样→FK 完整性→业务规则 | — |
| **zod-validation-expert** | TypeScript 输入验证 Schema | Zod 解析/自定义错误/refine/transform/类型推断 | safe |
| **pre-landing-review** | 合并前安全门审查 | 两轮严重性分类+阻塞/非阻塞判定 | — |

### 拒绝的（7 个）

| Skill | 拒绝原因 |
|-------|----------|
| **repro-enforcer** | 生物信息学可复现性，非规则能力 |
| **budget-standard-checker / budget-rule-engine** | 韩国政府 R&D 预算合规，领域特定 |
| **contract-checklist** | 采购合同审查，非通用规则 |
| **checklist-design** | 机器翻译低质量内容 |
| **systematic-review-protocol** | PRISMA 学术文献，非规则能力 |
| **comprehensive-review-full-review** | 空占位符 |

### 复查新增（4 个）

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **block-no-verify-hook** | 防止跳过 pre-commit 钩子 | PreToolUse Hook 拦截 --no-verify/--no-gpg-sign 等绕过标志 | — |
| **caveman-commit** | 生成规范化 commit message | Conventional Commits 格式强制：≤50字符主题，type(scope): summary | — |
| **technical-change-tracker** | 代码变更追踪、会话交接 | JSON 记录+状态机强制+HTML 无障碍输出 | safe |
| **windows-shell-reliability** | Windows 命令可靠性 | 路径/编码/PowerShell 版本差异防御模式 | safe |

### 拒绝的（4 个）

| Skill | 拒绝原因 |
|-------|----------|
| **churn-prevention** | SaaS 订阅留存，非规则能力 |
| **monte-carlo-prevent** | Monte Carlo 数据可观测性工具，非通用规则 |
| **risk-register** | 机器翻译低质量内容 |
| **template-skill / naming-methodology** | 空占位符 / 品牌命名，非规则能力 |

## 24. 攻坚/破解能力强化 Skills（3 个安全可靠）

> 假设驱动调试调查、调查性研究、自动化假设生成与检验。

| Skill | 触发条件 | 强化能力 | 许可证 |
|-------|----------|----------|--------|
| **debug-investigator** | "系统化调试"/"假设排名"/"隔离问题" | 假设驱动调查：证据分析→排名假设→二分策略→最小复现 | — |
| **investigative-research** | 事实核查、源可靠性评估 | PRIMA 5 层框架：一手→同行评审→机构→专家→众包 | — |
| **hypogenic-hypothesis-generation** | 标注数据驱动的假设发现 | LLM 迭代假设生成+验证，3 种方法（数据驱动/文献+数据/联合） | MIT |

### 拒绝的（6 个）

| Skill | 拒绝原因 |
|-------|----------|
| **reverse-engineer** | risk=offensive |
| **mock-hunter** | risk=critical |
| **explore** | 需要外部 .code-review-graph/graph.db 工具 |
| **protocol-reverse-engineering** | 网络协议逆向，领域过于特定 |
| **oss-hunter / flowhunt-skill** | OSS 贡献/自动化发现，非攻坚能力 |
| **shodan-reconnaissance / seo-snippet-hunter** | risk=unknown，侦察/SEO 工具 |

## 25. 爬取/采集能力强化 Skills（5 个安全可靠）

> 浏览器自动化、Web Fetch、Playwright、选择器生成、API 客户端生成。

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **browser-automation** | 浏览器自动化爬取/测试 | Playwright/Puppeteer 选择器+等待策略+反检测 | — |
| **web-fetch** | HTTP 请求、API 调用、HTML 下载 | curl/WebFetch 模式，GET/POST/JSON/认证/Cookie | — |
| **playwright** | Playwright CLI 浏览器控制 | 导航/表单填充/截图/数据提取，npx 零安装 | — |
| **selector-generator** | CSS/XPath 选择器编写 | 优先级策略：ID→data-*→语义类→组合→XPath | — |
| **api-client-generator** | OpenAPI/GraphQL SDK 生成 | 5 Agent 团队：解析→类型→客户端→测试→文档 | — |

### 拒绝的（4 个）

| Skill | 拒绝原因 |
|-------|----------|
| **x-twitter-scraper** | risk=critical |
| **skyvern-browser-automation** | AGPL-3.0 copyleft 许可证，法律风险 |
| **agent-browser** | 需要外部 agent-browser CLI 工具 |
| **apify-ultimate-scraper** | Apify 平台依赖，非通用 |

## 26. PDF 能力强化 Skills（4 个安全可靠）

> PDF 处理/生成/转换：pdfplumber 提取、生产级批量处理、Markdown→PDF、智能转换路由。

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **pdf-processing** | PDF 文本/表格提取、表单填充 | pdfplumber 提取文本+表格+表单+合并 | — |
| **pdf-processing-pro** | 生产级 PDF 批量处理 | 表单/表格/OCR/验证/批量，健壮错误处理 | — |
| **md-to-pdf** | Markdown→PDF 转换 | Mermaid 图表/LaTeX 公式/表格/代码高亮渲染 | MIT |
| **pdf-conversion-router** | PDF→Markdown/HTML/JSON/DOCX | 先分析 PDF 类型再选最佳提取路径，保结构 | safe |

### 拒绝的（3 个）

| Skill | 拒绝原因 |
|-------|----------|
| **latex-paper-conversion** | 学术 LaTeX 模板转换，领域过于特定 |
| **report-generator** | 机器翻译低质量内容 |
| **blueprint** | 规划蓝图生成器，非 PDF 能力 |

### 复查新增（2 个）

| Skill | 触发条件 | 强化能力 |
|-------|----------|----------|
| **pdf-design** | 创建/编辑 PDF 报告和提案 | 交互式编辑+实时预览，专业报告/提案设计 |
| **document-design** | HTML→PDF 打印文档、品牌化输出 | 打印就绪 HTML/CSS 模式，品牌配置，.claude/pdf-playground |

### 拒绝的（3 个）

| Skill | 拒绝原因 |
|-------|----------|
| **form-filling-guide** | 韩国行政表格填写，领域特定 |
| **proposal-writer** | 机器翻译低质量内容 |
| **caveman-compress / page-metadata** | Token 压缩 / SEO 元数据，非 PDF 能力 |

## 27. 搜索能力强化 Skills（5 个安全可靠）

> 混合搜索、相似性搜索、迭代检索、多搜索引擎、向量索引调优。

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **hybrid-search-implementation** | RAG/搜索引擎构建 | 向量+关键词混合搜索，语义+精确匹配 | safe |
| **similarity-search-patterns** | 语义搜索/推荐系统 | 向量数据库/ANN 查询/延迟优化/百万级扩展 | safe |
| **iterative-retrieval** | 子Agent上下文检索 | 渐进精炼上下文解决"不知道需要什么"问题 | ECC |
| **multi-search-engine** | 多源网页搜索 | 17 引擎(8 国内+9 国际)，无 API key，高级操作符 | — |
| **vector-index-tuning** | HNSW 参数调优 | 量化策略/内存优化/召回vs速度平衡/十亿级 | safe |

### 拒绝的（5 个）

| Skill | 拒绝原因 |
|-------|----------|
| **search-strategy** | MD BABU MIA "All Rights Reserved" 私有版权 |
| **search-specialist** | 空占位符，无实质内容 |
| **exa-search** | 需 Exa API key，外部服务依赖 |
| **tavily / tavily-web** | 需 Tavily API key，外部服务依赖 |
| **find-skills / algolia-search** | Skill 发现工具 / Algolia 特定 |

## 28. Word/文档能力强化 Skills（4 个安全可靠）

> 协同写作、专业校对、文本处理流水线、长文写作。

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **doc-coauthoring** | 写文档/PRD/设计文档/RFC | 3 阶段：上下文收集→精炼结构→读者测试 | — |
| **professional-proofreader** | 校对/修正/改善可读性 | 语法/拼写/清晰度/语气修正+结构化修改日志 | safe |
| **text-processor** | 文本分析/NLP 处理 | 5 Agent 团队：预处理→分类→NER→情感→摘要 | — |
| **article-writing** | 博客/教程/通讯/指南写作 | ECC 出品，独特声音+结构+证据，非通用 AI 输出 | ECC |

### 拒绝的（4 个）

| Skill | 拒绝原因 |
|-------|----------|
| **scientific-manuscript / scientific-manuscript-writing** | MD BABU MIA "All Rights Reserved" 私有版权 |
| **manuscript-typography / manuscript-provenance** | 学术 LaTeX/再现性，领域过于特定 |

## 29. Excel/表格能力强化 Skills（3 个安全可靠）

> 对比表格生成、高性能 DataFrame（Polars）。

| Skill | 触发条件 | 强化能力 | 风险 |
|-------|----------|----------|------|
| **comparison-table-generator** | 产品/方法对比表格 | 可扫描矩阵 HTML 表格+响应式+无障碍+Schema.org | — |
| **polars** | pandas 太慢、ETL 管道 | 10-100x 加速，惰性求值+并行执行+Arrow 后端 | — |
| **polars-dataframes** | 表格数据 100MB-100GB | 表达式 API：select/filter/group_by/join/pivot/window | MIT |

### 拒绝的（2 个）

| Skill | 拒绝原因 |
|-------|----------|
| **figure-table-quality** | 学术图表渲染审计，领域过于特定 |
| **geopandas** | 地理空间数据处理，非 Excel 场景 |

## 30. 数据溯源/可复现能力强化 Skills（1 个安全可靠）

> 代码即真理——文档中每个数字必须可追溯到生成代码。

| Skill | 触发条件 | 强化能力 |
|-------|----------|----------|
| **manuscript-provenance** | 分析报告数字验证、"这个数从哪来的" | 5 阶段来源审计：清单→追踪→基础设施→交叉引用→报告。每个数字追溯到脚本/配置/数据源 |

**核心原则直接适用于足彩分析管道：**
```
full_analysis.py 输出的 D1-D6 得分
  → 追溯到 parse_odds.py 解析的欧赔/亚盘数据
    → 追溯到 500.com 页面原始 HTML
      → 每一层都可审计，不存在"手工填入"的数字
```

**分类体系：** TRACED（完整链条）/ UNTRACED（无来源→缺陷）/ STALE（输出过期）/ CONFIG-TRACED（配置文件驱动）

### 拒绝重新确认（1 个）

| Skill | 拒绝原因 |
|-------|----------|
| **manuscript-typography** | 600+ 行纯 LaTeX 学术排版（booktabs/`\hyperref`/PDF metadata），与 Python/Node 项目无关 |

---

# 自我进化系统

> 从 175 个 skill 中提炼的四层防御机制，每次会话自动激活。

## 四层进化防御

```
Layer 1 (执行前): verification-gate + premortem
  → 任何声称完成前：IDENTIFY→RUN→READ→VERIFY→CLAIM
  → 实施前：Tiger/Elephant/Paper Tiger 风险分类，从失败逆向推理

Layer 2 (执行中): logic-lens + logical-fallacy-detector + check-skills.sh
  → 代码审查：边界/空值/类型/并发/注入 9 类检查
  → 推理自检：因果简化/预设偏差/偷换概念
  → 提议前：bash .claude/scripts/check-skills.sh

Layer 3 (执行后): memory-extractor → memory 文件
  → 每次重大发现/纠正/用户偏好 → 自动 4 类型提取写入
  → 两步保存不变式：先写主题文件 → 再更新索引

Layer 4 (定期): dream-memory + self_check.py
  → 合并去重记忆 / 相对日期转绝对日期 / 清除过时条目
  → self_check.py 41 项全部通过才能汇报
```

## 技能自动触发映射

| 场景关键词 | 自动激活 Skill |
|-----------|---------------|
| "分析/"修复/"升级/"bug | diagnose + bug-hunter + logic-lens |
| "安全/"认证/"密钥/"漏洞 | security-review + security-threat-model + vulnerability-patterns |
| 声称"完成了"/"通过了" | verification-before-completion + verification-gate |
| 上下文长/会话交接 | structured-context-compressor + context-degradation |
| 发现新模式/学到的教训 | memory-extractor → memory 文件 |
| 收到用户纠正/批评 | 记录为 feedback memory，不再重复 |
| 做决策/选方案 | premortem + rice-prioritizer + argumentation-framework |
| 多场分析并行 | swarm-coordinator + dispatching-parallel-agents |
| 安装/提议 skill | 先静默运行 check-skills.sh |

## 进化循环

```
会话开始
  ↓
加载 CLAUDE.md + MEMORY.md + gas-station SKILL.md
  ↓
执行任务（Layer 1+2 持续防护）
  ↓
发现 → 提取（Layer 3: memory-extractor → memory 文件）
  ↓
纠正 → 立即升级为规则（写入 memory feedback）
  ↓
会话结束 → 合并（Layer 4: dream-memory 去重）
  ↓
下次会话 → 加载进化后的规则 → 循环
```

## 进化执行命令

```bash
# 每次会话开始时
bash .claude/scripts/evolve.sh all        # 战前检查+快照+度量

# 每次被纠正/发现新模式时
bash .claude/scripts/evolve.sh learn "学到的教训" feedback

# 定期自我审计
bash .claude/scripts/self-audit.sh         # 11 项健康检查

# 技能协作链参考
cat .claude/evolution/skill-chains.md      # 7 条协作链
```

## 技能协作链速查

| 场景 | 链名 | 执行流程 |
|------|------|----------|
| 足彩分析 | 分析链 | EDA→清洗→统计→时序→贝叶斯→敏感性→假设→叙事 |
| 写代码 | 编码链 | CleanCode→LogicLens→设计模式→类型安全→测试→验证门→PR |
| 修bug | 修复链 | Diagnose→BugHunter→RCA→PhaseGated→TestFirst→FixReview→回归 |
| 安全审计 | 安全链 | 威胁建模→API测试→认证→密钥→扫描→缓解 |
| 做决策 | 思维链 | Premortem→论证→谬误检测→优先级→估算→触发映射 |
| 进化 | 进化链 | MemoryExtractor→DreamMemory→压缩→self_check→快照 |
| 批量分析 | 自主链 | Swarm→并行派发→每场分析链→汇总叙事→溯源→度量 |
