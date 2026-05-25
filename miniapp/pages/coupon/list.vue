<template>
  <view class="p20">
    <text class="t">我的优惠券</text>
    <view v-if="loading" class="ts">加载中...</view>
    <view v-else-if="coupons.length === 0" class="ts">暂无可用优惠券</view>
    <view v-for="c in coupons" :key="c.id" class="coupon-card">
      <view class="coupon-left">
        <text class="coupon-value" v-if="c.type === 'fixed'">¥{{ c.value }}</text>
        <text class="coupon-value" v-else>{{ c.value }}%</text>
        <text class="coupon-condition" v-if="c.min_amount > 0">满¥{{ c.min_amount }}可用</text>
        <text class="coupon-condition" v-else>无门槛</text>
      </view>
      <view class="coupon-right">
        <text class="coupon-name">{{ c.name }}</text>
        <text class="coupon-expire">有效期至 {{ formatDate(c.end_time) }}</text>
        <text class="coupon-status" :style="{color: c.status === 'unused' ? '#0F6E56' : '#999'}">
          {{ c.status === 'unused' ? '可使用' : c.status === 'used' ? '已使用' : '已过期' }}
        </text>
      </view>
    </view>
  </view>
</template>

<script>
import api from '@/utils/api'

export default {
  data() {
    return {
      coupons: [],
      loading: true
    }
  },
  onShow() {
    this.loadCoupons()
  },
  methods: {
    async loadCoupons() {
      this.loading = true
      try {
        const res = await api.getMyCoupons()
        if (res.code === 0) this.coupons = res.data || []
      } catch { /* 静默处理 */ }
      finally { this.loading = false }
    },
    formatDate(d) {
      if (!d) return ''
      return d.substring(0, 10)
    }
  }
}
</script>

<style scoped>
.p20 { padding: 20px; }
.t { font-size: 18px; font-weight: bold; display: block; margin-bottom: 16px; }
.ts { color: #999; font-size: 14px; text-align: center; padding: 40px; }
.coupon-card { background: #fff; border-radius: 10px; margin-bottom: 12px; display: flex; overflow: hidden; }
.coupon-left { background: #0F6E56; color: #fff; padding: 18px 14px; text-align: center; min-width: 90px; display: flex; flex-direction: column; justify-content: center; }
.coupon-value { font-size: 22px; font-weight: bold; }
.coupon-condition { font-size: 11px; margin-top: 4px; opacity: 0.8; }
.coupon-right { flex: 1; padding: 14px; display: flex; flex-direction: column; justify-content: center; }
.coupon-name { font-size: 15px; font-weight: bold; color: #333; }
.coupon-expire { font-size: 12px; color: #999; margin-top: 6px; }
.coupon-status { font-size: 12px; margin-top: 4px; }
</style>
