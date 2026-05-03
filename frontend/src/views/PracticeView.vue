<template>
  <div class="practice-view">
    <div class="page-header">
      <h1>刷题练习 - {{ bankName }}</h1>
      <div class="header-actions">
        <button class="btn btn-sm" @click="resetPractice" v-if="answeredCount > 0">重置刷题状态</button>
        <button class="btn btn-sm" @click="$router.push('/banks')">返回题库</button>
      </div>
    </div>

    <div class="stats-bar">
      <span>总题目: {{ totalQuestions }}</span>
      <span>当前: {{ currentIndex + 1 }} / {{ totalQuestions }}</span>
      <span>已答: {{ answeredCount }}</span>
      <span>正确: {{ correctCount }}</span>
      <span>准确率: {{ accuracyRate }}%</span>
      <span>模式: {{ practiceMode === 'sequential' ? '顺序刷题' : '随机刷题' }}</span>
    </div>

    <div v-if="loading" class="card"><div class="loading">加载中...</div></div>
    <div v-else-if="questions.length === 0" class="card">
      <div class="empty"><p>该题库暂无题目</p><button class="btn btn-primary" @click="$router.push('/upload')">去上传文档</button></div>
    </div>
    <div v-else-if="currentQuestion" class="card">
      <div class="question-header">
        <span :class="['type-tag', currentQuestion.question_type]">{{ typeText(currentQuestion.question_type) }}</span>
        <span class="question-id">#{{ currentQuestion.id }}</span>
      </div>
      <div class="question-content"><p>{{ currentQuestion.content }}</p></div>
      <div v-if="currentOptions.length > 0" class="question-options">
        <div v-for="(opt, idx) in currentOptions" :key="idx" :class="['option-item', { selected: selectedAnswer === getOptionLetter(opt) }]" @click="selectAnswer(opt)">
          {{ opt }}
        </div>
      </div>
      <div v-else-if="currentQuestion.question_type !== 'choice'" class="answer-input">
        <textarea v-model="selectedAnswer" placeholder="请输入你的答案" :disabled="isAnswered"></textarea>
      </div>
      <div class="action-buttons">
        <button class="btn" @click="prevQuestion" :disabled="currentIndex === 0">上一题</button>
        <button v-if="!isAnswered" class="btn btn-primary" @click="submitAnswer" :disabled="!selectedAnswer">提交答案</button>
        <button v-else class="btn btn-primary" @click="nextQuestion">{{ currentIndex === totalQuestions - 1 ? '完成' : '下一题' }}</button>
      </div>
      <div v-if="isAnswered" class="result">
        <div :class="['result-badge', { correct: isCurrentCorrect, wrong: !isCurrentCorrect }]">{{ isCurrentCorrect ? '回答正确！' : '回答错误' }}</div>
        <div class="correct-answer">正确答案: <strong>{{ currentQuestion.answer }}</strong></div>
        <div v-if="currentQuestion.explanation" class="explanation"><strong>解析:</strong> {{ currentQuestion.explanation }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const questions = ref([])
const currentIndex = ref(0)
const loading = ref(false)
const selectedAnswer = ref('')
const isAnswered = ref(false)
const isCurrentCorrect = ref(false)
const correctCount = ref(0)
const answeredCount = ref(0)
const bankName = ref('')
const practiceMode = ref('sequential')
const PRACTICE_STORAGE_KEY = 'practice_state'

const totalQuestions = computed(() => questions.value.length)
const accuracyRate = computed(() => answeredCount.value === 0 ? 0 : Math.round((correctCount.value / answeredCount.value) * 100))
const currentQuestion = computed(() => questions.value[currentIndex.value] || null)
const currentOptions = computed(() => {
  if (!currentQuestion.value) return []
  if (currentQuestion.value.options) {
    try {
      const opts = JSON.parse(currentQuestion.value.options)
      if (Array.isArray(opts) && opts.length > 0) return opts
    } catch {}
  }
  const content = currentQuestion.value.content || ''
  const options = []
  const patterns = [/[A-D][\.、]([^A-D\n]+)/g, /（[A-D]）([^A-D（）+]+)/g, /\([A-D]\)([^A-D（）\n]+)/g]
  for (const pattern of patterns) {
    const matches = [...content.matchAll(pattern)]
    if (matches.length > 0) {
      for (const match of matches) options.push(`${match[0].substring(0, 2)} ${match[1].trim()}`)
      break
    }
  }
  return options
})

const getOptionLetter = (opt) => opt.charAt(0)

const loadQuestions = async () => {
  loading.value = true
  try {
    const bankId = route.query.bank_id
    const mode = route.query.mode || 'sequential'
    practiceMode.value = mode
    if (bankId) {
      const bankRes = await axios.get(`/api/question-banks/${bankId}`)
      bankName.value = bankRes.data.name
    }
    const params = { limit: 500 }
    if (bankId) params.question_bank_id = bankId
    let loadedQuestions = (await axios.get('/api/questions', { params })).data
    if (mode === 'random') loadedQuestions = shuffleArray([...loadedQuestions])
    questions.value = loadedQuestions
    restorePracticeState()
  } catch (error) {
    questions.value = []
  } finally {
    loading.value = false
  }
}

const shuffleArray = (array) => { for (let i = array.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [array[i], array[j]] = [array[j], array[i]] } return array }

const savePracticeState = () => {
  const state = { bank_id: route.query.bank_id, mode: practiceMode.value, currentIndex: currentIndex.value, correctCount: correctCount.value, answeredCount: answeredCount.value, answers: {} }
  questions.value.forEach(q => { if (q.userAnswer !== undefined) state.answers[q.id] = { userAnswer: q.userAnswer, isCorrect: q.isCorrect, isAnswered: q.isAnswered } })
  localStorage.setItem(PRACTICE_STORAGE_KEY, JSON.stringify(state))
}

const restorePracticeState = () => {
  try {
    const saved = localStorage.getItem(PRACTICE_STORAGE_KEY)
    if (!saved) return
    const state = JSON.parse(saved)
    if (state.bank_id !== route.query.bank_id || state.mode !== practiceMode.value) return
    currentIndex.value = state.currentIndex || 0
    correctCount.value = state.correctCount || 0
    answeredCount.value = state.answeredCount || 0
    if (state.answers) {
      questions.value.forEach(q => { if (state.answers[q.id]) { q.userAnswer = state.answers[q.id].userAnswer; q.isCorrect = state.answers[q.id].isCorrect; q.isAnswered = state.answers[q.id].isAnswered } })
    }
    const currentQ = questions.value[currentIndex.value]
    if (currentQ && currentQ.isAnswered) { selectedAnswer.value = currentQ.userAnswer || ''; isAnswered.value = true; isCurrentCorrect.value = currentQ.isCorrect || false }
  } catch (e) {}
}

const resetPractice = () => {
  if (!confirm('确定要重置刷题状态吗？')) return
  localStorage.removeItem(PRACTICE_STORAGE_KEY)
  questions.value.forEach(q => { q.userAnswer = undefined; q.isCorrect = undefined; q.isAnswered = undefined })
  currentIndex.value = 0; correctCount.value = 0; answeredCount.value = 0; selectedAnswer.value = ''; isAnswered.value = false; isCurrentCorrect.value = false
}

const selectAnswer = (opt) => { if (!isAnswered.value) selectedAnswer.value = getOptionLetter(opt) }

const submitAnswer = async () => {
  if (!selectedAnswer.value || isAnswered.value || !currentQuestion.value) return
  try {
    const res = await axios.post('/api/practice/check', { question_id: currentQuestion.value.id, user_answer: selectedAnswer.value })
    isCurrentCorrect.value = res.data.correct
    isAnswered.value = true
    currentQuestion.value.userAnswer = selectedAnswer.value
    currentQuestion.value.isCorrect = isCurrentCorrect.value
    currentQuestion.value.isAnswered = true
    answeredCount.value++
    if (isCurrentCorrect.value) correctCount.value++
    savePracticeState()
  } catch (error) {}
}

const nextQuestion = () => { if (currentIndex.value < questions.value.length - 1) { currentIndex.value++; resetCurrentState(); restoreCurrentQuestionState() } }
const prevQuestion = () => { if (currentIndex.value > 0) { currentIndex.value--; resetCurrentState(); restoreCurrentQuestionState() } }
const resetCurrentState = () => { selectedAnswer.value = ''; isAnswered.value = false; isCurrentCorrect.value = false }
const restoreCurrentQuestionState = () => { const q = currentQuestion.value; if (q && q.isAnswered) { selectedAnswer.value = q.userAnswer || ''; isAnswered.value = true; isCurrentCorrect.value = q.isCorrect || false } }
const typeText = (type) => ({ choice: '选择题', true_false: '判断题', short_answer: '简答题', case_analysis: '案例分析' })[type] || type

onMounted(() => loadQuestions())
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h1 { margin: 0; font-size: 24px; }
.header-actions { display: flex; gap: 12px; }
.stats-bar { background: white; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px; display: flex; gap: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.stats-bar span { color: #666; }
.question-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.type-tag { padding: 4px 12px; border-radius: 4px; font-size: 14px; }
.type-tag.choice { background: #e6f7ff; color: #1890ff; }
.type-tag.true_false { background: #fff7e6; color: #fa8c16; }
.type-tag.short_answer { background: #f6ffed; color: #52c41a; }
.type-tag.case_analysis { background: #fff2f0; color: #ff4d4f; }
.question-id { color: #999; font-size: 14px; }
.question-content { margin-bottom: 24px; }
.question-content p { font-size: 18px; line-height: 1.8; white-space: pre-wrap; }
.question-options { margin-bottom: 24px; }
.option-item { padding: 16px; background: #f5f5f5; border-radius: 8px; margin-bottom: 12px; cursor: pointer; transition: all 0.3s; border: 2px solid transparent; }
.option-item:hover { background: #e6f7ff; border-color: #40a9ff; }
.option-item.selected { background: #bae7ff; border-color: #1890ff; }
.answer-input textarea { width: 100%; min-height: 100px; padding: 12px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 16px; resize: vertical; }
.action-buttons { margin-top: 20px; display: flex; gap: 12px; }
.result { margin-top: 24px; padding-top: 24px; border-top: 1px solid #f0f0f0; }
.result-badge { padding: 12px 24px; border-radius: 4px; font-size: 18px; font-weight: bold; margin-bottom: 16px; display: inline-block; }
.result-badge.correct { background: #f6ffed; color: #52c41a; }
.result-badge.wrong { background: #fff2f0; color: #ff4d4f; }
.correct-answer { margin-bottom: 12px; }
.explanation { color: #666; line-height: 1.6; }
.loading, .empty { text-align: center; padding: 40px; }
.empty p { margin-bottom: 16px; color: #666; }
.btn-sm { padding: 8px 16px; font-size: 14px; }
</style>
