<template>
  <div class="question-banks">
    <div class="page-header">
      <h1>题库管理</h1>
      <button class="btn btn-primary" @click="showAddModal = true">新建题库</button>
    </div>

    <div class="card">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="banks.length === 0" class="empty">
        <p>暂无题库</p>
        <button class="btn btn-primary" @click="showAddModal = true">创建第一个题库</button>
      </div>
      <table v-else class="bank-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>题库名称</th>
            <th>描述</th>
            <th>文档数</th>
            <th>题目数</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="bank in banks" :key="bank.id">
            <td>{{ bank.id }}</td>
            <td class="bank-name" @click="viewBank(bank)">{{ bank.name }}</td>
            <td>{{ bank.description || '-' }}</td>
            <td>{{ bank.document_count }}</td>
            <td>{{ bank.question_count }}</td>
            <td>{{ formatTime(bank.created_at) }}</td>
            <td class="actions">
              <button class="btn btn-sm" @click="viewBank(bank)">查看题目</button>
              <button class="btn btn-sm btn-primary" @click="startPractice(bank)" :disabled="bank.question_count === 0">开始刷题</button>
              <button class="btn btn-sm" @click="editBank(bank)">编辑</button>
              <button class="btn btn-sm btn-danger" @click="deleteBank(bank)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showAddModal || showEditModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <h3>{{ showEditModal ? '编辑题库' : '新建题库' }}</h3>
        <div class="form-group">
          <label>题库名称 *</label>
          <input type="text" v-model="form.name" placeholder="请输入题库名称">
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="form.description" placeholder="请输入描述（可选）"></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveBank" :disabled="!form.name">保存</button>
        </div>
      </div>
    </div>

    <div v-if="showPracticeModal" class="modal-overlay" @click.self="closePracticeModal">
      <div class="modal">
        <h3>选择刷题模式 - {{ selectedBank.name }}</h3>
        <p class="practice-info">共 {{ selectedBank.question_count }} 道题目</p>
        <div class="practice-modes">
          <button class="practice-mode-btn" @click="doPractice('sequential')">
            <div class="mode-icon">📝</div>
            <div class="mode-title">顺序刷题</div>
            <div class="mode-desc">按题目顺序依次答题</div>
          </button>
          <button class="practice-mode-btn" @click="doPractice('random')">
            <div class="mode-icon">🎲</div>
            <div class="mode-title">随机刷题</div>
            <div class="mode-desc">随机抽取题目答题</div>
          </button>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="closePracticeModal">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const banks = ref([])
const loading = ref(false)
const showAddModal = ref(false)
const showEditModal = ref(false)
const form = ref({ id: null, name: '', description: '' })
const showPracticeModal = ref(false)
const selectedBank = ref({ id: null, name: '', question_count: 0 })

const loadBanks = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/question-banks')
    banks.value = res.data
  } catch (error) {
    console.error('加载题库失败:', error)
  } finally {
    loading.value = false
  }
}

const viewBank = (bank) => {
  router.push(`/banks/${bank.id}`)
}

const startPractice = (bank) => {
  selectedBank.value = bank
  showPracticeModal.value = true
}

const closePracticeModal = () => {
  showPracticeModal.value = false
  selectedBank.value = { id: null, name: '', question_count: 0 }
}

const doPractice = (mode) => {
  router.push(`/practice?bank_id=${selectedBank.value.id}&mode=${mode}`)
  closePracticeModal()
}

const editBank = (bank) => {
  form.value = { id: bank.id, name: bank.name, description: bank.description }
  showEditModal.value = true
}

const deleteBank = async (bank) => {
  if (!confirm(`确定要删除题库"${bank.name}"吗？该操作将同时删除所有关联的题目。`)) return
  try {
    await axios.delete(`/api/question-banks/${bank.id}`)
    loadBanks()
  } catch (error) {
    alert('删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

const saveBank = async () => {
  try {
    if (showEditModal.value) {
      await axios.put(`/api/question-banks/${form.value.id}`, form.value)
    } else {
      await axios.post('/api/question-banks', form.value)
    }
    closeModal()
    loadBanks()
  } catch (error) {
    alert('保存失败: ' + (error.response?.data?.detail || error.message))
  }
}

const closeModal = () => {
  showAddModal.value = false
  showEditModal.value = false
  form.value = { id: null, name: '', description: '' }
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadBanks()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
}

.bank-table {
  width: 100%;
  border-collapse: collapse;
}

.bank-table th,
.bank-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.bank-table th {
  background: #fafafa;
  font-weight: 500;
}

.bank-name {
  cursor: pointer;
  color: #1890ff;
}

.bank-name:hover {
  text-decoration: underline;
}

.actions {
  display: flex;
  gap: 8px;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}

.loading, .empty {
  text-align: center;
  padding: 40px;
  color: #999;
}

.empty p {
  margin-bottom: 16px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 24px;
  border-radius: 8px;
  width: 450px;
  max-width: 90%;
}

.modal h3 {
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group textarea {
  width: 100%;
  min-height: 80px;
  padding: 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  resize: vertical;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.practice-info {
  text-align: center;
  color: #666;
  margin-bottom: 20px;
}

.practice-modes {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.practice-mode-btn {
  flex: 1;
  padding: 24px 16px;
  border: 2px solid #d9d9d9;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.practice-mode-btn:hover {
  border-color: #1890ff;
  background: #f0f7ff;
}

.practice-mode-btn .mode-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.practice-mode-btn .mode-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.practice-mode-btn .mode-desc {
  font-size: 12px;
  color: #999;
}
</style>
