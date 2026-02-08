"""
统一日志模块
替代全项目 print()，支持日志级别、文件轮转、结构化输出
"""

import logging
import os
from logging.handlers import RotatingFileHandler


# 全局日志格式
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 已初始化的 logger 缓存
_loggers = {}


def setup_logger(name: str = 'finance', level: str = None) -> logging.Logger:
    """
    获取或创建一个命名 logger
    
    Args:
        name: logger 名称 (如 'collector', 'processor', 'web_app')
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR)，默认从环境变量 LOG_LEVEL 读取
    
    Returns:
        配置好的 Logger 实例
    
    Usage:
        from logger import setup_logger
        logger = setup_logger('collector')
        logger.info("采集完成")
        logger.error("采集失败", exc_info=True)
    """
    # 避免重复初始化
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    
    # 如果已有 handler，说明已初始化
    if logger.handlers:
        _loggers[name] = logger
        return logger
    
    # 确定日志级别
    level = level or os.getenv('LOG_LEVEL', 'INFO')
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    
    # 控制台 Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件 Handler（10MB 轮转，保留 5 个备份）
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, f'{name}.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 所有模块的错误日志统一写入 error.log
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # 防止日志向上传播导致重复输出
    logger.propagate = False
    
    _loggers[name] = logger
    return logger
