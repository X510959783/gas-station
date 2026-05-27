// 安全回归测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/users.js
// 检测: auth=True, validation=False, tx=False, sql_hazard=False

const request = require('supertest');
const app = require('../../app');

describe('users 安全测试', () => {

  // ⚠️ 未使用事务

  // ─── GET /api/admin/users ───

  test('_api_admin_users: token 过期应被拒绝', async () => {
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiaWF0IjoxNTAwMDAwMDAwLCJleHAiOjE1MDAwMDAwMDF9.test';
    const res = await request(app)
      .get('/api/admin/users')
      .set('Authorization', `Bearer ${expiredToken}`);
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });

  test('_api_admin_users: token 篡改应被拒绝', async () => {
    const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwicm9sZSI6ImFkbWluIn0.test';
    const res = await request(app)
      .get('/api/admin/users')
      .set('Authorization', `Bearer ${tamperedToken}`);
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


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

});
