// 统一错误响应工具函数
// 所有路由文件共用，避免重复定义
// 使用方式：serverError(res, '可选日志信息', '模块标签')
function serverError(res, logMsg, tag) {
  if (logMsg) console.error(`[${tag || 'server'}]`, logMsg)
  return res.status(500).json({ code: 500, message: '服务器内部错误，请稍后重试' })
}

module.exports = { serverError }
