<template>
  <div class="question-detail">
    <router-link to="/questions" class="back-link">← 返回列表</router-link>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!question" class="empty">题目不存在</div>
    <div v-else class="card">
      <div class="question-header">
        <span :class="['type-tag', question.question_type]">{{ typeText(question.question_type) }}</span>
        <span class="question-id">#{{ question.id }}</span>
      </div>
      <div class="question-content"><h3>题目</h3><p>{{ question.content }}</p></div>
      <div v-if="question.options" class="question-options"><h3>选项</h3><div v-for="(opt, idx) in parseOptions(question.options)" :key="idx" class="option-item">{{ opt }}</div></div>
      <div class="question-answer"><h3>答案</h3><p class="answer-text">{{ question.answer }}</p></div>
      <div v-if="question.explanation" class="question-explanation"><h3>解析</h3><p>{{ question.explanation }}</p></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const question = ref(null)
const loading = ref(true)

const loadQuestion = async () => {
  loading.value = true
  try {
    const res = await axios.get(`/api/questions/${route.params.id}`)
    question.value = res.data
  } catch { question.value = null }
  finally { loading.value = false }
}

const parseOptions = (options) => { if (!options) return []; if (Array.isArray(options)) return options; try { return JSON.parse(options) } catch { return [] } }
const typeText = (type) => ({ choice: '选择题', true_false: '判断题', short_answer: '简答题', case_analysis: '案例分析' })[type] || type

onMounted(() => loadQuestion())
</script>

<style scoped>
.back-link { display: inline-block; margin-bottom: 16px; color: #1890ff; text-decoration: none; }
.back-link:hover { text-decoration: underline; }
.question-header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
.type-tag { padding: 4px 12px; border-radius: 4px; font-size: 14px; }
.type-tag.choice { background: #e6f7ff; color: #1890ff; }
.type-tag.true_false { background: #fff7e6; color: #fa8c16; }
.type-tag.short_answer { background: #f6ffed; color: #52c41a; }
.type-tag.case_analysis { background: #fff2f0; color: #ff4d4f; }
.question-id { color: #999; font-size: 14px; }
.question-content, .question-options, .question-answer, .question-explanation { margin-bottom: 24px; }
.question-content h3, .question-options h3, .question-answer h3, .question-explanation h3 { font-size: 14px; color: #666; margin-bottom: 8px; }
.question-content p, .question-explanation p { font-size: 16px; line-height: 1.8; }
.option-item { padding: 12px; background: #f5f5f5; border-radius: 4px; margin-bottom: 8px; }
.answer-text { font-size: 18px; color: #52c41a; font-weight: bold; }
.loading, .empty { text-align: center; padding: 40px; color: #999; }
</style>
