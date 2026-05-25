/**
 * Zod 校验中间件生成器
 * 使用：validate({ body: schema, query: schema, params: schema })
 */
function validate(schemas) {
  return (req, res, next) => {
    const errors = []
    for (const field of ['body', 'query', 'params']) {
      const schema = schemas[field]
      if (schema) {
        const result = schema.safeParse(req[field])
        if (!result.success) {
          errors.push(...result.error.errors.map(e => ({
            field: `${field}.${e.path.join('.')}`,
            message: e.message,
          })))
        } else {
          req[field] = result.data // 替换为校验/转换后的数据
        }
      }
    }
    if (errors.length) {
      return res.status(400).json({ code: 400, message: '参数校验失败', errors })
    }
    next()
  }
}

module.exports = validate
