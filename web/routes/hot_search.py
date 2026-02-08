"""
Hot search routes blueprint.
"""
import logging

from flask import Blueprint, jsonify, request

from cache import cache
from web.helpers import get_hot_search_collector

logger = logging.getLogger('web_app')

hot_search_bp = Blueprint('hot_search', __name__)


@hot_search_bp.route('/api/hot-searches')
def api_hot_searches():
    """获取实时热搜（2分钟缓存）"""
    platform = request.args.get('platform', None)  # weibo, toutiao, zhihu, baidu, douyin
    finance_only = request.args.get('finance_only', 'true').lower() == 'true'

    cache_key = f'hot_searches_{platform}_{finance_only}'
    cached = cache.get(cache_key, ttl_seconds=120)
    if cached is not None:
        return jsonify(cached)

    collector = get_hot_search_collector()
    if not collector:
        return jsonify({'error': '热搜模块未加载'}), 500

    try:
        if platform:
            # 获取指定平台热搜
            method_map = {
                'weibo': collector.fetch_weibo_hot,
                'toutiao': collector.fetch_toutiao_hot,
                'zhihu': collector.fetch_zhihu_hot,
                'baidu': collector.fetch_baidu_hot,
                'douyin': collector.fetch_douyin_hot
            }
            if platform in method_map:
                data = method_map[platform](finance_only)
                result = {'platform': platform, 'data': data}
                cache.set(cache_key, result)
                return jsonify(result)
            else:
                return jsonify({'error': '无效的平台'}), 400
        else:
            # 获取聚合热搜
            data = collector.get_aggregated_finance_hot(30)
            result = {'data': data}
            cache.set(cache_key, result)
            return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@hot_search_bp.route('/api/hot-searches/all')
def api_hot_searches_all():
    """获取所有平台热搜"""
    finance_only = request.args.get('finance_only', 'true').lower() == 'true'

    collector = get_hot_search_collector()
    if not collector:
        return jsonify({'error': '热搜模块未加载'}), 500

    try:
        data = collector.fetch_all_hot_searches(finance_only)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
