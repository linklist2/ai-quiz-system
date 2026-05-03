<template>
  <div class="settings-view">
    <h1>AI 配置</h1>
    <div class="card">
      <div class="form-group"><label>配置名称</label><input type="text" v-model="config.name" placeholder="例如：我的 API"></div>
      <div class="form-group">
        <label>API 地址</label>
        <input type="text" v-model="config.api_url" placeholder="https://api.openai.com/v1/chat/completions">
        <div class="hint">OpenAI 兼容的 API 地址，通常以 /v1/chat/completions 结尾</div>
      </div>
      <div class="form-group"><label>API Key</label><input type="password" v-model="config.api_key" placeholder="sk-..."></div>
      <div class="form-group">
        <label>模型名称</label>
        <input type="text" v-model="config.model_name" placeholder="gpt-3.5-turbo">
        <div class="hint">例如：gpt-3.5-turbo、gpt-4、claude-3-sonnet 等</div>
      </div>
      <div class="form-actions">
        <button class="btn btn-primary" @click="saveConfig" :disabled="saving">{{ saving ? '保存中...' : '保存配置' }}</button>
        <button class="btn" @click="testConnection" :disabled="testing">{{ testing ? '测试中...' : '测试连接' }}</button>
      </div>
      <div v-if="testResult" :class="['test-result', testResult.status]">{{ testResult.message }}</div>
    </div>
    <div class="card">
      <h2>使用说明</h2>
      <div class="help-content">
        <p><strong>支持的 AI 服务：</strong></p>
        <ul>
          <li>OpenAI API (GPT-3.5, GPT-4)</li>
          <li>硅基流动 (SiliconFlow)</li>
          <li>其他 OpenAI 兼容 API</li>
        </ul>
        <p><strong>配置步骤：</strong></p>
        <ol>
          <li>填写 API 地址（从 AI 服务提供商获取）</li>
          <li>填写 API Key（不要泄露给他人）</li>
          <li>填写模型名称</li>
          <li>点击「保存配置」</li>
          <li>可点击「测试连接」验证配置是否正确</li>
        </ol>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const config = ref({ name: '', api_url: '', api_key: '', model_name: 'gpt-3.5-turbo' })
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)

const loadConfig = async () => {
  try {
    const res = await axios.get('/api/ai/config')
    if (res.data && res.data.id) {
      config.value = { name: res.data.name, api_url: res.data.api_url, api_key: res.data.api_key, model_name: res.data.model_name }
    }
  } catch (error) {}
}

const saveConfig = async () => {
  saving.value = true
  testResult.value = null
  try {
    await axios.post('/api/ai/config', config.value)
    alert('配置保存成功')
  } catch (error) {
    alert('保存失败: ' + (error.response?.data?.detail || error.message))
  } finally { saving.value = false }
}

const testConnection = async () => {
  testing.value = true
  testResult.value = null
  try {
    await axios.post('/api/ai/config', config.value)
    await axios.post('/api/ai/config/test', config.value)
    testResult.value = { status: 'success', message: '连接成功！' }
  } catch (error) {
    testResult.value = { status: 'error', message: '连接失败: ' + (error.response?.data?.detail || error.message) }
  } finally { testing.value = false }
}

onMounted(() => loadConfig())
</script>

<style scoped>
.settings-view h1 { margin-bottom: 24px; }
.settings-view h2 { font-size: 18px; margin-bottom: 16px; }
.hint { font-size: 12px; color: #999; margin-top: 4px; }
.form-actions { display: flex; gap: 12px; margin-top: 24px; }
.test-result { margin-top: 16px; padding: 12px; border-radius: 4px; }
.test-result.success { background: #f6ffed; color: #52c41a; }
.test-result.error { background: #fff2f0; color: #ff4d4f; }
.help-content { color: #666; line-height: 1.8; }
.help-content p { margin-bottom: 8px; }
.help-content ul, .help-content ol { margin-left: 20px; margin-bottom: 16px; }
</style>
