const bcrypt = require('bcryptjs')
const mysql = require('mysql2/promise')
const cfg = require('./config/env')

const DB_CONFIG = {
  host: cfg.DB.host,
  user: cfg.DB.user,
  password: cfg.DB.password,
  database: cfg.DB.database,
}

// 必须通过环境变量指定
const ADMIN_USERNAME = process.env.RESET_USERNAME
const NEW_PASSWORD = process.env.RESET_PASSWORD

async function resetPassword() {
  if (!ADMIN_USERNAME || !NEW_PASSWORD) {
    console.error('[reset-password] 错误：必须设置 RESET_USERNAME 和 RESET_PASSWORD 环境变量')
    process.exit(1)
  }

  let conn
  try {
    conn = await mysql.createConnection(DB_CONFIG)
    console.log('[reset-password] 数据库连接成功')

    // 异步 bcrypt（不阻塞事件循环）
    const hash = await bcrypt.hash(NEW_PASSWORD, 10)

    const [rows] = await conn.query('SELECT id, username, real_name FROM admins WHERE username = ?', [ADMIN_USERNAME])

    if (rows.length === 0) {
      console.log(`[reset-password] 账号"${ADMIN_USERNAME}"不存在，正在创建...`)
      await conn.query(
        'INSERT INTO admins (username, password_hash, real_name, role) VALUES (?, ?, ?, ?)',
        [ADMIN_USERNAME, hash, '管理员', 'super_admin']
      )
      console.log('[reset-password] 账号创建成功')
    } else {
      await conn.query('UPDATE admins SET password_hash = ? WHERE username = ?', [hash, ADMIN_USERNAME])
      console.log('[reset-password] 密码更新成功')
    }

    // 不输出任何凭据到日志
    console.log('[reset-password] 用户密码已重置（通过环境变量）')

  } catch (err) {
    console.error('[reset-password] 操作失败:', err.message)
  } finally {
    if (conn) await conn.end()
  }
}

// 仅直接运行时执行
if (require.main === module) {
  resetPassword()
}

module.exports = { resetPassword }
