<template>
  <div class="inbox-container">
    <div class="mail-list">
      <div class="list-header">
        <h2>收件箱</h2>
        <el-button type="primary" @click="$router.push('/compose')">
          <el-icon><Plus /></el-icon>
          写邮件
        </el-button>
      </div>
      
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索邮件..."
          @keyup.enter="handleSearch"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      
      <el-scrollbar height="calc(100vh - 200px)">
        <div v-if="loading" class="loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          加载中...
        </div>
        
        <div v-else-if="mails.length === 0" class="empty">
          <el-empty description="暂无邮件" />
        </div>
        
        <div v-else class="mail-items">
          <div
            v-for="mail in mails"
            :key="mail.id"
            class="mail-item"
            :class="{ unread: !mail.is_read }"
            @click="viewMail(mail)"
          >
            <div class="mail-item-header">
              <span class="sender">{{ mail.from_addr }}</span>
              <span class="time">{{ formatTime(mail.created_at) }}</span>
            </div>
            <div class="mail-item-subject">{{ mail.subject }}</div>
            <div class="mail-item-preview">{{ mail.body }}</div>
            <div class="mail-item-footer">
              <el-tag v-if="mail.is_phishing" type="danger" size="small">钓鱼风险</el-tag>
              <el-tag v-if="mail.has_attachment" size="small">附件</el-tag>
            </div>
            
            <!-- 快捷操作 -->
            <div class="quick-actions">
              <el-button size="small" @click.stop="quickReply(mail)">回复</el-button>
              <el-button size="small" @click.stop="toggleStar(mail)">
                {{ mail.is_starred ? '★' : '☆' }}
              </el-button>
            </div>
          </div>
        </div>
      </el-scrollbar>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadMails"
        />
      </div>
    </div>
    
    <!-- 快捷回复弹窗 -->
    <el-dialog v-model="quickReplyVisible" title="快捷回复" width="500px">
      <div class="quick-reply-content">
        <div class="reply-to">回复至: {{ replyTo }}</div>
        <div class="reply-subject">主题: {{ replySubject }}</div>
        <el-input
          v-model="replyBody"
          type="textarea"
          :rows="6"
          placeholder="输入回复内容..."
        />
        <div class="quick-suggestions">
          <span>快捷回复:</span>
          <el-button size="small" @click="insertQuickReply('谢谢！')">谢谢</el-button>
          <el-button size="small" @click="insertQuickReply('收到，谢谢！')">收到</el-button>
          <el-button size="small" @click="insertQuickReply('好的，我了解了。')">好的</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="quickReplyVisible = false">取消</el-button>
        <el-button type="primary" @click="sendQuickReply" :loading="sending">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Search, Loading } from '@element-plus/icons-vue'
import { getMails, markAsRead, toggleStar as apiToggleStar, quickReply as apiQuickReply } from '../utils/api'

const router = useRouter()

const loading = ref(false)
const mails = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')

// 快捷回复
const quickReplyVisible = ref(false)
const replyMailId = ref(null)
const replyTo = ref('')
const replySubject = ref('')
const replyBody = ref('')
const sending = ref(false)

const loadMails = async () => {
  loading.value = true
  try {
    const data = await getMails('inbox', currentPage.value, pageSize.value)
    mails.value = data.mails || []
    total.value = data.total || 0
  } catch (error) {
    ElMessage.error('加载邮件失败')
  } finally {
    loading.value = false
  }
}

const viewMail = async (mail) => {
  // 标记为已读
  if (!mail.is_read) {
    await markAsRead(mail.id)
    mail.is_read = true
  }
  router.push(`/mail/${mail.id}`)
}

const handleSearch = () => {
  if (searchKeyword.value) {
    router.push({ path: '/search', query: { keyword: searchKeyword.value } })
  }
}

const toggleStar = async (mail) => {
  try {
    const result = await apiToggleStar(mail.id)
    mail.is_starred = result.is_starred
    ElMessage.success(result.is_starred ? '已标为星标' : '已取消星标')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const quickReply = (mail) => {
  replyMailId.value = mail.id
  replyTo.value = mail.from_addr
  replySubject.value = mail.subject
  replyBody.value = ''
  quickReplyVisible.value = true
}

const insertQuickReply = (text) => {
  replyBody.value = text
}

const sendQuickReply = async () => {
  if (!replyBody.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  
  sending.value = true
  try {
    await apiQuickReply(replyMailId.value, replyBody.value)
    ElMessage.success('回复发送成功')
    quickReplyVisible.value = false
  } catch (error) {
    ElMessage.error('发送失败')
  } finally {
    sending.value = false
  }
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
  
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadMails()
})
</script>

<style scoped>
.inbox-container {
  padding: 20px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.list-header h2 {
  margin: 0;
}

.search-bar {
  margin-bottom: 15px;
}

.loading, .empty {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px;
  color: #909399;
}

.mail-items {
  padding: 0 10px;
}

.mail-item {
  padding: 15px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
}

.mail-item:hover {
  background: #f5f7fa;
}

.mail-item.unread {
  background: #f0f9ff;
}

.mail-item.unread .mail-item-subject,
.mail-item.unread .sender {
  font-weight: bold;
}

.mail-item-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.sender {
  color: #303133;
}

.time {
  color: #909399;
  font-size: 12px;
}

.mail-item-subject {
  color: #303133;
  margin-bottom: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mail-item-preview {
  color: #909399;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mail-item-footer {
  margin-top: 8px;
  display: flex;
  gap: 5px;
}

.quick-actions {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  display: none;
}

.mail-item:hover .quick-actions {
  display: flex;
  gap: 5px;
}

.pagination {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.quick-reply-content {
  padding: 10px 0;
}

.reply-to, .reply-subject {
  margin-bottom: 10px;
  color: #606266;
}

.quick-suggestions {
  margin-top: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>