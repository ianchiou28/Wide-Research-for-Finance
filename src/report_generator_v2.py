"""
报告生成器 V2 - 输出结构化数据供前端可视化
"""

from datetime import datetime
from typing import List, Dict, Any
from collections import Counter
import json
import os


class ReportGeneratorV2:
    """结构化报告生成器"""
    
    def generate(self, processed_news: List[Dict]) -> Dict[str, Any]:
        """生成结构化报告数据"""
        if not processed_news:
            return self._empty_report()
        
        # 为每条新闻分配引用ID
        for i, news in enumerate(processed_news, 1):
            news['ref_id'] = i
        
        total = len(processed_news)
        
        # 情绪分析
        sentiment_data = self._analyze_sentiment(processed_news)
        
        # 热门实体
        entities_data = self._extract_entities(processed_news)
        
        # 事件分类
        events_data = self._categorize_events(processed_news)
        
        # 股票影响
        stock_impacts = self._extract_stock_impacts(processed_news)
        
        # 时间信息
        now = datetime.now()
        beijing_hour = now.hour
        ny_hour = (beijing_hour - 13) % 24
        
        return {
            'meta': {
                'generated_at': now.isoformat(),
                'beijing_time': f'{beijing_hour:02d}:00',
                'newyork_time': f'{ny_hour:02d}:00',
                'total_news': total,
                'report_type': 'hourly'
            },
            'sentiment': sentiment_data,
            'entities': entities_data,
            'events': events_data,
            'stock_impacts': stock_impacts,
            'news_list': self._format_news_list(processed_news)
        }
    
    def _empty_report(self) -> Dict[str, Any]:
        """生成空报告"""
        return {
            'meta': {
                'generated_at': datetime.now().isoformat(),
                'total_news': 0,
                'report_type': 'hourly'
            },
            'sentiment': {
                'overall': {'score': 0, 'label': '中性'},
                'cn': {'score': 0, 'label': '中性'},
                'us': {'score': 0, 'label': '中性'},
                'distribution': {'positive': 0, 'neutral': 0, 'negative': 0}
            },
            'entities': [],
            'events': {'high_impact': [], 'hot_search': [], 'stock_specific': [], 'other': []},
            'stock_impacts': [],
            'news_list': []
        }
    
    def _analyze_sentiment(self, news_list: List[Dict]) -> Dict:
        """分析情绪数据"""
        total = len(news_list)
        
        avg_overall = sum(n.get('sentiment', 0) for n in news_list) / total
        avg_cn = sum(n.get('sentiment_cn', n.get('sentiment', 0)) for n in news_list) / total
        avg_us = sum(n.get('sentiment_us', n.get('sentiment', 0)) for n in news_list) / total
        
        def get_label(score):
            if score > 0.3: return '积极'
            if score < -0.3: return '消极'
            return '中性'
        
        positive = sum(1 for n in news_list if n.get('sentiment', 0) > 0.3)
        negative = sum(1 for n in news_list if n.get('sentiment', 0) < -0.3)
        neutral = total - positive - negative
        
        return {
            'overall': {'score': round(avg_overall, 2), 'label': get_label(avg_overall)},
            'cn': {'score': round(avg_cn, 2), 'label': get_label(avg_cn)},
            'us': {'score': round(avg_us, 2), 'label': get_label(avg_us)},
            'distribution': {
                'positive': positive,
                'neutral': neutral,
                'negative': negative
            }
        }
    
    def _extract_entities(self, news_list: List[Dict]) -> List[Dict]:
        """提取热门实体"""
        all_entities = []
        entity_refs = {}
        entity_sentiment = {}
        
        for news in news_list:
            entities = news.get('entities', [])
            sentiment = news.get('sentiment', 0)
            
            for entity in entities:
                all_entities.append(entity)
                if entity not in entity_refs:
                    entity_refs[entity] = []
                    entity_sentiment[entity] = []
                entity_refs[entity].append(news['ref_id'])
                entity_sentiment[entity].append(sentiment)
        
        top_entities = Counter(all_entities).most_common(15)
        
        return [{
            'name': entity,
            'count': count,
            'refs': entity_refs.get(entity, [])[:5],
            'avg_sentiment': round(sum(entity_sentiment.get(entity, [0])) / max(len(entity_sentiment.get(entity, [1])), 1), 2)
        } for entity, count in top_entities]
    
    def _categorize_events(self, news_list: List[Dict]) -> Dict[str, List[Dict]]:
        """分类事件"""
        high_impact = []
        hot_search = []
        stock_specific = []
        other = []
        
        for news in news_list:
            event_item = {
                'ref_id': news['ref_id'],
                'title': news.get('title', ''),
                'summary': news.get('summary', ''),
                'source': news.get('source', ''),
                'url': news.get('url', ''),
                'event_type': news.get('event_type', '其他'),
                'sentiment': {
                    'overall': news.get('sentiment', 0),
                    'cn': news.get('sentiment_cn', news.get('sentiment', 0)),
                    'us': news.get('sentiment_us', news.get('sentiment', 0))
                },
                'stock_impact': news.get('stock_impact', [])
            }
            
            if news.get('impact_level') == '高':
                high_impact.append(event_item)
            elif news.get('category') == 'hot_search':
                hot_search.append(event_item)
            elif news.get('category') == 'stock_specific':
                stock_specific.append(event_item)
            else:
                other.append(event_item)
        
        return {
            'high_impact': high_impact,
            'hot_search': hot_search,
            'stock_specific': stock_specific,
            'other': other
        }
    
    def _extract_stock_impacts(self, news_list: List[Dict]) -> List[Dict]:
        """提取股票影响汇总"""
        stock_data = {}
        
        for news in news_list:
            impacts = news.get('stock_impact', [])
            if not impacts or not isinstance(impacts, list):
                continue
            
            for impact in impacts:
                if not isinstance(impact, dict):
                    continue
                
                symbol = impact.get('symbol', '')
                if not symbol:
                    continue
                
                if symbol not in stock_data:
                    stock_data[symbol] = {
                        'symbol': symbol,
                        'name': impact.get('name', symbol),
                        'up_count': 0,
                        'down_count': 0,
                        'neutral_count': 0,
                        'related_news': []
                    }
                
                direction = impact.get('direction', '')
                if direction == '上涨':
                    stock_data[symbol]['up_count'] += 1
                elif direction == '下跌':
                    stock_data[symbol]['down_count'] += 1
                else:
                    stock_data[symbol]['neutral_count'] += 1
                
                stock_data[symbol]['related_news'].append({
                    'ref_id': news['ref_id'],
                    'title': news.get('title', ''),
                    'direction': direction
                })
        
        # 计算综合预测
        results = []
        for symbol, data in stock_data.items():
            total_mentions = data['up_count'] + data['down_count'] + data['neutral_count']
            if data['up_count'] > data['down_count']:
                prediction = '看涨'
                confidence = data['up_count'] / total_mentions
            elif data['down_count'] > data['up_count']:
                prediction = '看跌'
                confidence = data['down_count'] / total_mentions
            else:
                prediction = '中性'
                confidence = 0.5
            
            results.append({
                **data,
                'prediction': prediction,
                'confidence': round(confidence, 2),
                'total_mentions': total_mentions
            })
        
        # 按提及次数排序
        results.sort(key=lambda x: x['total_mentions'], reverse=True)
        return results[:10]
    
    def _format_news_list(self, news_list: List[Dict]) -> List[Dict]:
        """格式化新闻列表"""
        return [{
            'ref_id': n['ref_id'],
            'title': n.get('title', ''),
            'source': n.get('source', ''),
            'url': n.get('url', ''),
            'summary': n.get('summary', ''),
            'sentiment': round(n.get('sentiment', 0), 2),
            'event_type': n.get('event_type', '其他'),
            'impact_level': n.get('impact_level', '低')
        } for n in news_list]
    
    def save_report(self, report_data: Dict) -> str:
        """保存报告为JSON"""
        output_dir = os.path.join('data', 'reports_json')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(output_dir, f'report_{timestamp}.json')
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def generate_text_report(self, report_data: Dict) -> str:
        """从结构化数据生成文本报告（兼容旧版）"""
        meta = report_data.get('meta', {})
        sentiment = report_data.get('sentiment', {})
        entities = report_data.get('entities', [])
        events = report_data.get('events', {})
        
        lines = [
            '=' * 60,
            f"财经新闻每小时简报 - {meta.get('generated_at', '')[:10]}",
            f"北京时间 {meta.get('beijing_time', '')} | 纽约时间 {meta.get('newyork_time', '')}",
            '=' * 60,
            '',
            '【市场情绪总览】',
            f"共分析 {meta.get('total_news', 0)} 条新闻",
            f"整体情绪: {sentiment.get('overall', {}).get('label', '中性')} ({sentiment.get('overall', {}).get('score', 0):.2f})",
            f"中国市场: {sentiment.get('cn', {}).get('label', '中性')} ({sentiment.get('cn', {}).get('score', 0):.2f})",
            f"美国市场: {sentiment.get('us', {}).get('label', '中性')} ({sentiment.get('us', {}).get('score', 0):.2f})",
            '',
            '【热点追踪】'
        ]
        
        for entity in entities[:10]:
            lines.append(f"  • {entity['name']} (提及{entity['count']}次)")
        
        lines.append('')
        lines.append('【重大事件提醒】')
        
        high_impact = events.get('high_impact', [])
        if high_impact:
            for event in high_impact:
                lines.append(f"  [{event['source']}] {event['title']}")
                lines.append(f"  摘要: {event['summary']}")
                lines.append('')
        else:
            lines.append('  本小时暂无高影响力事件')
        
        lines.append('')
        lines.append(f"报告生成时间: {meta.get('generated_at', '')}")
        
        return '\n'.join(lines)


# 测试
if __name__ == '__main__':
    generator = ReportGeneratorV2()
    
    # 模拟数据
    test_news = [
        {
            'title': '英伟达Q3财报超预期',
            'source': 'Reuters',
            'url': 'https://example.com/1',
            'content': '...',
            'summary': '英伟达第三季度营收超预期，AI芯片需求强劲',
            'sentiment': 0.8,
            'sentiment_cn': 0.3,
            'sentiment_us': 0.9,
            'entities': ['英伟达', 'AI', '芯片'],
            'event_type': '财报',
            'impact_level': '高',
            'stock_impact': [
                {'symbol': 'NVDA', 'name': '英伟达', 'direction': '上涨'}
            ]
        },
        {
            'title': '央行降准0.5个百分点',
            'source': '新华社',
            'url': 'https://example.com/2',
            'content': '...',
            'summary': '中国央行宣布降准，释放流动性',
            'sentiment': 0.5,
            'sentiment_cn': 0.7,
            'sentiment_us': 0.1,
            'entities': ['央行', 'A股', '银行'],
            'event_type': '政策',
            'impact_level': '高',
            'stock_impact': []
        }
    ]
    
    report = generator.generate(test_news)
    print(json.dumps(report, ensure_ascii=False, indent=2))
