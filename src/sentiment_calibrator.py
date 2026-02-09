"""
情绪评分校准器
- 时间衰减权重：越新的新闻权重越大
- 来源权重：高信誉 > 低信誉
- 历史偏差校正：基于回测结果修正系统性偏差
"""

import math
import json
import os
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from logger import setup_logger

logger = setup_logger('sentiment_calibrator')


# ============== 来源可信度权重 ==============
# 权重含义：1.0 = 基准，>1.0 = 高可信，<1.0 = 低可信
SOURCE_WEIGHTS: Dict[str, float] = {
    # 官方 / 国际权威
    'Reuters':        1.4,
    'Bloomberg':      1.4,
    'WSJ':            1.3,
    'Financial Times': 1.3,
    'CNBC':           1.2,
    'AP News':        1.2,
    '美联储':          1.5,
    'SEC公告':         1.4,
    '中国人民银行':     1.5,
    '证监会':          1.4,
    '新华社':          1.3,

    # 国内财经
    '同花顺':          1.0,
    '东方财富':         1.0,
    '财联社':          1.1,
    '第一财经':         1.1,
    '证券时报':         1.1,
    '经济参考报':       1.1,

    # 社交 / 热搜
    '微博热搜':         0.6,
    '百度热搜':         0.6,
    '抖音热搜':         0.5,
    '头条热搜':         0.6,
    '知乎热搜':         0.7,

    # RSS 聚合
    'Yahoo Finance':   1.1,
    'MarketWatch':     1.1,
    'Seeking Alpha':   1.0,
    'Investing.com':   1.0,
}


def _time_decay_weight(hours_ago: float, half_life: float = 6.0) -> float:
    """
    时间衰减权重，指数衰减。
    half_life=6 表示 6 小时后权重减半。
    
    weight = exp(-ln2 / half_life * hours_ago)
    """
    if hours_ago <= 0:
        return 1.0
    decay_rate = math.log(2) / half_life
    return math.exp(-decay_rate * hours_ago)


def _source_weight(source_name: str) -> float:
    """获取来源权重，未知来源返回 0.8"""
    return SOURCE_WEIGHTS.get(source_name, 0.8)


