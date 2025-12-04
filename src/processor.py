import os
import json
import time
from openai import OpenAI
from typing import List, Dict

class NLPProcessor:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com",
            timeout=120.0,  # 设置120秒超时
            max_retries=2   # 自动重试2次
        )
    
    def process_batch(self, articles: List[Dict], batch_size=20) -> List[Dict]:
        """两阶段处理：先筛选标题，再深度分析"""
        if not articles:
            return []
        
        print(f"\n[阶段1] 标题筛选 ({len(articles)}条)...")
        interesting = self._filter_by_title(articles)
        print(f"  筛选出 {len(interesting)} 条感兴趣的新闻")
        
        if not interesting:
            return []
        
        print(f"\n[阶段2] 深度分析...")
        all_processed = []
        for batch_start in range(0, len(interesting), batch_size):
            batch = interesting[batch_start:batch_start + batch_size]
            processed = self._process_single_batch(batch)
            all_processed.extend(processed)
            print(f"  已处理 {len(all_processed)}/{len(interesting)} 条")
        
        return all_processed
    
    def _filter_by_title(self, articles: List[Dict]) -> List[Dict]:
        """阶段1：仅用标题快速筛选"""
        titles_text = "\n".join([f"{i+1}. [{a['source']}] {a['title']}" 
                                  for i, a in enumerate(articles)])
        
        prompt = f"""你是财经分析师，快速判断以下新闻标题是否值得深入分析。

{titles_text}

筛选标准（满足任一即可）：
- 涉及重大市场事件（IPO/并购/财报/政策）
- 提及知名公司或行业龙头
- 可能影响股市走势
- 涉及宏观经济数据

    只返回你认为最有价值的20条以内，按重要度从高到低排序。

    返回JSON数组（仅包含值得分析的序号）：
[1, 3, 5]

如果都不感兴趣，返回：[]"""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=500,
                    timeout=60.0  # 单次请求60秒超时
                )
                
                content = response.choices[0].message.content
                if content is None:
                    return articles[:20]
                indices = self._parse_indices(content, len(articles))

                selected = []
                seen = set()
                for idx in indices:
                    if idx in seen:
                        continue
                    seen.add(idx)
                    selected.append(articles[idx-1])
                    if len(selected) >= 20:
                        break
                return selected
            
            except Exception as e:
                print(f"筛选失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)  # 等待3秒后重试
                    continue
        
        print(f"筛选最终失败，保留前20篇文章")
        return articles[:20]
    
    def _process_single_batch(self, articles: List[Dict]) -> List[Dict]:
        """处理单个批次"""
        articles_text = ""
        for i, article in enumerate(articles):
            articles_text += f"\n[文章{i+1}]\n标题: {article['title']}\n来源: {article['source']}\n内容: {article['content']}\n"
        
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
    "stock_impact": []
  }}
]

重要说明：
- sentiment: 整体市场情绪 (-1.0到+1.0)
- sentiment_cn: 对中国股市影响 (-1.0到+1.0)
- sentiment_us: 对美国股市影响 (-1.0到+1.0)
- stock_impact: 相关股票影响预测（最多3个，如无直接相关股票则为空数组）

必须返回所有{len(articles)}篇文章的分析结果。"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=2000,
                    timeout=90.0  # 单次请求90秒超时
                )
                
                content = response.choices[0].message.content
                if content is None:
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    return []
                
                result = self._extract_json(content)
                if not result:
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    return []
                
                processed = []
                for item in result:
                    idx = item.get('index', 0) - 1
                    if 0 <= idx < len(articles):
                        processed.append({
                            **articles[idx],
                            'summary': item.get('summary', ''),
                            'sentiment': float(item.get('sentiment', 0)),
                            'sentiment_cn': float(item.get('sentiment_cn', item.get('sentiment', 0))),
                            'sentiment_us': float(item.get('sentiment_us', item.get('sentiment', 0))),
                            'entities': item.get('key_entities', []),
                            'event_type': item.get('event_type', '其他'),
                            'impact_level': item.get('impact_level', '中'),
                            'stock_impact': item.get('stock_impact', [])
                        })
                
                return processed
            
            except Exception as e:
                print(f"批次处理失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # 等待5秒后重试
                    continue
        
        print(f"批次处理最终失败，跳过此批次")
        return []
    
    def _extract_json(self, text: str):
        """从文本中提取JSON数组"""
        text = text.strip()
        start = text.find('[')
        end = text.rfind(']')
        if start == -1 or end == -1 or start >= end:
            return None
        
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            return None

    def _parse_indices(self, raw_content: str, total: int) -> List[int]:
        """从模型输出里提取最多20个有效的索引"""
        content = raw_content.strip()
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            start = content.find('[')
            end = content.rfind(']')
            if start == -1 or end == -1 or start >= end:
                raise
            data = json.loads(content[start:end+1])

        if not isinstance(data, list):
            raise ValueError("Model应返回列表")

        normalized: List[int] = []
        for item in data:
            idx = None
            if isinstance(item, int):
                idx = item
            elif isinstance(item, str) and item.strip().isdigit():
                idx = int(item.strip())

            if idx is None:
                continue
            if 0 < idx <= total:
                normalized.append(idx)

            if len(normalized) >= 20:
                break

        return normalized
