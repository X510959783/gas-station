#!/usr/bin/env node
// 记忆搜索 — 本地 RAG 替代方案
// 用法：node scripts/memory-search.js "搜索关键词"
//       由 hooks 在编辑相关文件时自动触发

const fs = require('fs')
const path = require('path')

const EVOLUTION_DIR = path.resolve(__dirname, '..', '..', '.claude', 'evolution')
const TRAP_FILE = path.resolve(EVOLUTION_DIR, '..', 'rules.md')

function loadLessons() {
  const lessonsFile = path.join(EVOLUTION_DIR, 'lessons.md')
  if (!fs.existsSync(lessonsFile)) return []
  const content = fs.readFileSync(lessonsFile, 'utf-8')
  const lessons = []
  const lines = content.split('\n')
  for (const line of lines) {
    const match = line.match(/^- \*\*(.+?)\*\* — (.+)$/)
    if (match) {
      lessons.push({ title: match[1].trim(), detail: match[2].trim(), line })
    }
  }
  return lessons
}

function search(keyword, context) {
  const lessons = loadLessons()
  const keywordLower = keyword.toLowerCase()

  // 关键词匹配
  const matches = lessons.filter(l =>
    l.title.toLowerCase().includes(keywordLower) ||
    l.detail.toLowerCase().includes(keywordLower)
  )

  if (matches.length === 0) {
    console.log(`  [记忆] 未找到与 "${keyword}" 相关的教训`)
    return []
  }

  console.log(`  [记忆] 找到 ${matches.length} 条相关教训：`)
  matches.forEach((m, i) => {
    console.log(`    ${i + 1}. ${m.title}`)
    console.log(`       ${m.detail.slice(0, 120)}`)
  })
  return matches
}

// 根据当前编辑的文件自动推断关键词
function inferKeywords(filePath) {
  const keywords = []
  const basename = path.basename(filePath)

  // 文件→关键词映射（中英双语）
  const map = {
    'validate.js': ['zod', 'issues', 'errors', '校验', 'validation', 'safeParse', '中间件'],
    'db.js': ['连接池', 'connection', 'queue', '事务', 'transaction', 'mysql', 'pool'],
    'logger.js': ['logger', '日志', 'logging', '静态方法', 'mock', '接口一致'],
    'auth.js': ['jwt', 'token', '鉴权', '过期', 'refresh', 'secret', '密钥'],
    'app.js': ['中间件', 'middleware', 'rate', '限流', '错误处理', 'rfc', 'helmet', 'cors'],
    'orders.js': ['order', '订单', '事务', 'transaction', 'bola', '参数化查询'],
    'feedback.js': ['xss', 'sanitize', '反馈', '校验'],
    'coupons.js': ['优惠券', 'coupon', '事务', 'transaction', '竞态'],
    'errors.js': ['apperror', 'rfc', '错误', 'validation', 'notfound', '全局错误处理'],
    'env.js': ['jwt', 'secret', '密钥', '环境变量', 'max_order', '配置'],
    'scheduler.js': ['定时', 'scheduler', '预警', 'cron'],
    'sms.js': ['短信', 'sms', '验证码', '限流'],
    'products.js': ['商品', 'product', '校验', 'status'],
    'stations.js': ['站点', 'station', 'sort'],
  }

  for (const [file, keys] of Object.entries(map)) {
    if (basename.includes(file)) {
      keywords.push(...keys)
    }
  }

  return keywords
}

