1. 读 `.claude/evolution/lessons.md` 最后 10 条教训
2. 检查是否有重复出现的教训 → 升级为 pattern
3. 检查是否有出现 3 次以上的 pattern → 升级为 rule
4. **运行 `node server/scripts/calibration-score.js` → 查看 Brier 分数和校准偏差**
   - Brier > 0.20 持续 → 哪个领域偏差最大？→ 写思维规则修正
   - 系统性过度自信/不够自信 → 调整对应领域的默认确信度偏移
   - 验证过的预测如果涉及新场景 → 追加到 `.claude/evolution/base-rates.md`
5. 更新 `.claude/evolution/rules-evolved.md` 如有新规则（含校准驱动的修正）
6. 如有新规则 → 同步到 `.claude/rules.md` 内嵌
7. WebSearch 获取最新的 OWASP/Node.js/安全/架构 最佳实践
8. 将发现写入 `.claude/evolution/lessons.md`
9. 更新 `.claude/session-handoff.md`
