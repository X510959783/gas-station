<template>
  <view class="pay-page">
    <text class="icon">💰</text>
    <text class="msg" v-if="orderAmount > 0">待支付 ¥{{ orderAmount }}</text>
    <text class="msg" v-else>暂无待支付订单</text>
    <text class="tip">支付功能正在对接中，请联系门店完成支付</text>
    <button class="btn" @click="callStore">联系门店</button>
    <button class="btn outline" @click="goOrders">查看订单</button>
  </view>
</template>

<script>
export default {
  data() {
    return { orderAmount: 0 }
  },
  onLoad(options) {
    if (options.amount) this.orderAmount = Number(options.amount) || 0
  },
  methods: {
    callStore() {
      uni.makePhoneCall({ phoneNumber: '0710-3017777' })
    },
    goOrders() {
      uni.switchTab({ url: '/pages/order/list' })
    }
  }
}
</script>

<style scoped>
.pay-page { display: flex; flex-direction: column; align-items: center; padding: 80px 20px; }
.icon { font-size: 56px; }
.msg { font-size: 20px; font-weight: bold; margin: 16px 0; color: #333; }
.tip { color: #999; font-size: 13px; margin-bottom: 40px; text-align: center; }
.btn { width: 240px; height: 44px; line-height: 44px; background: #0F6E56; color: #fff; border-radius: 8px; border: none; margin-bottom: 12px; }
.btn.outline { background: #fff; color: #0F6E56; border: 1px solid #0F6E56; }
</style>
