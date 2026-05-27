#!/usr/bin/env node
// 校准计算器 — 算 Brier 分数 + 校准曲线
// 用法：node scripts/calibration-score.js

const fs = require('fs')
const path = require('path')

const CALIBRATION_FILE = path.resolve(__dirname, '..', '..', '.claude', 'evolution', 'calibration.md')

function parsePredictions() {
  if (!fs.existsSync(CALIBRATION_FILE)) {
    console.log('校准文件不存在')
    return []
  }

  const content = fs.readFileSync(CALIBRATION_FILE, 'utf-8')
  const lines = content.split('\n')
  const predictions = []

  for (const line of lines) {
    // 匹配表格行：| 日期 | 预测 | 确信度 | 追踪 | 结果 | Brier | 教训 |
    const match = line.match(/^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(\d+)%\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|/)
    if (!match) continue
    const [, date, prediction, confidenceStr, tracking, result, brier, lesson] = match
    const confidence = parseInt(confidenceStr) / 100
    if (isNaN(confidence)) continue

    // 解析结果
    let actual = null
    if (result.trim() === '✓' || result.trim().toLowerCase() === 'yes') actual = 1
    else if (result.trim() === '✗' || result.trim().toLowerCase() === 'no') actual = 0

    predictions.push({
      date: date.trim(),
      prediction: prediction.trim(),
      confidence,
      tracking: tracking.trim(),
      result: result.trim(),
      actual,
      brier: brier.trim(),
      lesson: lesson.trim(),
    })
  }

  return predictions
}

function calculateBrier(predictions) {
  const resolved = predictions.filter(p => p.actual !== null)
  if (resolved.length === 0) return { brier: null, count: 0, resolved: 0 }

  const total = resolved.reduce((sum, p) => {
    const score = Math.pow(p.confidence - p.actual, 2)
    return sum + score
  }, 0)

  return {
    brier: (total / resolved.length).toFixed(4),
    count: predictions.length,
    resolved: resolved.length,
    score: (total / resolved.length),
  }
}

function checkCalibration(predictions) {
  const resolved = predictions.filter(p => p.actual !== null)
  if (resolved.length < 10) return null

  // 按置信度分组
  const buckets = {}
  for (const p of resolved) {
    const bucket = Math.round(p.confidence * 20) / 20 // 0.05 精度
    const key = Math.round(bucket * 100)
    if (!buckets[key]) buckets[key] = { total: 0, actual: 0 }
    buckets[key].total++
    buckets[key].actual += p.actual
  }

  const calib = []
  for (const [key, bucket] of Object.entries(buckets)) {
    const predicted = parseInt(key) / 100
    const actual = bucket.actual / bucket.total
    calib.push({ predicted, actual, count: bucket.total, bias: (actual - predicted).toFixed(2) })
  }

  return calib.sort((a, b) => a.predicted - b.predicted)
}

function analyzeBias(predictions) {
  const resolved = predictions.filter(p => p.actual !== null)
  if (resolved.length === 0) return null

  let overconfident = 0
  let underconfident = 0
  let calibrated = 0

  for (const p of resolved) {
    const diff = p.confidence - p.actual
    if (Math.abs(diff) < 0.10) calibrated++
    else if (diff > 0) overconfident++
    else underconfident++
  }

  return {
    overconfident,
    underconfident,
    calibrated,
    overconfidenceRatio: (overconfident / resolved.length * 100).toFixed(1),
    underconfidenceRatio: (underconfident / resolved.length * 100).toFixed(1),
    calibrationRatio: (calibrated / resolved.length * 100).toFixed(1),
  }
}

// ═══ 主流程 ═══
const predictions = parsePredictions()
console.log(`\n=== 校准报告 ===`)
console.log(`  总预测数: ${predictions.length}`)

const resolved = predictions.filter(p => p.actual !== null)
console.log(`  已解决: ${resolved.length}`)
console.log(`  待验证: ${predictions.length - resolved.length}`)

if (resolved.length > 0) {
  const brier = calculateBrier(predictions)
  console.log(`\n  Brier 分数: ${brier.brier}`)

  // 评级
  let grade
  if (brier.score < 0.12) grade = '超级预测者水平 🏆'
  else if (brier.score < 0.15) grade = '优秀'
  else if (brier.score < 0.20) grade = '良好'
  else if (brier.score < 0.25) grade = '有信息量'
  else if (brier.score < 0.30) grade = '不如随机'
  else grade = '系统性错误——需要反转'

  console.log(`  评级: ${grade}`)
}

const bias = analyzeBias(predictions)
if (bias) {
  console.log(`\n  校准偏差:`)
  console.log(`    过度自信: ${bias.overconfidenceRatio}% (${bias.overconfident}/${resolved.length})`)
  console.log(`    不够自信: ${bias.underconfidenceRatio}% (${bias.underconfident}/${resolved.length})`)
  console.log(`    校准良好: ${bias.calibrationRatio}% (${bias.calibrated}/${resolved.length})`)
}

const calib = checkCalibration(predictions)
if (calib) {
  console.log(`\n  校准曲线:`)
  for (const c of calib) {
    const bar = '█'.repeat(Math.round(c.actual * 20))
    const target = '·'.repeat(Math.round(c.predicted * 20))
    console.log(`    ${Math.round(c.predicted*100)}% → 实际 ${Math.round(c.actual*100)}% (${c.count}次) ${bar}`)
  }
}

console.log()
