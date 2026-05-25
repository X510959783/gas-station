<template>
  <view class="container">
    <view class="card">
      <view class="title">实名注册</view>
      <view class="subtitle">请填写真实信息完成注册</view>

      <input class="input" v-model="form.realName" placeholder="真实姓名" />
      <input class="input" v-model="form.idCard" placeholder="身份证号（18位）" maxlength="18" />
      <input class="input" v-model="form.phone" placeholder="手机号" type="number" maxlength="11" />

      <view class="sms-row">
        <input class="input sms-input" v-model="form.smsCode" placeholder="验证码" type="number" maxlength="6" />
        <button class="sms-btn" :disabled="countdown > 0" @click="sendSms">
          {{ countdown > 0 ? countdown + 's' : '获取验证码' }}
        </button>
      </view>

      <textarea class="input address-input" v-model="form.address" placeholder="收货地址（省/市/区 + 详细地址）" />

      <button class="submit-btn" :disabled="submitting" @click="handleSubmit">
        {{ submitting ? '提交中...' : '提交注册' }}
      </button>
    </view>
  </view>
</template>

<script>
import api from '@/utils/api'

export default {
  data() {
    return {
      form: { realName: '', idCard: '', phone: '', smsCode: '', address: '' },
      countdown: 0,
      timer: null,
      submitting: false
    }
  },
  methods: {
    async sendSms() {
      if (!this.form.phone || this.form.phone.length !== 11) {
        return uni.showToast({ title: '请输入正确手机号', icon: 'none' })
      }
      try {
        const res = await api.sendSms(this.form.phone)
        if (res.code === 0) {
          uni.showToast({ title: '验证码已发送', icon: 'success' })
          this.countdown = 60
          this.timer = setInterval(() => { if (--this.countdown <= 0) clearInterval(this.timer) }, 1000)
        } else {
          uni.showToast({ title: res.message || '发送失败', icon: 'none' })
        }
      } catch { uni.showToast({ title: '发送失败', icon: 'none' }) }
    },
    async handleSubmit() {
      const f = this.form
      if (!f.realName || !f.idCard || !f.phone || !f.smsCode || !f.address) {
        return uni.showToast({ title: '请填写所有字段', icon: 'none' })
      }
      if (f.idCard.length !== 18) {
        return uni.showToast({ title: '身份证号应为18位', icon: 'none' })
      }

      this.submitting = true
      try {
        // 先验证短信
        const vRes = await api.verifySms(f.phone, f.smsCode)
        if (vRes.code !== 0) {
          this.submitting = false
          return uni.showToast({ title: vRes.message || '验证码错误', icon: 'none' })
        }
        // 提交注册
        const res = await api.register({
          real_name: f.realName,
          id_card: f.idCard,
          phone: f.phone,
          address: f.address,
          sms_code: f.smsCode
        })
        if (res.code === 0) {
          uni.setStorageSync('yxrq_user', JSON.stringify({
            real_name: f.realName, phone: f.phone, address: f.address,
            is_verified: 1
          }))
          uni.showToast({ title: '注册成功', icon: 'success' })
          setTimeout(() => { uni.reLaunch({ url: '/pages/index/index' }) }, 800)
        } else {
          uni.showToast({ title: res.message || '注册失败', icon: 'none' })
        }
      } catch { uni.showToast({ title: '注册失败，请重试', icon: 'none' }) }
      finally { this.submitting = false }
    }
  },
  beforeUnmount() {
    if (this.timer) clearInterval(this.timer)
  }
}
</script>

<style scoped>
.container { padding: 20px; min-height: 100vh; box-sizing: border-box; }
.card { background: #fff; border-radius: 12px; padding: 30px 24px; }
.title { font-size: 22px; font-weight: bold; text-align: center; color: #333; margin-bottom: 6px; }
.subtitle { font-size: 13px; text-align: center; color: #999; margin-bottom: 28px; }
.input { width: 100%; height: 46px; border: 1px solid #e8e8e8; border-radius: 8px; padding: 0 14px; margin-bottom: 16px; font-size: 14px; box-sizing: border-box; }
.address-input { height: 72px; padding: 12px 14px; resize: none; }
.sms-row { display: flex; gap: 10px; margin-bottom: 16px; }
.sms-input { flex: 1; margin-bottom: 0; }
.sms-btn { flex-shrink: 0; height: 46px; line-height: 46px; background: #07C160; color: #fff; border: none; border-radius: 8px; font-size: 13px; padding: 0 16px; }
.submit-btn { width: 100%; height: 48px; line-height: 48px; background: #0F6E56; color: #fff; border-radius: 8px; font-size: 16px; border: none; margin-top: 6px; }
</style>
