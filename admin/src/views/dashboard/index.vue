<template>
  <div>
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="6" v-for="card in cards" :key="card.label">
        <div class="stat-card" :style="{borderLeftColor:card.color}">
          <div class="num">{{ card.value }}</div>
          <div class="lbl">{{ card.label }}</div>
        </div>
      </el-col>
    </el-row>
    <el-row :gutter="16">
      <el-col :span="16">
        <div class="card"><h3>最近7天订单趋势</h3><div ref="chartEl" style="height:300px"></div></div>
      </el-col>
      <el-col :span="8">
        <div class="card"><h3>快捷操作</h3>
          <el-button type="primary" @click="$router.push('/orders')" style="width:100%;margin-bottom:8px">订单管理</el-button>
          <el-button type="warning" @click="$router.push('/orders')" style="width:100%;margin-bottom:8px">待配送订单</el-button>
          <el-button type="success" @click="$router.push('/warnings')" style="width:100%;margin-bottom:8px">预警管理</el-button>
          <el-button @click="$router.push('/products')" style="width:100%;margin-bottom:8px">商品管理</el-button>
          <el-button @click="$router.push('/stations')" style="width:100%;margin-bottom:8px">配送站管理</el-button>
          <el-button type="danger" @click="$router.push('/deposits')" style="width:100%">钢瓶押金</el-button>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'

const cards = reactive([
  { label:'今日订单', value:0, color:'#2e75b6' },
  { label:'待处理订单', value:0, color:'#f39c12' },
  { label:'配送中', value:0, color:'#27ae60' },
  { label:'异常预警', value:0, color:'#e74c3c' },
])
const chartEl = ref(null)

onMounted(async () => {
  try {
    const res = await api.getDashboard()
    if (res.code === 0) {
      cards[0].value = res.data.todayOrders
      cards[1].value = res.data.pending
      cards[2].value = res.data.delivering
      cards[3].value = res.data.alerts
    }
  } catch {}
  try {
    const trend = await api.getAnalysisTrend(7)
    if (trend.code === 0 && chartEl.value) {
      const chart = echarts.init(chartEl.value)
      chart.setOption({
        tooltip: { trigger:'axis' },
        xAxis: { data: trend.data.map(d=>d.date) },
        yAxis: {},
        series: [
          { name:'订单量', type:'line', data:trend.data.map(d=>d.orders), smooth:true, areaStyle:{opacity:.1} },
          { name:'销售额', type:'bar', data:trend.data.map(d=>d.sales) },
        ]
      })
    }
  } catch {}
})
</script>

<style scoped>
.stat-card{border-left:4px solid;border-radius:8px;padding:20px;background:white}
.stat-card .num{font-size:32px;font-weight:700}
.stat-card .lbl{color:#888;font-size:13px;margin-top:4px}
.card{background:white;border-radius:8px;padding:16px;margin-bottom:16px}
.card h3{font-size:15px;margin-bottom:12px;color:#1a3a5c}
</style>
