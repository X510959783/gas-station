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
// 全局限流
app.use(rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 200,
  message: { code: 429, message: '请求过于频繁，请稍后再试' }
}))

// 敏感接口严格限流（登录/短信）
const strictLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 5,
  message: { code: 429, message: '操作过于频繁，请1分钟后再试' }
})
app.use('/api/auth', strictLimiter)
app.use('/api/sms', strictLimiter)
app.use('/api/admin/login', strictLimiter)
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

// 智能预警引擎（每日凌晨2:00自动巡检）
const { startScheduler } = require('./utils/scheduler')
startScheduler()

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
  res.status(404).json({ code: 404, message: '接口不存在' })
})

// ─── 全局错误处理 ───
app.use((err, req, res, next) => {
  logger.error(`[${req.id}] ${err.message}`, { stack: err.stack, url: req.originalUrl })
  const status = err.status || 500
  res.status(status).json({
    code: status,
    message: status === 500 ? '服务器内部错误' : err.message
  })
})

app.listen(cfg.PORT, () => {
  logger.info(`园中园燃气后端服务运行在 http://localhost:${cfg.PORT}`)
})
