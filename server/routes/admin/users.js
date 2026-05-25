const router = require('express').Router()
const pool = require('../../config/db')
const { adminRequired } = require('../../middleware/auth')

router.use(adminRequired)

function serverError(res, logMsg) {
  if (logMsg) console.error('[admin-users]', logMsg)
  return res.status(500).json({ code: 500, message: '服务器内部错误，请稍后重试' })
}

// 脱敏函数
function maskPhone(phone) {
  if (!phone || phone.length < 7) return phone
  return phone.slice(0, 3) + '****' + phone.slice(-4)
}

router.get('/', async (req, res) => {
  const page = Math.max(parseInt(req.query.page) || 1, 1)
  const pageSize = Math.min(Math.max(parseInt(req.query.pageSize) || 50, 1), 200)
  try {
    // 显式列出字段，排除敏感信息
    const [rows] = await pool.query(
      `SELECT u.id, u.nickname, u.real_name, u.phone, u.is_verified, u.role,
        u.total_orders, u.total_gas_amount, u.last_order_date, u.created_at,
        s.name as station_name
       FROM users u LEFT JOIN stations s ON u.assigned_station_id=s.id
       ORDER BY u.created_at DESC LIMIT ? OFFSET ?`,
      [pageSize, (page - 1) * pageSize]
    )
    // 手机号脱敏
    rows.forEach(r => { r.phone = maskPhone(r.phone) })

    const [[{total}]] = await pool.query('SELECT COUNT(*) as total FROM users')
    res.json({ code: 0, data: { items: rows, total, page } })
  } catch (e) { return serverError(res, '用户列表失败: ' + e.message) }
})

module.exports = router
