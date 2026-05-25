/** 短信发送（开发阶段用模拟方式） */
const crypto = require('crypto')

async function sendSMS(phone, code) {
  // 生产环境不输出验证码明文
  if (process.env.NODE_ENV === 'production') {
    console.log(`[短信] 验证码已发送至 ${phone.slice(0,3)}****${phone.slice(-4)}`)
  } else {
    console.log(`[短信][开发] ${phone} 验证码: ${code}`)
  }
  return { success: true };
}

function generateCode() {
  return crypto.randomInt(100000, 1000000).toString()
}

module.exports = { sendSMS, generateCode };
