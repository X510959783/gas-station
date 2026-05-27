const router = require('express').Router();
const pool = require('../config/db');
const { z } = require('zod')
const validate = require('../middleware/validate')
const { authRequired } = require('../middleware/auth');
const { serverError } = require('../utils/response')

const myCouponsSchema = z.object({
  status: z.enum(['unused', 'used', 'expired']).optional(),
})

// 可领取的优惠券
router.get('/available', authRequired, async (req, res) => {
  try {
    const [rows] = await pool.query(
      'SELECT id, name, type, value, min_amount, start_time, end_time, total_count, used_count, received_count, sort_order, created_at FROM coupons WHERE status=1 AND NOW() BETWEEN start_time AND end_time AND used_count < total_count ORDER BY created_at DESC'
    );
    res.json({ code: 0, data: rows });
  } catch (e) { return serverError(res, '优惠券列表失败: ' + e.message) }
});

// 领取优惠券（事务保护，防止竞态重复领取）
router.post('/:couponId/receive', authRequired, async (req, res) => {
  const cid = parseInt(req.params.couponId);
  if (Number.isNaN(cid) || cid <= 0) return res.status(400).json({ code: 400, message: '优惠券 ID 无效' })
  const conn = await pool.getConnection()
  try {
    await conn.beginTransaction()

    const [coupons] = await conn.query('SELECT id, name, type, value, min_amount, total_count, received_count, start_time, end_time FROM coupons WHERE id=? FOR UPDATE', [cid])
    if (coupons.length === 0) { await conn.rollback(); conn.release(); return res.json({ code: 1, message: '优惠券不存在' }) }
    const c = coupons[0];
    if (c.received_count >= c.total_count) { await conn.rollback(); conn.release(); return res.json({ code: 1, message: '已抢完' }) }

    const [got] = await conn.query('SELECT COUNT(*) as c FROM user_coupons WHERE user_id=? AND coupon_id=? FOR UPDATE', [req.user.id, cid])
    if (got[0].c > 0) { await conn.rollback(); conn.release(); return res.json({ code: 1, message: '已领取过' }) }

    await conn.query('INSERT INTO user_coupons (user_id, coupon_id, status) VALUES (?,?,"unused")', [req.user.id, cid])
    await conn.query('UPDATE coupons SET received_count=received_count+1 WHERE id=?', [cid])

    await conn.commit()
    conn.release()
    res.json({ code: 0, data: { success: true } })
  } catch (e) {
    await conn.rollback()
    conn.release()
    return serverError(res, '领取优惠券失败: ' + e.message)
  }
});

// 我的优惠券
router.get('/my', authRequired, validate({ query: myCouponsSchema }), async (req, res) => {
  const { status } = req.query;
  let sql = 'SELECT uc.*, c.name, c.type, c.value, c.min_amount, c.end_time FROM user_coupons uc JOIN coupons c ON uc.coupon_id=c.id WHERE uc.user_id=?';
  const params = [req.user.id];
  if (status) { sql += ' AND uc.status=?'; params.push(status); }
  sql += ' ORDER BY uc.created_at DESC';
  try {
    const [rows] = await pool.query(sql, params);
    res.json({ code: 0, data: rows });
  } catch (e) { return serverError(res, '我的优惠券失败: ' + e.message) }
});

module.exports = router;
