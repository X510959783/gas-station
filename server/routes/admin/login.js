const router = require('express').Router()
const bcrypt = require('bcryptjs')
const jwt = require('jsonwebtoken')
const pool = require('../../config/db')
const cfg = require('../../config/env')
const SECRET = cfg.JWT_SECRET || require('crypto').randomBytes(32).toString('hex')
const { z } = require('zod')
const validate = require('../../middleware/validate')

const MAX_FAILURES = 5
const BLOCK_MINUTES = 15

function serverError(res, logMsg) {
  if (logMsg) console.error('[admin-login]', logMsg)
  return res.status(500).json({ code: 500, message: '服务器内部错误，请稍后重试' })
}

// 登录失败检查 — 基于数据库（进程重启不丢失）
async function checkLoginBlock(username, ip) {
  const [rows] = await pool.query(
    'SELECT COUNT(*) as c FROM login_attempts WHERE username=? AND ip=? AND created_at > DATE_SUB(NOW(), INTERVAL ? MINUTE)',
    [username, ip, BLOCK_MINUTES]
  )
  return rows[0].c >= MAX_FAILURES
}
async function recordLoginFailure(username, ip) {
  await pool.query('INSERT INTO login_attempts (username, ip, created_at) VALUES (?, ?, NOW())', [username, ip])
}

const loginSchema = z.object({
  username: z.string().min(1, '请输入用户名'),
  password: z.string().min(1, '请输入密码'),
})

router.post('/', validate({ body: loginSchema }), async (req, res) => {
  const ip = req.ip || req.connection?.remoteAddress || 'unknown'
  const { username, password } = req.body
  try {
    if (await checkLoginBlock(username, ip)) {
      return res.status(429).json({ code: 429, message: `登录失败次数过多，请${BLOCK_MINUTES}分钟后再试` })
    }
    const [rows] = await pool.query('SELECT id, username, password_hash, real_name, role, status FROM admins WHERE username = ? AND status = 1', [username])
    if (rows.length === 0) {
      await recordLoginFailure(username, ip)
      return res.status(401).json({ code: 401, message: '用户名或密码错误' })
    }
    const admin = rows[0]
    const valid = await bcrypt.compare(password, admin.password_hash)
    if (!valid) {
      await recordLoginFailure(username, ip)
      return res.status(401).json({ code: 401, message: '用户名或密码错误' })
    }
    await pool.query('UPDATE admins SET last_login_at = NOW() WHERE id = ?', [admin.id])
    const token = jwt.sign(
      { id: admin.id, type: 'admin', role: admin.role, real_name: admin.real_name },
      SECRET, { expiresIn: '7d' }
    )
    res.json({ code: 0, data: { token, user: { id: admin.id, username: admin.username, real_name: admin.real_name, role: admin.role } } })
  } catch (e) { return serverError(res, '管理员登录失败: ' + e.message) }
})

module.exports = router
