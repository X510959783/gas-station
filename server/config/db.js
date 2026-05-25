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
  queueLimit: 0,
  enableKeepAlive: true,
  keepAliveInitialDelay: 10000,
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

module.exports = pool;
