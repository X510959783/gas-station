const pool = require('../config/db')

/**
 * 操作审计日志
 * 用法：router.post('/xxx', opLog('创建商品'), handler)
 * 自动从 req.user 获取管理员信息
 */
function opLog(action, targetType) {
  return async (req, res, next) => {
    const originalJson = res.json.bind(res)
    res.json = function (body) {
      if (req.user && req.user.type === 'admin') {
        pool.query(
          `INSERT INTO operation_logs (admin_id, admin_name, action, target_type, ip, detail)
           VALUES (?, ?, ?, ?, ?, ?)`,
          [
            req.user.id,
            req.user.real_name || req.user.username,
            action,
            targetType || '',
            req.ip || req.connection?.remoteAddress || '',
            JSON.stringify({ body: req.body, result: body }).slice(0, 500),
          ]
        ).catch(() => {}) // 日志失败不影响主流程
      }
      originalJson(body)
    }
    next()
  }
}

module.exports = opLog
