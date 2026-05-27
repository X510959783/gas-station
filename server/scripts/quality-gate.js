#!/usr/bin/env node
// 质量门禁 — 改一行代码后自动跑的全套检查
// 用法：node scripts/quality-gate.js <文件路径>
//       由 hooks 在每次 Edit/Write 后自动触发

const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..')
const HANDOFF = path.resolve(ROOT, '..', '.claude', 'session-handoff.md')

function run(cmd, opts = {}) {
  try {
    const out = execSync(cmd, { cwd: ROOT, encoding: 'utf-8', timeout: 30000, ...opts })
    return { ok: true, output: out.trim() }
  } catch (e) {
    return { ok: false, output: (e.stdout || e.stderr || e.message || '').trim() }
  }
}

function checkEslint(filePath) {
  const rel = path.relative(ROOT, filePath)
  const result = run(`npx eslint "${rel}" --no-error-on-unmatched-pattern 2>&1`)
  return { pass: result.ok && !result.output.includes('error'), detail: result.output.slice(0, 200) }
}

function checkTests(filePath) {
  const rel = path.relative(ROOT, filePath)
  // 只在改测试文件或路由文件时跑
  const normalizedRel = rel.replace(/\\/g, '/')
  if (!normalizedRel.includes('tests/') && !normalizedRel.includes('routes/')) {
    return { pass: true, detail: '(非测试/路由文件，跳过)', ran: false }
  }

  // 找对应的测试文件
  let testPath = normalizedRel
  if (normalizedRel.includes('routes/')) {
    const basename = path.basename(rel, '.js')
    const dir = normalizedRel.includes('admin/') ? 'admin/' : ''
    testPath = `tests/api/${dir}${basename}.test.js`
  }
  const fullTestPath = path.join(ROOT, ...testPath.split('/'))
  if (!fs.existsSync(fullTestPath)) {
    testPath = 'tests/api/auth.test.js' // fallback
  }

  const result = run(`npx jest "${testPath}" --passWithNoTests --no-coverage 2>&1`)
  const lines = result.output.split('\n')
  const testLine = lines.find(l => l.includes('Tests:')) || ''
  return { pass: result.ok, detail: testLine.slice(0, 100), ran: true }
}

function checkDbConsistency() {
  try {
    const envFile = path.join(ROOT, '.env')
    if (fs.existsSync(envFile)) require('dotenv').config({ path: envFile })

    const mockFields = {
      users: ['id', 'open_id', 'nickname', 'avatar', 'real_name', 'id_card', 'phone', 'address',
              'address_lat', 'address_lng', 'assigned_station_id', 'is_verified', 'role',
              'total_orders', 'total_gas_amount', 'last_order_date', 'avg_order_cycle', 'created_at', 'updated_at'],
      orders: ['id', 'order_no', 'user_id', 'station_id', 'driver_id', 'product_id', 'product_name',
               'product_spec', 'product_price', 'quantity', 'total_amount', 'deposit_amount',
               'contact_name', 'contact_phone', 'delivery_address', 'delivery_time', 'delivery_remark',
               'status', 'coupon_id', 'coupon_discount', 'pay_amount', 'pay_time', 'delivered_time', 'created_at', 'updated_at'],
      products: ['id', 'name', 'description', 'price', 'spec', 'deposit_price', 'stock', 'status', 'sort_order', 'image', 'created_at', 'updated_at'],
      coupons: ['id', 'name', 'type', 'value', 'min_amount', 'total_count', 'used_count', 'received_count', 'start_time', 'end_time', 'status', 'created_at', 'updated_at'],
      user_coupons: ['id', 'user_id', 'coupon_id', 'status', 'used_order_id', 'received_at', 'used_at'],
      deposits: ['id', 'user_id', 'order_no', 'spec_type', 'bottle_count', 'deposit_per_bottle', 'total_deposit', 'returned_count', 'status', 'remark', 'created_at', 'updated_at'],
      feedbacks: ['id', 'user_id', 'type', 'content', 'contact', 'status', 'created_at'],
      sms_codes: ['id', 'phone', 'code', 'type', 'is_used', 'expired_at', 'created_at'],
      stations: ['id', 'name', 'short_name', 'address', 'lat', 'lng', 'phone', 'contact_person', 'service_area_radius', 'status', 'is_default', 'sort_order', 'created_at', 'updated_at'],
      admins: ['id', 'username', 'password_hash', 'real_name', 'phone', 'role', 'status', 'last_login_at', 'created_at'],
      warnings: ['id', 'user_id', 'user_name', 'user_phone', 'rule_type', 'level', 'message', 'status', 'created_at', 'resolved_at'],
    }

    const { execSync } = require('child_process')
    const dbScript = path.join(ROOT, 'scripts', 'db-inspect.js')
    let issues = []

    for (const [table, fields] of Object.entries(mockFields)) {
      try {
        const raw = execSync(`node "${dbScript}" "${table}" --json`, {
          cwd: ROOT, encoding: 'utf-8', timeout: 5000,
          stdio: ['pipe', 'pipe', 'pipe']
        })
        const lines = raw.split('\n').filter(l => l.startsWith('['))
        if (lines.length === 0) continue
        const realFields = JSON.parse(lines[0])

        if (realFields.length === 0) continue
        const realSet = new Set(realFields)
        const missingInDB = fields.filter(f => !realSet.has(f))
        const missingInMock = realFields.filter(f =>
          !fields.includes(f) && !['updated_at', 'assigned_station_id', 'pay_amount',
            'station_id', 'driver_id', 'address_lat', 'address_lng'].includes(f)
        )

        if (missingInDB.length > 0) issues.push(`CRITICAL: mock有DB无(${table}): ${missingInDB.join(',')}`)
        if (missingInMock.length > 0) issues.push(`⚠ DB有mock无(${table}): ${missingInMock.join(',')}`)
      } catch { continue }
    }

    if (issues.length === 0 && Object.keys(mockFields).length > 0) {
      // 都通过了
      return { available: true, issues: [] }
    }
    return { available: true, issues }
  } catch {
    return { available: false, issues: [] }
  }
}

