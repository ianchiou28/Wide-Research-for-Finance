import os
import sys
import glob
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.append('src')
from weekly_summary import WeeklySummary

load_dotenv()

def parse_json_report(json_data):
    """解析JSON格式的报告"""
    if not json_data:
        return {}
    
    data = {
        'sentiment': {'overall': 0, 'cn': 0, 'us': 0},
        'stocks': [],
        'events': []
    }
    
    # 解析情绪数据
    if 'sentiment' in json_data:
        sentiment = json_data['sentiment']
        if 'overall' in sentiment:
            data['sentiment']['overall'] = sentiment['overall'].get('score', 0)
        if 'cn' in sentiment:
            data['sentiment']['cn'] = sentiment['cn'].get('score', 0)
        if 'us' in sentiment:
            data['sentiment']['us'] = sentiment['us'].get('score', 0)
    
    # 从事件中提取股票影响
    stock_map = {}  # 用于去重和合并
    
    events = json_data.get('events', {})
    all_events = []
    all_events.extend(events.get('high_impact', []))
    all_events.extend(events.get('stock_specific', []))
    all_events.extend(events.get('other', []))
    
    for event in all_events:
        stock_impacts = event.get('stock_impact', [])
        event_sentiment = event.get('sentiment', {})
        overall_sentiment = event_sentiment.get('overall', 0) if isinstance(event_sentiment, dict) else event_sentiment
        
        for symbol in stock_impacts:
            if symbol not in stock_map:
                stock_map[symbol] = {
                    'symbol': symbol,
                    'name': symbol,  # 默认使用symbol作为名称
                    'direction': '上涨' if overall_sentiment > 0.2 else '下跌' if overall_sentiment < -0.2 else '中性',
                    'sentiment_sum': overall_sentiment,
                    'count': 1,
                    'events': [event.get('summary', event.get('title', ''))]
                }
            else:
                stock_map[symbol]['sentiment_sum'] += overall_sentiment
                stock_map[symbol]['count'] += 1
                stock_map[symbol]['events'].append(event.get('summary', event.get('title', '')))
        
        # 保存事件信息
        if event.get('summary') or event.get('title'):
            data['events'].append({
                'title': event.get('title', ''),
                'summary': event.get('summary', ''),
                'sentiment': overall_sentiment,
                'stocks': stock_impacts
            })
    
    # 计算平均情绪并确定方向
    for symbol, stock_data in stock_map.items():
        avg_sentiment = stock_data['sentiment_sum'] / stock_data['count']
        stock_data['direction'] = '上涨' if avg_sentiment > 0.2 else '下跌' if avg_sentiment < -0.2 else '中性'
        stock_data['avg_sentiment'] = avg_sentiment
        del stock_data['sentiment_sum']
        data['stocks'].append(stock_data)
    
    return data

def parse_report(content):
    """解析文本格式报告（兼容旧格式）"""
    if not content:
        return {}
    
    lines = content.split('\n')
    data = {
        'sentiment': {'overall': 0, 'cn': 0, 'us': 0},
        'stocks': []
    }
    
    for line in lines:
        if '整体情绪' in line:
            try:
                data['sentiment']['overall'] = float(line.split('指数:')[1].split(')')[0].strip())
            except:
                pass
        if '中国市场' in line:
            try:
                data['sentiment']['cn'] = float(line.split('指数:')[1].split(')')[0].strip())
            except:
                pass
        if '美国市场' in line:
            try:
                data['sentiment']['us'] = float(line.split('指数:')[1].split(')')[0].strip())
            except:
                pass
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

def get_weekly_reports():
    """获取过去7天的报告，优先使用JSON格式"""
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    weekly = []
    
    # 优先使用JSON格式报告
    json_reports = glob.glob('data/reports_json/report_*.json')
    if json_reports:
        for report_path in json_reports:
            try:
                mtime = datetime.fromtimestamp(os.path.getctime(report_path))
                if mtime >= week_ago:
                    with open(report_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        parsed = parse_json_report(json_data)
                        if parsed and (parsed.get('stocks') or parsed.get('events')):
                            weekly.append(parsed)
            except Exception as e:
                print(f"解析JSON报告失败 {report_path}: {e}")
        
        if weekly:
            return weekly
    
    # 回退到文本格式
    txt_reports = glob.glob('data/reports/report_*.txt')
    if txt_reports:
        for report_path in txt_reports:
            try:
                mtime = datetime.fromtimestamp(os.path.getctime(report_path))
                if mtime >= week_ago:
                    with open(report_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        parsed = parse_report(content)
                        if parsed:
                            weekly.append(parsed)
            except:
                pass
    
    return weekly

if __name__ == '__main__':
    print("开始生成周报分析...\n")
    
    parsed_reports = get_weekly_reports()
    if not parsed_reports:
        print("❌ 无可用报告数据")
        sys.exit(1)
    
    # 统计找到的股票数
    total_stocks = sum(len(r.get('stocks', [])) for r in parsed_reports)
    total_events = sum(len(r.get('events', [])) for r in parsed_reports)
    print(f"✓ 找到 {len(parsed_reports)} 份报告")
    print(f"✓ 共计 {total_stocks} 条股票提及")
    print(f"✓ 共计 {total_events} 条事件\n")
    
    print("正在分析数据并生成预测...\n")
    weekly_gen = WeeklySummary()
    analysis = weekly_gen.generate(parsed_reports)
    
    filename = weekly_gen.save_analysis(analysis)
    print(f"✓ 周报已保存: {filename}\n")
    
    print("【周报分析结果】")
    print(f"总结: {analysis.get('summary', '无')}\n")
    
    stocks = analysis.get('stocks', [])
    if stocks:
        print("【个股预测】")
        for stock in stocks:
            print(f"  {stock['symbol']} ({stock['name']})")
            print(f"    预测: {stock['prediction']} | 信心: {stock['confidence']}")
            print(f"    原因: {stock['reason']}\n")
    else:
        print("无个股预测数据")
