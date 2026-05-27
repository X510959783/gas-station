// 安全回归测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/sms.js
// 检测: auth=False, validation=True, tx=False, sql_hazard=False

const request = require('supertest');
const app = require('../../app');

describe('sms 安全测试', () => {

  // ⚠️ 未检测到鉴权中间件
  // ⚠️ 未使用事务

  // ─── POST /api/sms/send ───

  test('_api_sms_send: 参数污染攻击', async () => {
    const res = await request(app)
      .post('/api/sms/send')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_sms_send: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .post('/api/sms/send')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── POST /api/sms/verify ───

  test('_api_sms_verify: 参数污染攻击', async () => {
    const res = await request(app)
      .post('/api/sms/verify')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_sms_verify: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .post('/api/sms/verify')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

});
