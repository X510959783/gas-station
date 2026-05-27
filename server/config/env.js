const path = require('path')
const dotenv = require('dotenv')

// 从项目根加载 .env（优先），无则从 .env.example 复制
dotenv.config({ path: path.resolve(__dirname, '..', '.env') })

// 生产环境强制要求 JWT_SECRET
if (process.env.NODE_ENV === 'production' && !process.env.JWT_SECRET) {
  console.error('[严重] 生产环境必须设置 JWT_SECRET 环境变量！')
  process.exit(1)
}

// JWT_SECRET: 环境变量优先，开发模式生成一次全局共享的随机密钥
// 保证所有模块（middleware/auth, routes/auth, routes/orders等）使用同一个密钥
const JWT_SECRET = process.env.JWT_SECRET || require('crypto').randomBytes(32).toString('hex')

function safeParseInt(val, defaultVal) {
  const n = parseInt(val)
  return Number.isNaN(n) ? defaultVal : n
}

module.exports = {
  PORT: safeParseInt(process.env.PORT, 3000),
  NODE_ENV: process.env.NODE_ENV || 'development',
  DB: {
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '',
    database: process.env.DB_NAME || 'gas_station',
  },
  JWT_SECRET,
  MAX_ORDER_QTY: safeParseInt(process.env.MAX_ORDER_QTY, 99),
  MAX_PAGE_SIZE: safeParseInt(process.env.MAX_PAGE_SIZE, 100),
  CORS_ORIGINS: process.env.CORS_ORIGINS
    ? process.env.CORS_ORIGINS.split(',').map(s => s.trim())
    : ['http://localhost:5173', 'http://localhost:3000'],
}
