"""
System routes blueprint - cache management.
"""
import logging

from flask import Blueprint, jsonify

from cache import cache
from web.helpers import require_api_key

logger = logging.getLogger('web_app')

system_bp = Blueprint('system', __name__)


@system_bp.route('/api/cache/stats')
def api_cache_stats():
    """查看缓存状态"""
    return jsonify(cache.stats())


@system_bp.route('/api/cache/clear', methods=['POST'])
@require_api_key
def api_cache_clear():
    """清空缓存（需要 API Key）"""
    cache.invalidate()
    logger.info("缓存已手动清空")
    return jsonify({'success': True, 'message': '缓存已清空'})
