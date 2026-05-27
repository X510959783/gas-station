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

    const hash = await bcrypt.hash(NEW_PASSWORD, 10)

    const [rows] = await conn.query('SELECT id, username, real_name FROM admins WHERE username = ?', [ADMIN_USERNAME])

    if (rows.length === 0) {
      await conn.query(
        'INSERT INTO admins (username, password_hash, real_name, role) VALUES (?, ?, ?, ?)',
        [ADMIN_USERNAME, hash, '管理员', 'super_admin']
      )
    } else {
      await conn.query('UPDATE admins SET password_hash = ? WHERE username = ?', [hash, ADMIN_USERNAME])
    }

    // 生产环境不应输出操作凭据
    if (process.env.NODE_ENV !== 'production') {
      console.log('[reset-password] 密码重置完成')
    }

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
