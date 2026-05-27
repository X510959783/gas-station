const router = require('express').Router()
const pool = require('../../config/db')
const opLog = require('../../middleware/opLog')
const { serverError } = require('../../utils/response')

router.get('/', async (req, res) => {
  const { status, page: p, pageSize: ps } = req.query
  const page = Math.max(parseInt(p) || 1, 1)
  const pageSize = Math.min(Math.max(parseInt(ps) || 50, 1), 200)
  let where = ''; const params = []
  if (status) { where = ' WHERE d.status=?'; params.push(status) }
  try {
    const [[{total}]] = await pool.query('SELECT COUNT(*) as total FROM deposits d' + where, params)
    const [rows] = await pool.query(
      'SELECT d.id, d.user_id, d.bottle_count, d.deposit_per_bottle, d.returned_count, d.status, d.created_at, u.nickname as user_nickname, u.real_name as user_real_name FROM deposits d LEFT JOIN users u ON d.user_id=u.id' + where + ' ORDER BY d.created_at DESC LIMIT ? OFFSET ?',
      [...params, pageSize, (page - 1) * pageSize]
    )
    res.json({ code: 0, data: { items: rows, total, page } })
  } catch (e) { return serverError(res, '押金列表失败: ' + e.message) }
})

// 退还押金 — 原子操作防竞态
router.put('/:id/return', opLog('退还押金', 'deposit'), async (req, res) => {
  const { returned_count } = req.body
  const count = parseInt(returned_count) || 0
  if (count <= 0) return res.status(400).json({ code: 400, message: '退还数量无效' })
  try {
    // 原子 UPDATE，无需 SELECT 再 UPDATE
    const [result] = await pool.query(
      `UPDATE deposits SET returned_count = returned_count + ?,
       status = CASE WHEN returned_count + ? >= bottle_count THEN 'returned' ELSE 'active' END
       WHERE id = ? AND (status = 'active' OR status = 'pending')`,
      [count, count, req.params.id]
    )
    if (result.affectedRows === 0) {
      return res.json({ code: 404, message: '押金记录不存在或状态不允许退还' })
    }
    // 获取更新后的记录计算退款
    const [updated] = await pool.query('SELECT id, bottle_count, deposit_per_bottle FROM deposits WHERE id = ?', [req.params.id])
    const d = updated[0]
    const refund = count * (d.deposit_per_bottle || 0)
    res.json({ code: 0, data: { success: true, refund } })
  } catch (e) { return serverError(res, '退还押金失败: ' + e.message) }
})

module.exports = router
