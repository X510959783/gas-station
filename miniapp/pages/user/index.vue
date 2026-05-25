<template>
  <view class="container">
    <view class="user-header">
      <view class="avatar">👤</view>
      <text class="nickname">{{ userName }}</text>
      <text class="tag" v-if="isVerified">实名用户</text>
      <text class="tag" v-else>未实名</text>
    </view>
    <view class="menu-list">
      <view class="menu-item" @click="goPage('/pages/order/list')">
        <text>我的订单</text><text class="arrow">></text>
      </view>
      <view class="menu-item" @click="goPage('/pages/coupon/list')">
        <text>我的优惠券</text><text class="arrow">></text>
      </view>
      <view class="menu-item" @click="callPhone">
        <text>联系我们</text><text class="arrow">></text>
      </view>
      <view class="menu-item" @click="goPage('/pages/feedback/index')">
        <text>问题反馈</text><text class="arrow">></text>
      </view>
      <view class="menu-item" @click="goPage('/pages/register/index')">
        <text>{{ isVerified ? '修改注册信息' : '完成实名注册' }}</text><text class="arrow">></text>
      </view>
    </view>
    <view class="about">襄阳市园中园燃气有限公司</view>
  </view>
</template>

<script>
import api from '@/utils/api'

export default {
  data() {
    return {
      userName: '用户',
      isVerified: false
    }
  },
  onShow() {
    this.loadUserInfo()
  },
  methods: {
    async loadUserInfo() {
      try {
        const res = await api.getProfile()
        if (res.code === 0 && res.data) {
          this.userName = res.data.real_name || res.data.nickname || '用户'
          this.isVerified = res.data.is_verified === 1
        }
      } catch { /* 静默处理 */ }
    },
    goPage(url) {
      if (url.startsWith('/pages/order') || url.startsWith('/pages/user')) {
        uni.switchTab({ url })
      } else {
        uni.navigateTo({ url })
      }
    },
    callPhone() {
      uni.makePhoneCall({ phoneNumber: '0710-3017777' })
    }
  }
}
</script>

<style scoped>
.container { }
.user-header { background: #0F6E56; padding: 40px 20px 30px; text-align: center; }
.avatar { width: 60px; height: 60px; background: rgba(255,255,255,0.2); border-radius: 50%; margin: 0 auto 12px; line-height: 60px; font-size: 28px; }
.nickname { display: block; font-size: 18px; color: #fff; font-weight: bold; }
.tag { display: inline-block; background: rgba(255,255,255,0.2); color: #fff; font-size: 11px; padding: 2px 10px; border-radius: 10px; margin-top: 6px; }
.menu-list { background: #fff; margin: 12px 16px; border-radius: 12px; }
.menu-item { display: flex; justify-content: space-between; padding: 16px 18px; border-bottom: 1px solid #f5f5f5; font-size: 15px; color: #333; }
.menu-item:last-child { border-bottom: none; }
.arrow { color: #ccc; }
.about { text-align: center; padding: 30px; color: #ccc; font-size: 12px; }
</style>
