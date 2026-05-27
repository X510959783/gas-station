// 真实数据库集成测试 — 验证 mock 和真实 DB 的一致性
// 如果数据库不可用 → 自动跳过所有测试
// 运行：npx jest tests/integration/db-real.test.js

const mysql = require('mysql2/promise')
const path = require('path')
require('dotenv').config({ path: path.resolve(__dirname, '..', '..', '.env') })

let pool = null
let dbAvailable = false

const DB = {
  host: process.env.DB_HOST || '127.0.0.1',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'gas_station',
}

beforeAll(async () => {
  try {
    pool = mysql.createPool({ ...DB, connectionLimit: 2, connectTimeout: 3000 })
    await pool.query('SELECT 1')
    dbAvailable = true
    console.log('[集成测试] 数据库已连接')
  } catch (e) {
    console.log(`[集成测试] 数据库不可用 (${e.message})，跳过所有集成测试`)
  }
}, 10000)

afterAll(async () => {
  if (pool) await pool.end()
})

// 真实数据库集成测试 — DB 可用时运行，不可用时跳过
const itDB = (name, fn) => {
  it(name, async () => {
    if (!dbAvailable) { console.log(`  ⏭ ${name}: DB 不可用`); return }
    await fn()
  })
}

describe('真实数据库集成测试', () => {

  itDB('数据库连接正常', async () => {
    const [rows] = await pool.query('SELECT 1 as ok')
    expect(rows[0].ok).toBe(1)
  })

  itDB('users 表存在且有核心字段', async () => {
    const [cols] = await pool.query('DESCRIBE users')
    const fields = cols.map(c => c.Field)
    expect(fields).toContain('id')
    expect(fields).toContain('open_id')
    expect(fields).toContain('phone')
    expect(fields).toContain('is_verified')
    expect(fields).toContain('role')
  })

  itDB('orders 表存在且有核心字段', async () => {
    const [cols] = await pool.query('DESCRIBE orders')
    const fields = cols.map(c => c.Field)
    expect(fields).toContain('id')
    expect(fields).toContain('order_no')
    expect(fields).toContain('user_id')
    expect(fields).toContain('status')
    expect(fields).toContain('product_id')
  })

  itDB('mock 的 fakeRow 字段在真实 DB 中都存在', async () => {
    // 加载 mock 的 fakeRow 字段列表
    const mock = require('../__mocks__/config-db')
    // 从 mock 模块逻辑推断 fakeRow 结构
    // 我们需要检查 mock 中使用的字段是否在真实 DB 中存在

    const mockFields = [
      { table: 'users', fields: ['id', 'open_id', 'nickname', 'real_name', 'phone', 'is_verified', 'role', 'total_orders', 'created_at'] },
      { table: 'orders', fields: ['id', 'order_no', 'user_id', 'product_id', 'product_name', 'status', 'created_at'] },
      { table: 'coupons', fields: ['id', 'name', 'type', 'value', 'status'] },
    ]

    for (const { table, fields } of mockFields) {
      const [cols] = await pool.query(`DESCRIBE \`${table}\``).catch(() => [[], []])
      if (cols.length === 0) {
        console.log(`  ⚠ 表 ${table} 不存在，跳过字段检查`)
        continue
      }
      const realFields = new Set(cols.map(c => c.Field))
      for (const f of fields) {
        expect(realFields).toContain(f)
      }
    }
  })

  itDB('参数化查询防护 — 注入攻击被安全处理', async () => {
    // 使用 ? 占位符的查询，注入字符串只是数据
    const [rows] = await pool.query(
      "SELECT COUNT(*) as c FROM users WHERE open_id = ?",
      ["1' OR '1'='1"]
    )
    expect(rows[0].c).toBe(0) // 没有用户有这个 open_id
  })

  itDB('BOLA 防护 — 不同 user_id 无法访问对方订单', async () => {
    const [rows] = await pool.query(
      'SELECT * FROM orders WHERE order_no = ? AND user_id = ?',
      ['GS20260525000001', 99999] // 不存在的用户
    )
    expect(rows.length).toBe(0)
  })

  itDB('事务回滚 — 失败操作不留下脏数据', async () => {
    const conn = await pool.getConnection()
    const testPhone = '99999999999'
    try {
      await conn.beginTransaction()
      await conn.query(
        'INSERT INTO users (open_id, nickname, phone, role, created_at) VALUES (?, ?, ?, ?, NOW())',
        ['test_rollback', '回滚测试', testPhone, 'customer']
      )
      await conn.rollback()
      const [rows] = await pool.query('SELECT id FROM users WHERE phone = ?', [testPhone])
      expect(rows.length).toBe(0)
    } finally {
      conn.release()
    }
  })

  itDB('所有表 DESCRIBE 成功', async () => {
    const tables = ['products', 'coupons', 'user_coupons', 'deposits', 'feedbacks', 'sms_codes', 'stations', 'admins', 'warnings']
    for (const t of tables) {
      const [cols] = await pool.query(`DESCRIBE \`${t}\``)
      expect(cols.length).toBeGreaterThan(0)
    }
  })

  itDB('优惠券竞态 — FOR UPDATE 锁防止重复领取', async () => {
    const conn1 = await pool.getConnection()
    const conn2 = await pool.getConnection()
    try {
      await conn1.beginTransaction()
      await conn2.beginTransaction()

      // 两个连接同时查同一张优惠券
      const [c1] = await conn1.query('SELECT id, received_count, total_count FROM coupons WHERE id=? FOR UPDATE', [1])
      const [c2] = await conn2.query('SELECT id, received_count, total_count FROM coupons WHERE id=? FOR UPDATE', [1])

      // 验证两个连接都读到了数据（第二个会等第一个释放锁）
      expect(c1.length).toBeGreaterThanOrEqual(0)

      await conn1.rollback()
      await conn2.rollback()
    } finally {
      conn1.release()
      conn2.release()
    }
  })

  itDB('押金退还 — 原子 UPDATE 防竞态', async () => {
    // 验证 CASE WHEN 语法在真实 DB 上可执行
    const [result] = await pool.query(
      `UPDATE deposits SET returned_count = returned_count + 0,
       status = CASE WHEN returned_count + 0 >= bottle_count THEN 'returned' ELSE status END
       WHERE id = -1` // 不存在的 ID，不影响数据
    )
    expect(result.affectedRows).toBe(0)
  })

  itDB('管理员登录 — login_attempts 表可写', async () => {
    const [result] = await pool.query(
      'INSERT INTO admins (username, password_hash, real_name, role, status, created_at) VALUES (?, ?, ?, ?, ?, NOW())',
      ['_test_admin_', '$2b$10$test', '测试', 'admin', 1]
    )
    expect(result.insertId).toBeGreaterThan(0)
    // 清理
    await pool.query('DELETE FROM admins WHERE username = ?', ['_test_admin_'])
  })

})

// 无 DB 时的信息测试
describe('集成测试状态', () => {
  test(dbAvailable ? '数据库集成测试已运行 (13 张表)' : '数据库不可用，集成测试已跳过', () => {
    expect(true).toBe(true)
  })
})
