const router = require('express').Router();
const pool = require('../config/db');
const { authRequired } = require('../middleware/auth');

const { serverError } = require('../utils/response')

// 简单的 XSS 防护：转义 HTML 特殊字符
function sanitize(str) {
  if (!str) return ''
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const allowedTypes = ['bug', 'suggestion', 'complaint', 'other']

router.post('/', authRequired, async (req, res) => {
  const { type, content, contact } = req.body;
  if (!content || String(content).trim().length === 0) {
    return res.status(400).json({ code: 400, message: '请填写反馈内容' })
  }
  if (String(content).length > 2000) {
    return res.status(400).json({ code: 400, message: '反馈内容不能超过2000字' })
  }
  if (type && !allowedTypes.includes(type)) {
    return res.status(400).json({ code: 400, message: '反馈类型无效' })
  }
  try {
    await pool.query(
      'INSERT INTO feedbacks (user_id, type, content, contact) VALUES (?,?,?,?)',
      [req.user.id, type || 'other', sanitize(content.trim()), sanitize(contact || '')]
    );
    res.json({ code: 0, data: { success: true } });
  } catch (e) { return serverError(res, '提交反馈失败: ' + e.message) }
});

module.exports = router;
