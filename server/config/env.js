const path = require('path')
const dotenv = require('dotenv')

// 从项目根加载 .env（优先），无则从 .env.example 复制
dotenv.config({ path: path.resolve(__dirname, '..', '.env') })

// 生产环境强制要求 JWT_SECRET
if (process.env.NODE_ENV === 'production' && !process.env.JWT_SECRET) {
  console.error('[严重] 生产环境必须设置 JWT_SECRET 环境变量！')
  process.exit(1)
}

module.exports = {
  PORT: parseInt(process.env.PORT) || 3000,
  NODE_ENV: process.env.NODE_ENV || 'development',
  DB: {
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '',
    database: process.env.DB_NAME || 'gas_station',
  },
  JWT_SECRET: process.env.JWT_SECRET,
  CORS_ORIGINS: process.env.CORS_ORIGINS
    ? process.env.CORS_ORIGINS.split(',').map(s => s.trim())
    : ['http://localhost:5173', 'http://localhost:3000'],
}
