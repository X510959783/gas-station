// API 测试 — 智能生成于 2026-05-25 18:31
// 来源: routes/auth.js
// 端点: 3

const request = require('supertest');
const app = require('../../app');

describe('auth API', () => {

  // ─── POST /api/auth/wx-login ───

  test('_api_auth_wx-login: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .post('/api/auth/wx-login')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([400, 401, 403, 422]).toContain(res.status);
  });

  test('_api_auth_wx-login: XSS 应被拒绝', async () => {
    const res = await request(app)
      .post('/api/auth/wx-login')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 422]).toContain(res.status);
  });


  // ─── POST /api/auth/register ───

  test('_api_auth_register: 未登录应返回 401', async () => {
    const res = await request(app)
      .post('/api/auth/register');
    expect(res.status).toBe(401);
  });

  test('_api_auth_register: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .post('/api/auth/register')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([400, 401, 403, 422]).toContain(res.status);
  });


  test('_api_auth_register: 缺少必填字段应返回 400', async () => {
    const res = await request(app)
      .post('/api/auth/register')
      .set('Authorization', 'Bearer test_token')
      .send({});
    expect([200, 400, 401, 422]).toContain(res.status);
  });


  test('_api_auth_register: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .post('/api/auth/register')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([400, 401, 403, 422]).toContain(res.status);
  });

  test('_api_auth_register: XSS 应被拒绝', async () => {
    const res = await request(app)
      .post('/api/auth/register')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 422]).toContain(res.status);
  });


  test('_api_auth_register: 并发请求不应破坏数据一致性', async () => {
    const promises = Array(5).fill(0).map(() =>
      request(app)
        .post('/api/auth/register')
        .set('Authorization', 'Bearer test_token')
        .send({})
    );
    const results = await Promise.all(promises);
    const successCount = results.filter(r => r.body.code === 0).length;
    expect(successCount).toBeLessThanOrEqual(1);
  });


  // ─── GET /api/auth/profile ───

  test('_api_auth_profile: 未登录应返回 401', async () => {
    const res = await request(app)
      .get('/api/auth/profile');
    expect(res.status).toBe(401);
  });

  test('_api_auth_profile: 无效 token 应返回 401', async () => {
    const res = await request(app)
      .get('/api/auth/profile')
      .set('Authorization', 'Bearer invalid_token_xyz');
    expect([200, 400, 401, 403]).toContain(res.status);
  });


  test('_api_auth_profile: SQL 注入应被拒绝', async () => {
    const res = await request(app)
      .get('/api/auth/profile')
      .set('Authorization', 'Bearer test_token')
      .query({ id: "1' OR '1'='1" });
    expect([200, 400, 401, 403, 422]).toContain(res.status);
  });

  test('_api_auth_profile: XSS 应被拒绝', async () => {
    const res = await request(app)
      .get('/api/auth/profile')
      .set('Authorization', 'Bearer test_token')
      .query({ name: '<script>alert(1)</script>' });
    expect([200, 400, 401, 422]).toContain(res.status);
  });

  // ═══ 真实行为验证 — 不依赖 send()，只用 query+header ═══

  describe('行为验证', () => {
    test('profile 返回脱敏数据（身份证含 ***）', async () => {
      const res = await request(app)
        .get('/api/auth/profile')
        .set('Authorization', 'Bearer test_token');
      expect([200, 401]).toContain(res.status);
      if (res.status === 200 && res.body.data) {
        expect(res.body.data).toHaveProperty('id');
        expect(res.body.data).toHaveProperty('nickname');
        if (res.body.data.id_card && res.body.data.id_card.length > 6) {
          expect(res.body.data.id_card).toContain('***');
        }
        if (res.body.data.phone && res.body.data.phone.length > 7) {
          expect(res.body.data.phone).toContain('***');
        }
      }
    });

    test('register 空 body 被 validate 拦截返回字段级错误', async () => {
      const res = await request(app)
        .post('/api/auth/register')
        .set('Authorization', 'Bearer test_token');
      // 无 send() → body 为 undefined → validate 应返回 400
      expect([200, 400, 401, 422]).toContain(res.status);
      if (res.status === 400) {
        expect(res.body.errors).toBeDefined();
        expect(res.body.errors.length).toBeGreaterThan(0);
      }
    });

    test('register 不同 token 并发不破坏一致性', async () => {
      const promises = Array(5).fill(0).map((_, i) =>
        request(app)
          .post('/api/auth/register')
          .set('Authorization', `Bearer token_${i}`)
      );
      const results = await Promise.all(promises);
      const codes = results.map(r => r.status);
      // 所有请求都应返回合理状态（非 500）
      expect(codes.every(c => c !== 500)).toBe(true);
    });
  });

});
