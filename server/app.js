require('./config/env') // 必须在最前面加载环境变量

const express = require('express')
const cors = require('cors')
const helmet = require('helmet')
const rateLimit = require('express-rate-limit')
const bodyParser = require('body-parser')
const requestId = require('./middleware/requestId')
const logger = require('./utils/logger')
const cfg = require('./config/env')

const app = express()

// ─── 全局中间件 ───
app.use(requestId)          // 请求追踪 ID
app.use(helmet())           // 安全头
app.use(cors({
  origin: (origin, cb) => {
    // 生产环境严格校验，开发环境允许所有来源
    if (!origin || cfg.NODE_ENV !== 'production' || cfg.CORS_ORIGINS.includes(origin)) {
      cb(null, true)
    } else {
      cb(null, false) // 返回 CORS 错误而非抛异常
    }
  }
}))
// 全局限流（测试环境跳过）
if (cfg.NODE_ENV !== 'test') {
  app.use(rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 200,
    message: { type: 'https://api.yzygas.com/errors/too-many-requests', title: 'Too Many Requests', status: 429, detail: '请求过于频繁，请稍后再试' }
  }))

  // 敏感接口严格限流（登录/短信）
  const strictLimiter = rateLimit({
    windowMs: 60 * 1000,
    max: 5,
    message: { type: 'https://api.yzygas.com/errors/too-many-requests', title: 'Too Many Requests', status: 429, detail: '操作过于频繁，请1分钟后再试' }
  })
  app.use('/api/auth', strictLimiter)
  app.use('/api/sms', strictLimiter)
  app.use('/api/admin/login', strictLimiter)
}
app.use(bodyParser.json({ limit: '1mb' }))

// ─── 请求日志 ───
app.use((req, res, next) => {
  const start = Date.now()
  res.on('finish', () => {
    logger.info(`${req.method} ${req.originalUrl} ${res.statusCode} ${Date.now() - start}ms`, {
      requestId: req.id,
      method: req.method,
      url: req.originalUrl,
      status: res.statusCode,
      duration: Date.now() - start,
    })
  })
  next()
})

// ─── 路由 ───
app.use('/api/auth', require('./routes/auth'))
app.use('/api/sms', require('./routes/sms'))
app.use('/api/products', require('./routes/products'))
app.use('/api/orders', require('./routes/orders'))
// 拆分后的 admin 子路由
app.use('/api/admin', require('./routes/admin/index'))
app.use('/api/stations', require('./routes/stations'))
app.use('/api/coupons', require('./routes/coupons'))
app.use('/api/feedback', require('./routes/feedback'))

// 智能预警引擎（每日凌晨2:00自动巡检，测试环境不启动）
if (cfg.NODE_ENV !== 'test') {
  const { startScheduler } = require('./utils/scheduler')
  startScheduler()
}

// ─── 健康检查 ───
app.get('/api/health', async (req, res) => {
  try {
    const pool = require('./config/db')
    await pool.query('SELECT 1')
    res.json({ status: 'ok', db: 'connected', time: new Date().toISOString() })
  } catch {
    res.status(503).json({ status: 'error', db: 'disconnected', time: new Date().toISOString() })
  }
})

// ─── 404 ───
app.use((req, res) => {
  res.status(404).json({
    type: 'https://api.yzygas.com/errors/not-found',
    title: 'Not Found',
    status: 404,
    detail: '接口不存在',
  })
})

// ─── 全局错误处理 (RFC 9457) ───
app.use((err, req, res, next) => {
  // AppError 实例 → RFC 9457 格式
  if (err.isOperational) {
    return res.status(err.status).json(err.toJSON())
  }

  // 未知错误 → 记录完整堆栈，返回安全消息
  logger.error(`[${req.id}] ${err.message}`, { stack: err.stack, url: req.originalUrl })
  res.status(500).json({
    type: 'https://api.yzygas.com/errors/internal-server-error',
    title: 'Internal Server Error',
    status: 500,
    detail: '服务器内部错误，请稍后重试',
  })
})

// ─── 全局未捕获异常保护（生产环境） ───
if (cfg.NODE_ENV !== 'test') {
  process.on('uncaughtException', (err) => {
    logger.error(`未捕获异常: ${err.message}`, { stack: err.stack })
    process.exit(1)
  })

  process.on('unhandledRejection', (reason) => {
    logger.error(`未处理的 Promise 拒绝: ${reason}`, { stack: reason?.stack })
  })
}

module.exports = app

// 测试环境下不启动 HTTP 服务（supertest 直接使用 app 对象）
if (cfg.NODE_ENV !== 'test') {
  app.listen(cfg.PORT, () => {
    logger.info(`园中园燃气后端服务运行在 http://localhost:${cfg.PORT}`)
  })
}
