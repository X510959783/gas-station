import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/login/index.vue'), meta: { noAuth: true } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/dashboard/index.vue') },
  { path: '/orders', name: 'Orders', component: () => import('../views/order/index.vue') },
  { path: '/users', name: 'Users', component: () => import('../views/user/index.vue') },
  { path: '/products', name: 'Products', component: () => import('../views/product/index.vue') },
  { path: '/stations', name: 'Stations', component: () => import('../views/station/index.vue') },
  { path: '/coupons', name: 'Coupons', component: () => import('../views/coupon/index.vue') },
  { path: '/warnings', name: 'Warnings', component: () => import('../views/warning/index.vue') },
  { path: '/analysis', name: 'Analysis', component: () => import('../views/analysis/index.vue') },
  { path: '/deposits', name: 'Deposits', component: () => import('../views/deposit/index.vue') },
]

const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token')
  if (!to.meta.noAuth && !token) return next('/login')
  next()
})

export default router
