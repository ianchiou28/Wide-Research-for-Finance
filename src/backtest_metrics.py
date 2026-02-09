"""
专业回测指标计算模块
覆盖: Sharpe / Sortino / Max Drawdown / Calmar / IC / 统计显著性 / 基准比较
"""

import math
import statistics
from typing import List, Dict, Tuple, Optional
from logger import setup_logger

logger = setup_logger('backtest_metrics')


class BacktestMetrics:
    """统一计算各项回测质量指标"""

    # ------------------------------------------------------------------
    # 准确率 & 精确率 / 召回率
    # ------------------------------------------------------------------

    @staticmethod
    def accuracy(predictions: List[Dict], actuals: List[Dict],
                 pred_key: str = 'predicted_direction',
                 actual_key: str = 'actual_direction') -> Dict:
        """
        方向预测的准确率、精确率、召回率。
        支持多分类(上涨/下跌/震荡)，同时保留二分类 TP/FP/FN/TN 指标(以 '上涨' 为正类)。
        """
        if not predictions or not actuals:
            return {'accuracy': 0, 'precision': 0, 'recall': 0, 'f1': 0, 'n': 0}

        actual_map = {a.get('date', a.get('analysis_date', '')): a for a in actuals}
        tp = fp = fn = tn = 0
        total_match = 0
        total_count = 0
        # 按方向统计
        class_stats = {}

        for p in predictions:
            key = p.get('date', p.get('analysis_date', ''))
            a = actual_map.get(key)
            if not a:
                continue
            pred_dir = p.get(pred_key, '')
            act_dir = a.get(actual_key, '')
            total_count += 1

            # 多分类准确率
            if pred_dir == act_dir:
                total_match += 1

            # 按方向统计
            for d in [pred_dir, act_dir]:
                if d and d not in class_stats:
                    class_stats[d] = {'tp': 0, 'fp': 0, 'fn': 0}
            if pred_dir == act_dir and pred_dir in class_stats:
                class_stats[pred_dir]['tp'] += 1
            else:
                if pred_dir in class_stats:
                    class_stats[pred_dir]['fp'] += 1
                if act_dir in class_stats:
                    class_stats[act_dir]['fn'] += 1

            # 保留二分类(上涨 vs 非上涨)指标
            is_positive_pred = pred_dir == '上涨'
            is_positive_act = act_dir == '上涨'
            if is_positive_pred and is_positive_act:
                tp += 1
            elif is_positive_pred and not is_positive_act:
                fp += 1
            elif not is_positive_pred and is_positive_act:
                fn += 1
            else:
                tn += 1

        overall_accuracy = (total_match / total_count * 100) if total_count else 0
        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

        # 计算每个方向的 precision/recall
        per_class = {}
        for d, s in class_stats.items():
            d_prec = s['tp'] / (s['tp'] + s['fp']) if (s['tp'] + s['fp']) else 0
            d_rec = s['tp'] / (s['tp'] + s['fn']) if (s['tp'] + s['fn']) else 0
            per_class[d] = {'precision': round(d_prec * 100, 2), 'recall': round(d_rec * 100, 2)}

        return {
            'accuracy': round(overall_accuracy, 2),
            'precision': round(precision * 100, 2),
            'recall': round(recall * 100, 2),
            'f1': round(f1 * 100, 2),
            'n': total_count,
            'num_classes': len(class_stats),
            'per_class': per_class,
            'confusion': {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn},
        }

    # ------------------------------------------------------------------
    # 收益相关指标
    # ------------------------------------------------------------------

    @staticmethod
    def sharpe_ratio(returns: List[float],
                     risk_free_rate: float = 0.02,
                     periods_per_year: int = 252) -> float:
        """
        年化夏普比率。
        returns: 每期收益率列表 (如 0.01 = 1%)
        """
        if not returns or len(returns) < 2:
            return 0.0
        avg = statistics.mean(returns)
        std = statistics.stdev(returns)
        if std == 0:
            return 0.0
        rf_per_period = risk_free_rate / periods_per_year
        return round((avg - rf_per_period) / std * math.sqrt(periods_per_year), 4)

    @staticmethod
    def sortino_ratio(returns: List[float],
                      risk_free_rate: float = 0.02,
                      periods_per_year: int = 252) -> float:
        """
        Sortino 比率 — 仅惩罚下行波动。
        """
        if not returns or len(returns) < 2:
            return 0.0
        avg = statistics.mean(returns)
        rf_per_period = risk_free_rate / periods_per_year
        downside = [r for r in returns if r < rf_per_period]
        if not downside:
            # 无下行波动，返回封顶值而非 inf，避免 JSON 序列化失败
            return 99.99 if avg > rf_per_period else 0.0
        dd_std = math.sqrt(sum((r - rf_per_period) ** 2 for r in downside) / len(downside))
        if dd_std == 0:
            return 0.0
        result = (avg - rf_per_period) / dd_std * math.sqrt(periods_per_year)
        # 封顶防止极端值
        return round(min(max(result, -99.99), 99.99), 4)

    @staticmethod
    def max_drawdown(equity_curve: List[float]) -> Dict:
        """
        最大回撤。
        equity_curve: 资金曲线（如 [100000, 102000, 99000, ...]）
        返回: {max_dd_pct, peak_idx, trough_idx, recovery_idx}
        """
        if not equity_curve or len(equity_curve) < 2:
            return {'max_dd_pct': 0, 'peak_idx': 0, 'trough_idx': 0}

        peak = equity_curve[0]
        peak_idx = 0
        max_dd = 0.0
        best_peak_idx = 0
        best_trough_idx = 0

        for i, v in enumerate(equity_curve):
            if v > peak:
                peak = v
                peak_idx = i
            dd = (peak - v) / peak if peak else 0
            if dd > max_dd:
                max_dd = dd
                best_peak_idx = peak_idx
                best_trough_idx = i

        return {
            'max_dd_pct': round(max_dd * 100, 2),
            'peak_idx': best_peak_idx,
            'trough_idx': best_trough_idx,
        }

    @staticmethod
    def calmar_ratio(annualized_return: float, max_dd_pct: float) -> float:
        """Calmar 比率 = 年化收益 / 最大回撤"""
        if max_dd_pct == 0:
            return 0.0
        return round(annualized_return / max_dd_pct, 4)

    # ------------------------------------------------------------------
    # 信息系数 (IC)
    # ------------------------------------------------------------------

    @staticmethod
    def information_coefficient(predicted_scores: List[float],
                                actual_returns: List[float]) -> Dict:
        """
        IC = rank_correlation(预测情绪, 实际涨跌幅)
        使用 Spearman rank 相关系数。
        """
        n = min(len(predicted_scores), len(actual_returns))
        if n < 5:
            return {'ic': 0, 'n': n, 'significant': False}

        # Spearman rank correlation（手动实现，避免引入 scipy）
        def _rank(data):
            sorted_pairs = sorted(enumerate(data), key=lambda x: x[1])
            ranks = [0.0] * len(data)
            i = 0
            while i < len(sorted_pairs):
                j = i
                while j < len(sorted_pairs) - 1 and sorted_pairs[j + 1][1] == sorted_pairs[i][1]:
                    j += 1
                avg_rank = (i + j) / 2.0 + 1
                for k in range(i, j + 1):
                    ranks[sorted_pairs[k][0]] = avg_rank
                i = j + 1
            return ranks

        pred_rank = _rank(predicted_scores[:n])
        act_rank = _rank(actual_returns[:n])

        d_sq_sum = sum((p - a) ** 2 for p, a in zip(pred_rank, act_rank))
        rho = 1 - (6 * d_sq_sum) / (n * (n ** 2 - 1)) if n > 1 else 0

        # 显著性检验 (t-test)
        if abs(rho) < 1 and n > 2:
            t_stat = rho * math.sqrt((n - 2) / (1 - rho ** 2))
            # 近似 p < 0.05 当 |t| > 2.0 (df >= 20)
            significant = abs(t_stat) > 2.0
        else:
            t_stat = 0
            significant = False

        return {
            'ic': round(rho, 4),
            't_stat': round(t_stat, 4),
            'n': n,
            'significant': significant,
        }

    # ------------------------------------------------------------------
    # 统计显著性 (vs 随机)
    # ------------------------------------------------------------------

    @staticmethod
    def significance_test(accuracy_pct: float, n: int,
                          null_accuracy: float = None,
                          num_classes: int = 3) -> Dict:
        """
        二项检验：给定准确率是否显著高于随机猜测。
        自动检测分类数: 2分类基线50%, 3分类基线33.33%。
        使用正态近似。
        """
        if n == 0:
            return {'z_stat': 0, 'p_value': 1.0, 'significant': False, 'n': 0}

        # 自动推断基线
        if null_accuracy is None:
            null_accuracy = 100.0 / num_classes

        p_hat = accuracy_pct / 100
        p0 = null_accuracy / 100
        se = math.sqrt(p0 * (1 - p0) / n) if n > 0 else 1

        z = (p_hat - p0) / se if se > 0 else 0

        # 正态分布 CDF 近似 (Abramowitz & Stegun)
        def _norm_cdf(x):
            if x < -8:
                return 0.0
            if x > 8:
                return 1.0
            a1, a2, a3 = 0.254829592, -0.284496736, 1.421413741
            a4, a5 = -1.453152027, 1.061405429
            p = 0.3275911
            sign = 1 if x >= 0 else -1
            x = abs(x) / math.sqrt(2)
            t = 1.0 / (1.0 + p * x)
            y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
            return 0.5 * (1.0 + sign * y)

        p_value = 1 - _norm_cdf(z)  # 单尾

        return {
            'z_stat': round(z, 4),
            'p_value': round(p_value, 6),
            'significant': p_value < 0.05,
            'n': n,
            'null_accuracy': null_accuracy,
        }

    # ------------------------------------------------------------------
    # 综合报告
    # ------------------------------------------------------------------

    @classmethod
    def full_report(cls, predictions: List[Dict], actuals: List[Dict],
                    equity_curve: Optional[List[float]] = None,
                    period_returns: Optional[List[float]] = None) -> Dict:
        """
        一次性计算所有指标，返回汇总字典。
        """
        acc = cls.accuracy(predictions, actuals)

        # 提取 predicted_scores 和 actual_returns 用于 IC
        actual_map = {a.get('date', a.get('analysis_date', '')): a for a in actuals}
        pred_scores = []
        act_returns = []
        for p in predictions:
            key = p.get('date', p.get('analysis_date', ''))
            a = actual_map.get(key)
            if a:
                pred_scores.append(p.get('confidence', 0.5) *
                                   (1 if p.get('predicted_direction') == '上涨' else -1))
                act_returns.append(a.get('actual_change_pct', a.get('actual_change', 0)))

        ic = cls.information_coefficient(pred_scores, act_returns)
        sig = cls.significance_test(acc['accuracy'], acc['n'])

        report = {
            'accuracy': acc,
            'ic': ic,
            'significance': sig,
        }

        if period_returns:
            report['sharpe_ratio'] = cls.sharpe_ratio(period_returns)
            report['sortino_ratio'] = cls.sortino_ratio(period_returns)

        if equity_curve:
            dd = cls.max_drawdown(equity_curve)
            report['max_drawdown'] = dd
            if period_returns:
                total_ret = (equity_curve[-1] / equity_curve[0] - 1) * 100 if equity_curve[0] else 0
                report['calmar_ratio'] = cls.calmar_ratio(total_ret, dd['max_dd_pct'])

        return report
