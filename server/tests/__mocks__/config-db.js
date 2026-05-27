// Mock for config/db — 返回符合 mysql2 格式的假数据
// SELECT 返回模拟行数据，INSERT/UPDATE/DELETE 返回操作结果对象

const jwt = require('jsonwebtoken');
const SECRET = process.env.JWT_SECRET || 'test_secret_key_not_for_production';

global.TEST_TOKEN = jwt.sign(
  { id: 1, role: 'customer', type: 'customer' },
  SECRET,
  { expiresIn: '100y' }
);
global.TEST_ADMIN_TOKEN = jwt.sign(
  { id: 999, role: 'admin', type: 'admin' },
  SECRET,
  { expiresIn: '100y' }
);

// 通用模拟行数据 — 与真实 DB 全部 13 张表字段对齐
const fakeRow = {
  // ── users ──
  id: 1, open_id: 'mock_openid_test', nickname: '测试用户', avatar: null,
  real_name: '测试姓名', id_card: '110101199001011234', phone: '13800138000',
  address: '测试地址', address_lat: null, address_lng: null,
  assigned_station_id: null, is_verified: 0, role: 'customer', type: 'customer',
  total_orders: 0, total_gas_amount: 0, last_order_date: null, avg_order_cycle: null,
  // ── orders ──
  order_no: 'GS20260525000001', user_id: 1, product_id: 1,
  product_name: '测试商品', product_spec: '15kg', product_price: 120.00,
  quantity: 1, total_amount: 120.00, deposit_amount: 0, pay_amount: 120.00,
  contact_name: '测试联系人', contact_phone: '13800138000',
  delivery_address: '测试地址', delivery_time: '尽快送达', delivery_remark: null,
  status: 'pending', station_id: null, driver_id: null,
  coupon_id: null, coupon_discount: 0, pay_time: null, delivered_time: null,
  // ── products ──
  name: '测试商品', description: null, price: 120.00, spec: '15kg',
  deposit_price: 0, stock: 100, sort_order: 1, image: null,
  // ── coupons ──
  type: 'fixed', value: 10.00, min_amount: 0, total_count: 100,
  received_count: 50, used_count: 10,
  start_time: new Date(Date.now() - 86400000).toISOString(),
  end_time: new Date(Date.now() + 864000000).toISOString(),
  // ── user_coupons ──
  used_order_id: null, received_at: new Date().toISOString(), used_at: null,
  // ── deposits ──
  order_no: 'GS20260525000001', spec_type: '15kg', bottle_count: 1,
  deposit_per_bottle: 200, total_deposit: 200, returned_count: 0, remark: null,
  // ── feedbacks ──
  content: '测试反馈内容', contact: '13800138000',
  // ── sms_codes ──
  code: '123456', is_used: 0,
  expired_at: new Date(Date.now() + 600000).toISOString(),
  // ── stations ──
  short_name: '测试站', lat: null, lng: null, phone: '13800138000',
  contact_person: '测试联系人', service_area_radius: 30, is_default: 0,
  // ── admins ──
  username: 'admin', password_hash: '$2b$10$test_hash', last_login_at: null,
  // ── warnings ──
  user_name: '测试用户', user_phone: '13800138000', rule_type: 'inactive',
  level: 'info', message: '测试预警', resolved_at: null,
  // ── 时间戳 ──
  created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
};

// 空的 FieldPacket 数组
const emptyFields = [];

// INSERT/UPDATE/DELETE 返回的结果对象
const writeResult = { insertId: 1, affectedRows: 1, changedRows: 1, fieldCount: 0, warningStatus: 0 };

// COUNT 查询返回
const countResult = { total: 0, count: 0, c: 0 };

function mockQuery(sql, params) {
  const sqlUpper = typeof sql === 'string' ? sql.toUpperCase() : '';

  // SELECT ... FOR UPDATE 返回空数组（模拟无竞态条件）
  if (sqlUpper.includes('FOR UPDATE')) {
    return Promise.resolve([[], emptyFields]);
  }

  // SELECT 查询返回模拟行数据
  if (sqlUpper.includes('SELECT')) {
    // COUNT(*) 查询返回计数
    if (sqlUpper.includes('COUNT(*)') || sqlUpper.includes('COUNT(')) {
      return Promise.resolve([[countResult], emptyFields]);
    }
    return Promise.resolve([[{ ...fakeRow }], emptyFields]);
  }

  // INSERT 查询
  if (sqlUpper.includes('INSERT')) {
    return Promise.resolve([writeResult, emptyFields]);
  }

  // UPDATE 查询
  if (sqlUpper.includes('UPDATE')) {
    return Promise.resolve([writeResult, emptyFields]);
  }

  // DELETE 查询
  if (sqlUpper.includes('DELETE')) {
    return Promise.resolve([writeResult, emptyFields]);
  }

  // 默认返回 SELECT 结果
  return Promise.resolve([[{ ...fakeRow }], emptyFields]);
}

const mockConnection = {
  query: mockQuery,
  execute: mockQuery,
  beginTransaction: () => Promise.resolve(),
  commit: () => Promise.resolve(),
  rollback: () => Promise.resolve(),
  release: () => Promise.resolve(),
};

const pool = {
  query: mockQuery,
  execute: mockQuery,
  getConnection: () => Promise.resolve({ ...mockConnection }),
};

module.exports = pool;
