<template>
  <div v-if="$route.meta.noAuth"><router-view /></div>
  <div v-else class="layout">
    <aside class="sidebar">
      <div class="logo">园中园燃气</div>
      <router-link v-for="m in menu" :key="m.path" :to="m.path" class="nav-item">{{ m.name }}</router-link>
      <a class="nav-item logout" @click="logout">退出登录</a>
    </aside>
    <main class="main">
      <div class="topbar">
        <span style="font-weight:600">{{ currentPage }}</span>
        <span>{{ adminName }} | {{ roleName }}</span>
      </div>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const adminName = computed(() => {
  try { return JSON.parse(localStorage.getItem('admin_info') || '{}').real_name || '管理员' } catch { return '管理员' }
})
const roleName = computed(() => {
  const map = { super_admin:'老板', admin:'管理员', dispatcher:'调度员', delivery:'配送员' }
  try { return map[JSON.parse(localStorage.getItem('admin_info') || '{}').role] || '' } catch { return '' }
})
const currentPage = computed(() => route.meta.title || '仪表盘')

const menu = [
  { path:'/dashboard', name:'仪表盘' },
  { path:'/orders', name:'订单管理' },
  { path:'/users', name:'用户管理' },
  { path:'/products', name:'商品管理' },
  { path:'/stations', name:'配送站管理' },
  { path:'/coupons', name:'优惠券' },
  { path:'/warnings', name:'预警管理' },
  { path:'/analysis', name:'用气分析' },
  { path:'/deposits', name:'钢瓶押金' },
]

function logout() { localStorage.clear(); router.push('/login') }
</script>

<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Microsoft YaHei",sans-serif;background:#f0f2f5}
.layout{display:flex;min-height:100vh}
.sidebar{width:200px;background:#1a3a5c;color:white;padding-top:16px;position:fixed;top:0;left:0;bottom:0;z-index:100}
.sidebar .logo{padding:0 16px 16px;font-size:16px;font-weight:700;border-bottom:1px solid rgba(255,255,255,.1);margin-bottom:8px}
.nav-item{display:block;padding:10px 20px;color:rgba(255,255,255,.7);text-decoration:none;font-size:14px;cursor:pointer}
.nav-item:hover,.nav-item.router-link-active{background:rgba(255,255,255,.1);color:white}
.logout{margin-top:40px;border-top:1px solid rgba(255,255,255,.1)}
.main{margin-left:200px;flex:1;padding:20px}
.topbar{background:white;padding:12px 20px;margin-bottom:20px;border-radius:8px;display:flex;justify-content:space-between}
</style>
