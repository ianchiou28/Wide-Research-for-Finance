"""
Shared helper functions extracted from web_app.py.
All route blueprints import from here.
"""
import os
import sys
import re
import glob
import json
import logging
from datetime import datetime, timedelta
from collections import Counter
from functools import wraps

from flask import request, jsonify

sys.path.append('src')
from weekly_summary import WeeklySummary
from cache import cache

logger = logging.getLogger('web_app')


def parse_timestamp_from_filename(filepath):
    """从文件名中解析时间戳，如 report_20251128_001110.txt -> datetime
    文件名格式: *_YYYYMMDD_HHMMSS.*
    比 os.path.getctime 可靠，因为 Docker 部署后 ctime 会变成部署时间
    """
    basename = os.path.basename(filepath)
    match = re.search(r'(\d{8})_(\d{6})', basename)
    if match:
        try:
            return datetime.strptime(f"{match.group(1)}_{match.group(2)}", '%Y%m%d_%H%M%S')
        except ValueError:
            pass
    # fallback to ctime
    return datetime.fromtimestamp(os.path.getctime(filepath))

# Module-level instance used by analyze_weekly_stocks
weekly_gen = WeeklySummary()


# ============== 安全工具 ==============
def safe_filename(filename: str) -> str:
    """防止路径遍历攻击，只允许安全的文件名"""
    if not filename:
        return None
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        return None
    # 不允许 .. 路径遍历
    if '..' in filename:
        return None
    return filename


