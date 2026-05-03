import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

import UploadView from './views/UploadView.vue'
import QuestionList from './views/QuestionList.vue'
import QuestionDetail from './views/QuestionDetail.vue'
import PracticeView from './views/PracticeView.vue'
import SettingsView from './views/SettingsView.vue'
import QuestionBanksView from './views/QuestionBanksView.vue'
import BankDetailView from './views/BankDetailView.vue'

const routes = [
  { path: '/', redirect: '/upload' },
  { path: '/upload', name: 'upload', component: UploadView },
  { path: '/questions', name: 'questions', component: QuestionList },
  { path: '/questions/:id', name: 'question-detail', component: QuestionDetail },
  { path: '/practice', name: 'practice', component: PracticeView },
  { path: '/settings', name: 'settings', component: SettingsView },
  { path: '/banks', name: 'banks', component: QuestionBanksView },
  { path: '/banks/:id', name: 'bank-detail', component: BankDetailView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')
