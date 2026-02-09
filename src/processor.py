import os
import sys
import json
import time
from openai import OpenAI
from typing import List, Dict
from logger import setup_logger

# 导入统一配置
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))
    from settings import Config
except ImportError:
    Config = None

# 导入市场上下文（可选增强）
try:
    from market_context import MarketContext
    _market_ctx = MarketContext()
except ImportError:
    _market_ctx = None

# 导入多模型集成分析器（可选增强）
try:
    from ensemble_analyzer import EnsembleAnalyzer
    _ensemble = EnsembleAnalyzer()
except ImportError:
    _ensemble = None

logger = setup_logger('processor')

class NLPProcessor:
    def __init__(self):
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            logger.warning("DEEPSEEK_API_KEY 环境变量未设置!")
        
        # 使用统一配置
        if Config:
            client_kwargs = Config.get_llm_client_kwargs()
            client_kwargs['api_key'] = api_key
            self.client = OpenAI(**client_kwargs)
            self._model = Config.LLM_MODEL
            self._timeout = Config.LLM_TIMEOUT
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com",
                timeout=120.0,
                max_retries=2
            )
            self._model = "deepseek-chat"
            self._timeout = 120.0
    
    def process_batch(self, articles: List[Dict], batch_size=20) -> List[Dict]:
        """两阶段处理：先筛选标题，再深度分析"""
        if not articles:
            return []
        
        logger.info(f"[阶段1] 标题筛选 ({len(articles)}条)...")
        interesting = self._filter_by_title(articles)
        logger.info(f"筛选出 {len(interesting)} 条感兴趣的新闻")
        
        if not interesting:
            return []
        
        logger.info(f"[阶段2] 深度分析...")
        all_processed = []
        for batch_start in range(0, len(interesting), batch_size):
            batch = interesting[batch_start:batch_start + batch_size]
            processed = self._process_single_batch(batch)
            all_processed.extend(processed)
            logger.info(f"已处理 {len(all_processed)}/{len(interesting)} 条")
        
        return all_processed
    
    def _filter_by_title(self, articles: List[Dict]) -> List[Dict]:
        """阶段1：仅用标题快速筛选"""
        titles_text = "\n".join([f"{i+1}. [{a['source']}] {a['title']}" 
                                  for i, a in enumerate(articles)])
        
        prompt = f"""你是资深财经编辑，根据以下标题快速筛选出对股市有实际影响的新闻。

{titles_text}

## 筛选标准（满足任一即可）
- 央行/监管机构政策（加息、降准、新规）
- 上市公司重大事项（财报、并购、增减持、停牌）
- 宏观经济关键指标（GDP、CPI、PMI、就业）
- 地缘政治风险（战争、制裁、贸易摩擦）
- 行业变革性事件（技术突破、供应链中断）

## 排除标准
- 纯市场评论无新增信息
- 旧闻重复报道
- 娱乐/体育/社会新闻

返回最有价值的 ≤20 条序号（JSON数组），按重要性排序：
[1, 3, 5]

如都不值得分析，返回：[]"""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=500,
                    timeout=60.0
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
                logger.warning(f"筛选失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
        
        logger.warning(f"筛选最终失败，保留前20篇文章")
        return articles[:20]
    
    def _process_single_batch(self, articles: List[Dict]) -> List[Dict]:
        """处理单个批次"""
        articles_text = ""
        for i, article in enumerate(articles):
            articles_text += f"\n[文章{i+1}]\n标题: {article['title']}\n来源: {article['source']}\n内容: {article['content']}\n"
        
        # 获取市场上下文（可选）
        market_section = ""
        if _market_ctx:
            try:
                market_section = _market_ctx.get_context_text()
            except Exception as e:
                logger.debug(f"获取市场上下文失败: {e}")
        
        prompt = f"""你是资深金融分析师，请对每篇新闻进行 **逐步推理** 后给出结论。
{market_section}
## 分析框架（Chain-of-Thought）
对每篇文章：
1. **识别事件类型** — 央行决议 / 财报 / 政策法规 / 并购重组 / 地缘政治 / 宏观数据 / 其他
2. **判断影响范围** — 单只股票 / 行业板块 / 整体市场
3. **评估传导路径** — 事件 → 直接影响 → 间接传导 → 情绪扩散
4. **给出量化结论** — 情绪打分 + 影响等级

## Few-shot 示例
输入："美联储宣布加息25个基点，符合市场预期"
输出：
{{
  "index": 1,
  "summary": "美联储加息25bp符合预期",
  "reasoning": "加息符合预期利空有限，短期美元走强压制A股，但预期已消化",
  "sentiment": -0.2,
  "sentiment_cn": -0.3,
  "sentiment_us": -0.1,
  "key_entities": ["美联储", "美元"],
  "event_type": "央行决议",
  "impact_level": "高",
  "stock_impact": []
}}

输入："贵州茅台Q3净利润同比增长15%，超出市场预期"
输出：
{{
  "index": 2,
  "summary": "茅台Q3净利增15%超预期",
  "reasoning": "业绩超预期直接利好股价，白酒板块情绪提振，对美股无影响",
  "sentiment": 0.6,
  "sentiment_cn": 0.7,
  "sentiment_us": 0.0,
  "key_entities": ["贵州茅台", "白酒"],
  "event_type": "财报",
  "impact_level": "中",
  "stock_impact": [{{"symbol": "600519", "name": "贵州茅台", "impact": "利好", "reason": "业绩超预期"}}]
}}

## 待分析文章
{articles_text}

## 评分细则
- sentiment / sentiment_cn / sentiment_us: 范围 [-1.0, +1.0]
  · 重大利好/利空：±0.7 ~ ±1.0
  · 一般消息：±0.2 ~ ±0.5
  · 无明确方向或影响极小：-0.1 ~ +0.1
- impact_level: 高（影响大盘或行业龙头）/ 中（影响个股或子行业）/ 低（边际消息）
- stock_impact: 最多3个相关股票；无直接个股关联时为 []

返回纯JSON数组，必须包含所有{len(articles)}篇文章。"""

        # ---- 多模型集成模式 ----
        use_ensemble = os.getenv('ENSEMBLE_MODE', '').lower() in ('1', 'true', 'yes')
        if use_ensemble and _ensemble and _ensemble._client:
            logger.info("使用多模型集成分析 (EnsembleAnalyzer)...")
            result = _ensemble.analyze(prompt, len(articles))
            if result:
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
                            'stock_impact': item.get('stock_impact', []),
                            'ensemble_confidence': item.get('ensemble_confidence', ''),
                            'sentiment_std': item.get('sentiment_std', 0),
                        })
                if processed:
                    logger.info(f"集成分析完成, {len(processed)} 条结果")
                    return processed
            logger.warning("集成分析未返回结果，回退到单次调用")

        # ---- 单次调用模式（默认） ----
        max_retries = Config.LLM_MAX_RETRIES if Config else 3
        for attempt in range(max_retries):
            try:
                logger.debug(f"调用 DeepSeek API (尝试 {attempt+1}/{max_retries})...")
                response = self.client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=4000,
                    timeout=self._timeout
                )
                
                content = response.choices[0].message.content
                logger.debug(f"API 响应长度: {len(content) if content else 0}")
                if content is None:
                    logger.warning("API 返回空内容")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    return []
                
                result = self._extract_json(content)
                if not result:
                    logger.warning(f"JSON 解析失败，原始内容: {content[:200]}...")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    return []
                
                logger.debug(f"成功解析 {len(result)} 条结果")
                
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
                logger.error(f"批次处理失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
        
        logger.error("批次处理最终失败，跳过此批次")
        return []
    
    def _extract_json(self, text: str):
        """从文本中提取JSON数组，支持处理被截断的JSON"""
        import re
        text = text.strip()
        start = text.find('[')
        end = text.rfind(']')
        
        if start == -1:
            return None
        
        # 尝试正常解析
        if end != -1 and start < end:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
        
        # JSON 可能被截断，尝试修复
        json_text = text[start:]
        
        # 尝试逐个提取完整的对象
        results = []
        pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(pattern, json_text)
        
        for match in matches:
            try:
                obj = json.loads(match)
                if isinstance(obj, dict) and 'index' in obj:
                    results.append(obj)
            except json.JSONDecodeError:
                continue
        
        if results:
            logger.debug(f"通过正则提取了 {len(results)} 个对象")
            return results
        
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
