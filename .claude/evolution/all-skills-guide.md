# Claude Code Skills 全览 — 全网最火最热清单

> 2026-05-26 | 综合 GitHub / SkillsMP / 社区推荐 / 安全审计

---

## 一、必装基础层（任何项目都该有）

### 1. superpowers ⭐187K
**来源**: obra/superpowers  
**安装**: `npx superpowers` 或 `/plugin install superpowers@claude-plugins-official`

| 子技能 | 用途 | 跟我们项目的关系 |
|------|------|------|
| brainstorming | 实施前先设计→审批→再执行 | 框架升级前必用 |
| writing-plans | 拆成2-5分钟的可执行任务 | 避免边写边改 |
| test-driven-development | RED→GREEN→REFACTOR | 分析脚本先定输出标准 |
| subagent-driven-development | 每任务派遣独立子Agent+双阶段审查 | 复杂功能分拆执行 |
| systematic-debugging | 4阶段根因分析 | 数据解析/API编码问题排查 |
| requesting-code-review | 派遣审查Agent检查代码 | 每次改完代码跑一次 |
| verification-before-completion | 修完必须验证 | 避免"以为修好了" |
| dispatching-parallel-agents | 并行子Agent | 同时分析多场比赛 |

**已安装**: ✅（superpowers-zh 中文版）

### 2. planning-with-files ⭐13.4K
**来源**: OthmanAdi/planning-with-files  
**用途**: 创建持久化任务文件（`task_plan.md`/`findings.md`/`progress.md`），上下文压缩后任务不丢失  
**对我们**: 分析多场比赛时跟踪进度，不靠记忆
**安装**: `npx skills add OthmanAdi/planning-with-files`

### 3. claude-mem ⭐72.4K
**来源**: claude-mem  
**用途**: 跨会话自动记忆——自动检索相关记忆注入system prompt，每次对话结束后保存新发现  
**对我们**: 替代手工写 memory 文件，自动积累分析经验
**安装**: `npx skills add claude-mem`

---

## 二、代码质量（每次改代码必用）

### 4. code-reviewer（结构化代码审查）
**来源**: 多个独立版本  
**用途**: 结构化审查——安全漏洞/逻辑错误/性能问题/代码风格，输出分级报告（Critical/Important/Minor）  
**对我们**: 刚才37秒抓出6个bug——已验证价值
**安装**: superpowers 内含 ✅

### 5. env-doctor（环境诊断）
**来源**: 社区推荐 Top 4  
**用途**: 系统诊断项目启动问题——依赖缺失/配置错误/版本不兼容  
**对我们**: Python脚本/API调用/编码问题的自动排查
**安装**: `npx skills add env-doctor`

### 6. /simplify（内置）
**来源**: Claude Code 内置  
**用途**: 3个并行审查Agent同时检查代码质量——冗余/过度抽象/不可达代码  
**对我们**: 分析脚本精简

---

## 三、数据/内容处理（跟我们业务相关）

### 7. Anthropic Document Skills ⭐125K
**来源**: anthropics/skills  
**用途**: 创建真实格式的 docx/xlsx/pdf/pptx 文件——不是文本模拟  
**对我们**: 生成分析报告 PDF/Excel
**安装**: `npx skills add anthropics/skills --skill docx`

### 8. browser-automation（浏览器自动化）
**来源**: agent-browser  
**用途**: 每页200-400 tokens超高效浏览器自动化（vs Playwright MCP的2000-6000 tokens）  
**对我们**: 如果以后需要自动刷新500.com抓数据
**安装**: `npx skills add agent-browser`

### 9. firecrawl（网页抓取）
**来源**: firecrawl/cli ⭐353  
**用途**: 托管式网页爬取——处理JS渲染/反爬/登录  
**对我们**: 绕过titan007/500.com的反自动化限制
**安装**: `npx skills add firecrawl/cli`

---

## 四、Git/PR工作流

### 10. git-commit-writer（提交信息生成）
**来源**: 社区 Top 1  
**用途**: 自动分析staged变更→生成Conventional Commits格式的commit message  
**对我们**: 规范化提交记录
**安装**: `npx skills add git-commit-writer`

### 11. create-pr ⭐169.7K热度
**来源**: 社区增速最快  
**用途**: 自动生成PR描述→标记Reviewer→关联Issue  
**对我们**: 框架升级后自动出PR
**安装**: `npx skills add create-pr`

### 12. changelog-generator
**来源**: 社区推荐 Top 6  
**用途**: Git历史→用户向的发布说明  
**对我们**: 框架版本迭代记录

---

## 五、安全（不可忽视）

### 13. AgentShield（安全扫描）
**来源**: everything-claude-code 内含  
**用途**: 1282个测试用例（98%覆盖率），含 `--opus` 模式——3个Agent分别做红队/蓝队/审计对抗审查  
**对我们**: 分析脚本和数据处理代码的安全审查

### 14. Trail of Bits Code Audit
**来源**: Trail of Bits（专业安全公司）  
**用途**: 专业级CodeQL/Semgrep静态分析  
**对我们**: 代码安全性的专业级保障

---

## 六、不推荐的（节约你的时间）

| Skill/类型 | 原因 |
|------|------|
| UI/UX 设计类 | 跟我们的足彩分析项目无关 |
| 视频制作类 | 当前不需要 |
| 内容运营类（小红书/公众号） | 暂不需要 |
| Single-file无分层skill | 社区验证70%不合格 |
| 半年未更新的skill | 模型迭代快，旧skill可能失效 |
| 描述是营销文案的skill | Claude无法判断何时激活 |

---

## 七、建议安装优先级

| 优先级 | Skill | 原因 |
|:--:|------|------|
| 🔴 | code-reviewer（已有） | 刚才已验证——每次改代码必用 |
| 🔴 | brainstorming（已有） | 框架升级前必设计 |
| 🔴 | systematic-debugging（已有） | 排查数据/API问题的利器 |
| 🟡 | claude-mem | 替代手工memory，自动积累分析经验 |
| 🟡 | planning-with-files | 多场比赛分析跟踪进度 |
| 🟡 | git-commit-writer | 规范化提交 |
| 🟢 | firecrawl | 以后可能需要绕过反爬 |
| 🟢 | Document Skills | 生成分析报告PDF |

---

## ⚠️ 安全提醒

- Snyk扫描4000个skill: **36.82%有安全缺陷**，13.4%有严重漏洞
- 283个skill被发现泄露API密钥
- 安装前检查: GitHub Stars >1000、有维护记录、description为路由规则、有references/分层
- 优先选择: Anthropic官方 / Microsoft官方 / 10K+ stars发布者
