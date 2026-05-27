#!/usr/bin/env node
// CI 反馈闭环 — 跑完测试后自动分析失败原因，写入进化教训
// 用法：npm test && node scripts/test-feedback.js
//       或 npm run test:feedback

const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const RESULT_FILE = path.resolve(__dirname, '..', '.claude', 'test-results.json')
const LESSONS_FILE = path.resolve(__dirname, '..', '..', '.claude', 'evolution', 'lessons.md')

function run() {
  console.log('[CI Feedback] 运行测试...')
  let output
  try {
    output = execSync('npx jest --json --passWithNoTests', {
      cwd: path.resolve(__dirname, '..'),
      encoding: 'utf-8',
      timeout: 60000,
    })
  } catch (e) {
    output = e.stdout || e.message
  }

  let results
  try {
    results = JSON.parse(output)
  } catch {
    // JSON parse failed — probably test suite crashed
    const summary = { numFailedTests: -1, numPassedTests: 0, numTotalTests: 0, crash: true }
    fs.writeFileSync(RESULT_FILE, JSON.stringify(summary, null, 2))
    console.log('[CI Feedback] 测试套件崩溃，详情见', RESULT_FILE)
    return
  }

  const { numFailedTests, numPassedTests, numTotalTests, testResults } = results

  // 提取失败模式
  const failures = []
  if (testResults) {
    for (const suite of testResults) {
      if (suite.status === 'failed' && suite.assertionResults) {  // Jest uses assertionResults not testResults
        for (const test of suite.assertionResults) {
          if (test.status === 'failed') {
            failures.push({
              suite: suite.name,
              test: test.title,
              messages: test.failureMessages?.slice(0, 1).map(m => m.slice(0, 200)),
            })
          }
        }
      }
    }
  }

  const summary = {
    time: new Date().toISOString(),
    passed: numPassedTests,
    failed: numFailedTests,
    total: numTotalTests,
    failures: failures.slice(0, 20), // 最多记录 20 个
  }

  fs.writeFileSync(RESULT_FILE, JSON.stringify(summary, null, 2))
  console.log(`[CI Feedback] ${numPassedTests}/${numTotalTests} 通过, ${numFailedTests} 失败 → ${RESULT_FILE}`)

  // 如果有新失败，追加到 lessons.md
  if (numFailedTests > 0 && failures.length > 0) {
    const date = new Date().toISOString().slice(0, 10)
    const existing = fs.existsSync(LESSONS_FILE) ? fs.readFileSync(LESSONS_FILE, 'utf-8') : ''

    // 去重：避免重复记录同样的失败
    const newFailures = failures.filter(f => !existing.includes(f.test))
    if (newFailures.length > 0) {
      const lines = newFailures.map(f =>
        `- ${date}  测试失败: ${f.test} — ${(f.messages[0] || '').slice(0, 100)}`
      )
      fs.appendFileSync(LESSONS_FILE, '\n' + lines.join('\n') + '\n')
      console.log(`[CI Feedback] ${newFailures.length} 个新失败模式已写入 lessons.md`)
    } else {
      console.log('[CI Feedback] 无新失败模式')
    }
  }
}

run()
