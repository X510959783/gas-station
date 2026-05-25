<template>
  <div class="card">
    <el-radio-group v-model="search.level" @change="fetch" style="margin-bottom:12px">
      <el-radio-button value="">全部</el-radio-button>
      <el-radio-button value="danger">🔴 严重</el-radio-button>
      <el-radio-button value="warning">🟡 警告</el-radio-button>
      <el-radio-button value="info">🔵 提示</el-radio-button>
    </el-radio-group>
    <el-radio-group v-model="search.status" @change="fetch" style="margin-left:12px;margin-bottom:12px">
      <el-radio-button value="">全部</el-radio-button>
      <el-radio-button value="pending">待处理</el-radio-button>
      <el-radio-button value="resolved">已解决</el-radio-button>
    </el-radio-group>
    <el-table :data="list" stripe>
      <el-table-column prop="nickname" label="用户" width="120"/>
      <el-table-column prop="user_phone" label="手机号" width="130"/>
      <el-table-column label="类型" width="100"><template #default="{row}">{{ {overdue:'超期未购',decline:'用量下降',churn:'疑似流失',cycle_anomaly:'周期异常'}[row.rule_type]||row.rule_type }}</template></el-table-column>
      <el-table-column label="级别" width="80"><template #default="{row}"><el-tag :type="row.level==='danger'?'danger':row.level==='warning'?'warning':'info'" size="small">{{ row.level }}</el-tag></template></el-table-column>
      <el-table-column prop="message" label="详情" min-width="250" show-overflow-tooltip/>
      <el-table-column label="状态" width="90"><template #default="{row}"><el-tag :type="row.status==='pending'?'warning':'success'" size="small">{{ row.status==='pending'?'待处理':'已解决' }}</el-tag></template></el-table-column>
      <el-table-column prop="created_at" label="时间" width="160"/>
      <el-table-column label="操作" width="130">
        <template #default="{row}">
          <el-button v-if="row.status==='pending'" type="success" size="small" @click="resolve(row)">已处理</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const list = ref([])
const search = reactive({ level:'', status:'' })

onMounted(fetch)
async function fetch(){ const r=await api.getWarnings(search); if(r.code===0) list.value=r.data }
async function resolve(row){ await api.resolveWarning(row.id); ElMessage.success('已标记处理'); fetch() }
</script>
