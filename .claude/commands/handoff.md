1. 更新 `.claude/session-handoff.md`：当前进度、待办、开放假设、已知问题、下次检查项
2. 追加本轮教训到 `.claude/evolution/lessons.md`
3. 运行 `npm test --prefix server` 确认 230 通过
4. 运行 `node server/scripts/test-feedback.js` 更新 CI 状态
5. 检查 Gateway：`netstat -ano | grep 18789`
6. 如果有 @OpenClaw 的待办 → 写入 `D:\AI-Knowledge\review\feedback-claude-code.md`
