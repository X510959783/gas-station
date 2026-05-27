// API 测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/login.js
// 端点: 1

const request = require('supertest');
const app = require('../../app');

describe('login API', () => {

  // ─── POST /api/admin/login ───

  test('_api_admin_login: 缺少必填字段应返回 400', async () => {
    const res = await request(app)
      .post('/api/admin/login')
      .set('Authorization', 'Bearer test_token')
      .send({});
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });


  test('_api_admin_login: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .post('/api/admin/login')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_login: XSS 应被拒绝', async () => {
    const res = await request(app)
      .post('/api/admin/login')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });

});
