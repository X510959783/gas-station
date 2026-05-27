const express = require('express')
const router = express.Router()
const jwt = require('jsonwebtoken')
const pool = require('../config/db')
const { authRequired } = require('../middleware/auth')
const { z } = require('zod')
const validate = require('../middleware/validate')
const { serverError } = require('../utils/response')

// JWT 密钥：统一从 config/env 获取（所有模块共享同一密钥）
const { JWT_SECRET: SECRET } = require('../config/env')

// 微信登录 - 生产环境调用微信接口，开发环境用 mock
router.post('/wx-login', validate({ body: z.object({ code: z.string().optional() }) }), async (req, res) => {
  const { code } = req.body
  try {
    let openId
    if (process.env.NODE_ENV === 'production') {
      // TODO: 对接微信 code2session 接口获取真实 openid
      if (!code) return res.status(400).json({ code: 400, message: '请提供微信授权码' })
      openId = 'wx_' + code // 替换为实际微信接口调用
    } else {
      openId = 'mock_openid_' + (code || Date.now())
      console.log('[auth] 开发模式微信登录, openId:', openId)
    }
    let [rows] = await pool.query('SELECT id, open_id, nickname, real_name, phone, is_verified, role, total_orders FROM users WHERE open_id = ?', [openId])
    if (rows.length === 0) {
      const [result] = await pool.query('INSERT INTO users (open_id, nickname, role, created_at) VALUES (?, ?, ?, NOW())', [openId, '微信用户', 'customer'])
      const [newUser] = await pool.query('SELECT id, open_id, nickname, is_verified, role FROM users WHERE id = ?', [result.insertId])
      rows = newUser
    }
    const user = rows[0]
    const token = jwt.sign({ id: user.id, iat: Math.floor(Date.now() / 1000) }, SECRET, { expiresIn: '7d' })
    res.json({ code: 0, data: { token, is_verified: user.is_verified, user: { id: user.id, nickname: user.nickname } } })
  } catch (e) { return serverError(res, 'wx-login 失败: ' + e.message, 'auth') }
})

const registerSchema = z.object({
  real_name: z.string().min(1, '请输入姓名'),
  id_card: z.string().length(18, '身份证号应为18位'),
  phone: z.string().regex(/^\d{11}$/, '手机号格式不正确'),
  address: z.string().min(1, '请输入地址'),
  sms_code: z.string().optional(),
})

// 实名注册（事务保护，防止竞态条件）
router.post('/register', authRequired, validate({ body: registerSchema }), async (req, res) => {
  const { real_name, id_card, phone, address, sms_code } = req.body
  const conn = await pool.getConnection()
  try {
    await conn.beginTransaction()
    // SELECT FOR UPDATE 防止并发竞态
    const [current] = await conn.query('SELECT is_verified FROM users WHERE id = ? FOR UPDATE', [req.user.id])
    if (current.length > 0 && current[0].is_verified) {
      await conn.rollback()
      conn.release()
      return res.json({ code: 1, message: '您已完成实名认证，无需重复注册', data: { success: false } })
    }
    if (!sms_code) {
      if (process.env.NODE_ENV === 'production') {
        await conn.rollback()
        conn.release()
        return res.status(400).json({ code: 400, message: '请提供短信验证码' })
      }
      console.log('[auth] 开发模式跳过短信验证')
    } else {
      const [smsRows] = await conn.query('SELECT id, phone, code, is_used, expired_at FROM sms_codes WHERE phone = ? AND code = ? AND is_used = 0 AND expired_at > NOW() ORDER BY created_at DESC LIMIT 1 FOR UPDATE', [phone, sms_code])
      if (smsRows.length === 0) {
        await conn.rollback()
        conn.release()
        return res.status(400).json({ code: 400, message: '验证码错误或已过期' })
      }
      await conn.query('UPDATE sms_codes SET is_used = 1 WHERE id = ?', [smsRows[0].id])
    }
    await conn.query('UPDATE users SET real_name=?, id_card=?, phone=?, address=?, is_verified=1 WHERE id=? AND is_verified=0', [real_name, id_card, phone, address, req.user.id])
    await conn.commit()
    conn.release()
    res.json({ code: 0, data: { success: true }, message: '注册成功' })
  } catch (e) {
    await conn.rollback()
    conn.release()
    return serverError(res, 'register 失败: ' + e.message, 'auth')
  }
})

// 脱敏函数：身份证保留前3后4，手机号保留前3后4
function mask(str, head, tail) {
  if (!str) return ''
  return str.slice(0, head) + '***' + str.slice(-tail)
}

// 获取用户信息（敏感字段脱敏）
router.get('/profile', authRequired, async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT id, nickname, avatar, real_name, id_card, phone, address, is_verified, role, total_orders, total_gas_amount, last_order_date, avg_order_cycle, created_at FROM users WHERE id = ?', [req.user.id])
    if (rows.length === 0) return res.status(404).json({ code: 404, message: '用户不存在' })
    const user = rows[0]
    // 敏感字段脱敏后返回
    if (user.id_card) user.id_card = mask(user.id_card, 3, 4)
    if (user.phone) user.phone = mask(user.phone, 3, 4)
    res.json({ code: 0, data: user })
  } catch (e) { return serverError(res, 'profile 失败: ' + e.message, 'auth') }
})

module.exports = router
