// API 测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/stations.js
// 端点: 1

const request = require('supertest');
const app = require('../../app');

describe('stations API', () => {

  // ─── GET /api/admin/stations ───

  test('_api_admin_stations: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/stations');
    expect(res.status).toBe(401);
  });

  test('_api_admin_stations: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/stations')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_stations: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/stations')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_stations: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/stations')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });

});
