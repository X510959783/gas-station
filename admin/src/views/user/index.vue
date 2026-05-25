<template>
  <div class="card">
    <el-table :data="list" stripe>
      <el-table-column prop="nickname" label="昵称" width="120"/>
      <el-table-column prop="real_name" label="真实姓名" width="100"/>
      <el-table-column prop="phone" label="手机号" width="130"/>
      <el-table-column label="角色" width="80"><template #default="{row}"><el-tag :type="row.role==='merchant'?'success':''" size="small">{{ row.role==='merchant'?'商户':'用户' }}</el-tag></template></el-table-column>
      <el-table-column prop="total_orders" label="订单数" width="80"/>
      <el-table-column label="用气量(kg)" width="100"><template #default="{row}">{{ row.total_gas_amount||0 }}kg</template></el-table-column>
      <el-table-column label="最近下单" width="110"><template #default="{row}">{{ row.last_order_date||'-' }}</template></el-table-column>
      <el-table-column label="周期(天)" width="80"><template #default="{row}">{{ row.avg_order_cycle||'-' }}</template></el-table-column>
      <el-table-column prop="station_name" label="配送站" width="110"/>
      <el-table-column prop="address" label="地址" min-width="150" show-overflow-tooltip/>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
const list = ref([])
onMounted(async () => { const r = await api.getUsers(); if(r.code===0) list.value=r.data })
</script>
