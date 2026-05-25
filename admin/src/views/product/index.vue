<template>
  <div class="card">
    <div style="margin-bottom:12px"><el-button type="primary" @click="openEdit()">+ 新增商品</el-button></div>
    <el-table :data="list" stripe>
      <el-table-column prop="name" label="名称" width="150"/>
      <el-table-column prop="spec" label="规格" width="80"/>
      <el-table-column label="售价" width="100"><template #default="{row}"><b style="color:#e74c3c">¥{{ row.price }}</b></template></el-table-column>
      <el-table-column label="押金" width="80"><template #default="{row}">¥{{ row.deposit_price||0 }}</template></el-table-column>
      <el-table-column prop="stock" label="库存" width="80"/>
      <el-table-column label="状态" width="80"><template #default="{row}"><el-tag :type="row.status?'success':'info'" size="small">{{ row.status?'上架':'下架' }}</el-tag></template></el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{row}"><el-button size="small" @click="openEdit(row)">编辑</el-button></template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="showEdit" :title="editing.id?'编辑商品':'新增商品'" width="450px">
      <el-form label-width="80px">
        <el-form-item label="名称"><el-input v-model="edit.name"/></el-form-item>
        <el-form-item label="规格"><el-input v-model="edit.spec" placeholder="15kg"/></el-form-item>
        <el-form-item label="售价"><el-input-number v-model="edit.price" :min="0" :step="5"/></el-form-item>
        <el-form-item label="押金"><el-input-number v-model="edit.deposit_price" :min="0" :step="10"/></el-form-item>
        <el-form-item label="库存"><el-input-number v-model="edit.stock" :min="0"/></el-form-item>
        <el-form-item label="状态"><el-switch v-model="edit.status" active-text="上架" inactive-text="下架" :active-value="1" :inactive-value="0"/></el-form-item>
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
const edit = reactive({ name:'',spec:'',price:0,deposit_price:0,stock:0,status:1 })
const editing = ref({})

onMounted(fetch)
async function fetch(){ const r = await api.getProducts(); if(r.code===0) list.value=r.data }
function openEdit(row){
  editing.value = row||{}
  Object.assign(edit, {name:row?.name||'',spec:row?.spec||'',price:row?.price||0,deposit_price:row?.deposit_price||0,stock:row?.stock||0,status:row?.status??1})
  showEdit.value = true
}
async function save(){
  const data = { name: edit.name, spec: edit.spec, price: edit.price, deposit_price: edit.deposit_price, stock: edit.stock, status: edit.status }
  if (editing.value.id) { await api.updateProduct(editing.value.id, data) }
  else { await api.saveProduct(data) }
  ElMessage.success('已保存')
  showEdit.value = false; fetch()
}
</script>
