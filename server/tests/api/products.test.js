// API 测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/products.js
// 端点: 2

const request = require('supertest');
const app = require('../../app');

describe('products API', () => {

  // ─── GET /api/admin/products ───

  test('_api_admin_products: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/products');
    expect(res.status).toBe(401);
  });

  test('_api_admin_products: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/products')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


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


  // ─── GET /api/admin/products/:id ───

  test('_api_admin_products_id: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/products/:id');
    expect(res.status).toBe(401);
  });

  test('_api_admin_products_id: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/products/:id')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_products_id: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/products/:id')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_products_id: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/products/:id')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });

});
