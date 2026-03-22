<template>
  <div class="mail-list-container">
    <div class="toolbar">
      <el-button type="primary" @click="$router.push('/compose')">
        <el-icon><Edit /></el-icon>
        写邮件
      </el-button>
    </div>

    <el-table :data="mails" v-loading="loading" @row-click="editDraft" style="width: 100%">
      <el-table-column prop="to_users" label="收件人" width="200">
        <template #default="{ row }">{{ row.to_users?.join(', ') }}</template>
      </el-table-column>
      <el-table-column prop="subject" label="主题" />
      <el-table-column prop="body" label="预览" width="300" />
      <el-table-column prop="timestamp" label="时间" width="180">
        <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import dayjs from 'dayjs'

const router = useRouter()
const loading = ref(false)
const mails = ref([])

const formatTime = (time) => dayjs(time).format('YYYY-MM-DD HH:mm')

const loadData = async () => {
  loading.value = true
  try {
    const res = await api.get('/mail/drafts')
    mails.value = res.data.data || []
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const editDraft = (row) => router.push({ path: '/compose', query: { draft: row.mail_id } })

onMounted(() => loadData())
</script>

<style scoped>
.mail-list-container { background: #fff; padding: 20px; border-radius: 4px; }
.toolbar { margin-bottom: 20px; }
</style>