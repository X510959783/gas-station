const router = require('express').Router()
const pool = require('../../config/db')
const { adminRequired } = require('../../middleware/auth')
const { z } = require('zod')
const validate = require('../../middleware/validate')
const opLog = require('../../middleware/opLog')
const { serverError } = require('../../utils/response')

router.use(adminRequired)

// 订单列表
router.get('/', async (req, res) => {
  const { status, station_id, order_no, page: p, pageSize: ps } = req.query
  const page = Math.max(parseInt(p) || 1, 1)
  const pageSize = Math.min(Math.max(parseInt(ps) || 20, 1), 100)

  let base = 'FROM orders o LEFT JOIN users u ON o.user_id=u.id LEFT JOIN stations s ON o.station_id=s.id WHERE 1=1'
  const params = []
  if (status) { base += ' AND o.status=?'; params.push(status) }
  if (station_id) { base += ' AND o.station_id=?'; params.push(parseInt(station_id)) }
  if (order_no) { base += ' AND o.order_no LIKE ?'; params.push('%' + order_no.replace(/[%_]/g, '') + '%') }

  try {
    const sql = 'SELECT o.*, u.nickname, u.phone as user_phone, s.name as station_name ' + base + ' ORDER BY o.created_at DESC LIMIT ? OFFSET ?'
    const [[{total}]] = await pool.query('SELECT COUNT(*) as total ' + base, params)
    const [rows] = await pool.query(sql, [...params, pageSize, (page - 1) * pageSize])
    res.json({ code: 0, data: { items: rows, total, page } })
  } catch (e) { return serverError(res, '订单列表失败: ' + e.message) }
})

// 通用状态更新（校验 affectedRows）
async function updateStatus(res, id, status, extra = '', logName) {
  try {
    const sql = `UPDATE orders SET status=?${extra ? ', ' + extra : ''} WHERE id=? AND status!='completed' AND status!='cancelled'`
    const [result] = await pool.query(sql, [...status.split(','), id])
    if (result.affectedRows === 0) return res.json({ code: 404, message: '订单不存在或状态已完结' })
    res.json({ code: 0, data: { success: true } })
  } catch (e) {
    console.error(`[admin-orders] ${logName}失败:`, e.message)
    res.status(500).json({ code: 500, message: '服务器内部错误，请稍后重试' })
  }
}

router.put('/:id/deliver', opLog('标记配送', 'order'), (req, res) =>
  updateStatus(res, req.params.id, 'delivering', 'delivered_time=NOW()', '标记配送'))

router.put('/:id/complete', opLog('标记送达', 'order'), (req, res) =>
  updateStatus(res, req.params.id, 'completed', '', '标记送达'))

router.post('/:id/assign', opLog('派单', 'order'), validate({ body: z.object({ driver_id: z.number().int() }) }), async (req, res) => {
  try {
    const [result] = await pool.query(
      "UPDATE orders SET driver_id=?, status='assigned' WHERE id=? AND status NOT IN ('completed','cancelled')",
      [req.body.driver_id, req.params.id]
    )
    if (result.affectedRows === 0) return res.json({ code: 404, message: '订单不存在或已完结' })
    res.json({ code: 0, data: { success: true } })
  } catch (e) { return serverError(res, '派单失败: ' + e.message) }
})

module.exports = router
