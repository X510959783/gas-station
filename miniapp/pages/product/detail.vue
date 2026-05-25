<template>
  <view class="container">
    <view class="product-header">
      <text class="product-icon">🛢️</text>
      <text class="product-name">{{ product.name }}</text>
      <text class="product-spec">规格：{{ product.spec }}</text>
      <text class="product-price">¥{{ product.price }}</text>
      <text class="deposit" v-if="product.deposit_price > 0">钢瓶押金：¥{{ product.deposit_price }}</text>
    </view>

    <view class="info-card">
      <view class="info-row"><text class="label">数量</text>
        <view class="qty-ctrl">
          <text class="qty-btn" @click="qty > 1 ? qty-- : null">−</text>
          <text class="qty-num">{{ qty }}</text>
          <text class="qty-btn" @click="qty++">+</text>
        </view>
      </view>
      <view class="info-row"><text class="label">收货地址</text>
        <text class="value">{{ userAddress || '请先完善注册信息' }}</text>
      </view>
      <view class="info-row"><text class="label">配送时间</text>
        <picker mode="selector" :range="timeOptions" @change="onTimeChange">
          <text class="value picker">{{ deliveryTime }}</text>
        </picker>
      </view>
    </view>

    <view class="price-bar">
      <text class="total-label">合计</text>
      <text class="total-price">¥{{ product.price * qty }}</text>
    </view>

    <button class="order-btn" @click="handleOrder">立即下单</button>
  </view>
</template>

<script>
import api from '@/utils/api'

export default {
  data() {
    return {
      product: { id: 0, name: '', price: 0, spec: '', deposit_price: 0 },
      qty: 1,
      deliveryTime: '今天 上午',
      timeOptions: ['今天 上午', '今天 下午', '今天 晚上', '明天 上午', '明天 下午', '明天 晚上'],
      userAddress: ''
    }
  },
  onLoad(options) {
    this.product = {
      id: options.id || 0,
      name: decodeURIComponent(options.name || ''),
      price: Number(options.price) || 0,
      spec: decodeURIComponent(options.spec || ''),
      deposit_price: Number(options.deposit_price) || 0
    }
    this.loadUserInfo()
  },
  methods: {
    async loadUserInfo() {
      try {
        const res = await api.getProfile()
        if (res.code === 0 && res.data) {
          this.userAddress = res.data.address || ''
        }
      } catch { /* 未登录静默处理 */ }
    },
    onTimeChange(e) {
      this.deliveryTime = this.timeOptions[e.detail.value]
    },
    handleOrder() {
      const p = this.product
      uni.navigateTo({
        url: `/pages/order/confirm?id=${p.id}&name=${encodeURIComponent(p.name)}&price=${p.price}&spec=${encodeURIComponent(p.spec)}&qty=${this.qty}&time=${encodeURIComponent(this.deliveryTime)}&deposit=${p.deposit_price}`
      })
    }
  }
}
</script>

<style scoped>
.container { padding: 20px; }
.product-header { background: #fff; border-radius: 12px; padding: 30px 20px; text-align: center; margin-bottom: 12px; }
.product-icon { font-size: 56px; display: block; margin-bottom: 12px; }
.product-name { display: block; font-size: 18px; font-weight: bold; color: #333; }
.product-spec { display: block; font-size: 13px; color: #999; margin: 6px 0; }
.product-price { display: block; font-size: 28px; font-weight: bold; color: #E24B4A; margin-top: 10px; }
.deposit { display: block; font-size: 12px; color: #BA7517; margin-top: 6px; }

.info-card { background: #fff; border-radius: 12px; padding: 0 16px; margin-bottom: 12px; }
.info-row { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid #f5f5f5; }
.info-row:last-child { border-bottom: none; }
.label { font-size: 14px; color: #333; }
.value { font-size: 14px; color: #666; }
.picker { color: #0F6E56; }

.qty-ctrl { display: flex; align-items: center; gap: 16px; }
.qty-btn { width: 30px; height: 30px; border: 1px solid #ddd; border-radius: 15px; text-align: center; line-height: 30px; font-size: 18px; color: #333; }
.qty-num { font-size: 16px; font-weight: bold; min-width: 20px; text-align: center; }

.price-bar { background: #fff; border-radius: 12px; padding: 16px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.total-label { font-size: 15px; color: #333; }
.total-price { font-size: 22px; font-weight: bold; color: #E24B4A; }

.order-btn { width: 100%; height: 48px; line-height: 48px; background: #0F6E56; color: #fff; border-radius: 8px; font-size: 16px; border: none; }
</style>
