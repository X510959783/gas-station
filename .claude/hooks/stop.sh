#!/bin/bash
# Stop Hook — 会话结束前自动保存进化状态
# 被 Claude Code 在会话退出前调用

echo "[EVOLVE-HOOK] Stop 触发 — 保存进化状态..."

# 快照当前状态
bash .claude/scripts/evolve.sh snapshot 2>&1 | tail -1

# 采集度量
bash .claude/scripts/evolve.sh metrics 2>&1 | tail -1

# 提醒：如果有未写入的学习，现在写入
echo "[EVOLVE-HOOK] 会话结束。检查是否需要 dream-memory 合并..."
