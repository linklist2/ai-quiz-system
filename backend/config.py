import os

# 数据库配置
DATABASE_URL = "sqlite:///./ai_quiz.db"

# 上传文件存储目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# AI 配置默认值
DEFAULT_AI_CONFIG = {
    "api_url": "",
    "api_key": "",
    "model_name": "gpt-3.5-turbo"
}

# 文档分块配置
CHUNK_SIZE = 100000  # 每块字符数
CHUNK_OVERLAP = 200  # 相邻块重叠字符数

# 两轮解析配置
ANALYZE_CHUNK_SIZE = 5000  # 第一轮分析用的分块大小
ANALYZE_CHUNK_OVERLAP = 500  # 第一轮分析块重叠大小
