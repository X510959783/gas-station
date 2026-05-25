<template>
  <view class="container">
    <view class="logo-area">
      <text class="logo">🔥</text>
      <text class="title">襄阳市园中园燃气有限公司欢迎您</text>
      <text class="subtitle">安全用气 · 配送到家</text>
    </view>
    <button class="login-btn" @click="handleLogin" :disabled="loading">
      {{ loading ? '登录中...' : '微信授权登录' }}
    </button>
    <text class="tip">首次使用需完成实名注册</text>
  </view>
</template>

<script>
import api from '@/utils/api'

export default {
  data() {
    return { loading: false }
  },
  methods: {
    handleLogin() {
      if (this.loading) return
      this.loading = true
      // #ifdef MP-WEIXIN
      uni.login({
        provider: 'weixin',
        success: async (loginRes) => {
          try {
            const res = await api.wxLogin(loginRes.code)
            if (res.code === 0) {
              uni.setStorageSync('yxrq_token', res.data.token)
              uni.setStorageSync('yxrq_user', JSON.stringify(res.data.user || {}))
              if (res.data.is_verified) {
                uni.reLaunch({ url: '/pages/index/index' })
              } else {
                uni.reLaunch({ url: '/pages/register/index' })
              }
            } else {
              uni.showToast({ title: '登录失败，请重试', icon: 'none' })
            }
          } catch { uni.showToast({ title: '网络异常，请重试', icon: 'none' }) }
          finally { this.loading = false }
        },
        fail: () => { uni.showToast({ title: '微信登录失败', icon: 'none' }); this.loading = false }
      })
      // #endif

      // #ifndef MP-WEIXIN
      // 非微信环境（开发调试）：模拟登录
      this.mockLogin()
      // #endif
    },
    // 开发模式模拟登录
    async mockLogin() {
      try {
        const res = await api.wxLogin('dev_' + Date.now())
        if (res.code === 0) {
          uni.setStorageSync('yxrq_token', res.data.token)
          uni.setStorageSync('yxrq_user', JSON.stringify(res.data.user || {}))
          if (res.data.is_verified) {
            uni.reLaunch({ url: '/pages/index/index' })
          } else {
            uni.reLaunch({ url: '/pages/register/index' })
          }
        } else {
          uni.showToast({ title: res.message || '登录失败，请重试', icon: 'none' })
        }
      } catch { uni.showToast({ title: '网络异常，请重试', icon: 'none' }) }
      finally { this.loading = false }
    }
  }
}
</script>

<style scoped>
.container {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 100vh; padding: 60px 40px; box-sizing: border-box;
}
.logo-area { text-align: center; margin-bottom: 80px; }
.logo { font-size: 72px; display: block; margin-bottom: 24px; }
.title { display: block; font-size: 18px; font-weight: bold; color: #333; margin-bottom: 8px; }
.subtitle { display: block; font-size: 14px; color: #999; }
.login-btn {
  width: 280px; height: 48px; line-height: 48px; background-color: #07C160; color: #fff;
  border-radius: 8px; font-size: 16px; border: none; margin-bottom: 16px;
}
.tip { font-size: 12px; color: #ccc; }
</style>