function searchMemory(filePath) {
  const memoryScript = path.resolve(ROOT, 'scripts', 'memory-search.js')
  const result = run(`node "${memoryScript}" "${filePath}" 2>&1`)
  const output = result.output
  const matchCount = (output.match(/⚠ 共 (\d+) 条/g) || []).map(m => parseInt(m.match(/\d+/)[0]) || 0)
  const total = matchCount.reduce((a, b) => a + b, 0)
  return { total, summary: output.split('\n').filter(l => l.match(/^\s+\d+\./)).slice(0, 3).join('\n') }
}

function checkTestQuality() {
  // 扫描测试文件中的万能框断言
  const testDir = path.join(ROOT, 'tests')
  if (!fs.existsSync(testDir)) return { universalFrames: 0, total: 0 }

  let universalCount = 0
  let totalAsserts = 0

  function scanDir(dir) {
    for (const entry of fs.readdirSync(dir)) {
      const full = path.join(dir, entry)
      if (fs.statSync(full).isDirectory()) { scanDir(full); continue }
      if (!entry.endsWith('.test.js')) continue
      const content = fs.readFileSync(full, 'utf-8')
      const lines = content.split('\n')
      for (const line of lines) {
        if (line.includes('toContain(res.status)') || line.includes('.toBe(')) {
          totalAsserts++
          // 万能框：期望 5+ 个状态码
          const match = line.match(/\[([^\]]+)\]/)
          if (match && match[1].split(',').length >= 5) {
            universalCount++
          }
        }
      }
    }
  }
  scanDir(testDir)

  const ratio = totalAsserts > 0 ? Math.round((universalCount / totalAsserts) * 100) : 0
  return { universalFrames: universalCount, total: totalAsserts, ratio }
}

function updateHandoff(filePath, lint, tests, memory) {
  if (!fs.existsSync(HANDOFF)) return
  const date = new Date().toISOString().slice(0, 19).replace('T', ' ')
  const fileName = path.basename(filePath)
  const dir = filePath.replace(/\\/g, '/')
  const type = dir.includes('routes/') ? '路由' :
               dir.includes('middleware/') ? '中间件' :
               dir.includes('config/') ? '配置' :
               dir.includes('utils/') ? '工具' :
               dir.includes('tests/') ? '测试' : '其他'

  const lintStatus = lint.pass ? '✓' : '✗'
  const testStatus = tests.ran ? (tests.pass ? '✓' : '✗') : '-'
  const lessonCount = memory.total

  const row = `| ${date} | ${fileName} | ${type} | ${lintStatus} | ${testStatus} | ${lessonCount} 条 |`

  let content = fs.readFileSync(HANDOFF, 'utf-8')

  // 插入到表格后，保持最近 10 条
  const tableEnd = content.indexOf('## 当前状态')
  if (tableEnd > 0) {
    const before = content.slice(0, tableEnd)
    const after = content.slice(tableEnd)

    // 提取现有行
    const lines = before.split('\n')
    const headerIdx = lines.findIndex(l => l.includes('| 时间 | 文件 | 类型'))
    const separatorIdx = lines.findIndex(l => l.includes('|------|------|------'))
    const firstDataIdx = separatorIdx + 1

    // 找空行结束表格
    let tableEndIdx = firstDataIdx
    while (tableEndIdx < lines.length && lines[tableEndIdx].startsWith('|')) {
      tableEndIdx++
    }

    // 插入新行，保留最近 8 条
    const oldRows = lines.slice(firstDataIdx, tableEndIdx).filter(l => l.trim())
    const newRows = [row, ...oldRows].slice(0, 8)

    const newTable = [
      ...lines.slice(0, firstDataIdx),
      ...newRows,
      ...lines.slice(tableEndIdx),
    ].join('\n')

    content = newTable + '\n' + after
    fs.writeFileSync(HANDOFF, content)
  }
}

