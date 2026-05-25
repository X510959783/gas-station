<template>
  <div class="card">
    <el-radio-group v-model="filter" style="margin-bottom:12px">
      <el-radio-button value="active">在租中</el-radio-button>
      <el-radio-button value="returned">已退还</el-radio-button>
    </el-radio-group>
    <el-table :data="list" stripe>
      <el-table-column prop="user_nickname" label="客户" width="120"/>
      <el-table-column prop="order_no" label="订单号" width="160"/>
      <el-table-column prop="spec_type" label="规格" width="80"/>
      <el-table-column label="租用数量" width="80"><template #default="{row}">{{ row.bottle_count }}只</template></el-table-column>
      <el-table-column label="单瓶押金" width="80"><template #default="{row}">¥{{ row.deposit_per_bottle }}</template></el-table-column>
      <el-table-column label="押金总额" width="100"><template #default="{row}"><b style="color:#e74c3c">¥{{ row.total_deposit }}</b></template></el-table-column>
      <el-table-column label="已退" width="60"><template #default="{row}">{{ row.returned_count||0 }}</template></el-table-column>
      <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status==='active'?'warning':'success'" size="small">{{ row.status==='active'?'在租':'已退还' }}</el-tag></template></el-table-column>
      <el-table-column prop="created_at" label="日期" width="100"/>
      <el-table-column label="操作" width="100">
        <template #default="{row}">
          <el-button v-if="row.status==='active'" type="primary" size="small" @click="returnDeposit(row)">退瓶退款</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })
api.interceptors.request.use(c => { const t = localStorage.getItem('admin_token'); if (t) c.headers.Authorization = `Bearer ${t}`; return c })

const filter = ref('active'), list = ref([])

async function fetch() {
  try { const r = await api.get('/admin/deposits', { params: { status: filter.value } }); if (r.data.code === 0) list.value = r.data.data } catch {}
}

onMounted(fetch)
watch(filter, fetch)

async function returnDeposit(row) {
  try { const r = await api.put(`/admin/deposits/${row.id}/return`, { returned_count: row.bottle_count - (row.returned_count || 0) }); if (r.data.code === 0) { ElMessage.success(`已退款 ¥${r.data.data.refund}`); fetch() } } catch { ElMessage.error('操作失败') }
}
</script>
