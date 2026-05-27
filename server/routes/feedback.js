const router = require('express').Router();
const pool = require('../config/db');
const { z } = require('zod')
const validate = require('../middleware/validate')
const { authRequired } = require('../middleware/auth');
const { serverError } = require('../utils/response')

// XSS 防护：输出转义
function sanitize(str) {
  if (!str) return ''
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

const feedbackSchema = z.object({
  type: z.enum(['bug', 'suggestion', 'complaint', 'other']).default('other'),
  content: z.string().min(1, '请填写反馈内容').max(2000, '反馈内容不能超过2000字'),
  contact: z.string().max(100).optional().default(''),
})

router.post('/', authRequired, validate({ body: feedbackSchema }), async (req, res) => {
  const { type, content, contact } = req.body;
  try {
    await pool.query(
      'INSERT INTO feedbacks (user_id, type, content, contact) VALUES (?,?,?,?)',
      [req.user.id, type, sanitize(content.trim()), sanitize(contact.trim())]
    );
    res.json({ code: 0, data: { success: true } });
  } catch (e) { return serverError(res, '提交反馈失败: ' + e.message) }
});

module.exports = router;