// ═══ 主流程 ═══
const filePath = process.argv[2]
if (!filePath) {
  console.log('用法: node scripts/quality-gate.js <文件路径>')
  process.exit(0)
}

const fileName = path.basename(filePath)
console.log(`\n━━━ 质量门禁: ${fileName} ━━━`)

// 1. ESLint
const lint = checkEslint(filePath)
console.log(`  ${lint.pass ? '✅' : '❌'} ESLint${lint.detail ? ': ' + lint.detail.slice(0, 80) : ''}`)

// 2. 测试
const tests = checkTests(filePath)
if (tests.ran) {
  console.log(`  ${tests.pass ? '✅' : '❌'} 测试${tests.detail ? ': ' + tests.detail : ''}`)
} else {
  console.log(`  ⏭  测试: ${tests.detail}`)
}

// 3. 记忆搜索
const memory = searchMemory(filePath)
if (memory.total > 0) {
  console.log(`  🧠 记忆: ${memory.total} 条相关教训`)
} else {
  console.log(`  🧠 记忆: 无相关教训`)
}

// 4. 数据库一致性检查
const dbCheck = checkDbConsistency()
if (dbCheck.available) {
  if (dbCheck.issues.length > 0) {
    console.log(`  🔴 DB 一致性: ${dbCheck.issues.length} 个问题`)
    dbCheck.issues.slice(0, 3).forEach(i => console.log(`    ${i}`))
  } else {
    console.log(`  ✅ DB 一致性: mock 和真实数据库字段匹配`)
  }
} else {
  console.log(`  ⏭  DB 一致性: 数据库不可用`)
}

// 5. 测试质量
const quality = checkTestQuality()
if (quality.universalFrames > 0) {
  console.log(`  📊 测试质量: ${quality.universalFrames}/${quality.total} 万能框断言 (${quality.ratio}%)`)
}

// 6. 更新 handoff（结构化记录）
updateHandoff(filePath, lint, tests, memory)

// 6. 校准统计
let calibStats = { brier: null, count: 0 }
try {
  const calibScript = path.join(ROOT, 'scripts', 'calibration-score.js')
  const calibOut = execSync(`node "${calibScript}" 2>&1`, { cwd: ROOT, encoding: 'utf-8', timeout: 5000 })
  const brierMatch = calibOut.match(/Brier 分数: ([\d.]+)/)
  const countMatch = calibOut.match(/已解决: (\d+)/)
  if (brierMatch) calibStats.brier = parseFloat(brierMatch[1])
  if (countMatch) calibStats.count = parseInt(countMatch[1])
} catch {}

// 汇总
console.log(`  ─────────────────`)
if (calibStats.count > 0) {
  const calibIcon = calibStats.brier < 0.12 ? '🏆' : calibStats.brier < 0.20 ? '✅' : '⚠'
  console.log(`  ${calibIcon} 校准: Brier ${calibStats.brier?.toFixed(4)} (${calibStats.count} 个已验证预测)`)
}
const allPass = lint.pass && tests.pass
console.log(`  ${allPass ? '✅ 通过' : '⚠ 有问题'}`)

// 持久化到 .claude/last-quality.json（下次会话加载）
const qualityResult = {
  time: new Date().toISOString(),
  file: fileName,
  filePath: filePath,
  lint: { pass: lint.pass },
  tests: { pass: tests.pass, detail: tests.detail },
  memory: { lessons: memory.total },
  db: dbCheck,
  testQuality: quality,
  dbIssues: dbCheck.issues,
  riskLevel: dbCheck.issues.some(i => i.startsWith('CRITICAL')) ? 'critical' :
             dbCheck.issues.length > 0 ? 'warning' : 'ok',
  allPass,
}
const qualityFile = path.resolve(ROOT, '..', '.claude', 'last-quality.json')
const qualityDir = path.dirname(qualityFile)
if (!fs.existsSync(qualityDir)) fs.mkdirSync(qualityDir, { recursive: true })
fs.writeFileSync(qualityFile, JSON.stringify(qualityResult, null, 2))
console.log()
