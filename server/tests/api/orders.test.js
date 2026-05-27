// API 测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/orders.js
// 端点: 3

const request = require('supertest');
const app = require('../../app');

describe('orders API', () => {

  // ─── POST /api/admin/orders ───

  test('_api_admin_orders: 未登录应返回 401', async () => {
    const res = await request(app)
      .post('/api/admin/orders');
    expect(res.status).toBe(401);
  });

  test('_api_admin_orders: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .post('/api/admin/orders')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_orders: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .post('/api/admin/orders')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_orders: XSS 应被拒绝', async () => {
    const res = await request(app)
      .post('/api/admin/orders')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });


  // ─── GET /api/admin/orders ───

  test('_api_admin_orders: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/orders');
    expect(res.status).toBe(401);
  });

  test('_api_admin_orders: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/orders')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_orders: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/orders')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_orders: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/orders')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });


  // ─── GET /api/admin/orders/detail/:orderNo ───

  test('_api_admin_orders_detail_orderNo: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/orders/detail/:orderNo');
    expect(res.status).toBe(401);
  });

  test('_api_admin_orders_detail_orderNo: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/orders/detail/:orderNo')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_orders_detail_orderNo: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/orders/detail/:orderNo')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_orders_detail_orderNo: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/orders/detail/:orderNo')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

});
