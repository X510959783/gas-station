<template>
  <view class="p20">
    <text class="t">问题反馈</text>
    <view class="picker-row">
      <text class="picker-label">反馈类型</text>
      <picker mode="selector" :range="types" @change="onTypeChange">
        <text class="picker-value">{{ form.type || '请选择' }}</text>
      </picker>
    </view>
    <textarea class="ta" v-model="form.content" placeholder="请描述您遇到的问题..." />
    <input class="input" v-model="form.contact" placeholder="联系方式（选填）" />
    <button class="btn" :disabled="submitting" @click="handleSubmit">
      {{ submitting ? '提交中...' : '提交反馈' }}
    </button>
  </view>
</template>

<script>
import api from '@/utils/api'

export default {
  data() {
    return {
      types: ['配送问题', '商品问题', '服务投诉', '建议意见', '其他'],
      form: { type: '', content: '', contact: '' },
      submitting: false
    }
  },
  methods: {
    onTypeChange(e) {
      this.form.type = this.types[e.detail.value]
    },
    async handleSubmit() {
      if (!this.form.content.trim()) {
        return uni.showToast({ title: '请填写反馈内容', icon: 'none' })
      }
      this.submitting = true
      try {
        const res = await api.submitFeedback({
          type: this.form.type || '其他',
          content: this.form.content,
          contact: this.form.contact
        })
        if (res.code === 0) {
          uni.showToast({ title: '感谢您的反馈！', icon: 'success' })
          this.form = { type: '', content: '', contact: '' }
        } else {
          uni.showToast({ title: res.message || '提交失败', icon: 'none' })
        }
      } catch { uni.showToast({ title: '提交失败', icon: 'none' }) }
      finally { this.submitting = false }
    }
  }
}
</script>

<style scoped>
.p20 { padding: 20px; }
.t { font-size: 18px; font-weight: bold; margin-bottom: 16px; display: block; }
.picker-row { display: flex; justify-content: space-between; align-items: center; background: #fff; border-radius: 8px; padding: 12px 14px; margin-bottom: 12px; }
.picker-label { font-size: 14px; color: #333; }
.picker-value { font-size: 14px; color: #0F6E56; }
.ta { width: 100%; height: 120px; border: 1px solid #eee; border-radius: 8px; padding: 12px; font-size: 14px; box-sizing: border-box; margin-bottom: 12px; background: #fff; }
.input { width: 100%; height: 46px; border: 1px solid #eee; border-radius: 8px; padding: 0 14px; font-size: 14px; box-sizing: border-box; margin-bottom: 16px; background: #fff; }
.btn { width: 100%; height: 44px; background: #0F6E56; color: #fff; border-radius: 8px; border: none; }
</style>
