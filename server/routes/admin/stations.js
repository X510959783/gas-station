const router = require('express').Router()
const pool = require('../../config/db')
const { adminRequired } = require('../../middleware/auth')
const { z } = require('zod')
const validate = require('../../middleware/validate')
const opLog = require('../../middleware/opLog')

const stationSchema = z.object({
  name: z.string().min(1),
  short_name: z.string().optional(),
  address: z.string().min(1),
  lat: z.number().min(-90).max(90),
  lng: z.number().min(-180).max(180),
  phone: z.string().optional(),
  service_area_radius: z.number().int().optional(),
  is_default: z.number().int().optional(),
})

router.use(adminRequired)

router.get('/', async (req, res) => {
  const [rows] = await pool.query('SELECT id, name, short_name, address, lat, lng, phone, service_area_radius, sort_order, status, is_default FROM stations ORDER BY sort_order')
  res.json({ code: 0, data: rows })
})

router.post('/', opLog('创建配送站', 'station'), validate({ body: stationSchema }), async (req, res) => {
  try {
    const d = req.body
    const [r] = await pool.query('INSERT INTO stations SET ?', [d])
    res.json({ code: 0, data: { id: r.insertId } })
  } catch (e) {
    console.error('[admin-stations] 创建失败:', e.message)
    res.status(500).json({ code: 500, message: '服务器内部错误，请稍后重试' })
  }
})

router.put('/:id', opLog('更新配送站', 'station'), validate({ body: stationSchema.partial() }), async (req, res) => {
  try {
    const [result] = await pool.query('UPDATE stations SET ? WHERE id=?', [req.body, req.params.id])
    if (result.affectedRows === 0) return res.json({ code: 404, message: '配送站不存在' })
    res.json({ code: 0, data: { success: true } })
  } catch (e) { res.status(500).json({ code: 500, message: '服务器内部错误，请稍后重试' }) }
})

router.put('/:id/toggle', opLog('切换配送站状态', 'station'), async (req, res) => {
  try {
    const [result] = await pool.query('UPDATE stations SET status=1-status WHERE id=?', [req.params.id])
    if (result.affectedRows === 0) return res.json({ code: 404, message: '配送站不存在' })
    res.json({ code: 0, data: { success: true } })
  } catch (e) { res.status(500).json({ code: 500, message: '服务器内部错误，请稍后重试' }) }
})

module.exports = router
