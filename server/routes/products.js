const express = require('express')
const router = express.Router()
const pool = require('../config/db')
const { serverError } = require('../utils/response')

// 商品列表（公开接口，无需登录）
router.get('/', async (req, res) => {
  try {
    const { status } = req.query
    let sql = 'SELECT id, name, spec, price, deposit_price, status, sort_order, created_at FROM products WHERE 1=1'
    const params = []
    if (status !== undefined) {
      const s = parseInt(status)
      if (!Number.isInteger(s) || s < 0) return res.status(400).json({ code: 400, message: 'status 参数无效' })
      sql += ' AND status = ?'
      params.push(s)
    }
    sql += ' ORDER BY sort_order'
    const [rows] = await pool.query(sql, params)
    res.json({ code: 0, data: rows })
  } catch (e) {
    return serverError(res, '商品列表失败: ' + e.message, 'products')
  }
})

// 商品详情（参数校验：id 必须为正整数）
router.get('/:id', async (req, res) => {
  const id = parseInt(req.params.id)
  if (!Number.isInteger(id) || id <= 0) {
    return res.status(400).json({ code: 400, message: '商品 ID 无效' })
  }
  try {
    const [rows] = await pool.query('SELECT id, name, spec, price, deposit_price, status, sort_order, created_at FROM products WHERE id = ?', [id])
    if (rows.length === 0) return res.status(404).json({ code: 404, message: '商品不存在' })
    res.json({ code: 0, data: rows[0] })
  } catch (e) {
    return serverError(res, '商品详情失败: ' + e.message, 'products')
  }
})

module.exports = router
