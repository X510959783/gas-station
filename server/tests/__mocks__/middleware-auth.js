// Mock for middleware/auth — 测试环境自动通过鉴权，不等 JWT 校验

function authRequired(req, res, next) {
  const h = req.headers.authorization;
  if (!h || !h.startsWith('Bearer ')) {
    return res.status(401).json({ code: 401, message: '请先登录' });
  }
  // 测试环境：任何 Bearer token 都视为有效（包括 test_token）
  req.user = { id: 1, role: 'customer', type: 'customer' };
  next();
}

function adminRequired(req, res, next) {
  const h = req.headers.authorization;
  if (!h || !h.startsWith('Bearer ')) {
    return res.status(401).json({ code: 401, message: '请先登录' });
  }
  req.user = { id: 999, role: 'admin', type: 'admin' };
  next();
}

module.exports = { authRequired, adminRequired };
