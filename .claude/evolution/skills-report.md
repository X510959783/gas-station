# Claude Code Skills 全网调查报告

> 2026-05-26 | 综合 GitHub、技术博客、社区讨论

---

## 一、Skills 是什么

Skills 是 Claude Code 的扩展机制——用 `SKILL.md` 文件定义专业工作流，Claude 自动检测并在任务匹配时加载。

| 对比 | Skills（新） | 旧 Slash Commands |
|------|:--:|:--:|
| 触发方式 | Claude 自动判断 + 手动 `/` | 只能手动 `/` |
| 文件结构 | 目录（可含脚本/模板/参考文档） | 单个 .md 文件 |
| 动态上下文 | 支持 `!` shell 命令注入 | 不支持 |
| 子 Agent 委托 | 支持 | 不支持 |

---

## 二、跟我们项目直接相关的 Skills

### 🔴 必须安装

| Skill | 来源 | 对我们有什么用 | 安装 |
|------|------|------|------|
| **code-reviewer** | superpowers-zh | 每次分析脚本写完自动审查——减少编码错误/逻辑漏洞/阈值不一致 | `npx superpowers-zh` |
| **TDD / writing-plans** | superpowers-zh | 框架改进前先出计划——不是边写边改 | 同上 |
| **systematic-debugging** | superpowers-zh | 四阶段调试法——排查数据解析/API编码问题的利器 | 同上 |
| **brainstorming** | superpowers-zh | 框架升级前先头脑风暴→设计方案→审批→执行 | 同上 |

### 🟡 强烈推荐

| Skill | 来源 | 用途 |
|------|------|------|
| **zh-code-reviewer** | claude-code-skills-zh | 中文代码审查，输出中文报告 |
| **perf-profiler** | claude-code-skills-zh | 分析脚本性能瓶颈 |
| **refactor-advisor** | claude-code-skills-zh | 识别代码坏味道并给重构建议 |
| **claude-mem** | 全球 72K+⭐ | 跨会话自动记忆——我们的记忆规则可以自动化 |

### 🟢 未来可能有用

| Skill | 用途 |
|------|------|
| **TrendRadar** (56.7K⭐) | AI舆情监控——监控足彩市场动态和新闻 |
| **caveman** (57K⭐) | 节省 65% token——分析脚本可以更精简 |
| **视频制作类** | 有需要时做分析报告视频 |

---

## 三、对我们最有价值的架构模式

### Planner → Worker → Reviewer 链

这是行业最佳实践——恰好我们已经在做类似的事：

```
Planner（设计分析方案）
  → Worker（执行数据解析 + 六维评分）
    → Reviewer（验证结果 + 检查一致性）
```

**我们缺的是 Reviewer 环节。** 目前分析结果没有独立的审查步骤，导致编码错误、阈值不一致、输出漏项等问题反复出现。

### 安装 code-reviewer 之后的工作流

```
1. /brainstorming → 讨论框架改进
2. 修改 full_analysis.py
3. /code-reviewer → 自动审查代码（类型/逻辑/阈值一致性）
4. 修复问题 → 继续
```

---

## 四、安装计划

### 立即安装（今天）

```bash
# superpowers-zh（含 brainwriting + code-reviewer + TDD + debugging）
npx superpowers-zh

# claude-code-skills-zh（中文优化）
git clone https://github.com/laolaoshiren/claude-code-skills-zh.git
cp -r claude-code-skills-zh/skills/zh-code-reviewer ~/.claude/skills/
```

### 评估后安装

```bash
# claude-mem（自动跨会话记忆）
npx skills add claude-mem

# caveman（节省token）
npx skills add caveman
```

---

## 五、预期收益

| 问题 | 现在怎么解决的 | 安装 Skill 后 |
|------|------|------|
| 代码 bug 反复出现 | 用户发现 → 我再改 | Reviewer 自动抓 |
| 框架改了但代码没同步 | 用户指出 → 我再修 | Reviewer 检查一致性 |
| 调试效率低 | 逐行 print 排查 | systematic-debugging 四阶段法 |
| 分析输出漏项 | 用户发现 → 补 | TDD 先定义输出标准 |
| 记忆规则手工维护 | 手动写 memory 文件 | claude-mem 自动记录 |
