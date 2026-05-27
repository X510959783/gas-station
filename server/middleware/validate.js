/**
 * Zod 校验中间件生成器 — 使用：validate({ body: schema, query: schema, params: schema })
 * 校验失败 → next(ValidationError) → 全局错误处理 → RFC 9457 响应
 */
const { ValidationError } = require('../utils/errors')

function validate(schemas) {
  return (req, res, next) => {
    const errors = []
    for (const field of ['body', 'query', 'params']) {
      const schema = schemas[field]
      if (schema) {
        const result = schema.safeParse(req[field])
        if (!result.success) {
          errors.push(...result.error.issues.map(e => ({
            field: `${field}.${e.path.join('.')}`,
            message: e.message,
          })))
        } else if (result.data !== undefined) {
          req[field] = result.data
        }
      }
    }
    if (errors.length) {
      return next(new ValidationError(errors))
    }
    next()
  }
}

module.exports = validate
