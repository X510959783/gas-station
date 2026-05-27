执行全面审计：

1. **安全**：`grep -rn "pool\.query\|pool\.execute" server/routes/ --include="*.js"` 确认全部参数化
2. **校验**：`grep -rn "validate(" server/routes/ --include="*.js"` 列出有 Zod 的路由
3. **错误处理**：`grep -rn "res\.status.*\.json" server/routes/ --include="*.js"` 列出旧格式错误响应
4. **事务**：`grep -rn "getConnection\|beginTransaction" server/routes/ --include="*.js"` 确认写操作有事务
5. **测试**：`npx jest --passWithNoTests` 确认全量通过
6. **ESLint**：`npx eslint server/routes/ server/utils/ server/middleware/ server/app.js server/config/`
7. **Gateway**：`netstat -ano | grep 18789 | grep LISTENING`
8. 输出审计报告，标记每项 ✓ / ✗
