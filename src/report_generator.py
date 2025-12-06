from datetime import datetime
from typing import List, Dict
from collections import Counter

class ReportGenerator:
    def generate(self, processed_news: List[Dict]) -> str:
        """生成每小时报告"""
        if not processed_news:
            return "无新闻数据"
        
        # 为每条新闻分配引用ID
        for i, news in enumerate(processed_news, 1):
            news['ref_id'] = i

        # 统计分析
        total = len(processed_news)
        avg_sentiment = sum(n['sentiment'] for n in processed_news) / total
        avg_sentiment_cn = sum(n.get('sentiment_cn', n['sentiment']) for n in processed_news) / total
        avg_sentiment_us = sum(n.get('sentiment_us', n['sentiment']) for n in processed_news) / total
        
        sentiment_label = "积极" if avg_sentiment > 0.3 else "消极" if avg_sentiment < -0.3 else "中性"
        sentiment_label_cn = "积极" if avg_sentiment_cn > 0.3 else "消极" if avg_sentiment_cn < -0.3 else "中性"
        sentiment_label_us = "积极" if avg_sentiment_us > 0.3 else "消极" if avg_sentiment_us < -0.3 else "中性"
        
        # 热门实体
        all_entities = []
        entity_refs = {}
        for news in processed_news:
            entities = news.get('entities', [])
            all_entities.extend(entities)
            for entity in set(entities):
                if entity not in entity_refs:
                    entity_refs[entity] = []
                entity_refs[entity].append(news['ref_id'])
        top_entities = Counter(all_entities).most_common(10)
        
        # 生成报告
        now = datetime.now()
        beijing_hour = now.hour
        ny_hour = (beijing_hour - 13) % 24
        report = f"""
{'='*60}
财经新闻每小时简报 - {now.strftime('%Y年%m月%d日')} 北京时间{beijing_hour:02d}时 纽约时间{ny_hour:02d}时
{'='*60}

【市场情绪总览】
- 共分析 {total} 条新闻
- 整体情绪: {sentiment_label} (情绪指数: {avg_sentiment:.2f})
- 中国市场: {sentiment_label_cn} (指数: {avg_sentiment_cn:.2f})
- 美国市场: {sentiment_label_us} (指数: {avg_sentiment_us:.2f})

【热点追踪】
本小时最受关注的主体：
"""
        for entity, count in top_entities[:10]:
            refs = sorted(entity_refs.get(entity, []))
            refs_str = ",".join(map(str, refs[:5]))
            if len(refs) > 5:
                refs_str += "..."
            report += f"  • {entity} (提及{count}次) [相关新闻:{refs_str}]\n"
        
        # 高影响事件
        high_impact = [n for n in processed_news if n.get('impact_level') == '高']
        # 国内热点
        hot_search = [n for n in processed_news if n.get('category') == 'hot_search']
        # 自选股动态
        stock_specific = [n for n in processed_news if n.get('category') == 'stock_specific']
        
        report += f"\n【重大事件提醒】\n"
        if high_impact:
            for news in high_impact:
                sentiment_text = '积极' if news['sentiment'] > 0.3 else '消极' if news['sentiment'] < -0.3 else '中性'
                sentiment_cn_text = '积极' if news.get('sentiment_cn', news['sentiment']) > 0.3 else '消极' if news.get('sentiment_cn', news['sentiment']) < -0.3 else '中性'
                sentiment_us_text = '积极' if news.get('sentiment_us', news['sentiment']) > 0.3 else '消极' if news.get('sentiment_us', news['sentiment']) < -0.3 else '中性'
                
                stock_text = ""
                stock_impact = news.get('stock_impact', [])
                if stock_impact and isinstance(stock_impact, list):
                    stocks = []
                    for stock in stock_impact:
                        if isinstance(stock, dict):
                            direction_icon = '↑' if stock.get('direction') == '上涨' else '↓' if stock.get('direction') == '下跌' else '→'
                            stocks.append(f"{stock.get('symbol', '')}({stock.get('name', '')}){direction_icon}")
                    if stocks:
                        stock_text = f"\n  股票影响: {' | '.join(stocks)}"
                
                report += f"""
  [ID:{news['ref_id']}] [{news['source']}] {news['event_type']}
  标题: {news['title']}
  摘要: {news['summary']}
  情绪: {sentiment_text} | 中国: {sentiment_cn_text} | 美国: {sentiment_us_text}{stock_text}
  链接: {news['url']}
"""
        else:
            report += "  本小时暂无高影响力事件\n"
        
        report += f"\n【国内热点追踪】\n"
        if hot_search:
            for news in hot_search:
                report += f"""
  [ID:{news['ref_id']}] [{news['source']}] {news['title']}
  摘要: {news['summary']}
  链接: {news['url']}
"""
        else:
            report += "  暂无特别关注的国内热点\n"

        report += f"\n【我的自选股动态】\n"
        if stock_specific:
            for news in stock_specific:
                report += f"""
  [ID:{news['ref_id']}] {news['title']}
  摘要: {news['summary']}
  链接: {news['url']}
"""
        else:
            report += "  暂无自选股相关新闻\n"

        # 其他新闻
        other_news = [n for n in processed_news if n.get('impact_level') != '高' and n.get('category') not in ['hot_search', 'stock_specific']]
        report += f"\n【其他新闻 ({len(other_news)}条)】\n"
        for news in other_news:
            report += f"  {news['ref_id']}. [{news['source']}] {news['title']}\n"
        
        report += f"\n\n【情绪分布】\n"
        positive = sum(1 for n in processed_news if n['sentiment'] > 0.3)
        negative = sum(1 for n in processed_news if n['sentiment'] < -0.3)
        neutral = total - positive - negative
        report += f"  积极: {positive} | 中性: {neutral} | 消极: {negative}\n"
        
        report += f"\n{'='*60}\n"
        report += f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "本报告由AI自动生成，仅供参考\n"
        
        return report
