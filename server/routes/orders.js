const express = require('express')
const router = express.Router()
const pool = require('../config/db')
const { authRequired } = require('../middleware/auth')
const { serverError } = require('../utils/response')

// 生成订单编号（使用数据库自增ID，避免并发竞态）
function getOrderNo(date, insertId) {
  const dateStr = date.getFullYear().toString() +
    String(date.getMonth() + 1).padStart(2, '0') +
    String(date.getDate()).padStart(2, '0')
  return 'GS' + dateStr + String(insertId).padStart(6, '0')
}

// 创建订单（事务保护，避免数据不一致）
router.post('/', authRequired, async (req, res) => {
  const userId = req.user.id

  const { product_id, quantity, delivery_time, contact_name, contact_phone, delivery_address, delivery_remark } = req.body

  if (!product_id) return res.status(400).json({ code: 400, message: '请选择商品' })
  if (!contact_phone) return res.status(400).json({ code: 400, message: '请填写联系电话' })
  if (!delivery_address) return res.status(400).json({ code: 400, message: '请填写配送地址' })

  const conn = await pool.getConnection()
  try {
    await conn.beginTransaction()

    const [products] = await conn.query('SELECT id, name, price, spec, deposit_price FROM products WHERE id = ? AND status = 1 FOR UPDATE', [product_id])
    if (products.length === 0) throw { code: 400, message: '商品不存在或已下架' }
    const realProduct = products[0]

    const qty = Math.min(Math.max(quantity || 1, 1), 99)
    const realPrice = Number(realProduct.price)
    const total_amount = realPrice * qty

    const [result] = await conn.query(
      `INSERT INTO orders (order_no, user_id, product_id, product_name, product_spec, product_price, quantity, total_amount,
        contact_name, contact_phone, delivery_address, delivery_time, delivery_remark, status, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', NOW())`,
      ['TEMP', userId, realProduct.id, realProduct.name, realProduct.spec, realPrice, qty, total_amount,
       contact_name || '', contact_phone, delivery_address, delivery_time || '尽快送达', delivery_remark || '']
    )

    const insertId = result.insertId
    const order_no = getOrderNo(new Date(), insertId)
    await conn.query('UPDATE orders SET order_no = ? WHERE id = ?', [order_no, insertId])

    await conn.query(
      'UPDATE users SET total_orders = total_orders + 1, total_gas_amount = total_gas_amount + ?, last_order_date = CURDATE() WHERE id = ?',
      [total_amount, userId]
    )

    await conn.commit()
    conn.release()

    const [rows] = await pool.query('SELECT id, order_no, user_id, product_id, product_name, product_spec, product_price, quantity, total_amount, contact_name, contact_phone, delivery_address, delivery_time, delivery_remark, status, created_at FROM orders WHERE id = ?', [insertId])
    console.log('[orders] 新订单:', order_no)
    res.json({ code: 0, data: rows[0] })
  } catch (e) {
    await conn.rollback()
    conn.release()
    if (e.code === 400) return res.status(400).json(e)
    return serverError(res, '创建订单失败: ' + e.message, 'orders')
  }
})

// 订单列表（支持分页）
router.get('/', authRequired, async (req, res) => {
  const userId = req.user.id
  const { status, page, limit } = req.query
  const p = Math.max(parseInt(page) || 1, 1)
  const l = Math.min(Math.max(parseInt(limit) || 20, 1), 100)

  try {
    let where = 'WHERE user_id = ?'
    const params = [userId]
    if (status && status !== 'all') { where += ' AND status = ?'; params.push(status) }

    const [countResult] = await pool.query(`SELECT COUNT(*) as total FROM orders ${where}`, params)
    const total = countResult[0].total

    const [rows] = await pool.query(
      `SELECT id, order_no, user_id, product_id, product_name, product_spec, product_price, quantity, total_amount, contact_name, contact_phone, delivery_address, delivery_time, delivery_remark, status, created_at FROM orders ${where} ORDER BY created_at DESC LIMIT ? OFFSET ?`,
      [...params, l, (p - 1) * l]
    )
    res.json({ code: 0, data: rows, pagination: { page: p, limit: l, total, totalPages: Math.ceil(total / l) } })
  } catch (e) {
    return serverError(res, '订单列表失败: ' + e.message, 'orders')
  }
})

// 订单详情（通过 order_no）
router.get('/detail/:orderNo', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT id, order_no, user_id, product_id, product_name, product_spec, product_price, quantity, total_amount, contact_name, contact_phone, delivery_address, delivery_time, delivery_remark, status, created_at FROM orders WHERE order_no = ?', [req.params.orderNo])
    if (rows.length === 0) return res.status(404).json({ code: 404, message: '订单不存在' })
    res.json({ code: 0, data: rows[0] })
  } catch (e) {
    return serverError(res, '订单详情失败: ' + e.message, 'orders')
  }
})

module.exports = router
