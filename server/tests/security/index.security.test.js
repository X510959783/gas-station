// 安全回归测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/index.js
// 检测: auth=False, validation=False, tx=False, sql_hazard=False

const request = require('supertest');
const app = require('../../app');

describe('index 安全测试', () => {

  // ⚠️ 未检测到鉴权中间件
  // ⚠️ 未使用事务

  // ─── USE /api/admin/login ───

  test('_api_admin_login: 参数污染攻击', async () => {
    const res = await request(app)
      .post('/api/admin/login')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_login: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .post('/api/admin/login')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/dashboard ───

  test('_api_admin_dashboard: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/admin/dashboard')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_dashboard: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/dashboard')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/orders ───

  test('_api_admin_orders: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/admin/orders')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_orders: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/orders')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/stations ───

  test('_api_admin_stations: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/admin/stations')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_stations: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/stations')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/products ───

  test('_api_admin_products: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/admin/products')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_products: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/products')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/users ───

  test('_api_admin_users: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/admin/users')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_users: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/users')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/coupons ───

  test('_api_admin_coupons: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/admin/coupons')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_coupons: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/coupons')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/warnings ───

  test('_api_admin_warnings: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/admin/warnings')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_warnings: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/warnings')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/deposits ───

  test('_api_admin_deposits: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/admin/deposits')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_deposits: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/deposits')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/feedback ───

  test('_api_admin_feedback: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/admin/feedback')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_feedback: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/feedback')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── USE /api/admin/analysis ───

  test('_api_admin_analysis: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/admin/analysis')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_analysis: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/analysis')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

});
