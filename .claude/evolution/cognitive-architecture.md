# 认知分层架构 (Clean Architecture 应用于 AI Agent)

## 当前问题

```
用户需求 → [分析+实现+验证 混在一起] → 输出
              ↑ 互相污染，三件事都做不好
```

## 重构后

```
用户需求
  ↓
┌─────────────────────────────────┐
│  Layer 1: 分析层 (纯推理)        │
│  - premise + research-critique  │
│  - logical-fallacy-detector     │
│  - estimate-calibrator          │
│  → 输出: 明确的方案+验收标准     │
└──────────────┬──────────────────┘
               ↓ 方案批准
┌─────────────────────────────────┐
│  Layer 2: 实现层 (纯编码)        │
│  - python-design-patterns        │
│  - python-type-safety           │
│  - logic-lens                   │
│  → 输出: 通过所有测试的代码      │
└──────────────┬──────────────────┘
               ↓ 测试通过
┌─────────────────────────────────┐
│  Layer 3: 验证层 (纯审查)        │
│  - verification-gate            │
│  - pr-review (self)             │
│  - manuscript-provenance        │
│  → 输出: 带证据的完成声明        │
└─────────────────────────────────┘
```

## 层间接口（不可跨越）

```
Layer 1 → Layer 2: 方案文档 + 验收标准 + 测试清单
Layer 2 → Layer 3: 代码 + 测试结果 + 类型检查报告
Layer 3 → 用户:  完成声明 + 验证证据

跨层禁止:
  ❌ Layer 2 不能修改方案 (那是 Layer 1 的事)
  ❌ Layer 3 不能修改代码 (那是 Layer 2 的事)
  ❌ Layer 1 不能跳过 Layer 3 直接输出 (绕过验证)
```

## 执行规则

- 任何需求 → 必须从 Layer 1 开始，不得跳过
- Layer 1 输出不够清晰 → 不进入 Layer 2
- Layer 2 测试不通过 → 不进入 Layer 3
- Layer 3 验证失败 → 回到 Layer 2，严重问题回到 Layer 1
- 简单需求（<5行修改）→ 三层可以快速过，但不可跳过
