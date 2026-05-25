const router = require('express').Router()
const pool = require('../../config/db')
const { z } = require('zod')
const validate = require('../../middleware/validate')
const opLog = require('../../middleware/opLog')

const productSchema = z.object({
  name: z.string().min(1), spec: z.string().optional(),
  price: z.number().positive(), deposit_price: z.number().optional(),
  stock: z.number().int().optional(), status: z.number().int().optional(),
  sort_order: z.number().int().optional(),
})

router.get('/', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT id, name, spec, price, deposit_price, status, sort_order, created_at FROM products ORDER BY sort_order')
    res.json({ code: 0, data: rows })
  } catch (e) {
    console.error('[admin-products] 列表失败:', e.message)
    res.status(500).json({ code: 500, message: '服务器内部错误' })
  }
})

router.post('/', opLog('创建商品', 'product'), validate({ body: productSchema }), async (req, res) => {
  try {
    const [r] = await pool.query('INSERT INTO products SET ?', [req.body])
    res.json({ code: 0, data: { id: r.insertId } })
  } catch (e) { res.status(500).json({ code: 500, message: '服务器内部错误' }) }
})

router.put('/:id', opLog('更新商品', 'product'), validate({ body: productSchema.partial() }), async (req, res) => {
  try {
    const [result] = await pool.query('UPDATE products SET ? WHERE id=?', [req.body, req.params.id])
    if (result.affectedRows === 0) return res.json({ code: 404, message: '商品不存在' })
    res.json({ code: 0, data: { success: true } })
  } catch (e) { res.status(500).json({ code: 500, message: '服务器内部错误' }) }
})

module.exports = router
