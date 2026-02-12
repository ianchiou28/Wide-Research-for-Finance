"""
Report routes blueprint - handles report viewing, structured data, and history.
"""
import os
import glob
import json
import logging
from datetime import datetime

from flask import Blueprint, render_template, jsonify, request

from cache import cache
from web.helpers import (
    safe_filename,
    get_translator,
    get_latest_report,
    get_latest_summary,
    get_stock_recommendations,
    get_market_prediction,
    parse_report,
    analyze_weekly_stocks,
    parse_timestamp_from_filename,
)

logger = logging.getLogger('web_app')

report_bp = Blueprint('report', __name__)


@report_bp.route('/')
@report_bp.route('/<path:path>')
def index(path=None):
    # Serve the Vue app for the root route and any other route not matched by API
    return render_template('index.html')


@report_bp.route('/test')
def test():
    return render_template('test.html')


@report_bp.route('/api/latest')
def api_latest():
    """聚合接口：获取首页所需的所有实时数据（5分钟缓存）"""
    cached = cache.get('api_latest', ttl_seconds=300)
    if cached is not None:
        return jsonify(cached)

    report_content = get_latest_report()

    # 获取最新报告的时间戳
    reports = glob.glob('data/reports/report_*.txt')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if reports:
        latest_file = max(reports, key=lambda f: parse_timestamp_from_filename(f))
        timestamp = parse_timestamp_from_filename(latest_file).strftime('%Y-%m-%d %H:%M:%S')

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

    cache.set('api_latest', data)
    return jsonify(data)


@report_bp.route('/api/report/latest')
def api_report_latest():
    """获取最新小时简报内容"""
    content = get_latest_report()
    return jsonify({'content': content if content else ''})


@report_bp.route('/api/summary/latest')
def api_summary_latest():
    """获取最新每日摘要内容"""
    content = get_latest_summary()
    return jsonify({'content': content if content else ''})


@report_bp.route('/api/hourly_report')
def hourly_report():
    """获取最新小时简报的完整内容"""
    # 获取最新报告文件路径
    reports = glob.glob('data/reports/report_*.txt')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    if reports:
        latest_file = max(reports, key=lambda f: parse_timestamp_from_filename(f))
        # 从文件名解析时间
        timestamp = parse_timestamp_from_filename(latest_file).strftime('%Y-%m-%d %H:%M:%S')

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


@report_bp.route('/api/daily_summary')
def daily_summary():
    # 获取所有摘要文件列表
    summary_files = glob.glob('data/summaries/summary_*.txt')
    summary_files.sort(key=lambda f: parse_timestamp_from_filename(f), reverse=True)

    # 如果请求特定文件
    requested_file = request.args.get('file')
    if requested_file:
        requested_file = safe_filename(requested_file)
        if not requested_file:
            return jsonify({'content': '无效的文件名', 'error': True}), 400
        file_path = f'data/summaries/{requested_file}'
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return jsonify({'content': content, 'file': requested_file})
            except Exception as e:
                logger.error(f"读取摘要文件失败: {e}")
        return jsonify({'content': '无法读取文件', 'error': True})

    # 返回文件列表和最新内容
    file_names = [os.path.basename(f) for f in summary_files]
    content = get_latest_summary()
    return jsonify({
        'files': file_names,
        'content': content if content else '暂无每日摘要',
        'latest': file_names[0] if file_names else None
    })


@report_bp.route('/api/stock_recommendations')
def stock_recommendations():
    return jsonify(get_stock_recommendations())


@report_bp.route('/api/market_prediction')
def market_prediction():
    return jsonify(get_market_prediction())


@report_bp.route('/api/sentiment')
def sentiment():
    report = get_latest_report()
    data = parse_report(report)
    return jsonify(data.get('sentiment', {}))


@report_bp.route('/api/weekly_analysis')
def weekly_analysis():
    # 获取所有周报文件列表
    weekly_files = glob.glob('data/weekly/analysis_*.json')
    weekly_files.sort(key=lambda f: parse_timestamp_from_filename(f), reverse=True)

    # 如果请求特定文件
    requested_file = request.args.get('file')
    if requested_file:
        requested_file = safe_filename(requested_file)
        if not requested_file:
            return jsonify({'error': True, 'message': '无效的文件名'}), 400
        file_path = f'data/weekly/{requested_file}'
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['file'] = requested_file
                    return jsonify(data)
            except Exception as e:
                logger.error(f"读取周报文件失败: {e}")
        return jsonify({'error': True, 'message': '无法读取文件'})

    # 返回文件列表
    file_names = [os.path.basename(f) for f in weekly_files]

    # 获取最新的周报数据
    if weekly_files:
        latest = weekly_files[0]
        try:
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['files'] = file_names
                data['latest'] = file_names[0] if file_names else None
                return jsonify(data)
        except:
            pass

    # 如果没有JSON文件，则生成分析
    result = analyze_weekly_stocks()
    result['files'] = file_names
    return jsonify(result)


