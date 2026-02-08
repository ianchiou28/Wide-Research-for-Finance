"""
简单的 TTL 内存缓存
线程安全，支持按 key 或全量失效
"""
import time
import threading
from typing import Any, Optional
from logger import setup_logger

logger = setup_logger('cache')


class SimpleCache:
    """线程安全的 TTL 内存缓存"""

    def __init__(self, default_ttl: int = 300):
        """
        Args:
            default_ttl: 默认缓存有效期（秒），默认 5 分钟
        """
        self._cache: dict = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl

    def get(self, key: str, ttl_seconds: Optional[int] = None) -> Optional[Any]:
        """获取缓存值，过期返回 None"""
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < ttl:
                    return value
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """写入缓存"""
        with self._lock:
            self._cache[key] = (value, time.time())

    def invalidate(self, key: Optional[str] = None) -> None:
        """
        失效缓存。
        key=None 时清空全部，否则只清指定 key。
        """
        with self._lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()

    def stats(self) -> dict:
        """返回缓存统计信息"""
        with self._lock:
            now = time.time()
            total = len(self._cache)
            expired = sum(
                1 for _, (_, ts) in self._cache.items()
                if now - ts >= self._default_ttl
            )
            return {
                'total_keys': total,
                'expired_keys': expired,
                'active_keys': total - expired,
            }


# 全局单例，供 web_app.py 直接导入使用
cache = SimpleCache(default_ttl=300)
