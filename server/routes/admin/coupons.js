const router = require('express').Router()
const pool = require('../../config/db')
const { z } = require('zod')
const validate = require('../../middleware/validate')
const opLog = require('../../middleware/opLog')

const couponSchema = z.object({
  name: z.string().min(1), type: z.enum(['fixed','percent']),
  value: z.number().positive(), min_amount: z.number().optional(),
  total_count: z.number().int(), start_time: z.string(),
  end_time: z.string(), status: z.number().int().optional(),
})

router.get('/', async (req, res) => {
  const page = Math.max(parseInt(req.query.page) || 1, 1)
  const pageSize = Math.min(Math.max(parseInt(req.query.pageSize) || 50, 1), 200)
  try {
    const [rows] = await pool.query('SELECT id, name, type, value, min_amount, total_count, received_count, used_count, start_time, end_time, status, sort_order, created_at FROM coupons ORDER BY created_at DESC LIMIT ? OFFSET ?', [pageSize, (page - 1) * pageSize])
    const [[{total}]] = await pool.query('SELECT COUNT(*) as total FROM coupons')
    res.json({ code: 0, data: { items: rows, total, page } })
  } catch (e) {
    console.error('[admin-coupons] 列表失败:', e.message)
    res.status(500).json({ code: 500, message: '服务器内部错误，请稍后重试' })
  }
})

router.post('/', opLog('创建优惠券', 'coupon'), validate({ body: couponSchema }), async (req, res) => {
  try {
    const [r] = await pool.query('INSERT INTO coupons SET ?', [req.body])
    res.json({ code: 0, data: { id: r.insertId } })
  } catch (e) { res.status(500).json({ code: 500, message: '服务器内部错误' }) }
})

router.put('/:id', opLog('更新优惠券', 'coupon'), validate({ body: couponSchema.partial() }), async (req, res) => {
  try {
    const [result] = await pool.query('UPDATE coupons SET ? WHERE id=?', [req.body, req.params.id])
    if (result.affectedRows === 0) return res.json({ code: 404, message: '优惠券不存在' })
    res.json({ code: 0, data: { success: true } })
  } catch (e) { res.status(500).json({ code: 500, message: '服务器内部错误' }) }
})

module.exports = router
