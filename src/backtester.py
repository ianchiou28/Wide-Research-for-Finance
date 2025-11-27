"""
回测系统
验证基于新闻的预测准确性，评估策略表现
"""

import os
import json
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

# 尝试导入数据库模块
try:
    from database import (
        get_connection, save_prediction, verify_prediction, 
        get_prediction_accuracy, get_reports
    )
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False

class NewsBacktester:
    """基于新闻的策略回测器"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        self.reports_dir = os.path.join(data_dir, 'reports')
        self.weekly_dir = os.path.join(data_dir, 'weekly')
        
        # 存储历史预测
        self.predictions = []
        self.verified_results = []
    
    def load_historical_reports(self, days: int = 30) -> List[Dict]:
        """加载历史报告"""
        reports = []
        cutoff = datetime.now() - timedelta(days=days)
        
        # 从文件加载
        report_files = glob.glob(os.path.join(self.reports_dir, 'report_*.txt'))
        
        for filepath in report_files:
            try:
                mtime = datetime.fromtimestamp(os.path.getctime(filepath))
                if mtime < cutoff:
                    continue
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析报告
                parsed = self._parse_report_for_backtest(content)
                parsed['file_path'] = filepath
                parsed['date'] = mtime.strftime('%Y-%m-%d')
                parsed['timestamp'] = mtime.isoformat()
                reports.append(parsed)
            except Exception as e:
                print(f"加载报告失败 {filepath}: {e}")
        
        # 按时间排序
        reports.sort(key=lambda x: x['timestamp'])
        print(f"✓ 加载了 {len(reports)} 份历史报告")
        return reports
    
    def _parse_report_for_backtest(self, content: str) -> Dict:
        """解析报告内容用于回测"""
        data = {
            'sentiment_overall': 0,
            'sentiment_cn': 0,
            'sentiment_us': 0,
            'hot_topics': [],
            'stocks': [],
            'events': []
        }
        
        lines = content.split('\n')
        
        # 解析情绪指数
        for line in lines:
            if '整体情绪' in line and '指数:' in line:
                try:
                    score = float(line.split('指数:')[1].split(')')[0].strip())
                    data['sentiment_overall'] = score
                except:
                    pass
            if '中国市场' in line and '指数:' in line:
                try:
                    score = float(line.split('指数:')[1].split(')')[0].strip())
                    data['sentiment_cn'] = score
                except:
                    pass
            if '美国市场' in line and '指数:' in line:
                try:
                    score = float(line.split('指数:')[1].split(')')[0].strip())
                    data['sentiment_us'] = score
                except:
                    pass
        
        # 解析股票影响
        for line in lines:
            if '股票影响:' in line:
                stocks_str = line.split('股票影响:')[1].strip()
                for stock in stocks_str.split('|'):
                    stock = stock.strip()
                    if '(' in stock and ')' in stock:
                        symbol = stock.split('(')[0].strip()
                        direction = '上涨' if '↑' in stock else '下跌' if '↓' in stock else '中性'
                        data['stocks'].append({
                            'symbol': symbol,
                            'predicted_direction': direction
                        })
        
        return data
    
    def load_weekly_analyses(self, days: int = 60) -> List[Dict]:
        """加载周报分析数据"""
        analyses = []
        cutoff = datetime.now() - timedelta(days=days)
        
        analysis_files = glob.glob(os.path.join(self.weekly_dir, 'analysis_*.json'))
        
        for filepath in analysis_files:
            try:
                mtime = datetime.fromtimestamp(os.path.getctime(filepath))
                if mtime < cutoff:
                    continue
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data['file_path'] = filepath
                data['date'] = mtime.strftime('%Y-%m-%d')
                data['timestamp'] = mtime.isoformat()
                analyses.append(data)
            except Exception as e:
                print(f"加载周报失败 {filepath}: {e}")
        
        analyses.sort(key=lambda x: x['timestamp'])
        print(f"✓ 加载了 {len(analyses)} 份周报分析")
        return analyses
    
    def extract_predictions(self, reports: List[Dict]) -> List[Dict]:
        """从报告中提取预测"""
        predictions = []
        
        for report in reports:
            date = report.get('date', '')
            
            # 市场预测
            sentiment_cn = report.get('sentiment_cn', 0)
            sentiment_us = report.get('sentiment_us', 0)
            
            # A股预测
            predictions.append({
                'date': date,
                'market': 'A股',
                'symbol': 'SH000001',  # 上证指数
                'predicted_direction': '上涨' if sentiment_cn > 0.2 else '下跌' if sentiment_cn < -0.2 else '震荡',
                'confidence': abs(sentiment_cn),
                'source': 'sentiment'
            })
            
            # 美股预测
            predictions.append({
                'date': date,
                'market': '美股',
                'symbol': 'DJI',  # 道琼斯
                'predicted_direction': '上涨' if sentiment_us > 0.2 else '下跌' if sentiment_us < -0.2 else '震荡',
                'confidence': abs(sentiment_us),
                'source': 'sentiment'
            })
            
            # 个股预测
            for stock in report.get('stocks', []):
                predictions.append({
                    'date': date,
                    'market': self._identify_market(stock['symbol']),
                    'symbol': stock['symbol'],
                    'predicted_direction': stock['predicted_direction'],
                    'confidence': 0.5,  # 默认置信度
                    'source': 'news'
                })
        
        self.predictions = predictions
        print(f"✓ 提取了 {len(predictions)} 条预测")
        return predictions
    
    def _identify_market(self, symbol: str) -> str:
        """识别市场"""
        if symbol.isdigit():
            if symbol.startswith('6'):
                return 'A股'
            else:
                return 'A股'
        return '美股'
    
    def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """获取历史价格数据（需要实现具体的数据源）"""
        # TODO: 接入真实的历史价格数据
        # 可以使用 akshare, tushare 或 yfinance
        return []
    
    def verify_predictions(self, predictions: List[Dict], price_data: Dict[str, List]) -> List[Dict]:
        """验证预测准确性"""
        verified = []
        
        for pred in predictions:
            symbol = pred['symbol']
            date = pred['date']
            predicted_dir = pred['predicted_direction']
            
            # 查找对应的价格数据
            prices = price_data.get(symbol, [])
            
            # 找到预测日期后的价格
            actual_change = None
            for price in prices:
                if price['date'] > date:
                    actual_change = price.get('change_pct', 0)
                    break
            
            if actual_change is not None:
                # 判断实际方向
                if actual_change > 0.5:
                    actual_dir = '上涨'
                elif actual_change < -0.5:
                    actual_dir = '下跌'
                else:
                    actual_dir = '震荡'
                
                is_correct = (predicted_dir == actual_dir) or \
                            (predicted_dir == '震荡' and abs(actual_change) < 1)
                
                verified.append({
                    **pred,
                    'actual_direction': actual_dir,
                    'actual_change': actual_change,
                    'is_correct': is_correct
                })
        
        self.verified_results = verified
        return verified
    
    def calculate_accuracy(self, verified: List[Dict] = None) -> Dict:
        """计算预测准确率"""
        if verified is None:
            verified = self.verified_results
        
        if not verified:
            return {'total': 0, 'correct': 0, 'accuracy': 0}
        
        # 总体准确率
        total = len(verified)
        correct = sum(1 for v in verified if v.get('is_correct', False))
        accuracy = correct / total * 100 if total > 0 else 0
        
        # 按市场分类
        by_market = defaultdict(lambda: {'total': 0, 'correct': 0})
        for v in verified:
            market = v.get('market', 'unknown')
            by_market[market]['total'] += 1
            if v.get('is_correct', False):
                by_market[market]['correct'] += 1
        
        for market in by_market:
            t = by_market[market]['total']
            c = by_market[market]['correct']
            by_market[market]['accuracy'] = c / t * 100 if t > 0 else 0
        
        # 按置信度分层
        high_conf = [v for v in verified if v.get('confidence', 0) > 0.5]
        low_conf = [v for v in verified if v.get('confidence', 0) <= 0.5]
        
        high_correct = sum(1 for v in high_conf if v.get('is_correct', False))
        low_correct = sum(1 for v in low_conf if v.get('is_correct', False))
        
        return {
            'total': total,
            'correct': correct,
            'accuracy': accuracy,
            'by_market': dict(by_market),
            'high_confidence': {
                'total': len(high_conf),
                'correct': high_correct,
                'accuracy': high_correct / len(high_conf) * 100 if high_conf else 0
            },
            'low_confidence': {
                'total': len(low_conf),
                'correct': low_correct,
                'accuracy': low_correct / len(low_conf) * 100 if low_conf else 0
            }
        }
    
    def simulate_trading(self, verified: List[Dict], initial_capital: float = 100000) -> Dict:
        """模拟交易策略"""
        capital = initial_capital
        trades = []
        wins = 0
        losses = 0
        
        for pred in verified:
            if pred.get('predicted_direction') == '震荡':
                continue  # 不交易震荡预测
            
            # 每次交易投入10%资金
            position_size = capital * 0.1
            actual_change = pred.get('actual_change', 0) / 100
            
            # 计算收益
            if pred['predicted_direction'] == '上涨':
                pnl = position_size * actual_change
            else:  # 做空
                pnl = position_size * (-actual_change)
            
            capital += pnl
            
            if pnl > 0:
                wins += 1
            else:
                losses += 1
            
            trades.append({
                'date': pred.get('date'),
                'symbol': pred.get('symbol'),
                'direction': pred['predicted_direction'],
                'pnl': pnl,
                'capital_after': capital
            })
        
        total_trades = wins + losses
        total_return = (capital - initial_capital) / initial_capital * 100
        
        return {
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_return': total_return,
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': wins / total_trades * 100 if total_trades > 0 else 0,
            'trades': trades[-20:]  # 返回最近20笔交易
        }
    
    def generate_report(self) -> Dict:
        """生成回测报告"""
        reports = self.load_historical_reports(30)
        predictions = self.extract_predictions(reports)
        
        # 注意：这里需要真实的价格数据来验证
        # 目前返回基于预测的统计
        
        # 统计预测分布
        direction_counts = defaultdict(int)
        market_counts = defaultdict(int)
        
        for pred in predictions:
            direction_counts[pred['predicted_direction']] += 1
            market_counts[pred['market']] += 1
        
        return {
            'report_date': datetime.now().isoformat(),
            'analysis_period': '30天',
            'total_reports_analyzed': len(reports),
            'total_predictions': len(predictions),
            'prediction_distribution': {
                'by_direction': dict(direction_counts),
                'by_market': dict(market_counts)
            },
            'note': '需要接入历史价格数据以计算真实准确率',
            'recommendations': [
                '建议接入 akshare 或 tushare 获取A股历史数据',
                '建议接入 yfinance 获取美股历史数据',
                '可以设置定时任务自动验证预测结果'
            ]
        }
    
    def backtest_sentiment_strategy(self, reports: List[Dict]) -> Dict:
        """回测基于情绪的交易策略"""
        if not reports:
            reports = self.load_historical_reports(30)
        
        # 模拟策略：情绪 > 0.3 做多，情绪 < -0.3 做空
        signals = []
        
        for i, report in enumerate(reports[:-1]):  # 排除最后一天
            sentiment = report.get('sentiment_cn', 0)
            
            if sentiment > 0.3:
                signals.append({
                    'date': report['date'],
                    'signal': 'BUY',
                    'sentiment': sentiment,
                    'confidence': min(abs(sentiment), 1.0)
                })
            elif sentiment < -0.3:
                signals.append({
                    'date': report['date'],
                    'signal': 'SELL',
                    'sentiment': sentiment,
                    'confidence': min(abs(sentiment), 1.0)
                })
            else:
                signals.append({
                    'date': report['date'],
                    'signal': 'HOLD',
                    'sentiment': sentiment,
                    'confidence': 0
                })
        
        return {
            'strategy_name': '情绪驱动策略',
            'description': '基于新闻情绪指数进行买卖决策',
            'parameters': {
                'buy_threshold': 0.3,
                'sell_threshold': -0.3
            },
            'signals': signals,
            'total_signals': len(signals),
            'buy_signals': sum(1 for s in signals if s['signal'] == 'BUY'),
            'sell_signals': sum(1 for s in signals if s['signal'] == 'SELL'),
            'hold_signals': sum(1 for s in signals if s['signal'] == 'HOLD'),
            'note': '需要历史价格数据来计算实际收益'
        }


class StrategyEvaluator:
    """策略评估器"""
    
    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        if not returns or len(returns) < 2:
            return 0
        
        import statistics
        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        
        if std_return == 0:
            return 0
        
        # 年化
        daily_rf = risk_free_rate / 252
        sharpe = (avg_return - daily_rf) / std_return * (252 ** 0.5)
        return sharpe
    
    @staticmethod
    def calculate_max_drawdown(capital_history: List[float]) -> Tuple[float, int, int]:
        """计算最大回撤"""
        if not capital_history:
            return 0, 0, 0
        
        max_dd = 0
        peak = capital_history[0]
        peak_idx = 0
        trough_idx = 0
        
        for i, value in enumerate(capital_history):
            if value > peak:
                peak = value
                peak_idx = i
            
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
                trough_idx = i
        
        return max_dd * 100, peak_idx, trough_idx
    
    @staticmethod
    def calculate_calmar_ratio(total_return: float, max_drawdown: float) -> float:
        """计算卡玛比率"""
        if max_drawdown == 0:
            return 0
        return total_return / max_drawdown


# 测试
if __name__ == '__main__':
    print("=== 回测系统测试 ===\n")
    
    backtester = NewsBacktester()
    
    # 生成回测报告
    print("1. 生成回测报告...")
    report = backtester.generate_report()
    print(f"   分析了 {report['total_reports_analyzed']} 份报告")
    print(f"   提取了 {report['total_predictions']} 条预测")
    print(f"   预测分布: {report['prediction_distribution']['by_direction']}")
    
    # 回测情绪策略
    print("\n2. 回测情绪策略...")
    strategy_result = backtester.backtest_sentiment_strategy([])
    print(f"   策略: {strategy_result['strategy_name']}")
    print(f"   买入信号: {strategy_result['buy_signals']}")
    print(f"   卖出信号: {strategy_result['sell_signals']}")
    print(f"   持有信号: {strategy_result['hold_signals']}")
    
    print("\n=== 测试完成 ===")
