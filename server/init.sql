-- 液化气配送系统 数据库初始化
CREATE DATABASE IF NOT EXISTS gas_station DEFAULT CHARSET utf8mb4;
USE gas_station;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  open_id VARCHAR(100) UNIQUE NOT NULL,
  nickname VARCHAR(100),
  avatar VARCHAR(500),
  real_name VARCHAR(50),
  id_card VARCHAR(20),
  phone VARCHAR(20),
  address VARCHAR(500),
  address_lat DECIMAL(10,7) DEFAULT 0,
  address_lng DECIMAL(10,7) DEFAULT 0,
  assigned_station_id INT DEFAULT NULL,
  role ENUM('customer','merchant') DEFAULT 'customer',
  is_verified TINYINT DEFAULT 0,
  total_orders INT DEFAULT 0,
  total_gas_amount DECIMAL(10,2) DEFAULT 0,
  last_order_date DATE,
  avg_order_cycle INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_open_id (open_id),
  INDEX idx_phone (phone),
  INDEX idx_assigned_station (assigned_station_id)
);

-- 管理员表
CREATE TABLE IF NOT EXISTS admins (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(32) UNIQUE NOT NULL,
  password_hash VARCHAR(256) NOT NULL,
  real_name VARCHAR(32),
  phone VARCHAR(20),
  role VARCHAR(20) DEFAULT 'delivery',
  status TINYINT DEFAULT 1,
  last_login_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 商品表
CREATE TABLE IF NOT EXISTS products (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100),
  description TEXT,
  price DECIMAL(10,2),
  spec VARCHAR(20),
  deposit_price DECIMAL(10,2) DEFAULT 0,
  stock INT DEFAULT 0,
  status TINYINT DEFAULT 1,
  sort_order INT DEFAULT 0,
  image VARCHAR(500),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 订单表
CREATE TABLE IF NOT EXISTS orders (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_no VARCHAR(50) UNIQUE,
  user_id INT NOT NULL,
  station_id INT,
  driver_id INT,
  product_id INT NOT NULL,
  product_name VARCHAR(100),
  product_spec VARCHAR(20),
  product_price DECIMAL(10,2),
  quantity INT DEFAULT 1,
  total_amount DECIMAL(10,2),
  deposit_amount DECIMAL(10,2) DEFAULT 0,
  contact_name VARCHAR(50),
  contact_phone VARCHAR(20),
  delivery_address VARCHAR(500),
  delivery_time VARCHAR(50),
  delivery_remark VARCHAR(200),
  status VARCHAR(20) DEFAULT 'pending',
  coupon_id INT,
  coupon_discount DECIMAL(10,2) DEFAULT 0,
  pay_amount DECIMAL(10,2),
  pay_time DATETIME,
  delivered_time DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id),
  INDEX idx_station_id (station_id),
  INDEX idx_order_no (order_no),
  INDEX idx_status (status)
);

-- 配送站表
CREATE TABLE IF NOT EXISTS stations (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  short_name VARCHAR(50),
  address VARCHAR(500) NOT NULL,
  lat DECIMAL(10,7) NOT NULL DEFAULT 0,
  lng DECIMAL(10,7) NOT NULL DEFAULT 0,
  phone VARCHAR(20),
  contact_person VARCHAR(50),
  service_area_radius INT DEFAULT 0,
  status TINYINT DEFAULT 1,
  is_default TINYINT DEFAULT 0,
  sort_order INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_status (status)
);

-- 优惠券模板表
CREATE TABLE IF NOT EXISTS coupons (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100),
  type ENUM('fixed','percent') DEFAULT 'fixed',
  value DECIMAL(10,2),
  min_amount DECIMAL(10,2) DEFAULT 0,
  total_count INT DEFAULT 0,
  used_count INT DEFAULT 0,
  received_count INT DEFAULT 0,
  start_time DATETIME,
  end_time DATETIME,
  status TINYINT DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 用户优惠券表
CREATE TABLE IF NOT EXISTS user_coupons (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  coupon_id INT NOT NULL,
  status ENUM('unused','used','expired') DEFAULT 'unused',
  used_order_id VARCHAR(50),
  received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  used_at DATETIME,
  INDEX idx_user_id (user_id)
);

-- 短信验证码表
CREATE TABLE IF NOT EXISTS sms_codes (
  id INT PRIMARY KEY AUTO_INCREMENT,
  phone VARCHAR(20) NOT NULL,
  code VARCHAR(10) NOT NULL,
  type ENUM('register','login','reset') DEFAULT 'register',
  is_used TINYINT DEFAULT 0,
  expired_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_phone (phone)
);

-- 预警记录表
CREATE TABLE IF NOT EXISTS warnings (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  user_name VARCHAR(50),
  user_phone VARCHAR(20),
  rule_type ENUM('overdue','decline','churn','cycle_anomaly'),
  level ENUM('info','warning','danger') DEFAULT 'warning',
  message VARCHAR(500),
  status ENUM('pending','contacted','resolved') DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  resolved_at DATETIME,
  INDEX idx_user_id (user_id)
);

-- 反馈表
CREATE TABLE IF NOT EXISTS feedbacks (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT,
  type VARCHAR(50),
  content TEXT,
  contact VARCHAR(50),
  status TINYINT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 钢瓶押金表
CREATE TABLE IF NOT EXISTS deposits (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  order_no VARCHAR(50),
  spec_type VARCHAR(20),
  bottle_count INT DEFAULT 0,
  deposit_per_bottle DECIMAL(10,2),
  total_deposit DECIMAL(10,2),
  returned_count INT DEFAULT 0,
  status VARCHAR(20) DEFAULT 'active',
  remark VARCHAR(500),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id)
);

-- 操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  admin_id INT,
  admin_name VARCHAR(50),
  action VARCHAR(100),
  target_type VARCHAR(50),
  target_id INT,
  detail TEXT,
  ip VARCHAR(50),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ===== 初始数据 =====
INSERT INTO admins (username, password_hash, real_name, phone, role) VALUES
('admin', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '老板', '', 'super_admin'),
('manager', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '王经理', '', 'admin'),
('dispatcher', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '赵调度', '', 'dispatcher'),
('zhangsan', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '张三', '', 'delivery'),
('lisi', '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', '李四', '', 'delivery');

INSERT INTO products (name, spec, price, deposit_price, stock, sort_order) VALUES
('5kg 家用瓶', '5kg', 45, 80, 400, 1),
('15kg 标准瓶', '15kg', 120, 150, 3500, 2),
('50kg 商用瓶', '50kg', 380, 280, 800, 3);

INSERT INTO stations (name, short_name, address, lat, lng, phone, is_default, sort_order) VALUES
('襄阳市园中园燃气有限公司', '园中园站', '湖北省襄阳市', 32.0090, 112.1224, '400-123-4567', 1, 1);
