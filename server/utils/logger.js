// 统一日志工具
// 替代散落的 console.log / console.error
// 生产环境可扩展为写文件/发送到日志服务

const LOG_LEVELS = { debug: 0, info: 1, warn: 2, error: 3 }
const currentLevel = LOG_LEVELS[process.env.LOG_LEVEL] || LOG_LEVELS.info

function formatTime() {
  return new Date().toISOString().replace('T', ' ').slice(0, 19)
}

function logger(tag) {
  const prefix = tag ? `[${tag}]` : ''
  return {
    debug: (msg) => {
      if (currentLevel > LOG_LEVELS.debug) return
      console.log(`${formatTime()} ${prefix}[DEBUG]`, msg)
    },
    info: (msg, meta) => {
      if (currentLevel > LOG_LEVELS.info) return
      if (meta) console.log(`${formatTime()} ${prefix}[INFO]`, msg, meta)
      else console.log(`${formatTime()} ${prefix}[INFO]`, msg)
    },
    warn: (msg, meta) => {
      if (currentLevel > LOG_LEVELS.warn) return
      if (meta) console.warn(`${formatTime()} ${prefix}[WARN]`, msg, meta)
      else console.warn(`${formatTime()} ${prefix}[WARN]`, msg)
    },
    error: (msg, err) => {
      console.error(`${formatTime()} ${prefix}[ERROR]`, msg)
      if (err) console.error(`${formatTime()} ${prefix}[ERROR]`, err.stack || err.message || err)
    },
  }
}

// 无 tag 快捷方法：logger.info(msg) 等价于 logger() 实例
function noTagLog(level, msg, meta) {
  logger()[level](msg, meta)
}
logger.debug = (msg, meta) => noTagLog('debug', msg, meta)
logger.info = (msg, meta) => noTagLog('info', msg, meta)
logger.warn = (msg, meta) => noTagLog('warn', msg, meta)
logger.error = (msg, err) => noTagLog('error', msg, err)

module.exports = logger
