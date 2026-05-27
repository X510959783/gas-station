#!/usr/bin/env node
// 记忆索引构建器 — 将 lessons + patterns + rules 编译为可搜索 JSON
// 用法：node scripts/build-memory-index.js
//       每次进化后重新构建

const fs = require('fs')
const path = require('path')

const EVOLUTION_DIR = path.resolve(__dirname, '..', '..', '.claude', 'evolution')
const INDEX_FILE = path.resolve(__dirname, '..', '.claude', 'memory-index.json')

function extractLessons() {
  const lessonsFile = path.join(EVOLUTION_DIR, 'lessons.md')
  if (!fs.existsSync(lessonsFile)) return []
  const content = fs.readFileSync(lessonsFile, 'utf-8')
  const entries = []
  const lines = content.split('\n')
  for (const line of lines) {
    const match = line.match(/^- \*\*(.+?)\*\* — (.+)$/)
    if (match) {
      entries.push({
        type: 'lesson',
        title: match[1].trim(),
        detail: match[2].trim(),
        text: line,
        source: 'lessons.md',
      })
    }
  }
  return entries
}

function extractPatterns() {
  const patternsFile = path.join(EVOLUTION_DIR, 'patterns.md')
  if (!fs.existsSync(patternsFile)) return []
  const content = fs.readFileSync(patternsFile, 'utf-8')
  const entries = []
  const sections = content.split(/^## /m)
  for (const section of sections) {
    const lines = section.split('\n')
    const title = lines[0]?.replace(/^P\d+: /, '').trim()
    const trigger = lines.find(l => l.includes('触发条件'))
    if (title && trigger) {
      entries.push({
        type: 'pattern',
        title,
        detail: trigger.replace(/\*\*触发条件：\*\*\s*/, '').trim(),
        source: 'patterns.md',
      })
    }
  }
  return entries
}

function buildIndex() {
  const lessons = extractLessons()
  const patterns = extractPatterns()
  const allEntries = [...lessons, ...patterns]

  // 构建关键词映射
  const keywordMap = {}
  const keywords = new Set()

  for (const entry of allEntries) {
    const text = (entry.title + ' ' + entry.detail).toLowerCase()

    // 提取关键词
    const words = text.match(/\b[a-z一-鿿]{2,}\b/gi) || []
    for (const word of words) {
      const key = word.toLowerCase()
      if (!keywordMap[key]) keywordMap[key] = []
      if (!keywordMap[key].includes(entry.title)) {
        keywordMap[key].push(entry.title)
      }
      keywords.add(key)
    }
  }

  const index = {
    built: new Date().toISOString(),
    totalEntries: allEntries.length,
    lessons: lessons.length,
    patterns: patterns.length,
    entries: allEntries,
    keywords: [...keywords].sort(),
    keywordMap,
  }

  const dir = path.dirname(INDEX_FILE)
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(INDEX_FILE, JSON.stringify(index, null, 2))
  console.log(`[记忆索引] ${allEntries.length} 条 (${lessons.length} 教训 + ${patterns.length} 模式) → ${INDEX_FILE}`)
  console.log(`[记忆索引] ${keywords.size} 个关键词已索引`)
}

buildIndex()
