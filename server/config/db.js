const mysql = require('mysql2/promise');
const cfg = require('./env');

const pool = mysql.createPool({
  host: cfg.DB.host,
  user: cfg.DB.user,
  password: cfg.DB.password,
  database: cfg.DB.database,
  charset: 'utf8mb4',
  waitForConnections: true,
  connectionLimit: 10,
  maxIdle: 10,
  idleTimeout: 60000,
  queueLimit: 50,       // 队列上限，避免无限排队耗尽内存
  enableKeepAlive: true,
  keepAliveInitialDelay: 10000,
  connectTimeout: 10000,
});

// 连接池级错误监听 — 防止静默断连
pool.on('error', (err) => {
  console.error('[DB] 连接池错误:', err.message);
});

// 启动时验证数据库连接
pool.getConnection()
  .then(conn => {
    console.log('[DB] 数据库连接成功');
    conn.release();
  })
  .catch(err => {
    console.error('[DB] 数据库连接失败:', err.message);
    if (cfg.NODE_ENV === 'production') process.exit(1);
  });

// 优雅关闭
const gracefulShutdown = async () => {
  console.log('[DB] 正在关闭连接池...');
  await pool.end();
  console.log('[DB] 连接池已关闭');
};

// 在 app.js 的 listen 回调中注册，这里只导出函数供 app.js 调用
module.exports = pool;
module.exports.shutdown = gracefulShutdown;
