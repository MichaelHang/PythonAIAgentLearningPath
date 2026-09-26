"""配置中心：所有环境变量从这里读取，其他模块不要直接 os.environ"""

import os

# LLM 接入
DEEPSEEK_API_KEY = (
    os.environ.get("DEEPSEEK_API_KEY")
    or os.environ.get("OPENAI_API_KEY", "")
).strip()
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "512"))
LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "30"))

# 文件工具的安全边界：所有文件读写都被限制在这个目录内
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", "workspace")
