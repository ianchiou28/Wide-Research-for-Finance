"""
多模型集成分析器
通过多次不同温度的 LLM 调用取中位值，提升情绪判断的稳健性。
"""

import os
import sys
import json
import statistics
from typing import List, Dict, Optional
from logger import setup_logger

try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))
    from settings import Config
except ImportError:
    Config = None

logger = setup_logger('ensemble_analyzer')


class EnsembleAnalyzer:
    """
    对同一批文章以不同 temperature 调用 LLM，
    取 sentiment 中位数作为最终值，用标准差衡量置信度。
    """

    # 默认温度组合：低温（保守）→ 中温（平衡）→ 高温（激进）
    DEFAULT_TEMPERATURES = [0.1, 0.3, 0.5]

    def __init__(self, temperatures: Optional[List[float]] = None,
                 min_agreement: float = 0.6):
        """
        Parameters
        ----------
        temperatures : list[float]
            每次调用使用的 temperature
        min_agreement : float
            方向投票达到此比例才采纳多数意见，否则标为"震荡"
        """
        self.temperatures = temperatures or self.DEFAULT_TEMPERATURES
        self.min_agreement = min_agreement

        try:
            from openai import OpenAI
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if Config:
                kw = Config.get_llm_client_kwargs()
                kw['api_key'] = api_key
                self._client = OpenAI(**kw)
                self._model = Config.LLM_MODEL
                self._timeout = Config.LLM_TIMEOUT
            else:
                self._client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com",
                    timeout=120.0,
                    max_retries=2,
                )
                self._model = "deepseek-chat"
                self._timeout = 120.0
        except Exception as e:
            logger.warning(f"EnsembleAnalyzer 初始化失败: {e}")
            self._client = None

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def analyze(self, prompt: str, n_articles: int) -> List[Dict]:
        """
        以多温度调用 LLM 并集成结果。

        Parameters
        ----------
        prompt : str
            完整的分析 prompt（不含 temperature 部分）。
        n_articles : int
            文章数量，用于校验返回条数。

        Returns
        -------
        list[dict]
            每篇文章的集成分析结果，新增字段:
            - sentiment_std  : 标准差（越小越确信）
            - ensemble_confidence : 置信度标签 (高/中/低)
        """
        if not self._client:
            logger.warning("EnsembleAnalyzer 无可用 client")
            return []

        all_runs: List[List[Dict]] = []

        for temp in self.temperatures:
            try:
                result = self._call_llm(prompt, temp)
                if result and len(result) >= n_articles * 0.5:
                    all_runs.append(result)
                else:
                    logger.warning(f"temp={temp} 返回条数不足，跳过")
            except Exception as e:
                logger.warning(f"temp={temp} 调用失败: {e}")

        if not all_runs:
            return []

        if len(all_runs) == 1:
            # 只拿到一次结果，直接返回
            return all_runs[0]

        return self._merge(all_runs, n_articles)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _call_llm(self, prompt: str, temperature: float) -> List[Dict]:
        """单次 LLM 调用"""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=4000,
            timeout=self._timeout,
        )
        content = response.choices[0].message.content
        if not content:
            return []
        return self._extract_json(content)

    def _merge(self, runs: List[List[Dict]], n_articles: int) -> List[Dict]:
        """
        合并多次调用结果: 中位数 sentiment, 投票 direction, stdev → confidence。
        """
        # 按 index 分组
        by_index: Dict[int, List[Dict]] = {}
        for run in runs:
            for item in run:
                idx = item.get('index', 0)
                by_index.setdefault(idx, []).append(item)

        merged = []
        for idx in sorted(by_index.keys()):
            items = by_index[idx]
            if not items:
                continue

            base = dict(items[0])  # 复制首次结果作为基础

            # 中位数 sentiment
            for key in ('sentiment', 'sentiment_cn', 'sentiment_us'):
                values = [it.get(key, 0) for it in items]
                values = [v for v in values if isinstance(v, (int, float))]
                if values:
                    base[key] = round(statistics.median(values), 3)

            # sentiment 标准差 → 置信度
            sentiments = [it.get('sentiment', 0) for it in items]
            sentiments = [v for v in sentiments if isinstance(v, (int, float))]
            if len(sentiments) >= 2:
                std = statistics.stdev(sentiments)
                base['sentiment_std'] = round(std, 4)
                if std < 0.1:
                    base['ensemble_confidence'] = '高'
                elif std < 0.25:
                    base['ensemble_confidence'] = '中'
                else:
                    base['ensemble_confidence'] = '低'
            else:
                base['sentiment_std'] = 0
                base['ensemble_confidence'] = '中'

            # impact_level 投票
            levels = [it.get('impact_level', '中') for it in items]
            base['impact_level'] = max(set(levels), key=levels.count)

            # event_type 投票
            types = [it.get('event_type', '其他') for it in items]
            base['event_type'] = max(set(types), key=types.count)

            merged.append(base)

        return merged

    @staticmethod
    def _extract_json(text: str) -> List[Dict]:
        """从 LLM 返回中提取 JSON 数组"""
        import re
        text = text.strip()
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1 and start < end:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        results = []
        pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        for m in re.findall(pattern, text):
            try:
                obj = json.loads(m)
                if isinstance(obj, dict) and 'index' in obj:
                    results.append(obj)
            except json.JSONDecodeError:
                continue
        return results
