<template>
  <div class="search-container">
    <div class="search-box">
      <el-input
        v-model="keyword"
        placeholder="搜索邮件、联系人、关键词"
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button :icon="Search" @click="handleSearch" />
        </template>
      </el-input>
    </div>

    <div class="results" v-if="results.length">
      <el-card v-for="(item, index) in results" :key="index" class="result-card" @click="viewMail(item)">
        <div class="result-header">
          <el-tag size="small">{{ item.folder === 'sent' ? '发件箱' : '收件箱' }}</el-tag>
          <span class="from">{{ item.from_user }}</span>
          <span class="time">{{ formatTime(item.timestamp) }}</span>
        </div>
        <div class="result-subject">{{ item.subject }}</div>
        <div class="result-preview">{{ item.body }}</div>
      </el-card>
    </div>

    <el-empty v-else-if="searched" description="未找到相关邮件" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/utils/api'
import dayjs from 'dayjs'
import { Search } from '@element-plus/icons-vue'

const router = useRouter()
const keyword = ref('')
const results = ref([])
const searched = ref(false)

const formatTime = (time) => dayjs(time).format('YYYY-MM-DD HH:mm')

const handleSearch = async () => {
  if (!keyword.value.trim()) return

  searched.value = true
  try {
    const res = await api.get('/mail/search', { params: { keyword: keyword.value } })
    results.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

const viewMail = (item) => {
  router.push(`/mail/${item.mail_id}`)
}
</script>

<style scoped>
.search-container { background: #fff; padding: 20px; border-radius: 4px; }
.search-box { margin-bottom: 20px; }
.result-card { margin-bottom: 10px; cursor: pointer; }
.result-header { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; }
.from { font-weight: bold; }
.time { color: #999; font-size: 12px; }
.result-subject { font-weight: bold; margin-bottom: 5px; }
.result-preview { color: #666; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>