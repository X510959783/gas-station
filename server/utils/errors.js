// RFC 9457 错误类体系 — 统一 API 错误响应
const logger = require('./logger')

class AppError extends Error {
  constructor(status, title, detail, errors = []) {
    super(detail)
    this.status = status
    this.title = title
    this.detail = detail
    this.errors = errors
    this.isOperational = true
  }

  // RFC 9457 JSON 序列化
  toJSON() {
    return {
      type: `https://api.yzygas.com/errors/${this.title.toLowerCase().replace(/\s+/g, '-')}`,
      title: this.title,
      status: this.status,
      detail: this.detail,
      ...(this.errors.length > 0 && { errors: this.errors }),
    }
  }
}

class ValidationError extends AppError {
  constructor(errors) {
    super(422, 'Validation Error', '请求参数校验失败', errors)
  }
}

class NotFoundError extends AppError {
  constructor(detail = '请求的资源不存在') {
    super(404, 'Not Found', detail)
  }
}

class AuthError extends AppError {
  constructor(detail = '请先登录') {
    super(401, 'Unauthorized', detail)
  }
}

class ForbiddenError extends AppError {
  constructor(detail = '权限不足') {
    super(403, 'Forbidden', detail)
  }
}

class RateLimitError extends AppError {
  constructor(detail = '请求过于频繁，请稍后再试') {
    super(429, 'Too Many Requests', detail)
  }
}

class ConflictError extends AppError {
  constructor(detail) {
    super(409, 'Conflict', detail)
  }
}

// serverError — 向后兼容的 500 错误
function serverError(res, logMsg, tag) {
  const log = logger(tag || 'server')
  if (logMsg) log.error(logMsg)
  return res.status(500).json({
    type: 'https://api.yzygas.com/errors/internal-server-error',
    title: 'Internal Server Error',
    status: 500,
    detail: '服务器内部错误，请稍后重试',
  })
}

module.exports = {
  AppError,
  ValidationError,
  NotFoundError,
  AuthError,
  ForbiddenError,
  RateLimitError,
  ConflictError,
  serverError,
}
