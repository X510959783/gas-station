<template>
  <div class="card">
    <div style="margin-bottom:12px"><el-button type="primary" @click="openEdit()">+ 新增优惠券</el-button></div>
    <el-table :data="list" stripe>
      <el-table-column prop="name" label="券名" width="180"/>
      <el-table-column label="类型" width="80"><template #default="{row}"><el-tag :type="row.type==='fixed'?'primary':'success'" size="small">{{ row.type==='fixed'?'满减券':'折扣券' }}</el-tag></template></el-table-column>
      <el-table-column label="面额" width="80"><template #default="{row}">{{ row.type==='fixed'?'¥'+row.value:row.value+'%' }}</template></el-table-column>
      <el-table-column label="最低消费" width="80"><template #default="{row}">¥{{ row.min_amount||0 }}</template></el-table-column>
      <el-table-column label="已领" width="60"><template #default="{row}">{{ row.received_count||0 }}/{{ row.total_count }}</template></el-table-column>
      <el-table-column label="已用" width="60"><template #default="{row}">{{ row.used_count||0 }}</template></el-table-column>
      <el-table-column label="有效期" width="180"><template #default="{row}">{{ row.start_time?.slice(0,10) }} ~ {{ row.end_time?.slice(0,10) }}</template></el-table-column>
      <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status?'success':'info'" size="small">{{ row.status?'有效':'失效' }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{row}"><el-button size="small" @click="openEdit(row)">编辑</el-button></template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="showEdit" :title="editing.id?'编辑优惠券':'新增优惠券'" width="480px">
      <el-form label-width="90px">
        <el-form-item label="券名"><el-input v-model="edit.name"/></el-form-item>
        <el-form-item label="类型"><el-radio-group v-model="edit.type"><el-radio value="fixed">满减券</el-radio><el-radio value="percent">折扣券</el-radio></el-radio-group></el-form-item>
        <el-form-item label="面额"><el-input-number v-model="edit.value" :min="1"/></el-form-item>
        <el-form-item label="最低消费"><el-input-number v-model="edit.min_amount" :min="0"/></el-form-item>
        <el-form-item label="发行总数"><el-input-number v-model="edit.total_count" :min="1"/></el-form-item>
        <el-form-item label="开始时间"><el-date-picker v-model="edit.start_time" type="datetime"/></el-form-item>
        <el-form-item label="结束时间"><el-date-picker v-model="edit.end_time" type="datetime"/></el-form-item>
      </el-form>
      <template #footer><el-button @click="showEdit=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const list = ref([]), showEdit = ref(false)
const edit = reactive({ name:'',type:'fixed',value:0,min_amount:0,total_count:100,start_time:'',end_time:'' })
const editing = ref({})

onMounted(fetch)
async function fetch(){ const r=await api.getCoupons(); if(r.code===0) list.value=r.data }
function openEdit(row){
  editing.value = row||{}
  Object.assign(edit, {name:row?.name||'',type:row?.type||'fixed',value:row?.value||0,min_amount:row?.min_amount||0,total_count:row?.total_count||100,start_time:row?.start_time||'',end_time:row?.end_time||''})
  showEdit.value = true
}
async function save(){
  if(editing.value.id){ await api.updateCoupon(editing.value.id, edit) }
  else { await api.saveCoupon(edit) }
  ElMessage.success('已保存'); showEdit.value = false; fetch()
}
</script>
