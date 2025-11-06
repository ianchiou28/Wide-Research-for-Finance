from datetime import datetime
from typing import List, Dict
from collections import Counter

class ReportGenerator:
    def generate(self, processed_news: List[Dict]) -> str:
        """生成每日报告"""
        if not processed_news:
            return "今日无新闻数据"
        
        # 统计分析
        total = len(processed_news)
        avg_sentiment = sum(n['sentiment'] for n in processed_news) / total
        sentiment_label = "积极" if avg_sentiment > 0.3 else "消极" if avg_sentiment < -0.3 else "中性"
        
        # 热门实体
        all_entities = []
        for news in processed_news:
            all_entities.extend(news.get('entities', []))
        top_entities = Counter(all_entities).most_common(10)
        
        # 高影响事件
        high_impact = [n for n in processed_news if n.get('impact_level') == '高']
        
        # 生成报告
        report = f"""
{'='*60}
财经新闻每日简报 - {datetime.now().strftime('%Y年%m月%d日')}
{'='*60}

【市场情绪总览】
- 共分析 {total} 条新闻
- 整体情绪: {sentiment_label} (情绪指数: {avg_sentiment:.2f})

【热点追踪】
今日最受关注的主体：
"""
        for entity, count in top_entities[:5]:
            report += f"  • {entity} (提及{count}次)\n"
        
        report += f"\n【重大事件提醒】\n"
        if high_impact:
            for news in high_impact[:5]:
                report += f"""
  [{news['source']}] {news['event_type']}
  标题: {news['title']}
  摘要: {news['summary']}
  情绪: {'积极' if news['sentiment'] > 0.3 else '消极' if news['sentiment'] < -0.3 else '中性'}
  链接: {news['url']}
"""
        else:
            report += "  今日暂无高影响力事件\n"
        
        report += f"\n【情绪分布】\n"
        positive = sum(1 for n in processed_news if n['sentiment'] > 0.3)
        negative = sum(1 for n in processed_news if n['sentiment'] < -0.3)
        neutral = total - positive - negative
        report += f"  积极: {positive} | 中性: {neutral} | 消极: {negative}\n"
        
        report += f"\n{'='*60}\n"
        report += "本报告由AI自动生成，仅供参考\n"
        
        return report
