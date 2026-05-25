const express = require('express')
const router = express.Router()
const crypto = require('crypto')
const pool = require('../config/db')
const { z } = require('zod')
const validate = require('../middleware/validate')

const { serverError } = require('../utils/response')

router.post('/send', validate({ body: z.object({ phone: z.string().regex(/^\d{11}$/, '手机号格式不正确') }) }), async (req, res) => {
  const { phone } = req.body
  try {
    const [recent] = await pool.query('SELECT id FROM sms_codes WHERE phone = ? AND created_at > DATE_SUB(NOW(), INTERVAL 60 SECOND)', [phone])
    if (recent.length > 0) return res.status(429).json({ code: 429, message: '发送过于频繁，请60秒后再试' })

    // 使用 crypto.randomInt 生成密码学安全的验证码
    const code = crypto.randomInt(100000, 1000000).toString()

    await pool.query('INSERT INTO sms_codes (phone, code, type, expired_at, created_at) VALUES (?, ?, ?, DATE_ADD(NOW(), INTERVAL 5 MINUTE), NOW())', [phone, code, 'register'])

    // 生产环境不输出验证码明文
    if (process.env.NODE_ENV !== 'production') {
      console.log(`[sms][开发] ${phone} 验证码: ${code}`)
    } else {
      console.log(`[sms] 验证码已发送至 ${phone.slice(0,3)}****${phone.slice(-4)}`)
    }

    res.json({ code: 0, data: { success: true } })
  } catch (e) { return serverError(res, '发送短信失败: ' + e.message) }
})

router.post('/verify', validate({ body: z.object({ phone: z.string().regex(/^\d{11}$/), code: z.string().min(4) }) }), async (req, res) => {
  const { phone, code } = req.body
  try {
    const [result] = await pool.query('UPDATE sms_codes SET is_used = 1 WHERE phone = ? AND code = ? AND is_used = 0 AND expired_at > NOW()', [phone, code])
    if (result.affectedRows === 0) return res.json({ code: 400, data: { success: false }, message: '验证码错误或已过期' })
    res.json({ code: 0, data: { success: true } })
  } catch (e) { return serverError(res, '验证短信失败: ' + e.message) }
})

module.exports = router
