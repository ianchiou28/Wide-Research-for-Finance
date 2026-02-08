"""
统一配置管理
集中管理所有配置项，消除硬编码，支持环境变量覆盖
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """全局配置"""
    
    # ============== LLM 配置 ==============
    LLM_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://api.deepseek.com')
    LLM_MODEL = os.getenv('LLM_MODEL', 'deepseek-chat')
    LLM_TIMEOUT = float(os.getenv('LLM_TIMEOUT', '120'))
    LLM_MAX_RETRIES = int(os.getenv('LLM_MAX_RETRIES', '2'))
    
    # ============== 数据采集配置 ==============
    FETCH_TIMEOUT = int(os.getenv('FETCH_TIMEOUT', '15'))
    MAX_PER_SOURCE = int(os.getenv('MAX_PER_SOURCE', '15'))
    FETCH_HOURS = int(os.getenv('FETCH_HOURS', '24'))
    
    # ============== 邮件配置 ==============
    EMAIL_FROM = os.getenv('EMAIL_FROM', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_TO = os.getenv('EMAIL_TO', '')
    SMTP_SERVER = os.getenv('SMTP_SERVER', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
    
    # ============== Web 配置 ==============
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
    ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', '')
    
    # ============== 数据库配置 ==============
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # sqlite / postgresql
    DB_PATH = os.getenv('DB_PATH', '')  # SQLite 路径（空=默认）
    
    # ============== 日志配置 ==============
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # ============== 路径配置 ==============
    DATA_DIR = os.getenv('DATA_DIR', 'data')
    REPORTS_DIR = os.path.join(DATA_DIR, 'reports')
    REPORTS_JSON_DIR = os.path.join(DATA_DIR, 'reports_json')
    SUMMARIES_DIR = os.path.join(DATA_DIR, 'summaries')
    WEEKLY_DIR = os.path.join(DATA_DIR, 'weekly')
    MONTHLY_DIR = os.path.join(DATA_DIR, 'monthly')
    LOGS_DIR = os.path.join(DATA_DIR, 'logs')
    
    # ============== 配置文件路径 ==============
    SOURCES_CONFIG = os.getenv('SOURCES_CONFIG', 'config/sources.yaml')
    USER_CONFIG = os.getenv('USER_CONFIG', 'src/user_config.yaml')
    
    @classmethod
    def ensure_dirs(cls):
        """确保所有数据目录存在"""
        for d in [cls.REPORTS_DIR, cls.REPORTS_JSON_DIR, cls.SUMMARIES_DIR,
                  cls.WEEKLY_DIR, cls.MONTHLY_DIR, cls.LOGS_DIR]:
            os.makedirs(d, exist_ok=True)
    
    @classmethod
    def get_llm_client_kwargs(cls) -> dict:
        """获取 OpenAI 客户端初始化参数"""
        return {
            'api_key': cls.LLM_API_KEY,
            'base_url': cls.LLM_BASE_URL,
            'timeout': cls.LLM_TIMEOUT,
            'max_retries': cls.LLM_MAX_RETRIES,
        }
    
    @classmethod
    def validate(cls) -> list:
        """验证关键配置，返回警告列表"""
        warnings = []
        if not cls.LLM_API_KEY:
            warnings.append("DEEPSEEK_API_KEY 未设置，LLM 功能不可用")
        if cls.SECRET_KEY == 'change-me-in-production':
            warnings.append("SECRET_KEY 未修改，请设置安全的随机密钥")
        if not cls.ADMIN_API_KEY:
            warnings.append("ADMIN_API_KEY 未设置，管理接口无认证保护")
        return warnings
