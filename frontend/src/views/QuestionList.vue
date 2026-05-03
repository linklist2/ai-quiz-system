<template>
  <div class="question-list">
    <div class="page-header">
      <h1>题目列表</h1>
      <button class="btn btn-primary" @click="showAddModal = true">添加题目</button>
    </div>
    <div class="card">
      <div class="filters">
        <select v-model="filterBank" @change="loadQuestions">
          <option value="">全部题库</option>
          <option v-for="bank in banks" :key="bank.id" :value="bank.id">{{ bank.name }}</option>
        </select>
        <select v-model="filterType" @change="loadQuestions">
          <option value="">全部类型</option>
          <option value="choice">选择题</option>
          <option value="true_false">判断题</option>
          <option value="short_answer">简答题</option>
          <option value="case_analysis">案例分析题</option>
        </select>
        <span class="total-count">共 {{ total }} 道题目</span>
      </div>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="questions.length === 0" class="empty">暂无题目</div>
      <table v-else class="question-table">
        <thead><tr><th>ID</th><th>类型</th><th>题目内容</th><th>答案</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="q in questions" :key="q.id">
            <td>{{ q.id }}</td>
            <td><span :class="['type-tag', q.question_type]">{{ typeText(q.question_type) }}</span></td>
            <td class="question-content">{{ q.content.substring(0, 80) }}{{ q.content.length > 80 ? '...' : '' }}</td>
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
    <div v-if="showViewModal" class="modal-overlay" @click.self="showViewModal = false">
      <div class="modal modal-large">
        <h3>题目详情</h3>
        <div class="detail-item"><label>类型：</label><span :class="['type-tag', viewQuestionData.question_type]">{{ typeText(viewQuestionData.question_type) }}</span></div>
        <div class="detail-item"><label>题目内容：</label><div class="detail-content">{{ viewQuestionData.content }}</div></div>
        <div v-if="viewQuestionData.options" class="detail-item"><label>选项：</label><div v-for="(opt, idx) in parseOptions(viewQuestionData.options)" :key="idx" class="option-item">{{ opt }}</div></div>
        <div class="detail-item"><label>答案：</label><span class="answer-text">{{ viewQuestionData.answer }}</span></div>
        <div v-if="viewQuestionData.explanation" class="detail-item"><label>解析：</label><div class="detail-content">{{ viewQuestionData.explanation }}</div></div>
        <div class="modal-actions"><button class="btn" @click="showViewModal = false">关闭</button></div>
      </div>
    </div>
    <div v-if="showAddModal || showEditModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal modal-large">
        <h3>{{ showEditModal ? '编辑题目' : '添加题目' }}</h3>
        <div class="form-row">
          <div class="form-group">
            <label>题目类型 *</label>
            <select v-model="form.question_type">
              <option value="choice">选择题</option><option value="true_false">判断题</option><option value="short_answer">简答题</option><option value="case_analysis">案例分析题</option>
            </select>
          </div>
          <div class="form-group">
            <label>题库 *</label>
            <select v-model="form.question_bank_id"><option v-for="bank in banks" :key="bank.id" :value="bank.id">{{ bank.name }}</option></select>
          </div>
        </div>
        <div class="form-group"><label>题目内容 *</label><textarea v-model="form.content" rows="4"></textarea></div>
        <div v-if="form.question_type === 'choice'" class="form-group"><label>选项</label><textarea v-model="optionsText" rows="4"></textarea></div>
        <div class="form-group"><label>答案 *</label><input type="text" v-model="form.answer"></div>
        <div class="form-group"><label>解析</label><textarea v-model="form.explanation" rows="3"></textarea></div>
        <div class="modal-actions">
          <button class="btn" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="saveQuestion">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const questions = ref([])
const banks = ref([])
const loading = ref(false)
const filterBank = ref('')
const filterType = ref('')
const total = ref(0)
const showAddModal = ref(false)
const showEditModal = ref(false)
const showViewModal = ref(false)
const viewQuestionData = ref({})
const optionsText = ref('')
const form = ref({ id: null, question_bank_id: null, question_type: 'choice', content: '', answer: '', explanation: '' })

const loadBanks = async () => {
  const res = await axios.get('/api/question-banks')
  banks.value = res.data
  if (banks.value.length > 0 && !form.value.question_bank_id) form.value.question_bank_id = banks.value[0].id
}

const loadQuestions = async () => {
  loading.value = true
  try {
    const params = { limit: 50 }
    if (filterBank.value) params.question_bank_id = filterBank.value
    if (filterType.value) params.question_type = filterType.value
    const res = await axios.get('/api/questions', { params })
    questions.value = res.data
    total.value = res.data.length
  } finally { loading.value = false }
}

const typeText = (type) => ({ choice: '选择题', true_false: '判断题', short_answer: '简答题', case_analysis: '案例分析' })[type] || type
const parseOptions = (opts) => { if (!opts) return []; if (Array.isArray(opts)) return opts; try { return JSON.parse(opts) } catch { return [] } }
const viewQuestion = (q) => { viewQuestionData.value = q; showViewModal.value = true }
const editQuestion = (q) => {
  form.value = { id: q.id, question_bank_id: q.question_bank_id, question_type: q.question_type, content: q.content, answer: q.answer, explanation: q.explanation }
  optionsText.value = parseOptions(q.options).map((o, i) => `${String.fromCharCode(65 + i)}. ${o}`).join('\n')
  showEditModal.value = true
}
const deleteQuestion = async (q) => { if (!confirm('确定要删除该题目吗？')) return; await axios.delete(`/api/questions/${q.id}`); loadQuestions() }
const saveQuestion = async () => {
  const data = { question_bank_id: form.value.question_bank_id, question_type: form.value.question_type, content: form.value.content, answer: form.value.answer, explanation: form.value.explanation }
  if (form.value.question_type === 'choice' && optionsText.value) {
    const options = []
    for (const line of optionsText.value.split('\n')) { const match = line.match(/^[A-D][\.、]\s*(.+)/); if (match) options.push(match[0]) }
    if (options.length > 0) data.options = JSON.stringify(options)
  }
  if (showEditModal.value) await axios.put(`/api/questions/${form.value.id}`, data)
  else await axios.post('/api/questions', data)
  closeModal(); loadQuestions()
}
const closeModal = () => { showAddModal.value = false; showEditModal.value = false; showViewModal.value = false; form.value = { id: null, question_bank_id: banks.value[0]?.id, question_type: 'choice', content: '', answer: '', explanation: '' }; optionsText.value = '' }

onMounted(() => { loadBanks(); loadQuestions() })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h1 { margin: 0; }
.filters { margin-bottom: 16px; display: flex; gap: 12px; align-items: center; }
.filters select { width: 150px; }
.total-count { margin-left: auto; color: #666; }
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
.form-row { display: flex; gap: 16px; }
.form-row .form-group { flex: 1; }
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
