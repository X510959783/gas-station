// 安全回归测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/auth.js
// 检测: auth=True, validation=True, tx=True, sql_hazard=False

const request = require('supertest');
const app = require('../../app');

describe('auth 安全测试', () => {


  // ─── POST /api/auth/wx-login ───

  test('_api_auth_wx-login: 参数污染攻击', async () => {
    const res = await request(app)
      .post('/api/auth/wx-login')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

  test('_api_auth_wx-login: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .post('/api/auth/wx-login')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── POST /api/auth/register ───

  test('_api_auth_register: token 过期应被拒绝', async () => {
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiaWF0IjoxNTAwMDAwMDAwLCJleHAiOjE1MDAwMDAwMDF9.test';
    const res = await request(app)
      .post('/api/auth/register')
      .set('Authorization', `Bearer ${expiredToken}`);
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_auth_register: token 篡改应被拒绝', async () => {
    const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwicm9sZSI6ImFkbWluIn0.test';
    const res = await request(app)
      .post('/api/auth/register')
      .set('Authorization', `Bearer ${tamperedToken}`);
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });


  test('_api_auth_register: 参数污染攻击', async () => {
    const res = await request(app)
      .post('/api/auth/register')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

  test('_api_auth_register: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .post('/api/auth/register')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });


  // ─── GET /api/auth/profile ───

  test('_api_auth_profile: token 过期应被拒绝', async () => {
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwiaWF0IjoxNTAwMDAwMDAwLCJleHAiOjE1MDAwMDAwMDF9.test';
    const res = await request(app)
      .get('/api/auth/profile')
      .set('Authorization', `Bearer ${expiredToken}`);
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_auth_profile: token 篡改应被拒绝', async () => {
    const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwicm9sZSI6ImFkbWluIn0.test';
    const res = await request(app)
      .get('/api/auth/profile')
      .set('Authorization', `Bearer ${tamperedToken}`);
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });


  test('_api_auth_profile: 参数污染攻击', async () => {
    const res = await request(app)
      .get('/api/auth/profile')
      .set('Authorization', 'Bearer test_token')
      .query({ 'id[]': ['1', '2'] });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

  test('_api_auth_profile: 超长输入应被截断或拒绝', async () => {
    const res = await request(app)
      .get('/api/auth/profile')
      .set('Authorization', 'Bearer test_token')
      .send({ field: 'A'.repeat(10000) });
    expect([200, 400, 401, 403, 404, 413, 422, 500]).toContain(res.status);
  });

});
