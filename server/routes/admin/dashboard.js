const router = require('express').Router()
const pool = require('../../config/db')
const { serverError } = require('../../utils/response')

router.get('/', async (req, res) => {
  try {
    // 日期范围查询（可用索引）代替 DATE() 函数
    const now = new Date()
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString().slice(0, 19).replace('T', ' ')
    const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1).toISOString().slice(0, 19).replace('T', ' ')

    // 并行查询（5条SQL → 1次数据库往返）
    const [
      [{todayOrders}],
      [{pending}],
      [{delivering}],
      [{alerts}],
      [{todaySales}]
    ] = await Promise.all([
      pool.query('SELECT COUNT(*) as todayOrders FROM orders WHERE created_at >= ? AND created_at < ?', [todayStart, todayEnd]).then(r => r[0]),
      pool.query("SELECT COUNT(*) as pending FROM orders WHERE status IN ('pending','paid')").then(r => r[0]),
      pool.query("SELECT COUNT(*) as delivering FROM orders WHERE status='delivering'").then(r => r[0]),
      pool.query("SELECT COUNT(*) as alerts FROM warnings WHERE status='pending'").then(r => r[0]),
      pool.query("SELECT COALESCE(SUM(pay_amount),0) as todaySales FROM orders WHERE created_at >= ? AND created_at < ? AND status!='cancelled'", [todayStart, todayEnd]).then(r => r[0]),
    ])

    res.json({ code: 0, data: { todayOrders, pending, delivering, alerts, todaySales } })
  } catch (e) { return serverError(res, '仪表盘失败: ' + e.message) }
})

module.exports = router
