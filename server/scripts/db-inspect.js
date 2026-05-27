#!/usr/bin/env node
// 数据库检查器 — 本地"MCP 眼睛"
// 用法：node scripts/db-inspect.js <table>       → DESCRIBE table
//       node scripts/db-inspect.js <table> <col>  → 检查字段是否存在

const mysql = require('mysql2/promise')
const path = require('path')

// 读取配置（复用 env.js，但不依赖测试 mock）
const envFile = path.resolve(__dirname, '..', '.env')
require('dotenv').config({ path: envFile })

const DB = {
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'gas_station',
}

async function main() {
  const table = process.argv[2]
  const column = process.argv[3]
  const jsonMode = process.argv.includes('--json')

  if (!table) {
    console.log('用法:')
    console.log('  node scripts/db-inspect.js <table>      列出表结构')
    console.log('  node scripts/db-inspect.js <table> <col> 检查字段是否存在')
    console.log('  node scripts/db-inspect.js <table> --json  输出 JSON 字段列表')
    process.exit(0)
  }

  let conn
  try {
    conn = await mysql.createConnection({
      ...DB,
      connectTimeout: 5000,
    })

    if (column && !jsonMode) {
      // 检查字段
      const [cols] = await conn.query(`DESCRIBE \`${table}\``)
      const found = cols.find(c => c.Field === column)
      if (found) {
        console.log(`✓ ${table}.${column} 存在 (${found.Type})`)
      } else {
        console.log(`✗ ${table}.${column} 不存在`)
        console.log(`  可用字段: ${cols.map(c => c.Field).join(', ')}`)
      }
    } else if (jsonMode) {
      // JSON 输出字段名列表
      const [cols] = await conn.query(`DESCRIBE \`${table}\``)
      console.log(JSON.stringify(cols.map(c => c.Field)))
    } else {
      // 列出表结构
      const [cols] = await conn.query(`DESCRIBE \`${table}\``)
      console.log(`\n${table} 表结构:`)
      console.log('─'.repeat(60))
      for (const c of cols) {
        const key = c.Key === 'PRI' ? 'PK' : c.Key === 'MUL' ? 'FK' : '  '
        const nullable = c.Null === 'YES' ? 'NULL' : 'NOT NULL'
        console.log(`  ${key} ${c.Field.padEnd(25)} ${c.Type.padEnd(15)} ${nullable} ${c.Default ? 'DEFAULT ' + c.Default : ''}`)
      }
    }
  } catch (e) {
    if (e.code === 'ECONNREFUSED' || e.code === 'ENOTFOUND') {
      console.log('✗ 数据库未运行或配置错误')
      console.log(`  尝试连接: ${DB.host}:3306/${DB.database}`)
    } else {
      console.log(`✗ 错误: ${e.message}`)
    }
  } finally {
    if (conn) await conn.end()
  }
}

main()