def require_api_key(f):
    """管理操作需要 API Key 认证"""
    @wraps(f)
    def decorated(*args, **kwargs):
        admin_key = os.getenv('ADMIN_API_KEY', '')
        if not admin_key:
            # 未配置API Key时跳过认证（向后兼容）
            return f(*args, **kwargs)
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if api_key != admin_key:
            logger.warning(f"Unauthorized API access attempt from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


# 导入翻译服务
def get_translator():
    try:
        from translator import translate_response, translate_report_data, translate_stock_data, translate_text
        return {
            'translate_response': translate_response,
            'translate_report_data': translate_report_data,
            'translate_stock_data': translate_stock_data,
            'translate_text': translate_text
        }
    except ImportError as e:
        print(f"Warning: Could not import translator: {e}")
        # 返回空操作函数
        return {
            'translate_response': lambda data, lang: data,
            'translate_report_data': lambda data, lang: data,
            'translate_stock_data': lambda data, lang: data,
            'translate_text': lambda text, lang: text
        }


# 导入新模块（延迟加载以避免启动错误）
def get_hot_search_collector():
    try:
        from hot_search import HotSearchCollector
        return HotSearchCollector()
    except ImportError:
        return None


def get_stock_tracker():
    try:
        from stock_tracker import StockTracker
        return StockTracker()
    except ImportError:
        return None


def get_crypto_collector():
    try:
        from crypto_collector import CryptoCollector
        return CryptoCollector()
    except ImportError:
        return None


def get_realtime_collector():
    try:
        from realtime_collector import RealtimeCollector
        return RealtimeCollector()
    except ImportError:
        return None


def get_backtester():
    try:
        from backtester import NewsBacktester
        return NewsBacktester()
    except ImportError:
        return None


def get_report_generator_v2():
    try:
        from report_generator_v2 import ReportGeneratorV2
        return ReportGeneratorV2()
    except ImportError:
        return None


def get_monthly_analyzer():
    try:
        from monthly_analysis import MonthlyAnalysis
        return MonthlyAnalysis()
    except ImportError:
        return None


def init_database():
    try:
        from database import init_database as db_init
        db_init()
    except ImportError:
        pass


def get_latest_report():
    """获取最新的小时报告（带缓存）"""
    cached = cache.get('latest_report', ttl_seconds=300)
    if cached is not None:
        return cached
    reports = glob.glob('data/reports/report_*.txt')
    if not reports:
        return None
    latest = max(reports, key=lambda f: parse_timestamp_from_filename(f))
    try:
        with open(latest, 'r', encoding='utf-8') as f:
            content = f.read()
            cache.set('latest_report', content)
            return content
    except:
        return None


def get_latest_summary():
    """获取最新的每日摘要（带缓存）"""
    cached = cache.get('latest_summary', ttl_seconds=300)
    if cached is not None:
        return cached
    summaries = glob.glob('data/summaries/summary_*.txt')
    if not summaries:
        return None
    latest = max(summaries, key=lambda f: parse_timestamp_from_filename(f))
    try:
        with open(latest, 'r', encoding='utf-8') as f:
            content = f.read()
            cache.set('latest_summary', content)
            return content
    except:
        return None


def get_weekly_reports():
    """获取过去7天的报告"""
    reports = glob.glob('data/reports/report_*.txt')
    if not reports:
        return []

    now = datetime.now()
    week_ago = now - timedelta(days=7)
    weekly = []

    for report_path in reports:
        try:
            mtime = parse_timestamp_from_filename(report_path)
            if mtime >= week_ago:
                with open(report_path, 'r', encoding='utf-8') as f:
                    weekly.append(f.read())
        except:
            pass

    return weekly


def parse_report(content):
    """解析报告内容"""
    if not content:
        return {}

    lines = content.split('\n')
    data = {
        'title': '',
        'sentiment': {'overall': 0, 'cn': 0, 'us': 0},
        'sentiment_label': {'overall': '中性', 'cn': '中性', 'us': '中性'},
        'hot_topics': [],
        'major_events': [],
        'stocks': [],
        'total_news': 0
    }

    # 解析标题
    for line in lines:
        if '财经新闻每小时简报' in line:
            data['title'] = line.strip()
            break

    # 解析新闻数量
    for line in lines:
        if '共分析' in line and '条新闻' in line:
            try:
                data['total_news'] = int(line.split('共分析')[1].split('条')[0].strip())
            except:
                pass

    # 解析情绪
    def get_sentiment_label(score):
        if score > 0.15:
            return '积极'
        elif score < -0.15:
            return '消极'
        return '中性'

    for i, line in enumerate(lines):
        if '整体情绪' in line:
            try:
                score = float(line.split('指数:')[1].split(')')[0].strip())
                data['sentiment']['overall'] = score
                data['sentiment_label']['overall'] = get_sentiment_label(score)
            except:
                pass
        if '中国市场' in line:
            try:
                score = float(line.split('指数:')[1].split(')')[0].strip())
                data['sentiment']['cn'] = score
                data['sentiment_label']['cn'] = get_sentiment_label(score)
            except:
                pass
        if '美国市场' in line:
            try:
                score = float(line.split('指数:')[1].split(')')[0].strip())
                data['sentiment']['us'] = score
                data['sentiment_label']['us'] = get_sentiment_label(score)
            except:
                pass

    # 解析热点
    in_hot = False
    for line in lines:
        if '【热点追踪】' in line:
            in_hot = True
            continue
        if in_hot and line.strip().startswith('•'):
            topic = line.strip().replace('•', '').strip()
            data['hot_topics'].append(topic)
        if in_hot and '【重大事件' in line:
            break

    # 解析重大事件
    if '【重大事件提醒】' in content:
        # 使用 split 获取 【重大事件提醒】 和 【其他新闻】 之间的内容
        # 如果 【其他新闻】 不存在，则取到文件末尾
        try:
            events_section = content.split('【重大事件提醒】')[1].split('【其他新闻')[0]

            event_lines = events_section.strip().split('\n')
            current_event = {}

            for line in event_lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith('[') and ']' in line:
                    # 当遇到新的 source，保存上一个事件
                    if current_event:
                        data['major_events'].append(current_event)
                    current_event = {'source': line.split(']')[0][1:].strip()}
                elif line.startswith('标题:'):
                    current_event['title'] = line.replace('标题:', '').strip()
                elif line.startswith('摘要:'):
                    current_event['summary'] = line.replace('摘要:', '').strip()
                elif line.startswith('情绪:'):
                    sentiment_line = line.replace('情绪:', '').strip()
                    parts = [p.strip() for p in sentiment_line.split('|')]
                    current_event['sentiment_overall'] = parts[0] if len(parts) > 0 else '中性'
                    current_event['sentiment_cn'] = parts[1].replace('中国:', '') if len(parts) > 1 else '中性'
                    current_event['sentiment_us'] = parts[2].replace('美国:', '') if len(parts) > 2 else '中性'
                elif line.startswith('链接:'):
                    url = line.replace('链接:', '').strip()
                    if url.startswith('http'):
                        current_event['url'] = url

            # 添加最后一个事件
            if current_event and 'title' in current_event:
                 data['major_events'].append(current_event)
        except IndexError:
            pass # Section not found

    # 解析股票影响
    for i, line in enumerate(lines):
        if '股票影响:' in line:
            stocks_str = line.split('股票影响:')[1].strip()
            for stock in stocks_str.split('|'):
                stock = stock.strip()
                if '(' in stock and ')' in stock:
                    symbol = stock.split('(')[0].strip()
                    name = stock.split('(')[1].split(')')[0]
                    direction = '上涨' if '↑' in stock else '下跌' if '↓' in stock else '中性'
                    data['stocks'].append({
                        'symbol': symbol,
                        'name': name,
                        'direction': direction
                    })

    return data


def analyze_weekly_stocks():
    """分析一周数据，预测个股涨跌"""
    reports = get_weekly_reports()
    if not reports:
        return {'stocks': [], 'summary': '数据不足'}

    # 解析所有报告
    parsed_reports = [parse_report(r) for r in reports]

    # 使用WeeklySummary生成分析
    try:
        analysis = weekly_gen.generate(parsed_reports)
        weekly_gen.save_analysis(analysis)
        return analysis
    except Exception as e:
        print(f"生成周报分析失败: {e}")
        return {'stocks': [], 'summary': '分析失败'}


def get_stock_recommendations():
    """获取股票推荐"""
    report = get_latest_report()
    if not report:
        return {'a_stocks': [], 'us_stocks': []}

    data = parse_report(report)
    stocks = data.get('stocks', [])

    # 分类A股和美股
    a_stocks = []
    us_stocks = []

    for stock in stocks:
        if stock['direction'] == '上涨':
            # 简单判断：数字开头的是A股代码
            if stock['symbol'].isdigit():
                a_stocks.append(stock)
            else:
                us_stocks.append(stock)

    return {
        'a_stocks': a_stocks[:5],
        'us_stocks': us_stocks[:5]
    }


def get_market_prediction():
    """获取大盘走势预测"""
    report = get_latest_report()
    if not report:
        return {}

    data = parse_report(report)
    sentiment = data.get('sentiment', {})

    def predict_trend(score):
        if score > 0.15:
            return '上涨'
        elif score < -0.15:
            return '下跌'
        else:
            return '震荡'

    return {
        'china': {
            'name': 'A股',
            'sentiment': sentiment.get('cn', 0),
            'trend': predict_trend(sentiment.get('cn', 0)),
            'icon': '↑' if sentiment.get('cn', 0) > 0.15 else '↓' if sentiment.get('cn', 0) < -0.15 else '→'
        },
        'us': {
            'name': '美股',
            'sentiment': sentiment.get('us', 0),
            'trend': predict_trend(sentiment.get('us', 0)),
            'icon': '↑' if sentiment.get('us', 0) > 0.15 else '↓' if sentiment.get('us', 0) < -0.15 else '→'
        },
        'global': {
            'name': '全球',
            'sentiment': sentiment.get('overall', 0),
            'trend': predict_trend(sentiment.get('overall', 0)),
            'icon': '↑' if sentiment.get('overall', 0) > 0.15 else '↓' if sentiment.get('overall', 0) < -0.15 else '→'
        }
    }
