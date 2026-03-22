<template>
  <div class="compose-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>写邮件</span>
        </div>
      </template>

      <el-form :model="form" ref="formRef" label-width="80px">
        <el-form-item label="收件人" prop="toUsers">
          <el-select
            v-model="form.toUsers"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入收件人邮箱"
            style="width: 100%"
          >
            <el-option
              v-for="user in suggestedUsers"
              :key="user.email"
              :label="user.email"
              :value="user.email"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="主题" prop="subject">
          <el-input v-model="form.subject" placeholder="请输入邮件主题" />
        </el-form-item>

        <el-form-item label="内容" prop="body">
          <el-input
            v-model="form.body"
            type="textarea"
            :rows="15"
            placeholder="请输入邮件内容"
          />
        </el-form-item>

        <el-form-item label="附件">
          <el-upload
            v-model:file-list="fileList"
            :auto-upload="false"
            :limit="5"
            :on-exceed="handleExceed"
          >
            <el-button>
              <el-icon><Upload /></el-icon>
              添加附件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">支持图片、文档、压缩包等，最大10MB</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSend" :loading="sending">
            发送邮件
          </el-button>
          <el-button @click="handleSaveDraft">保存草稿</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'
import { Plus } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const formRef = ref(null)
const sending = ref(false)
const fileList = ref([])
const suggestedUsers = ref([])

const form = ref({
  toUsers: [],
  subject: '',
  body: ''
})

// 加载草稿
const loadDraft = async (draftId) => {
  try {
    const res = await api.get(`/mail/${draftId}`)
    const mail = res.data.data
    form.value.toUsers = mail.to_users || []
    form.value.subject = mail.subject || ''
    form.value.body = mail.body || ''
  } catch (e) {
    console.error(e)
  }
}

// 处理文件
const handleFile = async () => {
  const attachments = []
  for (const file of fileList.value) {
    const reader = new FileReader()
    const data = await new Promise((resolve) => {
      reader.onload = () => resolve(reader.result.split(',')[1])
      reader.readAsDataURL(file.raw)
    })
    attachments.push({
      filename: file.name,
      content_type: file.raw.type,
      size: file.raw.size,
      data
    })
  }
  return attachments
}

// 发送邮件
const handleSend = async () => {
  if (!form.value.toUsers.length) {
    ElMessage.warning('请输入收件人')
    return
  }
  if (!form.value.subject) {
    ElMessage.warning('请输入主题')
    return
  }

  sending.value = true
  try {
    const attachments = await handleFile()
    const res = await api.post('/mail/send', {
      to_users: form.value.toUsers,
      subject: form.value.subject,
      body: form.value.body,
      attachments
    })

    if (res.data.success) {
      ElMessage.success('邮件发送成功')
      router.push('/sent')
    }
  } catch (e) {
    ElMessage.error('发送失败')
  } finally {
    sending.value = false
  }
}

// 保存草稿
const handleSaveDraft = async () => {
  ElMessage.info('草稿保存功能开发中')
}

const handleExceed = () => {
  ElMessage.warning('最多上传5个附件')
}

onMounted(() => {
  const draftId = route.query.draft
  if (draftId) {
    loadDraft(draftId)
  }
})
</script>

<style scoped>
.compose-container { background: #fff; padding: 20px; border-radius: 4px; }
.card-header { font-size: 18px; font-weight: bold; }
.el-upload__tip { color: #999; margin-top: 5px; }
</style>