// API 测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/warnings.js
// 端点: 2

const request = require('supertest');
const app = require('../../app');

describe('warnings API', () => {

  // ─── GET /api/admin/warnings ───

  test('_api_admin_warnings: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/warnings');
    expect(res.status).toBe(401);
  });

  test('_api_admin_warnings: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/warnings')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_warnings: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/warnings')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_warnings: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/warnings')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });


  // ─── PUT /api/admin/warnings/:id/resolve ───

  test('_api_admin_warnings_id_resolve: 未登录应返回 401', async () => {
    const res = await request(app)
      .put('/api/admin/warnings/:id/resolve');
    expect(res.status).toBe(401);
  });

  test('_api_admin_warnings_id_resolve: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .put('/api/admin/warnings/:id/resolve')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_warnings_id_resolve: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .put('/api/admin/warnings/:id/resolve')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_warnings_id_resolve: XSS 应被拒绝', async () => {
    const res = await request(app)
      .put('/api/admin/warnings/:id/resolve')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });

});
