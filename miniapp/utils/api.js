// API 请求模块 — 统一管理小程序所有后端请求
// 开发环境默认 localhost，生产环境通过编译时注入

const BASE_URL = process.env.VUE_APP_API_BASE || 'http://localhost:3000/api'

function request(options) {
  const token = uni.getStorageSync('yxrq_token')
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': '***' + token } : {}),
        ...options.header
      },
      success(res) {
        if (res.statusCode === 200) resolve(res.data)
        else if (res.statusCode === 401) {
          uni.removeStorageSync('yxrq_token')
          uni.removeStorageSync('yxrq_user')
          uni.reLaunch({ url: '/pages/auth/login' })
          reject(res.data)
        } else reject(res.data)
      },
      fail() {
        uni.showToast({ title: '网络请求失败，请检查网络', icon: 'none' })
        reject(new Error('网络请求失败'))
      }
    })
  })
}

export default {
  wxLogin: (code) => request({ method: 'POST', url: '/auth/wx-login', data: { code } }),
  register: (data) => request({ method: 'POST', url: '/auth/register', data }),
  getProfile: () => request({ method: 'GET', url: '/auth/profile' }),
  getProducts: (status) => request({ method: 'GET', url: '/products', data: { status: status || 1 } }),
  createOrder: (data) => request({ method: 'POST', url: '/orders', data }),
  getOrders: (status) => request({ method: 'GET', url: '/orders', data: { status } }),
  getOrderDetail: (orderNo) => request({ method: 'GET', url: `/orders/detail/${orderNo}` }),
  getStations: () => request({ method: 'GET', url: '/stations' }),
  getAvailableCoupons: () => request({ method: 'GET', url: '/coupons/available' }),
  receiveCoupon: (couponId) => request({ method: 'POST', url: `/coupons/${couponId}/receive` }),
  getMyCoupons: (status) => request({ method: 'GET', url: '/coupons/my', data: { status } }),
  submitFeedback: (data) => request({ method: 'POST', url: '/feedback', data }),
  sendSms: (phone) => request({ method: 'POST', url: '/sms/send', data: { phone } }),
  verifySms: (phone, code) => request({ method: 'POST', url: '/sms/verify', data: { phone, code } }),
}
