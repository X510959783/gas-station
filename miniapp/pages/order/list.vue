<template>
  <view class="container">
    <view class="tabs">
      <text v-for="t in tabs" :key="t.key" :class="['tab', activeTab===t.key?'active':'']" @click="activeTab=t.key">{{ t.label }}</text>
    </view>
    <view v-if="loading" class="empty">加载中...</view>
    <view v-else-if="filteredOrders.length===0" class="empty">暂无订单</view>
    <view v-for="o in filteredOrders" :key="o.id" class="order-card" @click="goDetail(o)">
      <view class="order-head">
        <text class="order-no">订单号：{{ o.order_no }}</text>
        <text class="order-status" :style="{color:statusColor(o.status)}">{{ statusText(o.status) }}</text>
      </view>
      <view class="order-body">
        <text class="order-name">{{ o.product_name }} {{ o.product_spec }}</text>
        <text class="order-qty">×{{ o.quantity }}</text>
      </view>
      <view class="order-foot">
        <text class="order-date">{{ formatDate(o.created_at) }}</text>
        <text class="order-price">¥{{ o.pay_amount || o.total_amount }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import api from '@/utils/api'

export default {
  data() {
    return {
      activeTab: 'all',
      loading: true,
      tabs: [
        { key: 'all', label: '全部' },
        { key: 'pending', label: '待配送' },
        { key: 'delivering', label: '配送中' },
        { key: 'completed', label: '已完成' }
      ],
      orders: []
    }
  },
  computed: {
    filteredOrders() {
      return this.activeTab === 'all'
        ? this.orders
        : this.orders.filter(o => o.status === this.activeTab)
    }
  },
  onShow() {
    this.loadOrders()
  },
  methods: {
    async loadOrders() {
      this.loading = true
      try {
        const res = await api.getOrders()
        if (res.code === 0) this.orders = res.data || []
      } catch { /* 静默处理 */ }
      finally { this.loading = false }
    },
    statusText(s) {
      const map = { pending: '待配送', paid: '已支付', assigned: '已派单', delivering: '配送中', completed: '已完成', cancelled: '已取消' }
      return map[s] || s
    },
    statusColor(s) {
      return { pending: '#BA7517', paid: '#378ADD', assigned: '#378ADD', delivering: '#378ADD', completed: '#0F6E56', cancelled: '#999' }[s] || '#999'
    },
    formatDate(d) {
      if (!d) return ''
      return d.substring(0, 10)
    },
    goDetail(o) {
      uni.navigateTo({ url: '/pages/order/detail?orderNo=' + o.order_no })
    }
  }
}
</script>

<style scoped>
.container { padding: 0; }
.tabs { display: flex; background: #fff; padding: 12px 16px; gap: 20px; }
.tab { font-size: 14px; color: #666; }
.tab.active { color: #0F6E56; font-weight: bold; }
.empty { text-align: center; padding: 60px; color: #999; font-size: 14px; }
.order-card { background: #fff; margin: 8px 16px; border-radius: 10px; padding: 14px; }
.order-head { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px; }
.order-no { color: #999; }
.order-status { font-weight: bold; }
.order-body { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 15px; }
.order-name { color: #333; }
.order-qty { color: #999; }
.order-foot { display: flex; justify-content: space-between; font-size: 13px; }
.order-date { color: #999; }
.order-price { font-size: 16px; font-weight: bold; color: #E24B4A; }
</style>
