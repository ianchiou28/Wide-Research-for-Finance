"""
预测优化器
基于回测结果自动优化预测策略，持续提升准确率
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import statistics


class PredictionOptimizer:
    """预测优化器 - 基于历史表现自动调整预测策略"""
    
    def __init__(self):
        self.config_file = 'data/prediction_config.json'
        self.history_file = 'data/optimization_history.json'
        self.config = self._load_config()
        self.history = self._load_history()
    
    def _load_config(self) -> Dict:
        """加载预测配置"""
        default_config = {
            # 方向判定阈值
            'thresholds': {
                'bullish': 1.0,      # 涨幅 > 1% 判定为上涨
                'bearish': -1.0,     # 跌幅 < -1% 判定为下跌
                'verify_days': 5,    # 验证天数
            },
            # 信号权重（根据历史准确率动态调整）
            'signal_weights': {
                '上涨': 1.0,
                '下跌': 1.0,
                '震荡': 1.0,
            },
            # 来源可信度
            'source_reliability': {
                'weekly_analysis': 1.0,
                'monthly_buy': 1.0,
                'monthly_sell': 1.0,
                'sentiment': 0.8,
                'news': 0.7,
            },
            # 股票特定调整（学习每只股票的预测难度）
            'stock_adjustments': {},
            # 时间段调整（某些时段预测更准）
            'time_adjustments': {
                'monday': 1.0,
                'friday': 1.0,
            },
            # 市场环境调整
            'market_regime': {
                'high_volatility': 0.8,  # 高波动时降低权重
                'low_volatility': 1.2,
            },
            # 最低置信度阈值（低于此值的预测不采信）
            'min_confidence': 0.3,
            # 版本
            'version': 1,
            'last_updated': datetime.now().isoformat(),
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    # 合并默认值和保存的配置
                    for key in default_config:
                        if key not in saved:
                            saved[key] = default_config[key]
                    return saved
        except Exception as e:
            print(f"加载配置失败: {e}")
        
        return default_config
    
    def _save_config(self):
        """保存配置"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            self.config['last_updated'] = datetime.now().isoformat()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def _load_history(self) -> Dict:
        """加载优化历史"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {'optimizations': [], 'accuracy_trend': []}
    
    def _save_history(self):
        """保存优化历史"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史失败: {e}")
    
    def analyze_backtest_results(self, weekly_results: Dict, monthly_results: Dict) -> Dict:
        """分析回测结果，找出优化点"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'findings': [],
            'recommendations': [],
            'adjustments': {}
        }
        
        # 1. 分析方向准确率
        direction_analysis = self._analyze_direction_accuracy(weekly_results)
        analysis['direction_analysis'] = direction_analysis
        
        # 2. 分析股票特定表现
        stock_analysis = self._analyze_stock_performance(weekly_results, monthly_results)
        analysis['stock_analysis'] = stock_analysis
        
        # 3. 分析来源可信度
        source_analysis = self._analyze_source_reliability(weekly_results, monthly_results)
        analysis['source_analysis'] = source_analysis
        
        # 4. 分析阈值效果
        threshold_analysis = self._analyze_threshold_effectiveness(weekly_results)
        analysis['threshold_analysis'] = threshold_analysis
        
        # 生成优化建议
        self._generate_recommendations(analysis)
        
        return analysis
    
    def _analyze_direction_accuracy(self, weekly_results: Dict) -> Dict:
        """分析不同方向的预测准确率"""
        verified = weekly_results.get('verified', [])
        
        by_direction = defaultdict(lambda: {'total': 0, 'correct': 0, 'avg_change': []})
        
        for pred in verified:
            direction = pred.get('predicted_direction', '')
            actual_change = pred.get('actual_change_pct', 0)
            is_correct = pred.get('is_correct', False)
            
            by_direction[direction]['total'] += 1
            if is_correct:
                by_direction[direction]['correct'] += 1
            by_direction[direction]['avg_change'].append(actual_change)
        
        result = {}
        for direction, data in by_direction.items():
            total = data['total']
            correct = data['correct']
            changes = data['avg_change']
            
            result[direction] = {
                'total': total,
                'correct': correct,
                'accuracy': round(correct / total * 100, 1) if total > 0 else 0,
                'avg_actual_change': round(statistics.mean(changes), 2) if changes else 0,
                'std_change': round(statistics.stdev(changes), 2) if len(changes) > 1 else 0
            }
        
        return result
    
    def _analyze_stock_performance(self, weekly_results: Dict, monthly_results: Dict) -> Dict:
        """分析每只股票的预测表现"""
        stock_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
        
        # 周报预测
        for pred in weekly_results.get('verified', []):
            symbol = pred.get('symbol', '')
            if symbol:
                stock_stats[symbol]['total'] += 1
                if pred.get('is_correct'):
                    stock_stats[symbol]['correct'] += 1
        
        # 月报预测
        for pred in monthly_results.get('verified_stocks', []):
            symbol = pred.get('symbol', '')
            if symbol:
                stock_stats[symbol]['total'] += 1
                if pred.get('is_correct'):
                    stock_stats[symbol]['correct'] += 1
        
        # 计算每只股票的准确率
        result = {}
        for symbol, data in stock_stats.items():
            if data['total'] >= 3:  # 至少3次预测才统计
                accuracy = data['correct'] / data['total'] * 100
                result[symbol] = {
                    'total': data['total'],
                    'correct': data['correct'],
                    'accuracy': round(accuracy, 1),
                    # 难以预测的股票降低权重
                    'suggested_weight': max(0.5, min(1.5, accuracy / 50))
                }
        
        return result
    
    def _analyze_source_reliability(self, weekly_results: Dict, monthly_results: Dict) -> Dict:
        """分析不同来源的可信度"""
        source_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
        
        for pred in weekly_results.get('verified', []):
            source = pred.get('source', 'unknown')
            source_stats[source]['total'] += 1
            if pred.get('is_correct'):
                source_stats[source]['correct'] += 1
        
        for pred in monthly_results.get('verified_stocks', []):
            source = pred.get('source', 'unknown')
            source_stats[source]['total'] += 1
            if pred.get('is_correct'):
                source_stats[source]['correct'] += 1
        
        result = {}
        for source, data in source_stats.items():
            if data['total'] >= 5:
                accuracy = data['correct'] / data['total'] * 100
                result[source] = {
                    'total': data['total'],
                    'correct': data['correct'],
                    'accuracy': round(accuracy, 1),
                    'suggested_weight': max(0.3, min(1.5, accuracy / 50))
                }
        
        return result
    
    def _analyze_threshold_effectiveness(self, weekly_results: Dict) -> Dict:
        """分析当前阈值的效果，尝试找最优阈值"""
        verified = weekly_results.get('verified', [])
        
        if not verified:
            return {}
        
        # 尝试不同阈值
        thresholds_to_try = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        best_threshold = 1.0
        best_accuracy = 0
        
        results = {}
        
        for threshold in thresholds_to_try:
            correct = 0
            total = 0
            
            for pred in verified:
                actual_change = pred.get('actual_change_pct', 0)
                predicted_dir = pred.get('predicted_direction', '')
                
                # 使用新阈值判定
                if actual_change > threshold:
                    actual_dir = '上涨'
                elif actual_change < -threshold:
                    actual_dir = '下跌'
                else:
                    actual_dir = '震荡'
                
                is_correct = (predicted_dir == actual_dir) or \
                            (predicted_dir == '震荡' and abs(actual_change) < threshold * 2)
                
                total += 1
                if is_correct:
                    correct += 1
            
            accuracy = correct / total * 100 if total > 0 else 0
            results[threshold] = {
                'accuracy': round(accuracy, 1),
                'correct': correct,
                'total': total
            }
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_threshold = threshold
        
        return {
            'current_threshold': self.config['thresholds']['bullish'],
            'best_threshold': best_threshold,
            'best_accuracy': round(best_accuracy, 1),
            'all_results': results
        }
    
    def _generate_recommendations(self, analysis: Dict):
        """基于分析生成优化建议"""
        recommendations = []
        adjustments = {}
        
        # 1. 方向权重调整
        direction_analysis = analysis.get('direction_analysis', {})
        for direction, data in direction_analysis.items():
            if data['total'] >= 10:
                accuracy = data['accuracy']
                if accuracy < 30:
                    recommendations.append(f"⚠️ {direction}预测准确率过低({accuracy}%)，建议降低权重或反向操作")
                    adjustments[f'signal_weights.{direction}'] = 0.5
                elif accuracy > 60:
                    recommendations.append(f"✓ {direction}预测表现良好({accuracy}%)，可提高权重")
                    adjustments[f'signal_weights.{direction}'] = 1.3
        
        # 2. 阈值调整
        threshold_analysis = analysis.get('threshold_analysis', {})
        if threshold_analysis:
            current = threshold_analysis.get('current_threshold', 1.0)
            best = threshold_analysis.get('best_threshold', 1.0)
            best_acc = threshold_analysis.get('best_accuracy', 0)
            
            if best != current:
                recommendations.append(f"📊 建议将阈值从{current}%调整为{best}%，可将准确率提升至{best_acc}%")
                adjustments['thresholds.bullish'] = best
                adjustments['thresholds.bearish'] = -best
        
        # 3. 来源可信度调整
        source_analysis = analysis.get('source_analysis', {})
        for source, data in source_analysis.items():
            if data['total'] >= 10:
                suggested = data['suggested_weight']
                current = self.config['source_reliability'].get(source, 1.0)
                if abs(suggested - current) > 0.2:
                    recommendations.append(f"📰 来源'{source}'可信度建议调整为{suggested:.2f}")
                    adjustments[f'source_reliability.{source}'] = suggested
        
        # 4. 股票特定调整
        stock_analysis = analysis.get('stock_analysis', {})
        difficult_stocks = []
        easy_stocks = []
        for symbol, data in stock_analysis.items():
            if data['accuracy'] < 30:
                difficult_stocks.append(symbol)
                adjustments[f'stock_adjustments.{symbol}'] = 0.5
            elif data['accuracy'] > 60:
                easy_stocks.append(symbol)
                adjustments[f'stock_adjustments.{symbol}'] = 1.3
        
        if difficult_stocks:
            recommendations.append(f"⚠️ 难以预测股票: {', '.join(difficult_stocks[:5])}，已降低权重")
        if easy_stocks:
            recommendations.append(f"✓ 易于预测股票: {', '.join(easy_stocks[:5])}，已提高权重")
        
        analysis['recommendations'] = recommendations
        analysis['adjustments'] = adjustments
    
    def apply_optimizations(self, analysis: Dict, auto_apply: bool = True) -> Dict:
        """应用优化调整"""
        adjustments = analysis.get('adjustments', {})
        applied = []
        
        for key, value in adjustments.items():
            parts = key.split('.')
            
            if len(parts) == 2:
                section, param = parts
                if section in self.config:
                    if isinstance(self.config[section], dict):
                        old_value = self.config[section].get(param, 'N/A')
                        if auto_apply:
                            self.config[section][param] = value
                        applied.append({
                            'key': key,
                            'old': old_value,
                            'new': value,
                            'applied': auto_apply
                        })
        
        if auto_apply and applied:
            self.config['version'] += 1
            self._save_config()
            
            # 记录优化历史
            self.history['optimizations'].append({
                'timestamp': datetime.now().isoformat(),
                'changes': applied,
                'analysis_summary': {
                    'direction': analysis.get('direction_analysis', {}),
                    'threshold': analysis.get('threshold_analysis', {}).get('best_threshold')
                }
            })
            self._save_history()
        
        return {
            'applied': applied,
            'auto_apply': auto_apply,
            'new_version': self.config['version']
        }
    
    def get_adjusted_prediction(self, prediction: Dict) -> Dict:
        """根据优化配置调整预测"""
        symbol = prediction.get('symbol', '')
        source = prediction.get('source', '')
        direction = prediction.get('predicted_direction', '')
        confidence = prediction.get('confidence', 0.5)
        
        # 获取各种权重
        signal_weight = self.config['signal_weights'].get(direction, 1.0)
        source_weight = self.config['source_reliability'].get(source, 1.0)
        stock_weight = self.config['stock_adjustments'].get(symbol, 1.0)
        
        # 计算调整后的置信度
        adjusted_confidence = confidence * signal_weight * source_weight * stock_weight
        
        # 如果下跌预测历史准确率很低，考虑反转
        if direction == '下跌' and signal_weight < 0.6:
            # 反转预测
            adjusted_direction = '上涨'
            adjusted_confidence *= 0.7  # 反转预测降低置信度
        else:
            adjusted_direction = direction
        
        return {
            **prediction,
            'adjusted_direction': adjusted_direction,
            'adjusted_confidence': min(1.0, adjusted_confidence),
            'weights_applied': {
                'signal': signal_weight,
                'source': source_weight,
                'stock': stock_weight
            },
            'should_trade': adjusted_confidence >= self.config['min_confidence']
        }
    
    def get_optimization_summary(self) -> Dict:
        """获取优化摘要"""
        # 计算准确率趋势
        accuracy_trend = []
        for opt in self.history.get('optimizations', [])[-10:]:
            direction = opt.get('analysis_summary', {}).get('direction', {})
            total = sum(d.get('total', 0) for d in direction.values())
            correct = sum(d.get('correct', 0) for d in direction.values())
            if total > 0:
                accuracy_trend.append({
                    'date': opt['timestamp'][:10],
                    'accuracy': round(correct / total * 100, 1)
                })
        
        return {
            'current_config': {
                'thresholds': self.config['thresholds'],
                'signal_weights': self.config['signal_weights'],
                'min_confidence': self.config['min_confidence'],
            },
            'version': self.config['version'],
            'last_updated': self.config['last_updated'],
            'total_optimizations': len(self.history.get('optimizations', [])),
            'accuracy_trend': accuracy_trend,
            'difficult_stocks': [k for k, v in self.config.get('stock_adjustments', {}).items() if v < 0.7],
            'reliable_sources': [k for k, v in self.config.get('source_reliability', {}).items() if v > 1.1]
        }


def run_optimization():
    """运行优化流程"""
    print(f"\n{'='*60}")
    print(f"🔧 预测优化系统")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    optimizer = PredictionOptimizer()
    
    # 加载回测结果
    weekly_results = {}
    monthly_results = {}
    
    try:
        with open('data/weekly_backtest_results.json', 'r', encoding='utf-8') as f:
            weekly_results = json.load(f)
    except:
        print("⚠️ 未找到周报回测结果")
    
    try:
        with open('data/monthly_backtest_results.json', 'r', encoding='utf-8') as f:
            monthly_results = json.load(f)
    except:
        print("⚠️ 未找到月报回测结果")
    
    if not weekly_results.get('verified') and not monthly_results.get('verified_stocks'):
        print("❌ 无回测数据可供分析，请先运行回测")
        return None
    
    # 分析回测结果
    print("📊 分析回测结果...")
    analysis = optimizer.analyze_backtest_results(weekly_results, monthly_results)
    
    # 输出分析结果
    print("\n【方向准确率分析】")
    for direction, data in analysis.get('direction_analysis', {}).items():
        acc = data['accuracy']
        icon = '✓' if acc >= 50 else '⚠️' if acc >= 35 else '❌'
        print(f"  {icon} {direction}: {data['correct']}/{data['total']} ({acc}%)")
    
    print("\n【阈值优化】")
    threshold = analysis.get('threshold_analysis', {})
    if threshold:
        print(f"  当前阈值: {threshold.get('current_threshold')}%")
        print(f"  建议阈值: {threshold.get('best_threshold')}% (准确率: {threshold.get('best_accuracy')}%)")
    
    print("\n【优化建议】")
    for rec in analysis.get('recommendations', []):
        print(f"  {rec}")
    
    # 应用优化
    print("\n📝 应用优化...")
    result = optimizer.apply_optimizations(analysis, auto_apply=True)
    
    if result['applied']:
        print(f"  ✓ 已应用 {len(result['applied'])} 项优化")
        for change in result['applied'][:5]:
            print(f"    - {change['key']}: {change['old']} → {change['new']}")
        print(f"  配置版本: v{result['new_version']}")
    else:
        print("  无需调整")
    
    # 保存分析报告
    report_file = 'data/optimization_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis,
            'applied': result['applied'],
            'summary': optimizer.get_optimization_summary()
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 优化报告已保存: {report_file}")
    
    return analysis


if __name__ == '__main__':
    run_optimization()
