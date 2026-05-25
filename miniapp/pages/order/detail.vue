<template>
  <view class="p20">
    <text class="t">订单详情</text>
    <view v-if="loading" class="ts">加载中...</view>
    <view v-else-if="order" class="detail-card">
      <view class="row"><text class="label">订单编号</text><text class="value">{{ order.order_no }}</text></view>
      <view class="row"><text class="label">订单状态</text><text class="value status" :style="{color:statusColor}">{{ statusText }}</text></view>
      <view class="row"><text class="label">商品名称</text><text class="value">{{ order.product_name }}（{{ order.product_spec }}）</text></view>
      <view class="row"><text class="label">数量</text><text class="value">×{{ order.quantity }}</text></view>
      <view class="row"><text class="label">单价</text><text class="value">¥{{ order.product_price }}</text></view>
      <view class="row"><text class="label">总金额</text><text class="value price">¥{{ order.pay_amount || order.total_amount }}</text></view>
      <view class="row"><text class="label">配送时间</text><text class="value">{{ order.delivery_time }}</text></view>
      <view class="row" v-if="order.delivery_address"><text class="label">配送地址</text><text class="value">{{ order.delivery_address }}</text></view>
      <view class="row"><text class="label">下单时间</text><text class="value">{{ formatDate(order.created_at) }}</text></view>
    </view>
  </view>
</template>

<script>
import api from '@/utils/api'

export default {
  data() {
    return {
      order: null,
      loading: true
    }
  },
  computed: {
    statusText() {
      const map = { pending: '待配送', paid: '已支付', assigned: '已派单', delivering: '配送中', completed: '已完成', cancelled: '已取消' }
      return map[this.order?.status] || this.order?.status || ''
    },
    statusColor() {
      return { pending: '#BA7517', paid: '#378ADD', assigned: '#378ADD', delivering: '#378ADD', completed: '#0F6E56', cancelled: '#999' }[this.order?.status] || '#999'
    }
  },
  onLoad(options) {
    if (options.orderNo) this.loadDetail(options.orderNo)
  },
  methods: {
    async loadDetail(orderNo) {
      try {
        const res = await api.getOrderDetail(orderNo)
        if (res.code === 0) this.order = res.data
      } catch { uni.showToast({ title: '加载失败', icon: 'none' }) }
      finally { this.loading = false }
    },
    formatDate(d) {
      if (!d) return ''
      return d.substring(0, 16).replace('T', ' ')
    }
  }
}
</script>

<style scoped>
.p20 { padding: 20px; }
.t { font-size: 18px; font-weight: bold; display: block; margin-bottom: 16px; }
.ts { color: #999; font-size: 14px; text-align: center; padding: 40px; }
.detail-card { background: #fff; border-radius: 12px; padding: 16px; }
.row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f5f5f5; font-size: 14px; }
.row:last-child { border-bottom: none; }
.label { color: #666; }
.value { color: #333; }
.price { font-size: 16px; font-weight: bold; color: #E24B4A; }
.status { font-weight: bold; }
</style>
