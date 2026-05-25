<template>
  <div>
    <div class="card"><div class="toolbar">
      <el-input v-model="search.order_no" placeholder="搜索订单号" clearable style="width:200px" @change="fetch"/>
      <el-select v-model="search.status" placeholder="订单状态" clearable style="width:130px" @change="fetch">
        <el-option v-for="s in statusOpts" :key="s.value" :label="s.label" :value="s.value"/>
      </el-select>
      <el-select v-model="search.station_id" placeholder="配送站" clearable style="width:150px" @change="fetch">
        <el-option v-for="s in stations" :key="s.id" :label="s.short_name||s.name" :value="s.id"/>
      </el-select>
      <el-button type="primary" @click="fetch">查询</el-button>
    </div></div>
    <div class="card">
      <el-table :data="list" stripe style="width:100%">
        <el-table-column prop="order_no" label="订单号" width="160"/>
        <el-table-column prop="nickname" label="客户" width="100"/>
        <el-table-column prop="product_name" label="商品" width="120"/>
        <el-table-column prop="quantity" label="数量" width="60"/>
        <el-table-column label="金额">
          <template #default="{row}"><span style="color:#e74c3c;font-weight:600">¥{{ row.pay_amount }}</span></template>
        </el-table-column>
        <el-table-column label="押金" width="80"><template #default="{row}">¥{{ row.deposit_amount||0 }}</template></el-table-column>
        <el-table-column prop="station_name" label="配送站" width="100"/>
        <el-table-column prop="delivery_address" label="地址" min-width="150" show-overflow-tooltip/>
        <el-table-column label="状态" width="90"><template #default="{row}"><el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{row}">
            <el-button v-if="row.status==='paid'||row.status==='pending'" type="success" size="small" @click="deliver(row)">配送</el-button>
            <el-button v-if="row.status==='delivering'" type="primary" size="small" @click="complete(row)">送达</el-button>
            <el-button size="small" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="page" :total="total" :page-size="20" layout="prev,pager,next" @current-change="fetch" style="margin-top:16px;justify-content:center"/>
    </div>
    <el-dialog v-model="detailVisible" title="订单详情" width="550px">
      <template v-if="detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="订单号">{{ detail.order_no }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="statusType(detail.status)">{{ detail.status }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="客户">{{ detail.nickname }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ detail.user_phone||detail.contact_phone }}</el-descriptions-item>
          <el-descriptions-item label="商品">{{ detail.product_name }}</el-descriptions-item>
          <el-descriptions-item label="数量">×{{ detail.quantity }}</el-descriptions-item>
          <el-descriptions-item label="实付">¥{{ detail.pay_amount }}</el-descriptions-item>
          <el-descriptions-item label="押金">¥{{ detail.deposit_amount||0 }}</el-descriptions-item>
          <el-descriptions-item label="地址" :span="2">{{ detail.delivery_address }}</el-descriptions-item>
          <el-descriptions-item label="下单时间" :span="2">{{ detail.created_at }}</el-descriptions-item>
        </el-descriptions>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const list = ref([]), total = ref(0), page = ref(1), stations = ref([])
const search = reactive({ order_no:'', status:'', station_id:'' })
const detailVisible = ref(false), detail = ref(null)
const statusOpts = [{label:'待配送',value:'pending'},{label:'已支付',value:'paid'},{label:'配送中',value:'delivering'},{label:'已完成',value:'completed'},{label:'已取消',value:'cancelled'}]
const statusType = s => ({pending:'warning',paid:'',delivering:'primary',completed:'success',cancelled:'info'}[s]||'')

onMounted(async () => { fetch(); const r = await api.getStations(); if(r.code===0) stations.value = r.data })
async function fetch() { try{const r=await api.getOrders({...search,page:page.value});if(r.code===0){list.value=r.data.items;total.value=r.data.total}}catch{} }
async function deliver(o){ await api.deliverOrder(o.id); ElMessage.success('已标记配送中'); fetch() }
async function complete(o){ await api.completeOrder(o.id); ElMessage.success('已标记送达'); fetch() }
function showDetail(o){ detail.value = o; detailVisible.value = true }
</script>
