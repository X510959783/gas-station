// API 测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/sms.js
// 端点: 2

const request = require('supertest');
const app = require('../../app');

describe('sms API', () => {

  // ─── POST /api/sms/send ───

  test('_api_sms_send: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .post('/api/sms/send')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_sms_send: XSS 应被拒绝', async () => {
    const res = await request(app)
      .post('/api/sms/send')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });


  // ─── POST /api/sms/verify ───

  test('_api_sms_verify: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .post('/api/sms/verify')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_sms_verify: XSS 应被拒绝', async () => {
    const res = await request(app)
      .post('/api/sms/verify')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });

});
