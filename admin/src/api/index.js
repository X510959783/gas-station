import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('admin_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res.data,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_info')
      window.location.hash = '#/login'
      return Promise.reject(err)
    }
    ElMessage.error(err.response?.data?.message || '请求失败')
    return Promise.reject(err)
  }
)

export default {
  login: (data) => api.post('/admin/login', data),
  getDashboard: () => api.get('/admin/dashboard'),
  getOrders: (params) => api.get('/admin/orders', { params }),
  deliverOrder: (id) => api.put(`/admin/orders/${id}/deliver`),
  completeOrder: (id) => api.put(`/admin/orders/${id}/complete`),
  assignOrder: (id, data) => api.post(`/admin/orders/${id}/assign`, data),
  getUsers: () => api.get('/admin/users'),
  getStations: () => api.get('/admin/stations'),
  saveStation: (data) => api.post('/admin/stations', data),
  updateStation: (id, data) => api.put(`/admin/stations/${id}`, data),
  toggleStation: (id) => api.put(`/admin/stations/${id}/toggle`),
  getCoupons: () => api.get('/admin/coupons'),
  saveCoupon: (data) => api.post('/admin/coupons', data),
  updateCoupon: (id, data) => api.put(`/admin/coupons/${id}`, data),
  getWarnings: (params) => api.get('/admin/warnings', { params }),
  resolveWarning: (id) => api.put(`/admin/warnings/${id}/resolve`),
  getAnalysisRanking: () => api.get('/admin/analysis/ranking'),
  getAnalysisTrend: (days) => api.get('/admin/analysis/trend', { params: { days } }),
  getFeedback: () => api.get('/admin/feedback'),
  getProducts: () => api.get('/admin/products'),
  saveProduct: (data) => api.post('/admin/products', data),
  updateProduct: (id, data) => api.put(`/admin/products/${id}`, data),
}
