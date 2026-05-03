<template>
  <div class="upload-view">
    <h1>上传文档</h1>

    <div class="card">
      <h3>上传新文档</h3>

      <div class="form-group">
        <div class="bank-selector">
          <div class="bank-select">
            <label>选择题库</label>
            <select v-model="selectedBankId">
              <option v-for="bank in banks" :key="bank.id" :value="bank.id">
                {{ bank.name }}
              </option>
            </select>
          </div>
          <button class="btn btn-sm" @click="showAddBankModal = true">新建题库</button>
        </div>
      </div>

      <div class="upload-area" @click="triggerUpload" @dragover.prevent="onDragOver" @drop.prevent="onDrop">
        <input type="file" ref="fileInput" @change="onFileSelect" accept=".pdf,.docx,.doc,.txt" style="display: none">
        <div class="upload-hint">
          <div class="upload-icon">📄</div>
          <div>点击或拖拽文件到此处上传</div>
          <div class="upload-formats">支持 PDF、Word、TXT 格式</div>
        </div>
      </div>

      <div v-if="selectedFile" class="selected-file">
        <span>已选择: {{ selectedFile.name }}</span>
        <button class="btn btn-primary" @click="uploadFile" :disabled="uploading">
          {{ uploading ? '上传中...' : '上传' }}
        </button>
      </div>
    </div>

    <div v-if="showAddBankModal" class="modal-overlay" @click.self="closeBankModal">
      <div class="modal">
        <h3>新建题库</h3>
        <div class="form-group">
          <label>题库名称 *</label>
          <input type="text" v-model="newBank.name" placeholder="请输入题库名称">
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="newBank.description" placeholder="请输入描述（可选）"></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="closeBankModal">取消</button>
          <button class="btn btn-primary" @click="createBank" :disabled="!newBank.name">创建</button>
        </div>
      </div>
    </div>

    <div v-if="parsingDoc" class="modal-overlay">
      <div class="modal progress-modal">
        <h3>文档解析中</h3>
        <div class="progress-info">
          <div class="progress-text">{{ parsingProgress.current }} / {{ parsingProgress.total }} 块</div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: parsingProgress.progress + '%' }"></div>
          </div>
          <div class="progress-percent">{{ parsingProgress.progress }}%</div>
        </div>
        <p class="progress-tip">正在使用 AI 解析文档，请稍候...</p>
      </div>
    </div>

    <div class="card">
      <h2>文档列表</h2>
      <div class="filter-bar">
        <label>筛选题库：</label>
        <select v-model="filterBankId" @change="loadDocuments">
          <option value="">全部题库</option>
          <option v-for="bank in banks" :key="bank.id" :value="bank.id">
            {{ bank.name }}
          </option>
        </select>
      </div>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="documents.length === 0" class="empty">暂无文档</div>
      <table v-else class="doc-table">
        <thead>
          <tr>
            <th>文件名</th>
            <th>题库</th>
            <th>状态</th>
            <th>题目数</th>
            <th>上传时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doc in documents" :key="doc.id">
            <td>{{ doc.filename }}</td>
            <td>{{ getBankName(doc.question_bank_id) }}</td>
            <td>
              <span :class="['status', doc.status]">{{ statusText(doc.status) }}</span>
            </td>
            <td>{{ doc.total_questions || '-' }}</td>
            <td>{{ formatTime(doc.created_at) }}</td>
            <td>
              <button v-if="doc.status === 'pending'" class="btn btn-primary" @click="parseDocument(doc.id)">
                解析
              </button>
              <span v-else-if="doc.status === 'processing'" class="parsing-indicator">解析中...</span>
              <button class="btn btn-danger" @click="deleteDocument(doc.id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const fileInput = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const documents = ref([])
const loading = ref(false)
const banks = ref([])
const selectedBankId = ref(null)
const filterBankId = ref('')
const parsingDoc = ref(null)
const parsingProgress = ref({ progress: 0, current: 0, total: 0 })
const showAddBankModal = ref(false)
const newBank = ref({ name: '', description: '' })
let progressEventSource = null

const getBankName = (bankId) => {
  const bank = banks.value.find(b => b.id === bankId)
  return bank ? bank.name : '-'
}

const loadBanks = async () => {
  try {
    const res = await axios.get('/api/question-banks')
    banks.value = res.data
    if (banks.value.length > 0 && !selectedBankId.value) {
      selectedBankId.value = banks.value[0].id
    }
  } catch (error) {
    console.error('加载题库失败:', error)
  }
}

