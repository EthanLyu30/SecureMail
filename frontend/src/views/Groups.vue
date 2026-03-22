<template>
  <div class="groups-container">
    <div class="toolbar">
      <el-button type="primary" @click="showCreateDialog = true">
        创建群组
      </el-button>
    </div>

    <el-card v-for="group in groups" :key="group.id" class="group-card">
      <template #header>
        <div class="group-header">
          <span>{{ group.name }}</span>
          <el-tag size="small">{{ group.role }}</el-tag>
        </div>
      </template>

      <div class="group-members">
        <div v-for="member in group.members" :key="member.id" class="member-item">
          <el-avatar :size="30">{{ member.username[0] }}</el-avatar>
          <span>{{ member.username }}</span>
          <span class="email">{{ member.email }}</span>
        </div>
      </div>

      <div class="group-actions" v-if="group.role === 'owner'">
        <el-button size="small" @click="showAddMember(group)">添加成员</el-button>
      </div>
    </el-card>

    <!-- 创建群组对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建群组" width="400px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="createForm.name" placeholder="请输入群组名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateGroup">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加成员对话框 -->
    <el-dialog v-model="showAddMemberDialog" title="添加成员" width="400px">
      <el-form :model="addMemberForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="addMemberForm.username" placeholder="请输入用户名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddMemberDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddMember">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const groups = ref([])
const showCreateDialog = ref(false)
const showAddMemberDialog = ref(false)
const currentGroup = ref(null)

const createForm = ref({ name: '' })
const addMemberForm = ref({ username: '' })

const loadGroups = async () => {
  try {
    const res = await api.get('/groups/')
    groups.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

const handleCreateGroup = async () => {
  try {
    const res = await api.post('/groups/', { name: createForm.value.name })
    if (res.data.success) {
      ElMessage.success('创建成功')
      showCreateDialog.value = false
      createForm.value.name = ''
      loadGroups()
    }
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

const showAddMember = (group) => {
  currentGroup.value = group
  showAddMemberDialog.value = true
}

const handleAddMember = async () => {
  try {
    const res = await api.post(`/groups/${currentGroup.value.id}/members`, {
      username: addMemberForm.value.username
    })
    if (res.data.success) {
      ElMessage.success('添加成功')
      showAddMemberDialog.value = false
      loadGroups()
    }
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

onMounted(() => loadGroups())
</script>

<style scoped>
.groups-container { background: #fff; padding: 20px; border-radius: 4px; }
.toolbar { margin-bottom: 20px; }
.group-card { margin-bottom: 15px; }
.group-header { display: flex; justify-content: space-between; align-items: center; }
.group-members { display: flex; flex-direction: column; gap: 10px; }
.member-item { display: flex; align-items: center; gap: 10px; }
.email { color: #999; font-size: 12px; }
.group-actions { margin-top: 10px; }
</style>