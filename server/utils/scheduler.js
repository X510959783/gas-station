/** 智能预警引擎 — 每日凌晨2:00自动巡检 */
const schedule = require('node-schedule');
const pool = require('../config/db');

async function runWarningCheck() {
  console.log('[预警引擎] 开始每日巡检...');
  try {
    // 规则1：超期未购（30天）
    const [r1] = await pool.query(
      `INSERT INTO warnings (user_id, user_name, user_phone, rule_type, level, message)
       SELECT u.id, u.real_name, u.phone, 'overdue', 'warning',
       CONCAT('用户', COALESCE(u.real_name,u.nickname),'已超过30天未购买')
       FROM users u WHERE u.is_verified=1 AND u.last_order_date < DATE_SUB(CURDATE(), INTERVAL 30 DAY)
       AND NOT EXISTS (SELECT 1 FROM warnings w WHERE w.user_id=u.id AND w.rule_type='overdue' AND w.created_at > DATE_SUB(CURDATE(), INTERVAL 7 DAY))`
    );
    console.log(`  超期未购: ${r1.affectedRows} 条`);

    // 规则2：用量下降（近2单对比下降>50%）
    const [users] = await pool.query('SELECT id FROM users WHERE is_verified=1 AND total_orders>=2');
    for (const u of users) {
      const [orders] = await pool.query('SELECT quantity FROM orders WHERE user_id=? AND status="completed" ORDER BY created_at DESC LIMIT 2', [u.id]);
      if (orders.length === 2 && orders[1].quantity > 0 && orders[0].quantity < orders[1].quantity * 0.5) {
        await pool.query(
          `INSERT IGNORE INTO warnings (user_id, rule_type, level, message) VALUES (?,'decline','warning',CONCAT('用气量较上次下降超过50%（',?, '→', ?, '）'))`,
          [u.id, orders[1].quantity, orders[0].quantity]
        );
      }
    }

    // 规则3：疑似流失（60天）
    const [r3] = await pool.query(
      `INSERT INTO warnings (user_id, user_name, user_phone, rule_type, level, message)
       SELECT u.id, u.real_name, u.phone, 'churn', 'danger',
       CONCAT('用户', COALESCE(u.real_name,u.nickname),'已超过60天未购买，疑似流失')
       FROM users u WHERE u.is_verified=1 AND u.last_order_date < DATE_SUB(CURDATE(), INTERVAL 60 DAY)
       AND u.total_orders>=3
       AND NOT EXISTS (SELECT 1 FROM warnings w WHERE w.user_id=u.id AND w.rule_type='churn' AND w.created_at > DATE_SUB(CURDATE(), INTERVAL 14 DAY))`
    );
    console.log(`  疑似流失: ${r3.affectedRows} 条`);

    // 规则4：周期异常（超过平均周期1.5倍）
    const [r4] = await pool.query(
      `INSERT INTO warnings (user_id, user_name, user_phone, rule_type, level, message)
       SELECT u.id, u.real_name, u.phone, 'cycle_anomaly', 'info',
       CONCAT('用户', COALESCE(u.real_name,u.nickname),'用气周期异常，可能忘记换气（周期', u.avg_order_cycle, '天）')
       FROM users u WHERE u.is_verified=1 AND u.avg_order_cycle>0
       AND u.last_order_date < DATE_SUB(CURDATE(), INTERVAL u.avg_order_cycle*1.5 DAY)
       AND NOT EXISTS (SELECT 1 FROM warnings w WHERE w.user_id=u.id AND w.rule_type='cycle_anomaly' AND w.created_at > DATE_SUB(CURDATE(), INTERVAL 3 DAY))`
    );
    console.log(`  周期异常: ${r4.affectedRows} 条`);

    console.log('[预警引擎] 巡检完成');
  } catch (e) { console.error('[预警引擎] 错误:', e.message); }
}

function startScheduler() {
  schedule.scheduleJob('0 2 * * *', runWarningCheck);
  console.log('[预警引擎] 已启动，每日凌晨2:00自动巡检');
}

module.exports = { startScheduler, runWarningCheck };
