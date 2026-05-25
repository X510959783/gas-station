<template>
  <div class="card">
    <div style="margin-bottom:12px"><el-button type="primary" @click="openEdit()">+ 新增配送站</el-button></div>
    <el-table :data="list" stripe>
      <el-table-column prop="name" label="站名" width="150"/>
      <el-table-column prop="short_name" label="简称" width="100"/>
      <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip/>
      <el-table-column prop="phone" label="电话" width="130"/>
      <el-table-column label="服务半径" width="100"><template #default="{row}">{{ row.service_area_radius?row.service_area_radius+'m':'不限' }}</template></el-table-column>
      <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status?'success':'info'" size="small">{{ row.status?'启用':'停用' }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{row}">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" :type="row.status?'warning':'success'" @click="toggle(row)">{{ row.status?'停用':'启用' }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="showEdit" :title="editing.id?'编辑配送站':'新增配送站'" width="500px">
      <el-form label-width="100px">
        <el-form-item label="站名"><el-input v-model="edit.name"/></el-form-item>
        <el-form-item label="简称"><el-input v-model="edit.short_name"/></el-form-item>
        <el-form-item label="地址"><el-input v-model="edit.address"/></el-form-item>
        <el-form-item label="经度"><el-input-number v-model="edit.lng" :precision="7" :step="0.001"/></el-form-item>
        <el-form-item label="纬度"><el-input-number v-model="edit.lat" :precision="7" :step="0.001"/></el-form-item>
        <el-form-item label="电话"><el-input v-model="edit.phone"/></el-form-item>
        <el-form-item label="服务半径(m)"><el-input-number v-model="edit.service_area_radius" :min="0"/></el-form-item>
        <el-form-item label="默认站"><el-switch v-model="edit.is_default" :active-value="1" :inactive-value="0"/></el-form-item>
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
const edit = reactive({ name:'',short_name:'',address:'',lat:0,lng:0,phone:'',service_area_radius:0,is_default:0 })
const editing = ref({})

onMounted(fetch)
async function fetch(){ const r = await api.getStations(); if(r.code===0) list.value=r.data }
function openEdit(row){
  editing.value = row||{}
  Object.assign(edit, {name:row?.name||'',short_name:row?.short_name||'',address:row?.address||'',lat:row?.lat||0,lng:row?.lng||0,phone:row?.phone||'',service_area_radius:row?.service_area_radius||0,is_default:row?.is_default||0})
  showEdit.value = true
}
async function save(){
  if(editing.value.id){ await api.updateStation(editing.value.id, edit) }
  else { await api.saveStation(edit) }
  ElMessage.success('已保存'); showEdit.value = false; fetch()
}
async function toggle(row){ await api.toggleStation(row.id); ElMessage.success('状态已切换'); fetch() }
</script>
