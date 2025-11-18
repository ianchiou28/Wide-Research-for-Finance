from flask import Flask, render_template, jsonify
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

app = Flask(__name__)
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
            return '↑ 上涨'
        elif score < -0.3:
            return '↓ 下跌'
        else:
            return '➡️ 震荡'
    
    return {
        'china': {
            'name': 'A股',
            'sentiment': sentiment.get('cn', 0),
            'trend': predict_trend(sentiment.get('cn', 0)),
            'icon': '↑' if sentiment.get('cn', 0) > 0.3 else '↓' if sentiment.get('cn', 0) < -0.3 else '➡️'
        },
        'us': {
            'name': '美股',
            'sentiment': sentiment.get('us', 0),
            'trend': predict_trend(sentiment.get('us', 0)),
            'icon': '↑' if sentiment.get('us', 0) > 0.3 else '↓' if sentiment.get('us', 0) < -0.3 else '➡️'
        },
        'global': {
            'name': '全球',
            'sentiment': sentiment.get('overall', 0),
            'trend': predict_trend(sentiment.get('overall', 0)),
            'icon': '↑' if sentiment.get('overall', 0) > 0.3 else '↓' if sentiment.get('overall', 0) < -0.3 else '➡️'
        }
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/overview')
def overview():
    return render_template('overview.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/api/hourly_report')
def hourly_report():
    """获取最新小时简报的完整内容"""
    content = get_latest_report()
    if not content:
        return jsonify({
            'content': '暂无数据',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        })
    
    data = parse_report(content)
    data['content'] = content  # 添加原始内容
    data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M')
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
