<template>
  <div class="mail-detail" v-loading="loading">
    <el-card v-if="mail">
      <!-- 邮件头部 -->
      <div class="mail-header">
        <h2>{{ mail.subject }}</h2>
        <div class="mail-meta">
          <span>发件人：{{ mail.from_user }}</span>
          <span>时间：{{ formatTime(mail.timestamp) }}</span>
        </div>
        <div class="mail-tags">
          <el-tag v-if="mail.is_phishing" type="danger">钓鱼邮件</el-tag>
          <el-tag v-if="mail.is_recalled" type="info">已撤回</el-tag>
        </div>
      </div>

      <!-- 收件人 -->
      <div class="mail-recipients">
        <div>收件人：{{ mail.to_users?.join(', ') }}</div>
        <div v-if="mail.cc_users?.length">抄送：{{ mail.cc_users.join(', ') }}</div>
      </div>

      <el-divider />

      <!-- 邮件正文 -->
      <div class="mail-body">
        {{ mail.body }}
      </div>

      <!-- 附件 -->
      <div class="mail-attachments" v-if="mail.attachments?.length">
        <el-divider />
        <h4>附件</h4>
        <div class="attachment-list">
          <div v-for="att in mail.attachments" :key="att.id" class="attachment-item">
            <el-icon><Document /></el-icon>
            <span>{{ att.filename }}</span>
            <el-button type="primary" link @click="downloadAttachment(att)">下载</el-button>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="mail-actions">
        <el-button type="primary" @click="handleReply">
          <el-icon><Reply /></el-icon>
          回复
        </el-button>
        <el-button @click="handleForward">
          <el-icon><Right /></el-icon>
          转发
        </el-button>
        <el-button @click="handleRecall" v-if="!mail.is_recalled && isSent">
          撤回
        </el-button>
        <el-button type="danger" @click="handleDelete">
          删除
        </el-button>
        <el-button @click="handleAddTodo">
          添加到待办
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/utils/api'
import { useUserStore } from '@/stores/user'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const mail = ref(null)

const isSent = computed(() => {
  return mail.value?.from_user === userStore.user?.email
})

const formatTime = (time) => dayjs(time).format('YYYY-MM-DD HH:mm HH:mm')

const loadMail = async () => {
  loading.value = true
  try {
    const res = await api.get(`/mail/${route.params.id}`)
    mail.value = res.data.data
  } catch (e) {
    ElMessage.error('加载邮件失败')
  } finally {
    loading.value = false
  }
}

const handleReply = () => {
  router.push({
    path: '/compose',
    query: {
      reply_to: mail.value.from_user,
      subject: `Re: ${mail.value.subject}`
    }
  })
}

const handleForward = () => {
  router.push({
    path: '/compose',
    query: {
      forward: mail.value.mail_id
    }
  })
}

const handleRecall = async () => {
  try {
    await ElMessageBox.confirm('确定要撤回这封邮件吗？', '提示')
    const res = await api.post(`/mail/${mail.value.mail_id}/recall`)
    if (res.data.success) {
      ElMessage.success('邮件已撤回')
      loadMail()
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('撤回失败')
    }
  }
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这封邮件吗？', '提示')
    await api.delete(`/mail/${mail.value.mail_id}`)
    ElMessage.success('已删除')
    router.back()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleAddTodo = () => {
  ElMessage.info('待办功能开发中')
}

const downloadAttachment = (att) => {
  ElMessage.info('附件下载功能开发中')
}

onMounted(() => loadMail())
</script>

<style scoped>
.mail-detail { background: #fff; padding: 20px; border-radius: 4px; }
.mail-header h2 { margin: 0 0 10px; }
.mail-meta { color: #666; font-size: 14px; margin-bottom: 10px; }
.mail-meta span { margin-right: 20px; }
.mail-tags { margin-bottom: 10px; }
.mail-recipients { color: #666; font-size: 14px; margin: 10px 0; }
.mail-body { min-height: 200px; white-space: pre-wrap; }
.mail-attachments h4 { margin: 10px 0; }
.attachment-item { display: flex; align-items: center; gap: 10px; margin: 10px 0; }
.mail-actions { margin-top: 20px; display: flex; gap: 10px; }
</style>