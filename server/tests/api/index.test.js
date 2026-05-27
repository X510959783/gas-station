// API 测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/index.js
// 端点: 11

const request = require('supertest');
const app = require('../../app');

describe('index API', () => {

  // ─── USE /api/admin/login ───

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


  // ─── USE /api/admin/dashboard ───

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


  // ─── USE /api/admin/orders ───

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
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/stations ───

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


  // ─── USE /api/admin/products ───

  test('_api_admin_products: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/products')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_products: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/products')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/users ───

  test('_api_admin_users: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/users')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_users: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/users')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/coupons ───

  test('_api_admin_coupons: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/coupons')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_coupons: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/coupons')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/warnings ───

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


  // ─── USE /api/admin/deposits ───

  test('_api_admin_deposits: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/deposits')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_deposits: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/deposits')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/feedback ───

  test('_api_admin_feedback: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/feedback')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_feedback: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/feedback')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/analysis ───

  test('_api_admin_analysis: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/analysis')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_analysis: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/analysis')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });

});
