---
name: check-hub
description: 检查共享中枢：执行 pending.md 中分配给 Claude Code 的任务，回应三位一体
---
立即执行以下步骤：

1. 读取 D:\AI-Knowledge\review\pending.md，找到 @ClaudeCode 标记的任务
2. 按优先级排序，依次执行
3. 每完成一个任务，在 pending.md 中将状态改为 ✅
4. 将执行结果写入 D:\AI-Knowledge\review\feedback-claude-code.md
5. 如果有三位一体待回应，阅读以下文件后写入 feedback-claude-code.md：
   - D:\AI-Knowledge\review\collaboration-protocol.md
   - D:\AI-Knowledge\review\feedback-openclaw.md
   - 回答：.claude/rules.md 是否自动加载？能否通过 CLI/API 被外部唤醒？推荐什么通信方式？对协作协议有什么修改建议？
