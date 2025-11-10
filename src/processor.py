import os
import json
from openai import OpenAI
from typing import List, Dict

class NLPProcessor:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )
    
    def process_batch(self, articles: List[Dict], batch_size=20) -> List[Dict]:
        """批量处理文章以降低成本"""
        if not articles:
            return []
        
        all_processed = []
        
        # 分批处理
        for batch_start in range(0, len(articles), batch_size):
            batch = articles[batch_start:batch_start + batch_size]
            processed = self._process_single_batch(batch)
            all_processed.extend(processed)
            print(f"  已处理 {len(all_processed)}/{len(articles)} 条")
        
        return all_processed
    
    def _process_single_batch(self, articles: List[Dict]) -> List[Dict]:
        """处理单个批次"""
        # 构建批量处理的prompt
        articles_text = ""
        for i, article in enumerate(articles):
            articles_text += f"\n[文章{i+1}]\n标题: {article['title']}\n来源: {article['source']}\n内容: {article['content'][:500]}\n"
        
        prompt = f"""分析以下财经新闻，为每篇文章返回JSON数组：

{articles_text}

返回格式（纯JSON数组，无其他文字）：
[
  {{
    "index": 1,
    "summary": "一句话摘要（中文，20字内）",
    "sentiment": 0.5,
    "sentiment_cn": 0.3,
    "sentiment_us": 0.6,
    "key_entities": ["公司A", "行业B"],
    "event_type": "财报/政策/并购/其他",
    "impact_level": "高/中/低",
    "stock_impact": [
      {{
        "symbol": "TSLA",
        "name": "特斯拉",
        "direction": "上涨/下跌/中性",
        "confidence": "高/中/低"
      }}
    ]
  }}
]

重要说明：
- sentiment: 整体市场情绪 (-1.0到+1.0)
- sentiment_cn: 对中国股市影响 (-1.0到+1.0)
- sentiment_us: 对美国股市影响 (-1.0到+1.0)
- stock_impact: 相关股票影响预测（最多3个，如无直接相关股票则为空数组）
- 例如：“特斯拉股东批准薪酬” → stock_impact: [{{"symbol":"TSLA","name":"特斯拉","direction":"上涨","confidence":"高"}}]

必须返回所有{len(articles)}篇文章的分析结果。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 合并原始文章和分析结果
            processed = []
            for item in result:
                idx = item['index'] - 1
                if idx < len(articles):
                    processed.append({
                        **articles[idx],
                        'summary': item['summary'],
                        'sentiment': item['sentiment'],
                        'sentiment_cn': item.get('sentiment_cn', item['sentiment']),
                        'sentiment_us': item.get('sentiment_us', item['sentiment']),
                        'entities': item['key_entities'],
                        'event_type': item['event_type'],
                        'impact_level': item['impact_level'],
                        'stock_impact': item.get('stock_impact', [])
                    })
            
            return processed
        
        except Exception as e:
            print(f"Processing error: {e}")
            return []
