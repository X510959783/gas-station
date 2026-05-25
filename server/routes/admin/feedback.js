const router = require('express').Router()
const pool = require('../../config/db')

router.get('/', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT id, user_id, content, contact, status, reply, created_at FROM feedbacks ORDER BY created_at DESC LIMIT 100')
    res.json({ code: 0, data: rows })
  } catch (e) {
    console.error('[admin-feedback] 列表失败:', e.message)
    res.status(500).json({ code: 500, message: '服务器内部错误，请稍后重试' })
  }
})

module.exports = router
