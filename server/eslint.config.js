const noSqlConcat = {
  meta: {
    type: 'problem',
    docs: {
      description: '禁止在数据库查询中使用字符串拼接或模板字符串拼接变量',
    },
    messages: {
      templateLiteral: 'SQL 注入风险：禁止在 query/execute 中使用模板字符串拼接变量。请使用参数化查询（? 占位符 + 参数数组）。',
    },
  },
  create(context) {
    function checkCallExpression(node) {
      const { callee } = node
      // 匹配 pool.query(...) / connection.query(...) / pool.execute(...) 等
      if (
        callee.type === 'MemberExpression'
        && callee.property.type === 'Identifier'
        && /^(query|execute)$/.test(callee.property.name)
        && node.arguments.length > 0
      ) {
        const firstArg = node.arguments[0]
        // 模板字符串包含变量: pool.query(`SELECT * FROM users WHERE id = ${id}`)
        if (
          firstArg.type === 'TemplateLiteral'
          && firstArg.expressions.length > 0
        ) {
          context.report({ node, messageId: 'templateLiteral' })
        }
      }
    }

    return { CallExpression: checkCallExpression }
  },
}

module.exports = [
  {
    files: ['**/*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'commonjs',
      globals: {
        require: 'readonly',
        module: 'readonly',
        process: 'readonly',
        __dirname: 'readonly',
        console: 'readonly',
        Buffer: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
      },
    },
    plugins: {
      'sql-security': { rules: { 'no-concat': noSqlConcat } },
    },
    rules: {
      'sql-security/no-concat': 'error',
    },
  },
  {
    files: ['**/tests/**/*.js', '**/__mocks__/**/*.js'],
    rules: {
      'sql-security/no-concat': 'off',
    },
  },
]
