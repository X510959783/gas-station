const jwt = require('jsonwebtoken');
const cfg = require('../config/env');

// JWT 密钥 — 生产环境必须设置，开发环境使用随机密钥
const SECRET = (() => {
  if (cfg.JWT_SECRET) return cfg.JWT_SECRET;
  if (cfg.NODE_ENV === 'production') {
    console.error('[致命] 生产环境未设置 JWT_SECRET，拒绝启动');
    process.exit(1);
  }
  const fallback = require('crypto').randomBytes(32).toString('hex');
  console.log('[JWT] 开发模式使用随机密钥，重启后需重新登录');
  return fallback;
})();

function authRequired(req, res, next) {
  const h = req.headers.authorization;
  if (!h || !h.startsWith('Bearer ')) {
    return res.status(401).json({ code: 401, message: '请先登录' });
  }
  try {
    req.user = jwt.verify(h.slice(7), SECRET);
    next();
  } catch {
    return res.status(401).json({ code: 401, message: '登录已过期' });
  }
}

function adminRequired(req, res, next) {
  // 先验证登录态
  const h = req.headers.authorization;
  if (!h || !h.startsWith('Bearer ')) {
    return res.status(401).json({ code: 401, message: '请先登录' });
  }
  try {
    req.user = jwt.verify(h.slice(7), SECRET);
  } catch {
    return res.status(401).json({ code: 401, message: '登录已过期' });
  }
  // 验证管理员身份
  if (req.user.type !== 'admin') {
    return res.status(403).json({ code: 403, message: '无管理员权限' });
  }
  next();
}

// SECRET 不导出（安全）
module.exports = { authRequired, adminRequired };
