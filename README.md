# AI Quiz System — AI 刷题系统

一款基于大语言模型的智能刷题系统，支持上传 PDF/Word 文档，AI 自动解析提取题目、答案与解析，并提供多种刷题模式进行练习。

## 功能特性

**文档处理**
- 支持 PDF、Word（.docx）、纯文本（.txt）格式
- 拖拽或点击上传，实时上传进度显示
- 上传后可选择对应题库进行管理

**AI 智能解析**
- 基于 LangChain 调用大语言模型（如 OpenAI GPT、DeepSeek 等）
- 支持 OpenAI 兼容 API，可接入硅基流动等第三方服务
- 智能分块处理长文档，避免遗漏
- 实时解析进度展示（SSE 推送）
- 支持选择题、判断题、简答题、案例分析题四种题型

**题库管理**
- 创建多个题库，分门别类管理题目
- 每个题库独立统计文档数、题目数
- 支持按题型筛选、搜索

**刷题练习**
- 顺序刷题 / 随机刷题两种模式
- 实时显示准确率、已答数量等统计
- 提交答案后即时反馈正误，并显示正确答案与解析
- 刷题状态自动保存到浏览器 localStorage，刷新不丢失

**题目管理**
- 支持手动添加、编辑、删除题目
- 可按题库、题型筛选题目列表

## 技术架构

**后端**
- Python 3 + FastAPI
- SQLite 数据库（轻量化部署）
- LangChain + LangChain-Community（AI 调用）
- 支持 PyPDF2 / pdfplumber（PDF 解析）
- 支持 python-docx（Word 文档解析）
- SSE（Server-Sent Events）实时推送解析进度

**前端**
- Vue 3（Composition API）+ Vite
- Vue Router（路由管理）
- Axios（HTTP 客户端）
- 纯 CSS，无 UI 框架依赖

**AI 集成**
- OpenAI API（GPT-3.5 / GPT-4）
- DeepSeek API
- 硅基流动（SiliconFlow）及所有 OpenAI 兼容 API

## 项目结构

```
ai-quiz-system/
├── backend/
│   ├── main.py              # FastAPI 入口，路由注册，生命周期管理
│   ├── config.py            # 数据库路径、文件存储路径、分块配置
│   ├── database.py          # SQLite 初始化与迁移
│   ├── models.py            # Pydantic 数据模型
│   ├── routers/
│   │   ├── documents.py     # 文档上传、列表、删除、状态更新
│   │   ├── questions.py     # 题目 CRUD
│   │   ├── question_banks.py # 题库 CRUD（含统计信息）
│   │   ├── ai_config.py     # AI 配置读取、保存、连接测试
│   │   └── practice.py      # 随机出题、答案核对
│   ├── services/
│   │   ├── document_parser.py # PDF/Word/TXT 文本提取与分块
│   │   └── ai_parser.py     # LLM 调用、Prompt 设计、JSON 解析、题目入库
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── main.js         # Vue 应用入口
    │   ├── App.vue         # 根组件（基础布局与导航）
    │   └── views/
    │       ├── UploadView.vue      # 上传文档 + 启动解析
    │       ├── QuestionBanksView.vue # 题库管理
    │       ├── BankDetailView.vue   # 题库内题目列表
    │       ├── QuestionList.vue     # 全局题目列表
    │       ├── QuestionDetail.vue   # 题目详情页
    │       ├── PracticeView.vue     # 刷题练习页
    │       └── SettingsView.vue     # AI 配置页
    ├── index.html
    ├── vite.config.js
    └── package.json
```

## 快速启动

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
python main.py
```

后端服务运行于 `http://localhost:8000`，FastAPI 自动生成 API 文档可访问 `http://localhost:8000/docs`。

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端服务运行于 `http://localhost:3000`，开发环境默认代理 `/api` 请求到后端。

### 3. 配置 AI

1. 打开前端 `http://localhost:3000`
2. 进入「设置」页面
3. 填写 API 地址、API Key、模型名称
4. 点击「测试连接」验证
5. 点击「保存配置」

示例配置：

| 服务 | API 地址 | 模型 |
|------|----------|------|
| OpenAI | `https://api.openai.com/v1/chat/completions` | `gpt-3.5-turbo` |
| 硅基流动 | `https://api.siliconflow.cn/v1/chat/completions` | `...` |
| DeepSeek | `https://api.deepseek.com/v1/chat/completions` | `deepseek-chat` |

### 4. 使用流程

1. 在「上传文档」页面上传 PDF/Word 文档（可新建题库）
2. 点击「解析」按钮，AI 开始提取题目
3. 解析完成后，在「题库」→「查看题目」查看结果
4. 进入「刷题」页面选择模式开始练习

## API 概览

**文档管理**
- `POST /api/documents/` — 上传文档
- `GET /api/documents/` — 获取文档列表
- `DELETE /api/documents/{id}` — 删除文档
- `POST /api/documents/{id}/parse` — 触发 AI 解析
- `GET /api/documents/{id}/progress` — SSE 解析进度流

**题目管理**
- `GET /api/questions/` — 获取题目列表（支持题库/文档/题型筛选）
- `GET /api/questions/{id}` — 获取题目详情
- `POST /api/questions/` — 创建题目
- `PUT /api/questions/{id}` — 更新题目
- `DELETE /api/questions/{id}` — 删除题目

**题库管理**
- `GET /api/question-banks/` — 获取题库列表（含题目/文档统计）
- `POST /api/question-banks/` — 创建题库
- `PUT /api/question-banks/{id}` — 更新题库
- `DELETE /api/question-banks/{id}` — 删除题库（级联删除题目）

**AI 配置**
- `GET /api/ai/config` — 获取当前配置
- `POST /api/ai/config` — 保存配置
- `POST /api/ai/config/test` — 测试连接

**刷题**
- `GET /api/practice/random` — 获取随机题目
- `POST /api/practice/check` — 核对答案

## 数据模型

**QuestionBank（题库）**
- `id`, `name`, `description`, `created_at`, `updated_at`

**Document（文档）**
- `id`, `question_bank_id`, `filename`, `file_path`, `status`（pending / processing / completed / failed）, `total_questions`, `created_at`, `updated_at`

**Question（题目）**
- `id`, `question_bank_id`, `document_id`, `question_type`（choice / true_false / short_answer / case_analysis）, `content`, `options`（JSON 数组）, `answer`, `explanation`, `created_at`

## 配置说明

后端配置文件 `backend/config.py`：

```python
DATABASE_URL = "sqlite:///./ai_quiz.db"   # 数据库路径
UPLOAD_DIR = ".../data"                    # 上传文件存储目录
CHUNK_SIZE = 100000                         # 文档分块大小（字符数）
CHUNK_OVERLAP = 200                         # 相邻块重叠字符数
```