const createBank = async () => {
  try {
    const res = await axios.post('/api/question-banks', newBank.value)
    await loadBanks()
    selectedBankId.value = res.data.id
    closeBankModal()
  } catch (error) {
    alert('创建题库失败: ' + (error.response?.data?.detail || error.message))
  }
}

const closeBankModal = () => {
  showAddBankModal.value = false
  newBank.value = { name: '', description: '' }
}

const triggerUpload = () => {
  fileInput.value.click()
}

const onFileSelect = (e) => {
  const file = e.target.files[0]
  if (file) {
    selectedFile.value = file
  }
}

const onDragOver = () => {}

const onDrop = (e) => {
  const file = e.dataTransfer.files[0]
  if (file) {
    selectedFile.value = file
  }
}

const uploadFile = async () => {
  if (!selectedFile.value) return

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  if (selectedBankId.value) {
    formData.append('question_bank_id', selectedBankId.value)
  }

  uploading.value = true
  try {
    await axios.post('/api/documents/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    selectedFile.value = null
    fileInput.value.value = ''
    loadDocuments()
  } catch (error) {
    alert('上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}

const loadDocuments = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterBankId.value) {
      params.question_bank_id = filterBankId.value
    }
    const res = await axios.get('/api/documents', { params })
    documents.value = res.data
  } catch (error) {
    console.error('加载文档失败:', error)
  } finally {
    loading.value = false
  }
}

const parseDocument = async (id) => {
  try {
    await axios.post(`/api/documents/${id}/parse`)
    parsingDoc.value = id
    parsingProgress.value = { progress: 0, current: 0, total: 0 }

    progressEventSource = new EventSource(`/api/documents/${id}/progress`)

    progressEventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.status === 'done') {
        closeProgressModal()
        return
      }
      parsingProgress.value = data

      if (data.status === 'completed') {
        setTimeout(() => {
          closeProgressModal()
          loadDocuments()
        }, 1000)
      } else if (data.status === 'failed') {
        alert('解析失败: ' + (data.error || '未知错误'))
        closeProgressModal()
        loadDocuments()
      }
    }

    progressEventSource.onerror = () => {
      closeProgressModal()
      loadDocuments()
    }
  } catch (error) {
    alert('启动解析失败: ' + (error.response?.data?.detail || error.message))
  }
}

const closeProgressModal = () => {
  if (progressEventSource) {
    progressEventSource.close()
    progressEventSource = null
  }
  parsingDoc.value = null
  parsingProgress.value = { progress: 0, current: 0, total: 0 }
}

const deleteDocument = async (id) => {
  if (!confirm('确定要删除吗？')) return
  try {
    await axios.delete(`/api/documents/${id}`)
    loadDocuments()
  } catch (error) {
    alert('删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

const statusText = (status) => {
  const map = {
    pending: '待解析',
    processing: '解析中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadBanks()
  loadDocuments()
})

onUnmounted(() => {
  closeProgressModal()
})
</script>

<style scoped>
.bank-selector {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.bank-select {
  flex: 1;
}

.bank-select label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.bank-select select {
  width: 100%;
}

.btn-sm {
  padding: 10px 16px;
  font-size: 14px;
  height: 40px;
}

.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 60px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s;
  margin-bottom: 16px;
}

.upload-area:hover {
  border-color: #40a9ff;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.upload-hint {
  color: #666;
}

.upload-formats {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.selected-file {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.filter-bar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-bar select {
  width: 200px;
}

.doc-table {
  width: 100%;
  border-collapse: collapse;
}

.doc-table th,
.doc-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.doc-table th {
  background: #fafafa;
  font-weight: 500;
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status.pending { background: #f5f5f5; color: #666; }
.status.processing { background: #e6f7ff; color: #1890ff; }
.status.completed { background: #f6ffed; color: #52c41a; }
.status.failed { background: #fff2f0; color: #ff4d4f; }

.parsing-indicator {
  color: #1890ff;
  font-size: 12px;
}

.loading, .empty {
  text-align: center;
  padding: 40px;
  color: #999;
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
  width: 400px;
  max-width: 90%;
  text-align: center;
}

.modal h3 {
  margin-bottom: 20px;
}

.modal .form-group {
  text-align: left;
}

.modal .form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.modal .form-group textarea,
.modal .form-group input {
  width: 100%;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.progress-modal h3 {
  margin-bottom: 24px;
}

.progress-info {
  margin-bottom: 16px;
}

.progress-text {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.progress-bar {
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #1890ff, #40a9ff);
  transition: width 0.3s ease;
}

.progress-percent {
  font-size: 24px;
  font-weight: bold;
  color: #1890ff;
}

.progress-tip {
  color: #999;
  font-size: 12px;
}
</style>
