// Schema 边界测试生成器 — 根据 Zod schema 自动生成边界测试数据
// 用法：generateEdgeCases(schema) → [{ label, input, expectFail }]

function generateEdgeCases(schema) {
  const shape = schema._def?.typeName === 'ZodObject' ? schema.shape : null
  if (!shape) return [{ label: '非 object schema', input: undefined, expectFail: true }]

  const cases = []

  // 1. 空对象
  cases.push({ label: '空对象', input: {}, expectFail: hasRequired(shape) })

  // 2. 每个字段的边界值
  for (const [key, field] of Object.entries(shape)) {
    const def = field._def || field

    // 字符串字段
    if (def.typeName === 'ZodString') {
      const checks = def.checks || []
      const hasMin = checks.find(c => c.kind === 'min')
      const hasMax = checks.find(c => c.kind === 'max')
      const hasRegex = checks.find(c => c.kind === 'regex')

      if (hasMin && hasMin.value > 0) {
        cases.push({ label: `${key}: 空字符串`, input: { [key]: '' }, expectFail: true })
        cases.push({ label: `${key}: 最短合法值`, input: { [key]: 'x'.repeat(hasMin.value) }, expectFail: false })
      }
      if (hasMax) {
        cases.push({ label: `${key}: 超长`, input: { [key]: 'x'.repeat((hasMax.value || 100) + 1) }, expectFail: true })
      }
      if (hasRegex) {
        cases.push({ label: `${key}: 格式错误`, input: { [key]: '!!!invalid!!!' }, expectFail: true })
      }
    }

    // 数字字段
    if (def.typeName === 'ZodNumber') {
      const checks = def.checks || []
      const hasMin = checks.find(c => c.kind === 'min')
      const hasMax = checks.find(c => c.kind === 'max')

      cases.push({ label: `${key}: 字符串而非数字`, input: { [key]: 'abc' }, expectFail: true })
      if (hasMin && hasMin.value > 0) {
        cases.push({ label: `${key}: 小于最小值`, input: { [key]: hasMin.value - 1 }, expectFail: true })
      }
      if (hasMax) {
        cases.push({ label: `${key}: 超过最大值`, input: { [key]: (hasMax.value || 100) + 1 }, expectFail: true })
      }
      if (def.typeName === 'ZodNumber' && field.isInt) {
        cases.push({ label: `${key}: 浮点数而非整数`, input: { [key]: 1.5 }, expectFail: true })
      }
    }

    // 枚举字段
    if (def.typeName === 'ZodEnum') {
      cases.push({ label: `${key}: 不在枚举中`, input: { [key]: '__invalid_enum_value__' }, expectFail: true })
    }

    // 可选字段 — 可以缺失
    if (field.isOptional?.()) {
      cases.push({ label: `${key}: 缺失可选字段`, input: {}, expectFail: false })
    }
  }

  // 3. 额外字段（mass assignment）
  cases.push({ label: 'mass assignment: 额外字段 is_admin', input: { is_admin: 1 }, expectFail: false })

  // 4. null / undefined 注入
  cases.push({ label: 'null 值注入', input: null, expectFail: true })

  return cases
}

function hasRequired(shape) {
  return Object.values(shape).some(f => !f.isOptional?.())
}

// 运行单个用例
async function runCase(request, app, method, path, authToken, { label, input, expectFail }) {
  let req = request(app)[method](path)
  if (authToken) req = req.set('Authorization', `Bearer ${authToken}`)
  const res = await req.send(input)
  const passed = expectFail ? res.status >= 400 : res.status < 400
  return { label, status: res.status, passed, expectFail, body: res.body }
}

module.exports = { generateEdgeCases, runCase }
