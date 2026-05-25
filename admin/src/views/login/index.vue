<template>
  <div class="login-bg">
    <div class="login-card">
      <h2>襄阳市园中园燃气有限公司</h2>
      <p>瓶装液化气充装站管理系统</p>
      <el-form @submit.prevent="handleLogin">
        <el-form-item><el-input v-model="username" placeholder="账号" size="large" /></el-form-item>
        <el-form-item><el-input v-model="password" type="password" placeholder="密码" size="large" show-password /></el-form-item>
        <el-button type="primary" size="large" style="width:100%" @click="handleLogin" :loading="loading">登录</el-button>
      </el-form>
      <p style="text-align:center;color:#aaa;margin-top:16px;font-size:12px">默认账号: admin / admin123</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()
const username = ref(''), password = ref(''), loading = ref(false)
async function handleLogin() {
  loading.value = true
  try {
    const res = await api.login({ username: username.value, password: password.value })
    if (res.code === 0) {
      localStorage.setItem('admin_token', res.data.token)
      localStorage.setItem('admin_info', JSON.stringify(res.data.user))
      router.push('/dashboard')
    } else { ElMessage.error(res.message || '登录失败') }
  } catch {} finally { loading.value = false }
}
</script>

<style scoped>
.login-bg{background:linear-gradient(135deg,#1a3a5c 0%,#2c5f2d 100%);min-height:100vh;display:flex;align-items:center;justify-content:center}
.login-card{background:white;border-radius:16px;padding:40px;width:400px;box-shadow:0 20px 60px rgba(0,0,0,.3)}
.login-card h2{text-align:center;color:#1a3a5c;margin-bottom:8px}
.login-card p{text-align:center;color:#888;margin-bottom:24px}
</style>
