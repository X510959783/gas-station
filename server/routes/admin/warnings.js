const router = require('express').Router()
const pool = require('../../config/db')
const { adminRequired } = require('../../middleware/auth')
const opLog = require('../../middleware/opLog')
const { serverError } = require('../../utils/response')

router.use(adminRequired)

router.get('/', async (req, res) => {
  const { level, status } = req.query
  let sql = 'SELECT w.*, u.nickname, u.phone as user_phone FROM warnings w LEFT JOIN users u ON w.user_id=u.id WHERE 1=1'
  const params = []
  if (level) { sql += ' AND w.level=?'; params.push(level) }
  if (status) { sql += ' AND w.status=?'; params.push(status) }
  const page = Math.max(1, parseInt(req.query.page) || 1)
  const limit = Math.min(100, Math.max(1, parseInt(req.query.limit) || 20))
  const offset = (page - 1) * limit
  sql += ' ORDER BY w.created_at DESC LIMIT ? OFFSET ?'
  params.push(limit, offset)
  try {
    const [rows] = await pool.query(sql, params)
    res.json({ code: 0, data: rows })
  } catch (e) { return serverError(res, '预警列表失败: ' + e.message) }
})

router.put('/:id/resolve', opLog('处理预警', 'warning'), async (req, res) => {
  try {
    const [result] = await pool.query(
      "UPDATE warnings SET status='resolved', resolved_at=NOW() WHERE id=? AND status='pending'",
      [req.params.id]
    )
    if (result.affectedRows === 0) return res.json({ code: 404, message: '预警不存在或已处理' })
    res.json({ code: 0, data: { success: true } })
  } catch (e) { return serverError(res, '处理预警失败: ' + e.message) }
})

module.exports = router
