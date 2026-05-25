const router = require('express').Router()
const pool = require('../../config/db')
const { adminRequired } = require('../../middleware/auth')

function serverError(res, logMsg) {
  if (logMsg) console.error('[analysis]', logMsg)
  return res.status(500).json({ code: 500, message: '服务器内部错误，请稍后重试' })
}

// 消费排行（手机号脱敏，支持分页）
router.get('/ranking', adminRequired, async (req, res) => {
  const page = Math.max(parseInt(req.query.page) || 1, 1)
  const limit = Math.min(Math.max(parseInt(req.query.limit) || 30, 1), 100)
  try {
    const [rows] = await pool.query(
      `SELECT id, nickname, real_name,
        CONCAT(LEFT(phone,3), '****', RIGHT(phone,4)) as phone,
        total_orders, total_gas_amount, avg_order_cycle, last_order_date
       FROM users WHERE total_orders > 0
       ORDER BY total_gas_amount DESC
       LIMIT ? OFFSET ?`,
      [limit, (page - 1) * limit]
    )
    res.json({ code: 0, data: rows, pagination: { page, limit } })
  } catch (e) { return serverError(res, '消费排行失败: ' + e.message) }
})

// 销售趋势（日期范围查询代替 DATE() 函数，支持索引）
router.get('/trend', adminRequired, async (req, res) => {
  const days = Math.min(Math.max(parseInt(req.query.days) || 30, 1), 365)
  try {
    const [rows] = await pool.query(
      `SELECT DATE(created_at) as date, COUNT(*) as orders,
        COALESCE(SUM(pay_amount), 0) as sales
       FROM orders
       WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL ? DAY) AND status != 'cancelled'
       GROUP BY DATE(created_at) ORDER BY date`,
      [days]
    )
    res.json({ code: 0, data: rows })
  } catch (e) { return serverError(res, '销售趋势失败: ' + e.message) }
})

module.exports = router