// ─── 上下文感知：分析文件内容 ───
function analyzeContext(filePath) {
  if (!fs.existsSync(filePath)) return { warnings: [], riskLevel: 'unknown' }

  const content = fs.readFileSync(filePath, 'utf-8')
  const warnings = []

  // 检测 Zod errors vs issues
  if (content.includes('result.error.errors') && !content.includes('result.error.issues')) {
    warnings.push('CRITICAL: 使用了 result.error.errors（Zod v3 API），应改为 result.error.issues（Zod v4）')
  }

  // 检测 logger 接口一致性
  if (content.includes('logger.info(') || content.includes('logger.error(')) {
    if (!content.includes("logger.info =") && !content.includes("module.exports")) {
      warnings.push('⚠ 使用了 logger.info() 但应确认 logger 有静态方法（当前 logger.js 已修复，如是 mock 需同步）')
    }
  }

  // 检测 SQL 模板字符串拼接
  if (content.includes('pool.query(`') || content.includes('pool.execute(`')) {
    warnings.push('CRITICAL: SQL 模板字符串拼接 — 必须改为参数化查询 (? 占位符 + 参数数组)')
  }

  // 检测缺少事务
  if ((content.includes('pool.query') || content.includes('conn.query'))
      && content.includes('INSERT') && content.includes('UPDATE')
      && !content.includes('beginTransaction')) {
    warnings.push('⚠ 多个写操作可能缺少事务保护')
  }

  // 检测缺少 BOLA 防护
  if (content.includes('router.get') && content.includes('user_id')
      && !content.includes('req.user.id') && !content.includes('AND user_id')) {
    warnings.push('⚠ 用户数据查询可能缺少所有权校验 (BOLA)')
  }

  // 检测 CORS/安全头
  if (filePath.includes('app.js') && content.includes('cors(')) {
    const hasProd = content.includes('production') && content.includes('CORS_ORIGINS')
    if (!hasProd) {
      warnings.push('⚠ CORS 在生产环境应严格校验来源')
    }
  }

  // 行号精度检测
  const lineIssues = []
  const lines = content.split('\n')
  lines.forEach((line, idx) => {
    const lineNum = idx + 1

    // Zod errors vs issues
    if (line.includes('result.error.errors') && !line.includes('result.error.issues')) {
      lineIssues.push({ line: lineNum, severity: 'critical', msg: 'Zod v4: 用了 .errors 应改为 .issues', code: line.trim().slice(0, 80) })
    }

    // SQL 模板字符串
    if ((line.includes('pool.query(`') || line.includes('pool.execute(`') || line.includes('conn.query(`')) && line.includes('${')) {
      lineIssues.push({ line: lineNum, severity: 'critical', msg: 'SQL 模板字符串拼接', code: line.trim().slice(0, 80) })
    }

    // logger.info() 无静态方法检查
    if (line.includes('logger.info(') && !content.includes('logger.info =') && !content.includes("logger.info = (msg")) {
      lineIssues.push({ line: lineNum, severity: 'warning', msg: 'logger.info() 需确认静态方法存在', code: line.trim().slice(0, 80) })
    }

    // 硬编码密钥
    if (line.match(/SECRET\s*=\s*['"][^'"]+['"]/) || line.match(/password\s*=\s*['"][^'"]+['"]/)) {
      lineIssues.push({ line: lineNum, severity: 'critical', msg: '疑似硬编码密钥/密码', code: line.trim().slice(0, 80) })
    }

    // 缺少 user_id 的查询
    if ((line.includes('SELECT') || line.includes('UPDATE') || line.includes('DELETE')) && line.includes('WHERE') && !line.includes('user_id') && (filePath.includes('orders') || filePath.includes('feedback') || filePath.includes('coupons'))) {
      // 只在用户数据相关文件中检查
      lineIssues.push({ line: lineNum, severity: 'warning', msg: '查询可能缺少 user_id 过滤 (BOLA)', code: line.trim().slice(0, 80) })
    }
  })

  // 合并到 warnings
  if (lineIssues.length > 0) {
    lineIssues.forEach(li => {
      warnings.push(`${li.severity === 'critical' ? 'CRITICAL' : '⚠'} L${li.line}: ${li.msg}`)
    })
  }

  // 风险等级
  let riskLevel = 'low'
  if (warnings.some(w => w.startsWith('CRITICAL'))) riskLevel = 'critical'
  else if (warnings.length >= 2) riskLevel = 'medium'

  return { warnings, riskLevel, lineIssues }
}

// ─── 主逻辑 ───
const args = process.argv.slice(2)
const filePath = args[0]
const explicitKeyword = args[1]

if (!filePath) {
  console.log('用法: node scripts/memory-search.js <文件路径> [关键词]')
  process.exit(0)
}

const fileName = path.basename(filePath)
console.log(`\n=== 记忆搜索: ${fileName} ===`)

// 1. 上下文感知分析
const context = analyzeContext(filePath)
if (context.warnings.length > 0) {
  const icon = context.riskLevel === 'critical' ? '🔴' : context.riskLevel === 'medium' ? '🟡' : '⚪'
  console.log(`  ${icon} 上下文风险: ${context.riskLevel.toUpperCase()}`)
  context.warnings.forEach(w => console.log(`    ${w}`))
} else {
  console.log(`  ✅ 上下文检查通过`)
}

// 2. 关键词搜索
const keywords = explicitKeyword
  ? [explicitKeyword]
  : inferKeywords(filePath)

const uniqueKeywords = [...new Set(keywords)]
console.log(`  🔍 关键词: ${uniqueKeywords.join(', ') || '(无)'}`)

let totalMatches = 0
for (const kw of uniqueKeywords) {
  const matches = search(kw)
  totalMatches += matches.length
}

if (totalMatches > 0) {
  console.log(`\n  ⚠ 共 ${totalMatches} 条相关教训，注意避免重复踩坑。`)
} else if (context.riskLevel === 'low') {
  console.log(`  ✅ 无相关教训，无风险`)
}
