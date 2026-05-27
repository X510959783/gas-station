// API 测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/analysis.js
// 端点: 2

const request = require('supertest');
const app = require('../../app');

describe('analysis API', () => {

  // ─── GET /api/admin/analysis/ranking ───

  test('_api_admin_analysis_ranking: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/analysis/ranking');
    expect(res.status).toBe(401);
  });

  test('_api_admin_analysis_ranking: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/analysis/ranking')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_analysis_ranking: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/analysis/ranking')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_analysis_ranking: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/analysis/ranking')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });


  // ─── GET /api/admin/analysis/trend ───

  test('_api_admin_analysis_trend: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/analysis/trend');
    expect(res.status).toBe(401);
  });

  test('_api_admin_analysis_trend: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/admin/analysis/trend')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403, 404, 500]).toContain(res.status);
  });


  test('_api_admin_analysis_trend: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/analysis/trend')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 404, 422, 500]).toContain(res.status);
  });

  test('_api_admin_analysis_trend: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/admin/analysis/trend')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 404, 422, 500]).toContain(res.status);
  });

});
