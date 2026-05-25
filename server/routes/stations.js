const router = require('express').Router();
const pool = require('../config/db');

const { serverError } = require('../utils/response')

// 获取所有启用的配送站（小程序端用，公开接口）
router.get('/', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT id, name, short_name, address, lat, lng, phone, service_area_radius, sort_order, status FROM stations WHERE status=1 ORDER BY sort_order')
    res.json({ code: 0, data: rows })
  } catch (e) { return serverError(res, '配送站列表失败: ' + e.message) }
});

module.exports = router;
