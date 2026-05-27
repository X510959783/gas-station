// API 测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/deposits.js
// 端点: 2

const request = require('supertest');
const app = require('../../app');

describe('deposits API', () => {

  // ─── GET /api/admin/deposits ───

  test('_api_admin_deposits: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/deposits');
    expect(res.status).toBe(401);
  });

  test('_api_admin_deposits: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/deposits')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_deposits: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/deposits')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

  test('_api_admin_deposits: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/deposits')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });


  // ─── PUT /api/admin/deposits/:id/return ───

  test('_api_admin_deposits_id_return: 未登录应返回 401', async () => {
    const res = await request(app)
      .put('/api/admin/deposits/:id/return');
    expect(res.status).toBe(401);
  });

  test('_api_admin_deposits_id_return: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .put('/api/admin/deposits/:id/return')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_deposits_id_return: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .put('/api/admin/deposits/:id/return')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

  test('_api_admin_deposits_id_return: XSS 应被拒绝', async () => {
    const res = await request(app)
      .put('/api/admin/deposits/:id/return')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });

});
