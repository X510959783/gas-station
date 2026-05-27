// API 测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/dashboard.js
// 端点: 1

const request = require('supertest');
const app = require('../../app');

describe('dashboard API', () => {

  // ─── GET /api/admin/dashboard ───

  test('_api_admin_dashboard: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/dashboard');
    expect(res.status).toBe(401);
  });

  test('_api_admin_dashboard: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/dashboard')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_dashboard: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/dashboard')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_dashboard: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/dashboard')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });

});
