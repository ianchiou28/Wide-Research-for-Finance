"""
运行回测验证
用法：python run_backtest.py [--weekly] [--monthly] [--all]
"""

import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

sys.path.append('src')
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='运行预测回测验证')
    parser.add_argument('--weekly', action='store_true', help='仅运行周报回测')
    parser.add_argument('--monthly', action='store_true', help='仅运行月报回测')
    parser.add_argument('--all', action='store_true', help='运行所有回测（默认）')
    parser.add_argument('--days', type=int, default=30, help='回测天数（默认30天）')
    args = parser.parse_args()
    
    # 默认运行所有
    if not args.weekly and not args.monthly:
        args.all = True
    
    print(f"\n{'='*60}")
    print(f"  📊 预测回测验证系统")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    from backtester import WeeklyAnalysisBacktester, MonthlyAnalysisBacktester
    
    results = {}
    
    # 周报回测
    if args.weekly or args.all:
        print("【周度分析回测】")
        print("-" * 40)
        weekly_bt = WeeklyAnalysisBacktester()
        weekly_result = weekly_bt.run_backtest(days=args.days, verify_days=5)
        results['weekly'] = weekly_result.get('stats', {})
        print()
    
    # 月报回测
    if args.monthly or args.all:
        print("【月度分析回测】")
        print("-" * 40)
        monthly_bt = MonthlyAnalysisBacktester()
        monthly_result = monthly_bt.run_backtest(days=args.days * 2)
        results['monthly'] = monthly_result.get('stats', {})
        print()
    
    # 汇总
    print(f"{'='*60}")
    print("【回测汇总】")
    print(f"{'='*60}")
    
    if 'weekly' in results:
        weekly = results['weekly']
        print(f"\n📈 周报预测:")
        print(f"   总预测数: {weekly.get('total_predictions', 0)}")
        print(f"   准确率: {weekly.get('accuracy', 0):.1f}%")
        if weekly.get('by_direction'):
            for d, s in weekly['by_direction'].items():
                print(f"   - {d}: {s.get('accuracy', 0):.1f}%")
    
    if 'monthly' in results:
        monthly = results['monthly']
        stock_stats = monthly.get('stock_predictions', {})
        event_stats = monthly.get('event_predictions', {})
        
        print(f"\n📊 月报预测:")
        print(f"   股票预测: {stock_stats.get('correct', 0)}/{stock_stats.get('total', 0)} ({stock_stats.get('accuracy', 0):.1f}%)")
        print(f"   事件预测: {event_stats.get('correct', 0)}/{event_stats.get('total', 0)} ({event_stats.get('accuracy', 0):.1f}%)")
    
    print(f"\n{'='*60}")
    print("回测完成！结果已保存到 data/ 目录")
    print(f"{'='*60}\n")
    
    return results


if __name__ == '__main__':
    main()
