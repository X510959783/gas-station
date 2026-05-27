const jwt = require('jsonwebtoken');
const cfg = require('../config/env');

// JWT 密钥：统一从 config/env 获取（env.js 负责环境变量+开发回退+生产校验）
const SECRET = cfg.JWT_SECRET;
if (cfg.NODE_ENV !== 'production') {
  console.log('[JWT] 开发模式，重启后需重新登录');
}

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
