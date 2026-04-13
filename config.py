import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # 企业微信配置
    WECHAT_CORPID = os.getenv("WECHAT_CORPID")
    WECHAT_SECRET = os.getenv("WECHAT_SECRET")
    WECHAT_AGENTID = os.getenv("WECHAT_AGENTID")
    WECHAT_WEBHOOK_KEY = os.getenv("WECHAT_WEBHOOK_KEY")
    WECHAT_TOKEN = os.getenv("WECHAT_TOKEN")
    WECHAT_ENCODING_AES_KEY = os.getenv("WECHAT_ENCODING_AES_KEY")
    
    # 管理端配置
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW")
    
    # AI问答配置
    AI_WEB_URL = os.getenv("AI_WEB_URL", "https://chat.openai.com")
    AI_USERNAME = os.getenv("AI_USERNAME")
    AI_PASSWORD = os.getenv("AI_PASSWORD")
    AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "15000"))
    
    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    
    # 自动更新配置
    GITHUB_REPO = os.getenv("GITHUB_REPO", "https://github.com/scottHGITUHB/auto_assistant.git")
    GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "master")
    UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "6"))  # 默认每6小时
    
    # 其他配置
    TZ = os.getenv("TZ", "Asia/Shanghai")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # 并发控制
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    
    # 会话缓存配置
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 默认1小时

# 创建全局配置实例
config = Config()
