"""
Stock routes blueprint - stock search, quotes, news, watchlist.
"""
import logging

from flask import Blueprint, jsonify, request

from web.helpers import get_stock_tracker, get_translator

logger = logging.getLogger('web_app')

stock_bp = Blueprint('stock', __name__)


@stock_bp.route('/api/stocks/search')
def api_stock_search():
    """搜索股票"""
    keyword = request.args.get('q', '')
    if not keyword:
        return jsonify({'error': '请提供搜索关键词'}), 400

    tracker = get_stock_tracker()
    if not tracker:
        return jsonify({'error': '股票模块未加载'}), 500

    try:
        results = tracker.search_stocks(keyword)
        return jsonify({'data': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_bp.route('/api/stocks/<symbol>/quote')
def api_stock_quote(symbol):
    """获取股票实时行情"""
    tracker = get_stock_tracker()
    if not tracker:
        return jsonify({'error': '股票模块未加载'}), 500

    try:
        quote = tracker.get_stock_quote(symbol)
        if quote:
            return jsonify(quote)
        return jsonify({'error': '获取行情失败'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_bp.route('/api/stocks/<symbol>/news')
def api_stock_news(symbol):
    """获取个股相关新闻"""
    name = request.args.get('name', '')
    limit = request.args.get('limit', 20, type=int)

    tracker = get_stock_tracker()
    if not tracker:
        return jsonify({'error': '股票模块未加载'}), 500

    try:
        news = tracker.get_stock_news(symbol, name, limit)
        return jsonify({'data': news})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_bp.route('/api/stocks/<symbol>/announcements')
def api_stock_announcements(symbol):
    """获取公司公告"""
    limit = request.args.get('limit', 10, type=int)

    tracker = get_stock_tracker()
    if not tracker:
        return jsonify({'error': '股票模块未加载'}), 500

    try:
        announcements = tracker.get_company_announcements(symbol, limit)
        return jsonify({'data': announcements})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_bp.route('/api/stocks/<symbol>/kline')
def api_stock_kline(symbol):
    """获取股票K线数据"""
    period = request.args.get('period', 'daily')  # daily/weekly/monthly
    limit = request.args.get('limit', 60, type=int)

    tracker = get_stock_tracker()
    if not tracker:
        return jsonify({'error': '股票模块未加载'}), 500

    try:
        kline = tracker.get_stock_kline(symbol, period, limit)
        return jsonify({'data': kline})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_bp.route('/api/stocks/<symbol>/detail')
def api_stock_detail(symbol):
    """获取股票详细信息（行情+K线+新闻）"""
    tracker = get_stock_tracker()
    if not tracker:
        return jsonify({'error': '股票模块未加载'}), 500

    try:
        detail = tracker.get_stock_detail(symbol)
        return jsonify(detail)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_bp.route('/api/watchlist', methods=['GET'])
def api_get_watchlist():
    """获取自选股列表"""
    category = request.args.get('category', None)  # stock, crypto
    lang = request.args.get('lang', 'zh')
    translator = get_translator()
    translate_text = translator['translate_text']

    try:
        from database import get_watchlist
        watchlist = get_watchlist(category)

        # 如果有股票追踪器，获取实时行情
        tracker = get_stock_tracker()
        if tracker and watchlist:
            for item in watchlist:
                if item.get('category') == 'stock':
                    quote = tracker.get_stock_quote(item['symbol'])
                    if quote:
                        item['quote'] = quote
                        # 翻译 quote 中的股票名称
                        if lang == 'en' and quote.get('name'):
                            item['quote']['name'] = translate_text(quote['name'], lang)
                # 翻译股票名称
                if lang == 'en' and item.get('name'):
                    item['name'] = translate_text(item['name'], lang)

        return jsonify({'data': watchlist})
    except ImportError:
        return jsonify({'error': 'Database module not loaded' if lang == 'en' else '数据库模块未加载'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_bp.route('/api/watchlist', methods=['POST'])
def api_add_watchlist():
    """添加自选股"""
    data = request.get_json()
    if not data or not data.get('symbol'):
        return jsonify({'error': '请提供股票代码'}), 400

    try:
        from database import add_to_watchlist
        success = add_to_watchlist(
            symbol=data['symbol'],
            name=data.get('name'),
            market=data.get('market'),
            category=data.get('category', 'stock')
        )
        if success:
            return jsonify({'message': '添加成功'})
        return jsonify({'error': '添加失败'}), 500
    except ImportError:
        return jsonify({'error': '数据库模块未加载'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@stock_bp.route('/api/watchlist/<symbol>', methods=['DELETE'])
def api_remove_watchlist(symbol):
    """移除自选股"""
    try:
        from database import remove_from_watchlist
        success = remove_from_watchlist(symbol)
        if success:
            return jsonify({'message': '移除成功'})
        return jsonify({'error': '移除失败'}), 404
    except ImportError:
        return jsonify({'error': '数据库模块未加载'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