class SentimentCalibrator:
    """情绪评分校准器"""

    def __init__(self, bias_file: str = 'data/sentiment_bias.json'):
        self._bias_file = bias_file
        self._bias = self._load_bias()  # {market: offset}

    # ----------------------------------------------------------------
    # 公开接口
    # ----------------------------------------------------------------

    def calibrate_batch(
        self,
        articles: List[Dict],
        reference_time: Optional[datetime] = None,
        half_life: float = 6.0,
    ) -> Dict[str, float]:
        """
        对一批新闻做加权平均情绪评分。

        每条 article 至少需要:
            - sentiment (float)
            - sentiment_cn (float, optional)
            - sentiment_us (float, optional)
            - source (str)
            - published_at (ISO str or datetime)

        返回:
            {
                'overall': 加权评分,
                'cn': 加权评分,
                'us': 加权评分,
                'article_count': n,
                'effective_weight': 总权重
            }
        """
        if not articles:
            return {'overall': 0, 'cn': 0, 'us': 0,
                    'article_count': 0, 'effective_weight': 0}

        ref = reference_time or datetime.now()

        weighted_overall = 0.0
        weighted_cn = 0.0
        weighted_us = 0.0
        total_weight = 0.0

        for art in articles:
            # 1) 时间权重
            pub = art.get('published_at')
            if isinstance(pub, str):
                try:
                    pub = datetime.fromisoformat(pub)
                except Exception:
                    pub = ref  # 无法解析就当做最新
            elif not isinstance(pub, datetime):
                pub = ref
            hours_ago = max(0, (ref - pub).total_seconds() / 3600)
            tw = _time_decay_weight(hours_ago, half_life)

            # 2) 来源权重
            sw = _source_weight(art.get('source', ''))

            # 3) 影响力权重 (高影响 = 1.5, 中 = 1.0, 低 = 0.7)
            impact = art.get('impact_level', '中')
            iw = {'高': 1.5, '中': 1.0, '低': 0.7}.get(impact, 1.0)

            w = tw * sw * iw

            weighted_overall += art.get('sentiment', 0) * w
            weighted_cn += art.get('sentiment_cn', art.get('sentiment', 0)) * w
            weighted_us += art.get('sentiment_us', art.get('sentiment', 0)) * w
            total_weight += w

        if total_weight == 0:
            return {'overall': 0, 'cn': 0, 'us': 0,
                    'article_count': len(articles), 'effective_weight': 0}

        raw = {
            'overall': weighted_overall / total_weight,
            'cn': weighted_cn / total_weight,
            'us': weighted_us / total_weight,
        }

        # 4) 偏差校正
        calibrated = {
            'overall': self._apply_bias(raw['overall'], 'overall'),
            'cn':      self._apply_bias(raw['cn'], 'cn'),
            'us':      self._apply_bias(raw['us'], 'us'),
            'article_count': len(articles),
            'effective_weight': round(total_weight, 2),
        }
        return calibrated

    def calibrate_single(self, article: Dict, reference_time: Optional[datetime] = None) -> Dict:
        """
        校准单条新闻的情绪分，返回带权重信息的新字段。
        不修改原 dict，返回新 dict。
        """
        ref = reference_time or datetime.now()
        pub = article.get('published_at')
        if isinstance(pub, str):
            try:
                pub = datetime.fromisoformat(pub)
            except Exception:
                pub = ref
        elif not isinstance(pub, datetime):
            pub = ref

        hours_ago = max(0, (ref - pub).total_seconds() / 3600)
        tw = _time_decay_weight(hours_ago)
        sw = _source_weight(article.get('source', ''))
        impact = article.get('impact_level', '中')
        iw = {'高': 1.5, '中': 1.0, '低': 0.7}.get(impact, 1.0)
        combined_weight = round(tw * sw * iw, 3)

        raw_sentiment = article.get('sentiment', 0)
        calibrated_sentiment = self._apply_bias(raw_sentiment * combined_weight, 'overall')

        return {
            **article,
            'calibrated_sentiment': round(calibrated_sentiment, 3),
            'weight': combined_weight,
            'weight_detail': {
                'time_decay': round(tw, 3),
                'source': round(sw, 2),
                'impact': round(iw, 1),
            },
        }

    # ----------------------------------------------------------------
    # 偏差校正（基于历史回测学习）
    # ----------------------------------------------------------------

    def learn_bias(self, predictions: List[Dict], actuals: List[Dict]) -> Dict[str, float]:
        """
        根据历史「预测情绪 vs 实际涨跌」计算系统性偏差。
        predictions: [ {date, sentiment_cn, sentiment_us, sentiment_overall} ]
        actuals:     [ {date, actual_cn_change, actual_us_change} ]

        偏差 = mean(predicted - actual_direction_mapped)
        """
        if not predictions or not actuals:
            return self._bias

        actual_map = {a['date']: a for a in actuals}
        errors = {'overall': [], 'cn': [], 'us': []}

        for pred in predictions:
            actual = actual_map.get(pred.get('date'))
            if not actual:
                continue

            # 将实际涨跌映射到 [-1, 1]
            def change_to_sentiment(change_pct: float) -> float:
                """将涨跌幅映射到情绪空间"""
                return max(-1.0, min(1.0, change_pct / 3.0))

            act_cn = change_to_sentiment(actual.get('actual_cn_change', 0))
            act_us = change_to_sentiment(actual.get('actual_us_change', 0))
            act_all = (act_cn + act_us) / 2

            errors['cn'].append(pred.get('sentiment_cn', 0) - act_cn)
            errors['us'].append(pred.get('sentiment_us', 0) - act_us)
            errors['overall'].append(pred.get('sentiment_overall', 0) - act_all)

        new_bias = {}
        for market, errs in errors.items():
            if len(errs) >= 5:  # 至少 5 个样本才计算偏差
                new_bias[market] = round(statistics.mean(errs), 4)
                logger.info(f"情绪偏差 [{market}]: {new_bias[market]:+.4f} (基于 {len(errs)} 个样本)")
            else:
                new_bias[market] = self._bias.get(market, 0)

        self._bias = new_bias
        self._save_bias()
        return new_bias

    def _apply_bias(self, raw_score: float, market: str) -> float:
        """
        减去系统性偏差，并 clip 到 [-1, 1]。
        如果系统总是偏乐观 +0.15，则减去 0.15。
        """
        bias = self._bias.get(market, 0)
        corrected = raw_score - bias
        return max(-1.0, min(1.0, round(corrected, 4)))

    def _load_bias(self) -> Dict[str, float]:
        try:
            if os.path.exists(self._bias_file):
                with open(self._bias_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {'overall': 0, 'cn': 0, 'us': 0}

    def _save_bias(self):
        try:
            os.makedirs(os.path.dirname(self._bias_file), exist_ok=True)
            with open(self._bias_file, 'w', encoding='utf-8') as f:
                json.dump(self._bias, f, ensure_ascii=False, indent=2)
            logger.info(f"偏差参数已保存: {self._bias}")
        except Exception as e:
            logger.warning(f"保存偏差参数失败: {e}")

    # ----------------------------------------------------------------
    # 辅助: 来源权重管理
    # ----------------------------------------------------------------

    @staticmethod
    def get_source_weight(source: str) -> float:
        return _source_weight(source)

    @staticmethod
    def list_source_weights() -> Dict[str, float]:
        return dict(SOURCE_WEIGHTS)

    def get_bias(self) -> Dict[str, float]:
        return dict(self._bias)
