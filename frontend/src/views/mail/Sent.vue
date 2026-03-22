<template>
  <div class="mail-list-container">
    <div class="toolbar">
      <el-button type="primary" @click="$router.push('/compose')">
        <el-icon><Edit /></el-icon>
        写邮件
      </el-button>
      <el-button @click="loadData">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <el-table
      :data="mails"
      v-loading="loading"
      @row-click="viewMail"
      style="width: 100%"
    >
      <el-table-column prop="to_users" label="收件人" width="200">
        <template #default="{ row }">
          {{ row.to_users?.join(', ') }}
        </template>
      </el-table-column>
      <el-table-column prop="subject" label="主题" />
      <el-table-column prop="body" label="预览" width="300">
        <template #default="{ row }">
          <span class="preview-text">{{ row.body }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="timestamp" label="时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.timestamp) }}
        </template>
      </el-table-column>
      <el-table-column width="100">
        <template #default="{ row }">
          <el-tag v-if="row.is_recalled" type="info" size="small">已撤回</el-tag>
          <el-tag v-if="row.has_attachment" size="small">附件</el-tag>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        :page-size="20"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadData"
      />
    </div>
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
const page = ref(1)
const total = ref(0)

const formatTime = (time) => dayjs(time).format('YYYY-MM-DD HH:mm')

const loadData = async () => {
  loading.value = true
  try {
    const res = await api.get('/mail/sent', { params: { page: page.value } })
    mails.value = res.data.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const viewMail = (row) => router.push(`/mail/${row.mail_id}`)

onMounted(() => loadData())
</script>

<style scoped>
.mail-list-container { background: #fff; padding: 20px; border-radius: 4px; }
.toolbar { margin-bottom: 20px; }
.preview-text { color: #999; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block; }
.pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
</style>