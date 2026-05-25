<template>
  <div>
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="12"><div class="card"><h3>近30天用气趋势</h3><div ref="trendEl" style="height:300px"></div></div></el-col>
      <el-col :span="12"><div class="card"><h3>用气排行 TOP20</h3><div ref="rankEl" style="height:300px"></div></div></el-col>
    </el-row>
    <div class="card">
      <h3>用户用气排行</h3>
      <el-table :data="ranking" stripe>
        <el-table-column label="排名" width="60"><template #default="{i}">{{ i+1 }}</template></el-table-column>
        <el-table-column prop="real_name" label="姓名" width="100"/>
        <el-table-column prop="nickname" label="昵称" width="120"/>
        <el-table-column prop="total_orders" label="总订单数" width="100"/>
        <el-table-column label="总用气量(kg)" width="120"><template #default="{row}"><b style="color:#2e75b6">{{ row.total_gas_amount||0 }}kg</b></template></el-table-column>
        <el-table-column label="平均周期" width="100"><template #default="{row}">{{ row.avg_order_cycle||'-' }}天</template></el-table-column>
        <el-table-column label="最近下单" width="120"><template #default="{row}">{{ row.last_order_date||'-' }}</template></el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'

const ranking = ref([])
const trendEl = ref(null), rankEl = ref(null)

onMounted(async () => {
  const r1 = await api.getAnalysisRanking(); if(r1.code===0) ranking.value=r1.data.slice(0,20)
  const r2 = await api.getAnalysisTrend(30)
  if(r2.code===0 && trendEl.value){
    const c1 = echarts.init(trendEl.value)
    c1.setOption({ tooltip:{trigger:'axis'}, xAxis:{data:r2.data.map(d=>d.date),axisLabel:{rotate:45,fontSize:11}}, yAxis:{}, series:[{name:'订单量',type:'line',data:r2.data.map(d=>d.orders),smooth:true,areaStyle:{opacity:.1},color:'#2e75b6'}] })
  }
  if(rankEl.value){
    const c2 = echarts.init(rankEl.value)
    const top = ranking.value.slice(0,20).reverse()
    c2.setOption({ tooltip:{}, grid:{left:120}, xAxis:{}, yAxis:{type:'category',data:top.map(u=>u.real_name||u.nickname||'?'),axisLabel:{fontSize:11}}, series:[{type:'bar',data:top.map(u=>u.total_gas_amount||0),color:'#27ae60',barMaxWidth:20}] })
  }
})
</script>

<style scoped>
.card{background:white;border-radius:8px;padding:16px;margin-bottom:16px}
.card h3{font-size:15px;margin-bottom:12px;color:#1a3a5c}
</style>
