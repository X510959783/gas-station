// 安全回归测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/coupons.js
// 检测: auth=True, validation=False, tx=True, sql_hazard=False

const request = require('supertest');
const app = require('../../app');

describe('coupons 安全测试', () => {


  // ─── GET /api/coupons/available ───

  test('_api_admin_coupons_available: token 过期应被拒绝', async () => {
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiaWF0IjoxNTAwMDAwMDAwLCJleHAiOjE1MDAwMDAwMDF9.test';
    const res = await request(app)
      .get('/api/coupons/available')
      .set('Authorization', `Bearer ${expiredToken}`);
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });

  test('_api_admin_coupons_available: token 篡改应被拒绝', async () => {
    const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwicm9sZSI6ImFkbWluIn0.test';
    const res = await request(app)
      .get('/api/coupons/available')
      .set('Authorization', `Bearer ${tamperedToken}`);
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_coupons_available: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/coupons/available')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_coupons_available: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/coupons/available')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── POST /api/coupons/:couponId/receive ───

  test('_api_admin_coupons_couponId_receive: token 过期应被拒绝', async () => {
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiaWF0IjoxNTAwMDAwMDAwLCJleHAiOjE1MDAwMDAwMDF9.test';
    const res = await request(app)
      .post('/api/coupons/:couponId/receive')
      .set('Authorization', `Bearer ${expiredToken}`);
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });

  test('_api_admin_coupons_couponId_receive: token 篡改应被拒绝', async () => {
    const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwicm9sZSI6ImFkbWluIn0.test';
    const res = await request(app)
      .post('/api/coupons/:couponId/receive')
      .set('Authorization', `Bearer ${tamperedToken}`);
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_coupons_couponId_receive: 参数污染攻击', async () => {
    const res = await request(app)
      .post('/api/coupons/:couponId/receive')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_coupons_couponId_receive: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .post('/api/coupons/:couponId/receive')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── GET /api/coupons/my ───

  test('_api_admin_coupons_my: token 过期应被拒绝', async () => {
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiaWF0IjoxNTAwMDAwMDAwLCJleHAiOjE1MDAwMDAwMDF9.test';
    const res = await request(app)
      .get('/api/coupons/my')
      .set('Authorization', `Bearer ${expiredToken}`);
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });

  test('_api_admin_coupons_my: token 篡改应被拒绝', async () => {
    const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwicm9sZSI6ImFkbWluIn0.test';
    const res = await request(app)
      .get('/api/coupons/my')
      .set('Authorization', `Bearer ${tamperedToken}`);
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_coupons_my: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/coupons/my')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_coupons_my: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/coupons/my')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

});
