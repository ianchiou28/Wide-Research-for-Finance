"""
运行月度分析
用法：python run_monthly_analysis.py [--year 2025] [--month 12] [--chat] [--refresh]
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

sys.path.append('src')
from monthly_analysis import MonthlyAnalysis

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description='生成月度深度分析报告')
    parser.add_argument('--year', type=int, default=datetime.now().year, help='年份')
    parser.add_argument('--month', type=int, default=datetime.now().month, help='月份')
    parser.add_argument('--chat', action='store_true', help='进入对话模式')
    parser.add_argument('--events-only', action='store_true', help='仅显示事件日历')
    parser.add_argument('--refresh', action='store_true', help='强制刷新事件（忽略缓存）')
    args = parser.parse_args()
    
    analyzer = MonthlyAnalysis()
    
    print(f"\n{'='*60}")
    print(f"  📅 {args.year}年{args.month}月 月度深度分析")
    print(f"{'='*60}\n")
    
    # 获取事件日历（支持自动抓取）
    print("正在获取本月重大事件（自动识别 + 预设日历）...\n")
    events = analyzer.get_monthly_events(args.year, args.month, force_refresh=args.refresh)
    
    print("【本月重大事件日历】\n")
    for e in events:
        importance_icon = "🔴" if e.get('importance') == 'critical' else "🟡" if e.get('importance') == 'high' else "🟢"
        source_tag = " [自动识别]" if e.get('source') == 'auto_detected' else ""
        
        print(f"  {importance_icon} {e.get('date', '待定')}  {e.get('name', '')}{source_tag}")
        
        # 显示影响评估（如果有）
        if e.get('impact_score'):
            direction_map = {'bullish': '📈利多', 'bearish': '📉利空', 'neutral': '➡️中性'}
            direction = direction_map.get(e.get('expected_direction', ''), '')
            print(f"      影响评分: {e['impact_score']}/10 {direction}")
        
        if e.get('note'):
            print(f"      └─ {e['note']}")
        
        if e.get('analysis'):
            print(f"      💡 {e['analysis'][:80]}...")
    
    if args.events_only:
        return
    
    print(f"\n{'─'*60}")
    print("正在生成深度分析报告，请稍候...\n")
    
    # 生成分析
    analysis = analyzer.generate_monthly_analysis(args.year, args.month)
    
    if analysis.get('error'):
        print(f"❌ 生成失败: {analysis.get('message')}")
        if analysis.get('raw_content'):
            print(f"\n原始内容预览:\n{analysis['raw_content'][:500]}...")
        return
    
    # 保存
    filename = analyzer.save_analysis(analysis)
    print(f"✓ 报告已保存: {filename}\n")
    
    # 打印摘要
    print(f"{'─'*60}")
    print("【月度总结】\n")
    print(f"  {analysis.get('summary', '无')}\n")
    
    # 宏观概览
    macro = analysis.get('macro_overview', {})
    if macro:
        print(f"{'─'*60}")
        print("【宏观环境】\n")
        if macro.get('global_economy'):
            print(f"  全球经济: {macro['global_economy'][:150]}...")
        if macro.get('central_banks'):
            print(f"  央行政策: {macro['central_banks'][:150]}...")
    
    # 加减仓建议
    recs = analysis.get('stock_recommendations', {})
    if recs:
        print(f"\n{'─'*60}")
        print("【加减仓建议】\n")
        
        buys = recs.get('buy', [])
        if buys:
            print("  📈 建议加仓:")
            for s in buys[:5]:
                print(f"     • {s.get('symbol', '')} ({s.get('name', '')})")
                if s.get('reason'):
                    print(f"       {s['reason'][:60]}")
                if s.get('target_price'):
                    print(f"       目标价: {s['target_price']}")
        
        sells = recs.get('sell', [])
        if sells:
            print("\n  📉 建议减仓:")
            for s in sells[:5]:
                print(f"     • {s.get('symbol', '')} ({s.get('name', '')})")
                if s.get('reason'):
                    print(f"       {s['reason'][:60]}")
    
    # 行业轮动
    sectors = analysis.get('sector_rotation', {})
    if sectors:
        print(f"\n{'─'*60}")
        print("【行业轮动】\n")
        
        if sectors.get('overweight'):
            print("  🟢 看好行业:")
            for s in sectors['overweight'][:3]:
                picks = ', '.join(s.get('top_picks', [])[:3]) if s.get('top_picks') else ''
                print(f"     • {s.get('sector', '')} - {s.get('reason', '')[:40]}")
                if picks:
                    print(f"       代表: {picks}")
        
        if sectors.get('underweight'):
            print("\n  🔴 回避行业:")
            for s in sectors['underweight'][:3]:
                print(f"     • {s.get('sector', '')} - {s.get('reason', '')[:40]}")
    
    # 关键日期
    key_dates = analysis.get('key_dates', [])
    if key_dates:
        print(f"\n{'─'*60}")
        print("【关键时间节点】\n")
        for d in key_dates[:10]:
            priority_icon = "🔴" if d.get('priority') == 'high' else "🟡" if d.get('priority') == 'medium' else "🟢"
            print(f"  {priority_icon} {d.get('date', '')} - {d.get('event', '')}")
            if d.get('action'):
                print(f"      → {d['action']}")
    
    # 风险提示
    risks = analysis.get('risk_warnings', {})
    if risks:
        print(f"\n{'─'*60}")
        print("【风险提示】\n")
        if risks.get('position_management'):
            print(f"  💰 仓位建议: {risks['position_management']}")
        if risks.get('main_uncertainties'):
            print("\n  ⚠️ 主要不确定性:")
            for u in risks['main_uncertainties'][:3]:
                print(f"     • {u}")
        if risks.get('black_swan_alerts'):
            print("\n  🦢 黑天鹅预警:")
            for b in risks['black_swan_alerts'][:2]:
                print(f"     • {b}")
    
    # 对话模式
    if args.chat:
        print(f"\n{'='*60}")
        print("进入对话模式，您可以追问任何细节。输入 'exit' 退出。")
        print(f"{'='*60}\n")
        
        while True:
            try:
                user_input = input("\n🙋 您的问题: ").strip()
                if user_input.lower() in ['exit', 'quit', '退出', 'q']:
                    print("再见！")
                    break
                if not user_input:
                    continue
                
                print("\n🤖 分析师回复:\n")
                reply = analyzer.chat(user_input)
                print(reply)
                
            except KeyboardInterrupt:
                print("\n\n再见！")
                break


if __name__ == '__main__':
    main()
