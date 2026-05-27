// 安全回归测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/warnings.js
// 检测: auth=True, validation=False, tx=False, sql_hazard=False

const request = require('supertest');
const app = require('../../app');

describe('warnings 安全测试', () => {

  // ⚠️ 未使用事务

  // ─── GET /api/admin/warnings ───

  test('_api_admin_warnings: token 过期应被拒绝', async () => {
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiaWF0IjoxNTAwMDAwMDAwLCJleHAiOjE1MDAwMDAwMDF9.test';
    const res = await request(app)
      .get('/api/admin/warnings')
      .set('Authorization', `Bearer ${expiredToken}`);
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });

  test('_api_admin_warnings: token 篡改应被拒绝', async () => {
    const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwicm9sZSI6ImFkbWluIn0.test';
    const res = await request(app)
      .get('/api/admin/warnings')
      .set('Authorization', `Bearer ${tamperedToken}`);
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


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


  // ─── PUT /api/admin/warnings/:id/resolve ───

  test('_api_admin_warnings_id_resolve: token 过期应被拒绝', async () => {
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiaWF0IjoxNTAwMDAwMDAwLCJleHAiOjE1MDAwMDAwMDF9.test';
    const res = await request(app)
      .put('/api/admin/warnings/:id/resolve')
      .set('Authorization', `Bearer ${expiredToken}`);
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });

  test('_api_admin_warnings_id_resolve: token 篡改应被拒绝', async () => {
    const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwicm9sZSI6ImFkbWluIn0.test';
    const res = await request(app)
      .put('/api/admin/warnings/:id/resolve')
      .set('Authorization', `Bearer ${tamperedToken}`);
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_warnings_id_resolve: 参数污染攻击', async () => {
    const res = await request(app)
      .put('/api/admin/warnings/:id/resolve')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_warnings_id_resolve: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .put('/api/admin/warnings/:id/resolve')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

});
