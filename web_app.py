from flask import Flask, render_template, jsonify, request
import os
import sys
import glob
from datetime import datetime, timedelta
from collections import Counter
import json
from dotenv import load_dotenv

load_dotenv()

sys.path.append('src')
from weekly_summary import WeeklySummary

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

def init_database():
    try:
        from database import init_database as db_init
        db_init()
    except ImportError:
        pass

# Configure Flask to serve the Vue frontend
# static_folder points to the assets directory built by Vite
# template_folder points to the dist directory where index.html is located
app = Flask(__name__, static_folder="frontend/dist/assets", template_folder="frontend/dist")
# Vite builds assets with relative paths like /assets/..., so we need to match that
app.static_url_path = "/assets"

weekly_gen = WeeklySummary()

def get_latest_report():
    """获取最新的小时报告"""
    reports = glob.glob('data/reports/report_*.txt')
    if not reports:
        return None
    latest = max(reports, key=os.path.getctime)
    try:
        with open(latest, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return None

def get_latest_summary():
    """获取最新的每日摘要"""
    summaries = glob.glob('data/summaries/summary_*.txt')
    if not summaries:
        return None
    latest = max(summaries, key=os.path.getctime)
    try:
        with open(latest, 'r', encoding='utf-8') as f:
            return f.read()
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
            mtime = datetime.fromtimestamp(os.path.getctime(report_path))
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
        if score > 0.3:
            return '积极'
        elif score < -0.3:
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
        if score > 0.3:
            return '上涨'
        elif score < -0.3:
            return '下跌'
        else:
            return '震荡'
    
    return {
        'china': {
            'name': 'A股',
            'sentiment': sentiment.get('cn', 0),
            'trend': predict_trend(sentiment.get('cn', 0)),
            'icon': '↑' if sentiment.get('cn', 0) > 0.3 else '↓' if sentiment.get('cn', 0) < -0.3 else '→'
        },
        'us': {
            'name': '美股',
            'sentiment': sentiment.get('us', 0),
            'trend': predict_trend(sentiment.get('us', 0)),
            'icon': '↑' if sentiment.get('us', 0) > 0.3 else '↓' if sentiment.get('us', 0) < -0.3 else '→'
        },
        'global': {
            'name': '全球',
            'sentiment': sentiment.get('overall', 0),
            'trend': predict_trend(sentiment.get('overall', 0)),
            'icon': '↑' if sentiment.get('overall', 0) > 0.3 else '↓' if sentiment.get('overall', 0) < -0.3 else '→'
        }
    }

@app.route('/')
@app.route('/<path:path>')
def index(path=None):
    # Serve the Vue app for the root route and any other route not matched by API
    return render_template('index.html')

# Removed specific route for /overview as it is now handled by Vue Router
# @app.route('/overview')
# def overview():
#     return render_template('overview.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/api/latest')
def api_latest():
    """聚合接口：获取首页所需的所有实时数据"""
    report_content = get_latest_report()
    
    # 获取最新报告的时间戳
    reports = glob.glob('data/reports/report_*.txt')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if reports:
        latest_file = max(reports, key=os.path.getctime)
        mtime = os.path.getctime(latest_file)
        timestamp = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    data = {
        'timestamp': timestamp,
        'stats': {
            'total_news': 0,
            'positive_news': 0,
            'negative_news': 0
        },
        'sentiment': {
            'score': 0,
            'label': 'Neutral',
            'breakdown': {'positive': 0, 'neutral': 0, 'negative': 0}
        },
        'recommendations': {'a_shares': [], 'us_shares': []},
        'market_prediction': [],
        'hot_topics': []
    }

    if report_content:
        parsed = parse_report(report_content)
        
        # 填充统计数据
        data['stats']['total_news'] = parsed.get('total_news', 0)
        # 简单估算正负面新闻数量 based on sentiment
        sentiment_score = parsed.get('sentiment', {}).get('overall', 0)
        data['stats']['positive_news'] = int(data['stats']['total_news'] * (0.5 + sentiment_score/2)) if sentiment_score > 0 else int(data['stats']['total_news'] * 0.3)
        
        # 填充情绪数据
        # 模拟 breakdown 数据，因为 parse_report 目前只返回单一数值
        overall_score = parsed.get('sentiment', {}).get('overall', 0)
        cn_score = parsed.get('sentiment', {}).get('cn', 0)
        us_score = parsed.get('sentiment', {}).get('us', 0)
        
        pos_pct = int(50 + overall_score * 50)
        neg_pct = int(20 - overall_score * 20)
        neu_pct = 100 - pos_pct - neg_pct
        
        data['sentiment'] = {
            'score': overall_score,
            'label': parsed.get('sentiment_label', {}).get('overall', '中性'),
            'breakdown': {
                'cn': cn_score,
                'us': us_score,
                'positive': max(0, pos_pct),
                'neutral': max(0, neu_pct),
                'negative': max(0, neg_pct)
            }
        }
        
        # 填充推荐
        recs = get_stock_recommendations()
        data['recommendations'] = {
            'a_shares': recs.get('a_stocks', []),
            'us_shares': recs.get('us_stocks', [])
        }
        
        # 填充预测
        preds = get_market_prediction()
        data['market_prediction'] = [
            {'name': v['name'], 'icon': v['icon'], 'trend': v['trend'], 'sentiment': f"指数: {v['sentiment']}"}
            for k, v in preds.items()
        ]
        
        # 填充热点
        data['hot_topics'] = parsed.get('hot_topics', [])
        
        # Add raw content for display
        data['content'] = report_content

    return jsonify(data)

@app.route('/api/report/latest')
def api_report_latest():
    """获取最新小时简报内容"""
    content = get_latest_report()
    return jsonify({'content': content if content else ''})

@app.route('/api/summary/latest')
def api_summary_latest():
    """获取最新每日摘要内容"""
    content = get_latest_summary()
    return jsonify({'content': content if content else ''})

@app.route('/api/hourly_report')
def hourly_report():
    """获取最新小时简报的完整内容"""
    # 获取最新报告文件路径
    reports = glob.glob('data/reports/report_*.txt')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    if reports:
        latest_file = max(reports, key=os.path.getctime)
        # 获取文件修改时间
        mtime = os.path.getctime(latest_file)
        timestamp = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    content = get_latest_report()
    if not content:
        return jsonify({
            'content': '暂无数据',
            'timestamp': timestamp
        })
    
    data = parse_report(content)
    data['content'] = content  # 添加原始内容
    data['timestamp'] = timestamp
    return jsonify(data)

@app.route('/api/daily_summary')
def daily_summary():
    content = get_latest_summary()
    if content:
        return jsonify({'content': content})
    return jsonify({'content': '暂无每日摘要'})

@app.route('/api/stock_recommendations')
def stock_recommendations():
    return jsonify(get_stock_recommendations())

@app.route('/api/market_prediction')
def market_prediction():
    return jsonify(get_market_prediction())

@app.route('/api/sentiment')
def sentiment():
    report = get_latest_report()
    data = parse_report(report)
    return jsonify(data.get('sentiment', {}))

@app.route('/api/weekly_analysis')
def weekly_analysis():
    # 优先读取最新的周报JSON文件
    weekly_files = glob.glob('data/weekly/analysis_*.json')
    if weekly_files:
        latest = max(weekly_files, key=os.path.getctime)
        try:
            with open(latest, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except:
            pass
    
    # 如果没有JSON文件，则生成分析
    return jsonify(analyze_weekly_stocks())


@app.route('/api/report/structured')
def api_report_structured():
    """获取结构化报告数据（供前端可视化）"""
    lang = request.args.get('lang', 'zh')  # 支持 'zh' 或 'en'
    translator = get_translator()
    
    # 优先从 reports_json 目录读取
    json_reports = glob.glob('data/reports_json/report_*.json')
    if json_reports:
        latest = max(json_reports, key=os.path.getctime)
        try:
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify(translator['translate_report_data'](data, lang))
        except:
            pass
    
    # 回退：解析最新的文本报告
    report_content = get_latest_report()
    if not report_content:
        return jsonify({
            'meta': {'total_news': 0, 'generated_at': datetime.now().isoformat()},
            'sentiment': {
                'overall': {'score': 0, 'label': '中性' if lang == 'zh' else 'Neutral'},
                'cn': {'score': 0, 'label': '中性' if lang == 'zh' else 'Neutral'},
                'us': {'score': 0, 'label': '中性' if lang == 'zh' else 'Neutral'},
                'distribution': {'positive': 0, 'neutral': 0, 'negative': 0}
            },
            'entities': [],
            'events': {'high_impact': [], 'hot_search': [], 'stock_specific': [], 'other': []},
            'stock_impacts': [],
            'news_list': []
        })
    
    # 解析文本报告为结构化数据
    parsed = parse_report(report_content)
    
    # 构建结构化响应
    sentiment_overall = parsed.get('sentiment', {}).get('overall', 0)
    sentiment_cn = parsed.get('sentiment', {}).get('cn', 0)
    sentiment_us = parsed.get('sentiment', {}).get('us', 0)
    
    def get_label(score):
        if lang == 'en':
            if score > 0.3: return 'Positive'
            if score < -0.3: return 'Negative'
            return 'Neutral'
        else:
            if score > 0.3: return '积极'
            if score < -0.3: return '消极'
            return '中性'
    
    # 获取时间戳
    reports = glob.glob('data/reports/report_*.txt')
    timestamp = datetime.now().isoformat()
    if reports:
        latest_file = max(reports, key=os.path.getctime)
        mtime = os.path.getctime(latest_file)
        timestamp = datetime.fromtimestamp(mtime).isoformat()
    
    now = datetime.now()
    beijing_hour = now.hour
    ny_hour = (beijing_hour - 13) % 24
    
    # 翻译实体名称（如果是英文模式）
    entities = parsed.get('hot_topics', [])[:10]
    if lang == 'en':
        entities = [translator['translate_response'](e, lang) for e in entities]
    
    # 翻译事件
    events_data = []
    for i, e in enumerate(parsed.get('major_events', [])):
        event = {
            'ref_id': i + 1,
            'title': e.get('title', ''),
            'summary': e.get('summary', ''),
            'source': e.get('source', ''),
            'url': '',
            'event_type': 'Major Event' if lang == 'en' else '重大事件',
            'sentiment': {'overall': 0, 'cn': 0, 'us': 0},
            'stock_impact': []
        }
        if lang == 'en':
            event['title'] = translator['translate_response'](event['title'], lang)
            event['summary'] = translator['translate_response'](event['summary'], lang)
        events_data.append(event)
    
    # 翻译股票影响
    def get_prediction(direction):
        if lang == 'en':
            if direction == '上涨': return 'Bullish'
            if direction == '下跌': return 'Bearish'
            return 'Neutral'
        else:
            if direction == '上涨': return '看涨'
            if direction == '下跌': return '看跌'
            return '中性'
    
    stock_impacts = []
    for s in parsed.get('stocks', [])[:6]:
        stock = {
            'symbol': s.get('symbol', ''),
            'name': s.get('name', ''),
            'prediction': get_prediction(s.get('direction', '')),
            'confidence': 0.6,
            'total_mentions': 1,
            'up_count': 1 if s.get('direction') == '上涨' else 0,
            'down_count': 1 if s.get('direction') == '下跌' else 0,
            'neutral_count': 0
        }
        if lang == 'en':
            stock['name'] = translator['translate_response'](stock['name'], lang)
        stock_impacts.append(stock)
    
    return jsonify({
        'meta': {
            'generated_at': timestamp,
            'beijing_time': f'{beijing_hour:02d}:00',
            'newyork_time': f'{ny_hour:02d}:00',
            'total_news': parsed.get('total_news', 0),
            'report_type': 'hourly'
        },
        'sentiment': {
            'overall': {'score': round(sentiment_overall, 2), 'label': get_label(sentiment_overall)},
            'cn': {'score': round(sentiment_cn, 2), 'label': get_label(sentiment_cn)},
            'us': {'score': round(sentiment_us, 2), 'label': get_label(sentiment_us)},
            'distribution': {
                'positive': int(parsed.get('total_news', 0) * 0.4),
                'neutral': int(parsed.get('total_news', 0) * 0.4),
                'negative': int(parsed.get('total_news', 0) * 0.2)
            }
        },
        'entities': [{'name': e, 'count': 1, 'avg_sentiment': 0} for e in entities],
        'events': {
            'high_impact': events_data,
            'hot_search': [],
            'stock_specific': [],
            'other': []
        },
        'stock_impacts': stock_impacts,
        'news_list': []
    })


# ============== 新增API接口 ==============

@app.route('/api/reports/history')
def api_reports_history():
    """获取历史报告列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    report_type = request.args.get('type', 'all')  # all, hourly, daily, weekly
    lang = request.args.get('lang', 'zh')
    
    reports = []
    
    # 获取小时报告
    if report_type in ['all', 'hourly']:
        hourly_files = glob.glob('data/reports/report_*.txt')
        for f in hourly_files:
            mtime = os.path.getctime(f)
            reports.append({
                'id': os.path.basename(f).replace('report_', '').replace('.txt', ''),
                'type': 'hourly',
                'title': 'Hourly Brief' if lang == 'en' else '每小时简报',
                'timestamp': datetime.fromtimestamp(mtime).isoformat(),
                'file_path': f
            })
    
    # 获取每日摘要
    if report_type in ['all', 'daily']:
        daily_files = glob.glob('data/summaries/summary_*.txt')
        for f in daily_files:
            mtime = os.path.getctime(f)
            reports.append({
                'id': os.path.basename(f).replace('summary_', '').replace('.txt', ''),
                'type': 'daily',
                'title': 'Daily Summary' if lang == 'en' else '每日摘要',
                'timestamp': datetime.fromtimestamp(mtime).isoformat(),
                'file_path': f
            })
    
    # 获取周报
    if report_type in ['all', 'weekly']:
        weekly_files = glob.glob('data/weekly/analysis_*.json')
        for f in weekly_files:
            mtime = os.path.getctime(f)
            reports.append({
                'id': os.path.basename(f).replace('analysis_', '').replace('.json', ''),
                'type': 'weekly',
                'title': 'Weekly Analysis' if lang == 'en' else '周度分析',
                'timestamp': datetime.fromtimestamp(mtime).isoformat(),
                'file_path': f
            })
    
    # 按时间排序
    reports.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # 分页
    total = len(reports)
    start = (page - 1) * per_page
    end = start + per_page
    
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
        'data': reports[start:end]
    })


@app.route('/api/reports/<report_id>')
def api_report_detail(report_id):
    """获取指定报告详情"""
    report_type = request.args.get('type', 'hourly')
    
    if report_type == 'hourly':
        filepath = f'data/reports/report_{report_id}.txt'
    elif report_type == 'daily':
        filepath = f'data/summaries/summary_{report_id}.txt'
    elif report_type == 'weekly':
        filepath = f'data/weekly/analysis_{report_id}.json'
    else:
        return jsonify({'error': '无效的报告类型'}), 400
    
    if not os.path.exists(filepath):
        return jsonify({'error': '报告不存在'}), 404
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            if filepath.endswith('.json'):
                data = json.load(f)
                return jsonify(data)
            else:
                content = f.read()
                parsed = parse_report(content) if report_type == 'hourly' else {}
                return jsonify({
                    'content': content,
                    'parsed': parsed,
                    'timestamp': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/hot-searches')
def api_hot_searches():
    """获取实时热搜"""
    platform = request.args.get('platform', None)  # weibo, toutiao, zhihu, baidu, douyin
    finance_only = request.args.get('finance_only', 'true').lower() == 'true'
    
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
                return jsonify({'platform': platform, 'data': data})
            else:
                return jsonify({'error': '无效的平台'}), 400
        else:
            # 获取聚合热搜
            data = collector.get_aggregated_finance_hot(30)
            return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/hot-searches/all')
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


@app.route('/api/stocks/search')
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


@app.route('/api/stocks/<symbol>/quote')
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


@app.route('/api/stocks/<symbol>/news')
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


@app.route('/api/stocks/<symbol>/announcements')
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


@app.route('/api/stocks/<symbol>/kline')
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


@app.route('/api/stocks/<symbol>/detail')
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


@app.route('/api/watchlist', methods=['GET'])
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


@app.route('/api/watchlist', methods=['POST'])
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


@app.route('/api/watchlist/<symbol>', methods=['DELETE'])
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


@app.route('/api/crypto/market')
def api_crypto_market():
    """获取加密货币市场数据"""
    symbols = request.args.get('symbols', 'BTC,ETH,SOL,DOGE,XRP')
    symbols_list = [s.strip().upper() for s in symbols.split(',')]
    
    collector = get_crypto_collector()
    if not collector:
        return jsonify({'error': '加密货币模块未加载'}), 500
    
    try:
        data = collector.get_market_data(symbols_list)
        # 直接返回列表格式，便于前端处理
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/crypto/global')
def api_crypto_global():
    """获取加密货币全球市场数据"""
    collector = get_crypto_collector()
    if not collector:
        return jsonify({'error': '加密货币模块未加载'}), 500
    
    try:
        data = collector.get_global_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/crypto/trending')
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


@app.route('/api/crypto/fear-greed')
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


@app.route('/api/crypto/<coin_id>')
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


@app.route('/api/realtime')
def api_realtime():
    """获取实时快讯"""
    collector = get_realtime_collector()
    if not collector:
        return jsonify({'error': '实时采集模块未加载'}), 500
    
    try:
        data = collector.fetch_all_realtime()
        return jsonify({'data': data, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/report')
def api_backtest_report():
    """获取回测报告"""
    backtester = get_backtester()
    if not backtester:
        return jsonify({'error': '回测模块未加载'}), 500
    
    try:
        report = backtester.generate_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/strategy')
def api_backtest_strategy():
    """回测情绪策略"""
    backtester = get_backtester()
    if not backtester:
        return jsonify({'error': '回测模块未加载'}), 500
    
    try:
        result = backtester.backtest_sentiment_strategy([])
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 初始化数据库
    init_database()
    
    # 生产环境配置
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    app.run(
        # debug=args.debug,
        debug=True,
        host='127.0.0.1',  # 只监听本地，通过Nginx代理
        port=5000,
        threaded=True
    )
