import os
import sys
import glob
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.append('src')
from weekly_summary import WeeklySummary

load_dotenv()

def parse_report(content):
    """解析报告内容"""
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

if __name__ == '__main__':
    print("开始生成周报分析...\n")
    
    reports = get_weekly_reports()
    if not reports:
        print("❌ 无可用报告数据")
        sys.exit(1)
    
    print(f"✓ 找到 {len(reports)} 份报告\n")
    
    parsed_reports = [parse_report(r) for r in reports]
    
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
