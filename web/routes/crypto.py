"""
Crypto routes blueprint - cryptocurrency market data.
"""
import logging

from flask import Blueprint, jsonify, request

from web.helpers import get_crypto_collector

logger = logging.getLogger('web_app')

crypto_bp = Blueprint('crypto', __name__)


@crypto_bp.route('/api/crypto/market')
def api_crypto_market():
    """获取加密货币市场数据"""
    symbols = request.args.get('symbols', 'BTC,ETH,SOL,DOGE,XRP')
    symbols_list = [s.strip().upper() for s in symbols.split(',')]

    collector = get_crypto_collector()
    if not collector:
        return jsonify({'error': '加密货币模块未加载'}), 500

    try:
        print(f"[Crypto API] 请求市场数据: {symbols_list}")
        data = collector.get_market_data(symbols_list)
        print(f"[Crypto API] 返回 {len(data)} 条数据")

        if not data:
            print("[Crypto API] 警告：所有数据源均未返回数据，请检查网络或配置代理")
            return jsonify({
                'error': '暂无数据',
                'message': '所有加密货币数据源均不可达，请检查网络连接或配置代理',
                'data': []
            }), 200

        # 添加数据源标识到响应头
        response = jsonify(data)
        response.headers['X-Data-Source'] = 'domestic-apis'
        return response
    except Exception as e:
        print(f"[Crypto API] 错误: {e}")
        return jsonify({'error': str(e), 'data': []}), 500


@crypto_bp.route('/api/crypto/global')
def api_crypto_global():
    """获取加密货币全球市场数据"""
    collector = get_crypto_collector()
    if not collector:
        return jsonify({'error': '加密货币模块未加载'}), 500

    try:
        print("[Crypto API] 请求全局市场数据")
        data = collector.get_global_data()
        print(f"[Crypto API] 全局数据返回: {bool(data)}")

        if not data or not data.get('total_market_cap'):
            print("[Crypto API] 警告：全局数据为空，所有数据源均不可达")
            return jsonify({
                'error': '暂无数据',
                'message': '无法获取全球市场数据，请检查网络连接或配置代理',
                'data': {}
            }), 200

        response = jsonify(data)
        response.headers['X-Data-Source'] = 'domestic-apis'
        return response
    except Exception as e:
        print(f"[Crypto API] 错误: {e}")
        return jsonify({'error': str(e), 'data': {}}), 500


@crypto_bp.route('/api/crypto/trending')
def api_crypto_trending():
    """获取热门加密货币"""
    collector = get_crypto_collector()
    if not collector:
        return jsonify({'error': '加密货币模块未加载'}), 500

    try:
        data = collector.get_trending()
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@crypto_bp.route('/api/crypto/fear-greed')
def api_crypto_fear_greed():
    """获取恐惧贪婪指数"""
    collector = get_crypto_collector()
    if not collector:
        return jsonify({'error': '加密货币模块未加载'}), 500

    try:
        data = collector.get_fear_greed_index()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@crypto_bp.route('/api/crypto/<coin_id>')
def api_crypto_detail(coin_id):
    """获取单个币种详情"""
    collector = get_crypto_collector()
    if not collector:
        return jsonify({'error': '加密货币模块未加载'}), 500

    try:
        data = collector.get_coin_details(coin_id)
        if data:
            return jsonify(data)
        return jsonify({'error': '获取详情失败'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
