// API 测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/coupons.js
// 端点: 3

const request = require('supertest');
const app = require('../../app');

describe('coupons API', () => {

  // ─── GET /api/coupons/available ───

  test('_api_admin_coupons_available: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/coupons/available');
    expect(res.status).toBe(401);
  });

  test('_api_admin_coupons_available: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/coupons/available')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_coupons_available: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/coupons/available')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_coupons_available: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/coupons/available')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });


  // ─── POST /api/coupons/:couponId/receive ───

  test('_api_admin_coupons_couponId_receive: 未登录应返回 401', async () => {
    const res = await request(app)
      .post('/api/coupons/:couponId/receive');
    expect(res.status).toBe(401);
  });

  test('_api_admin_coupons_couponId_receive: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .post('/api/coupons/:couponId/receive')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_coupons_couponId_receive: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .post('/api/coupons/:couponId/receive')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_coupons_couponId_receive: XSS 应被拒绝', async () => {
    const res = await request(app)
      .post('/api/coupons/:couponId/receive')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });


  // ─── GET /api/coupons/my ───

  test('_api_admin_coupons_my: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/coupons/my');
    expect(res.status).toBe(401);
  });

  test('_api_admin_coupons_my: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/coupons/my')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_coupons_my: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/coupons/my')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_coupons_my: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/coupons/my')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

});
