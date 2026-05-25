<template>
  <view class="container">
    <view class="card">
      <text class="card-title">商品信息</text>
      <view class="row"><text class="label">商品</text><text class="value">{{ order.name }}（{{ order.spec }}）</text></view>
      <view class="row"><text class="label">数量</text><text class="value">×{{ order.qty }}</text></view>
      <view class="row"><text class="label">单价</text><text class="value">¥{{ order.price }}</text></view>
      <view class="row"><text class="label">押金/瓶</text><text class="value">¥{{ order.deposit }}</text></view>
      <view class="row"><text class="label">配送时间</text><text class="value">{{ order.deliveryTime }}</text></view>
    </view>

    <view class="card">
      <text class="card-title">金额明细</text>
      <view class="row"><text class="label">商品总价</text><text class="value">¥{{ order.price * order.qty }}</text></view>
      <view class="row total"><text class="label">实付金额</text><text class="value price">¥{{ order.price * order.qty }}</text></view>
    </view>

    <button class="submit-btn" :disabled="submitting" @click="handleSubmit">
      {{ submitting ? '提交中...' : '提交订单' }}
    </button>
  </view>
</template>

<script>
import api from '@/utils/api'

export default {
  data() {
    return {
      order: { id: 0, name: '', price: 0, spec: '', qty: 1, deliveryTime: '', deposit: 0 },
      submitting: false
    }
  },
  onLoad(options) {
    this.order = {
      id: options.id || 0,
      name: decodeURIComponent(options.name || ''),
      price: Number(options.price) || 0,
      spec: decodeURIComponent(options.spec || ''),
      qty: Number(options.qty) || 1,
      deliveryTime: decodeURIComponent(options.time || '今天 上午'),
      deposit: Number(options.deposit) || 0
    }
  },
  methods: {
    async handleSubmit() {
      this.submitting = true
      try {
        const res = await api.createOrder({
          product_id: parseInt(this.order.id),
          product_name: this.order.name,
          product_spec: this.order.spec,
          product_price: this.order.price,
          quantity: this.order.qty,
          delivery_time: this.order.deliveryTime
        })
        if (res.code === 0) {
          uni.showToast({ title: '下单成功', icon: 'success' })
          setTimeout(() => { uni.switchTab({ url: '/pages/order/list' }) }, 800)
        } else {
          uni.showToast({ title: res.message || '下单失败', icon: 'none' })
        }
      } catch { uni.showToast({ title: '提交失败', icon: 'none' }) }
      finally { this.submitting = false }
    }
  }
}
</script>

<style scoped>
.container { padding: 20px; }
.card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
.card-title { font-size: 15px; font-weight: bold; color: #333; margin-bottom: 12px; display: block; }
.row { display: flex; justify-content: space-between; padding: 8px 0; font-size: 14px; }
.label { color: #666; }
.value { color: #333; }
.total { border-top: 1px solid #f5f5f5; margin-top: 8px; padding-top: 12px; }
.price { font-size: 18px; font-weight: bold; color: #E24B4A; }
.submit-btn { width: 100%; height: 48px; line-height: 48px; background: #0F6E56; color: #fff; border-radius: 8px; font-size: 16px; border: none; }
</style>
