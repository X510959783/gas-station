<template>
  <view>
    <swiper class="banner" indicator-dots autoplay circular interval="3000">
      <swiper-item><view class="banner-slide b1">安全用气 · 配送到家</view></swiper-item>
      <swiper-item><view class="banner-slide b2">新用户首单立减10元</view></swiper-item>
      <swiper-item><view class="banner-slide b3">一个电话 钢瓶到家</view></swiper-item>
    </swiper>

    <view class="section">
      <view class="section-title">选择液化气</view>
      <view class="product-grid">
        <view class="product-card" v-for="p in products" :key="p.id" @click="goDetail(p)">
          <view class="product-img"><text style="font-size:44px">🛢️</text></view>
          <text class="product-name">{{ p.name }}</text>
          <text class="product-spec">{{ p.spec }}</text>
          <view class="price-row">
            <text class="product-price">¥{{ p.price }}</text>
            <text class="buy-btn">立即订气</text>
          </view>
        </view>
      </view>
      <view v-if="products.length === 0" class="empty">暂无商品</view>
    </view>
  </view>
</template>

<script>
import api from '@/utils/api'

export default {
  data() {
    return { products: [] }
  },
  onShow() {
    this.loadProducts()
  },
  methods: {
    async loadProducts() {
      try {
        const res = await api.getProducts()
        if (res.code === 0) {
          this.products = res.data || []
        } else {
          uni.showToast({ title: '加载商品失败', icon: 'none' })
        }
      } catch { uni.showToast({ title: '网络异常，请下拉刷新', icon: 'none' }) }
    },
    goDetail(p) {
      uni.navigateTo({
        url: `/pages/product/detail?id=${p.id}&name=${encodeURIComponent(p.name)}&price=${p.price}&spec=${encodeURIComponent(p.spec)}&deposit_price=${p.deposit_price || 0}`
      })
    }
  }
}
</script>

<style scoped>
.banner { height: 180px; }
.banner-slide { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; color: #fff; }
.b1 { background: linear-gradient(135deg, #0F6E56, #1D9E75); }
.b2 { background: linear-gradient(135deg, #378ADD, #5BA3F5); }
.b3 { background: linear-gradient(135deg, #BA7517, #D4953A); }
.section { padding: 16px; }
.section-title { font-size: 16px; font-weight: bold; color: #333; margin-bottom: 12px; }
.product-grid { display: flex; gap: 12px; flex-wrap: wrap; }
.product-card { flex: 1; min-width: 140px; background: #fff; border-radius: 12px; padding: 20px 16px; text-align: center; }
.product-img { margin-bottom: 12px; }
.product-name { display: block; font-size: 15px; font-weight: bold; color: #333; }
.product-spec { display: block; font-size: 12px; color: #999; margin: 6px 0; }
.price-row { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; }
.product-price { font-size: 20px; font-weight: bold; color: #E24B4A; }
.buy-btn { font-size: 12px; color: #fff; background: #0F6E56; padding: 6px 12px; border-radius: 14px; }
.empty { text-align: center; padding: 60px; color: #999; }
</style>
