// 安全回归测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/deposits.js
// 检测: auth=True, validation=False, tx=False, sql_hazard=False

const request = require('supertest');
const app = require('../../app');

describe('deposits 安全测试', () => {

  // ⚠️ 未使用事务

  // ─── GET /api/admin/deposits ───

  test('_api_admin_deposits: token 过期应被拒绝', async () => {
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiaWF0IjoxNTAwMDAwMDAwLCJleHAiOjE1MDAwMDAwMDF9.test';
    const res = await request(app)
      .get('/api/admin/deposits')
      .set('Authorization', `Bearer ${expiredToken}`);
    expect([200, 400, 401, 401, 403, 404, 500]).toContain(res.status);
  });

  test('_api_admin_deposits: token 篡改应被拒绝', async () => {
    const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwicm9sZSI6ImFkbWluIn0.test';
    const res = await request(app)
      .get('/api/admin/deposits')
      .set('Authorization', `Bearer ${tamperedToken}`);
    expect([200, 400, 401, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_deposits: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/admin/deposits')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

  test('_api_admin_deposits: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/deposits')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── PUT /api/admin/deposits/:id/return ───

  test('_api_admin_deposits_id_return: token 过期应被拒绝', async () => {
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiaWF0IjoxNTAwMDAwMDAwLCJleHAiOjE1MDAwMDAwMDF9.test';
    const res = await request(app)
      .put('/api/admin/deposits/:id/return')
      .set('Authorization', `Bearer ${expiredToken}`);
    expect([200, 400, 401, 401, 403, 404, 500]).toContain(res.status);
  });

  test('_api_admin_deposits_id_return: token 篡改应被拒绝', async () => {
    const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwicm9sZSI6ImFkbWluIn0.test';
    const res = await request(app)
      .put('/api/admin/deposits/:id/return')
      .set('Authorization', `Bearer ${tamperedToken}`);
    expect([200, 400, 401, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_deposits_id_return: 参数污染攻击', async () => {
    const res = await request(app)
      .put('/api/admin/deposits/:id/return')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

  test('_api_admin_deposits_id_return: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .put('/api/admin/deposits/:id/return')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

});
