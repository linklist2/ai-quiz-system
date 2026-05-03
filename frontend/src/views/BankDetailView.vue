<template>
  <div class="bank-detail">
    <div class="page-header">
      <div class="header-left">
        <button class="btn btn-back" @click="$router.back()">← 返回</button>
        <h1>{{ bankName }} - 题目列表</h1>
      </div>
      <button class="btn btn-primary" @click="showAddModal = true">添加题目</button>
    </div>

    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">总题目</span>
        <span class="stat-value">{{ stats.total }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">选择题</span>
        <span class="stat-value">{{ stats.choice }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">判断题</span>
        <span class="stat-value">{{ stats.trueFalse }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">简答题</span>
        <span class="stat-value">{{ stats.shortAnswer }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">案例分析</span>
        <span class="stat-value">{{ stats.caseAnalysis }}</span>
      </div>
    </div>

    <div class="card">
      <div class="filters">
        <select v-model="filterType" @change="loadQuestions">
          <option value="">全部类型</option>
          <option value="choice">选择题</option>
          <option value="true_false">判断题</option>
          <option value="short_answer">简答题</option>
          <option value="case_analysis">案例分析题</option>
        </select>
      </div>

      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="questions.length === 0" class="empty">暂无题目</div>
      <table v-else class="question-table">
        <thead>
          <tr>
            <th style="width: 60px">ID</th>
            <th style="width: 100px">类型</th>
            <th>题目内容</th>
            <th style="width: 150px">答案</th>
            <th style="width: 200px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="q in questions" :key="q.id">
            <td>{{ q.id }}</td>
            <td>
              <span :class="['type-tag', q.question_type]">{{ typeText(q.question_type) }}</span>
            </td>
            <td class="question-content">{{ q.content.substring(0, 60) }}{{ q.content.length > 60 ? '...' : '' }}</td>
            <td>{{ q.answer || '-' }}</td>
            <td class="actions">
              <button class="btn btn-sm" @click="viewQuestion(q)">查看</button>
              <button class="btn btn-sm" @click="editQuestion(q)">编辑</button>
              <button class="btn btn-sm btn-danger" @click="deleteQuestion(q)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showAddModal || showEditModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal modal-large">
        <h3>{{ showEditModal ? '编辑题目' : '添加题目' }}</h3>
        <div class="form-group">
          <label>题目类型 *</label>
          <select v-model="form.question_type">
            <option value="choice">选择题</option>
            <option value="true_false">判断题</option>
            <option value="short_answer">简答题</option>
            <option value="case_analysis">案例分析题</option>
          </select>
        </div>
        <div class="form-group">
          <label>题目内容 *</label>
          <textarea v-model="form.content" rows="4"></textarea>
        </div>
        <div v-if="form.question_type === 'choice'" class="form-group">
          <label>选项</label>
          <textarea v-model="optionsText" rows="4"></textarea>
        </div>
        <div class="form-group">
          <label>答案 *</label>
          <input type="text" v-model="form.answer">
        </div>
        <div class="form-group">
          <label>解析</label>
          <textarea v-model="form.explanation" rows="3"></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveQuestion">保存</button>
        </div>
      </div>
    </div>

    <div v-if="showViewModal" class="modal-overlay" @click.self="showViewModal = false">
      <div class="modal modal-large">
        <h3>题目详情</h3>
        <div class="detail-item">
          <label>类型：</label>
          <span :class="['type-tag', viewQuestionData.question_type]">{{ typeText(viewQuestionData.question_type) }}</span>
        </div>
        <div class="detail-item">
          <label>题目内容：</label>
          <div class="detail-content">{{ viewQuestionData.content }}</div>
        </div>
        <div v-if="viewQuestionData.options" class="detail-item">
          <label>选项：</label>
          <div v-for="(opt, idx) in parseOptions(viewQuestionData.options)" :key="idx" class="option-item">{{ opt }}</div>
        </div>
        <div class="detail-item">
          <label>答案：</label>
          <span class="answer-text">{{ viewQuestionData.answer }}</span>
        </div>
        <div v-if="viewQuestionData.explanation" class="detail-item">
          <label>解析：</label>
          <div class="detail-content">{{ viewQuestionData.explanation }}</div>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="showViewModal = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const bankId = ref(route.params.id)
const bankName = ref('')
const questions = ref([])
const loading = ref(false)
const filterType = ref('')
const stats = ref({ total: 0, choice: 0, trueFalse: 0, shortAnswer: 0, caseAnalysis: 0 })
const showAddModal = ref(false)
const showEditModal = ref(false)
const showViewModal = ref(false)
const viewQuestionData = ref({})
const optionsText = ref('')
const form = ref({ id: null, question_type: 'choice', content: '', answer: '', explanation: '' })

const loadBankInfo = async () => {
  const res = await axios.get(`/api/question-banks/${bankId.value}`)
  bankName.value = res.data.name
}

const loadStats = async () => {
  const types = ['choice', 'true_false', 'short_answer', 'case_analysis']
  stats.value.total = 0
  for (const type of types) {
    const res = await axios.get('/api/questions/count', { params: { question_bank_id: bankId.value, question_type: type } })
    const key = type === 'true_false' ? 'trueFalse' : type === 'short_answer' ? 'shortAnswer' : type === 'case_analysis' ? 'caseAnalysis' : 'choice'
    stats.value[key] = res.data.count
    stats.value.total += res.data.count
  }
}

const loadQuestions = async () => {
  loading.value = true
  try {
    const params = { question_bank_id: bankId.value, limit: 500 }
    if (filterType.value) params.question_type = filterType.value
    const res = await axios.get('/api/questions', { params })
    questions.value = res.data
  } finally {
    loading.value = false
  }
}

const parseOptions = (opts) => {
  if (!opts) return []
  if (Array.isArray(opts)) return opts
  try { return JSON.parse(opts) } catch { return [] }
}

const typeText = (type) => ({ choice: '选择题', true_false: '判断题', short_answer: '简答题', case_analysis: '案例分析' })[type] || type

const viewQuestion = (q) => { viewQuestionData.value = q; showViewModal.value = true }

const editQuestion = (q) => {
  form.value = { id: q.id, question_type: q.question_type, content: q.content, answer: q.answer, explanation: q.explanation }
  const opts = parseOptions(q.options)
  optionsText.value = opts.map((o, i) => `${String.fromCharCode(65 + i)}. ${o}`).join('\n')
  showEditModal.value = true
}

const deleteQuestion = async (q) => {
  if (!confirm('确定要删除该题目吗？')) return
  await axios.delete(`/api/questions/${q.id}`)
  loadQuestions()
  loadStats()
}

const saveQuestion = async () => {
  const data = { question_bank_id: bankId.value, question_type: form.value.question_type, content: form.value.content, answer: form.value.answer, explanation: form.value.explanation }
  if (form.value.question_type === 'choice' && optionsText.value) {
    const options = []
    for (const line of optionsText.value.split('\n')) {
      const match = line.match(/^[A-D][\.、]\s*(.+)/)
      if (match) options.push(match[0])
    }
    if (options.length > 0) data.options = JSON.stringify(options)
  }
  if (showEditModal.value) {
    await axios.put(`/api/questions/${form.value.id}`, data)
  } else {
    await axios.post('/api/questions', data)
  }
  closeModal()
  loadQuestions()
  loadStats()
}

const closeModal = () => {
  showAddModal.value = false
  showEditModal.value = false
  form.value = { id: null, question_type: 'choice', content: '', answer: '', explanation: '' }
  optionsText.value = ''
}

onMounted(() => {
  loadBankInfo()
  loadStats()
  loadQuestions()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.header-left { display: flex; align-items: center; gap: 16px; }
.header-left h1 { margin: 0; }
.btn-back { background: #f5f5f5; color: #333; }
.stats-bar { background: white; padding: 16px 24px; border-radius: 8px; margin-bottom: 20px; display: flex; gap: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.stat-item { display: flex; flex-direction: column; align-items: center; }
.stat-label { font-size: 12px; color: #999; margin-bottom: 4px; }
.stat-value { font-size: 24px; font-weight: bold; color: #1890ff; }
.filters { margin-bottom: 16px; }
.question-table { width: 100%; border-collapse: collapse; }
.question-table th, .question-table td { padding: 12px; text-align: left; border-bottom: 1px solid #f0f0f0; }
.question-table th { background: #fafafa; }
.question-content { max-width: 400px; }
.type-tag { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.type-tag.choice { background: #e6f7ff; color: #1890ff; }
.type-tag.true_false { background: #fff7e6; color: #fa8c16; }
.type-tag.short_answer { background: #f6ffed; color: #52c41a; }
.type-tag.case_analysis { background: #fff2f0; color: #ff4d4f; }
.actions { display: flex; gap: 8px; }
.btn-sm { padding: 4px 12px; font-size: 12px; }
.loading, .empty { text-align: center; padding: 40px; color: #999; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: white; padding: 24px; border-radius: 8px; width: 500px; max-width: 90%; }
.modal-large { width: 700px; }
.modal h3 { margin-bottom: 20px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; margin-bottom: 8px; font-weight: 500; }
.form-group textarea, .form-group input, .form-group select { width: 100%; }
.detail-item { margin-bottom: 16px; }
.detail-item label { font-weight: 500; color: #666; }
.detail-content { margin-top: 8px; padding: 12px; background: #f5f5f5; border-radius: 4px; white-space: pre-wrap; }
.option-item { padding: 8px 12px; background: #e6f7ff; border-radius: 4px; margin-bottom: 4px; }
.answer-text { color: #52c41a; font-weight: bold; font-size: 16px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
</style>
