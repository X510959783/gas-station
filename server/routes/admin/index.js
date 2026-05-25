/** Admin 路由入口 — 聚合所有子路由 */
const router = require('express').Router()
const { adminRequired } = require('../../middleware/auth')

router.use('/login', require('./login'))
router.use('/dashboard', adminRequired, require('./dashboard'))
router.use('/orders', adminRequired, require('./orders'))
router.use('/stations', adminRequired, require('./stations'))
router.use('/products', adminRequired, require('./products'))
router.use('/users', adminRequired, require('./users'))
router.use('/coupons', adminRequired, require('./coupons'))
router.use('/warnings', adminRequired, require('./warnings'))
router.use('/deposits', adminRequired, require('./deposits'))
router.use('/feedback', adminRequired, require('./feedback'))
router.use('/analysis', adminRequired, require('./analysis'))

module.exports = router