@report_bp.route('/api/report/structured')
def api_report_structured():
    """获取结构化报告数据（供前端可视化）"""
    lang = request.args.get('lang', 'zh')  # 支持 'zh' 或 'en'
    translator = get_translator()

    # 优先从 reports_json 目录读取
    json_reports = glob.glob('data/reports_json/report_*.json')
    if json_reports:
        latest = max(json_reports, key=lambda f: parse_timestamp_from_filename(f))
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
            if score > 0.15: return 'Positive'
            if score < -0.15: return 'Negative'
            return 'Neutral'
        else:
            if score > 0.15: return '积极'
            if score < -0.15: return '消极'
            return '中性'

    # 获取时间戳
    reports = glob.glob('data/reports/report_*.txt')
    timestamp = datetime.now().isoformat()
    if reports:
        latest_file = max(reports, key=lambda f: parse_timestamp_from_filename(f))
        timestamp = parse_timestamp_from_filename(latest_file).isoformat()

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
            'url': e.get('url', ''),
            'event_type': 'Major Event' if lang == 'en' else '重大事件',
            'sentiment': {'overall': 0, 'cn': 0, 'us': 0},
            'stock_impact': []
        }
        if lang == 'en':
            event['title'] = translator['translate_response'](event['title'], lang)
            event['summary'] = translator['translate_response'](event['summary'], lang)
        events_data.append(event)

    # 翻译股票影响
    def get_prediction(direction, impact=''):
        """从direction或impact字段推断预测方向"""
        # 优先用 direction
        if direction in ('上涨',):
            return 'Bullish' if lang == 'en' else '看涨'
        if direction in ('下跌',):
            return 'Bearish' if lang == 'en' else '看跌'
        # 回退到 impact
        if impact in ('利好', '正面'):
            return 'Bullish' if lang == 'en' else '看涨'
        if impact in ('利空', '负面'):
            return 'Bearish' if lang == 'en' else '看跌'
        return 'Neutral' if lang == 'en' else '中性'

    stock_impacts = []
    for s in parsed.get('stocks', [])[:6]:
        direction = s.get('direction', '')
        impact = s.get('impact', '')
        prediction = get_prediction(direction, impact)
        
        is_up = prediction in ('看涨', 'Bullish')
        is_down = prediction in ('看跌', 'Bearish')
        
        stock = {
            'symbol': s.get('symbol', ''),
            'name': s.get('name', ''),
            'prediction': prediction,
            'confidence': 0.75 if is_up or is_down else 0.5,
            'total_mentions': 1,
            'up_count': 1 if is_up else 0,
            'down_count': 1 if is_down else 0,
            'neutral_count': 0 if (is_up or is_down) else 1
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
                'positive': sum(1 for e in parsed.get('major_events', []) if e.get('sentiment_overall', '') == '积极') or max(1, int(parsed.get('total_news', 0) * 0.3)),
                'neutral': max(0, parsed.get('total_news', 0) - max(1, int(parsed.get('total_news', 0) * 0.3)) - max(1, int(parsed.get('total_news', 0) * 0.2))),
                'negative': sum(1 for e in parsed.get('major_events', []) if e.get('sentiment_overall', '') == '消极') or max(1, int(parsed.get('total_news', 0) * 0.2))
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

@report_bp.route('/api/reports/history')
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
            ts = parse_timestamp_from_filename(f)
            reports.append({
                'id': os.path.basename(f).replace('report_', '').replace('.txt', ''),
                'type': 'hourly',
                'title': 'Hourly Brief' if lang == 'en' else '每小时简报',
                'timestamp': ts.isoformat(),
                'file_path': f
            })

    # 获取每日摘要
    if report_type in ['all', 'daily']:
        daily_files = glob.glob('data/summaries/summary_*.txt')
        for f in daily_files:
            ts = parse_timestamp_from_filename(f)
            reports.append({
                'id': os.path.basename(f).replace('summary_', '').replace('.txt', ''),
                'type': 'daily',
                'title': 'Daily Summary' if lang == 'en' else '每日摘要',
                'timestamp': ts.isoformat(),
                'file_path': f
            })

    # 获取周报
    if report_type in ['all', 'weekly']:
        weekly_files = glob.glob('data/weekly/analysis_*.json')
        for f in weekly_files:
            ts = parse_timestamp_from_filename(f)
            reports.append({
                'id': os.path.basename(f).replace('analysis_', '').replace('.json', ''),
                'type': 'weekly',
                'title': 'Weekly Analysis' if lang == 'en' else '周度分析',
                'timestamp': ts.isoformat(),
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


@report_bp.route('/api/reports/<report_id>')
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
                    'timestamp': parse_timestamp_from_filename(filepath).isoformat()
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
