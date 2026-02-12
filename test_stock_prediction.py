"""测试个股预测功能是否正常"""
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'config'))

from src.collector import NewsCollector
from src.processor import NLPProcessor
from src.report_generator_v2 import ReportGeneratorV2

print("=" * 60)
print("个股预测功能测试")
print("=" * 60)

# 采集新闻
print("\n[1/3] 采集新闻...")
collector = NewsCollector()
raw = collector.collect_all()
print(f"  采集到 {len(raw)} 条原始新闻")

if not raw:
    print("❌ 未采集到新闻，跳过测试")
    sys.exit(1)

# NLP处理
print("\n[2/3] NLP处理...")
processor = NLPProcessor()
processed = processor.process_batch(raw)
print(f"  处理完成 {len(processed)} 条")

# 检查stock_impact字段
has_impact = [n for n in processed if n.get('stock_impact')]
print(f"  含有stock_impact的新闻: {len(has_impact)} 条")
for n in has_impact[:5]:
    imp = n['stock_impact']
    print(f"    [{n.get('source','')}] {n.get('title','')[:40]}...")
    print(f"      stock_impact类型: {type(imp).__name__}, 值: {json.dumps(imp, ensure_ascii=False)[:120]}")

# 生成报告
print("\n[3/3] 生成结构化报告...")
generator = ReportGeneratorV2()
report = generator.generate(processed)

impacts = report.get('stock_impacts', [])
print(f"\n{'=' * 60}")
print(f"个股预测结果: {len(impacts)} 只股票")
print(f"{'=' * 60}")

if not impacts:
    print("⚠️ 没有个股预测数据")
else:
    all_neutral = all(s['prediction'] == '中性' for s in impacts)
    all_50 = all(s['confidence'] == 0.5 for s in impacts)
    
    for s in impacts:
        icon = '📈' if s['prediction'] == '看涨' else '📉' if s['prediction'] == '看跌' else '➡️'
        print(f"  {icon} {s['symbol']} ({s['name']}): {s['prediction']} "
              f"置信度={s['confidence']:.0%} "
              f"[↑{s['up_count']} ↓{s['down_count']} ={s.get('neutral_count',0)}]")
    
    if all_neutral and all_50:
        print("\n❌ 问题未修复！仍然全部中性/50%")
    else:
        print(f"\n✅ 修复成功！预测分布正常")

# 保存报告供前端使用
filename = generator.save_report(report)
print(f"\n报告已保存: {filename}")
