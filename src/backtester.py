"""
回测系统
验证基于新闻的预测准确性，评估策略表现
支持：周度分析回测、月度分析回测、自动验证
"""

import os
import re
import json
import glob
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger('backtester')

# ---- 统一回测配置 ----
DEFAULT_BACKTEST_CONFIG = {
    'weekly_threshold': 1.0,    # 周报: ±1% 判定涨跌
    'monthly_threshold': 2.0,   # 月报: ±2% 判定涨跌
    'event_threshold': 1.0,     # 事件: ±1% 判定利多利空
    'neutral_tolerance': 2.0,   # 震荡容忍度
    'verify_days_weekly': 5,
    'verify_days_monthly': 10,
}


def _load_backtest_config() -> Dict:
    """从 prediction_config.json 加载阈值，带默认回退"""
    cfg = dict(DEFAULT_BACKTEST_CONFIG)
    try:
        path = 'data/prediction_config.json'
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            thresholds = data.get('thresholds', {})
            if 'bullish' in thresholds:
                cfg['weekly_threshold'] = float(thresholds['bullish'])
            if 'bearish' in thresholds:
                pass  # 使用 bullish 的绝对值即可
            if 'verify_days' in thresholds:
                cfg['verify_days_weekly'] = int(thresholds['verify_days'])
    except Exception:
        pass
    return cfg


def _parse_timestamp_from_filename(filepath: str) -> datetime:
    """从文件名中解析 YYYYMMDD_HHMMSS 时间戳"""
    basename = os.path.basename(filepath)
    m = re.search(r'(\d{8})_(\d{6})', basename)
    if m:
        return datetime.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S')
    m = re.search(r'(\d{8})', basename)
    if m:
        return datetime.strptime(m.group(1), '%Y%m%d')
    return datetime.fromtimestamp(os.path.getmtime(filepath))

# 尝试导入价格数据源
try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    print("提示: 安装 akshare 可获取A股数据 (pip install akshare)")

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("提示: 安装 yfinance 可获取美股数据 (pip install yfinance)")

# 尝试导入数据库模块
try:
    from database import (
        get_connection, save_prediction, verify_prediction, 
        get_prediction_accuracy, get_reports
    )
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False

# 导入专业回测指标计算
try:
    from backtest_metrics import BacktestMetrics
    HAS_METRICS = True
except ImportError:
    HAS_METRICS = False


class PriceDataFetcher:
    """价格数据获取器"""
    
    def __init__(self):
        self.cache = {}  # 缓存价格数据
        self.cache_file = 'data/price_cache.json'
        self._load_cache()
    
    def _load_cache(self):
        """加载价格缓存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
        except:
            self.cache = {}
    
    def _save_cache(self):
        """保存价格缓存"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False)
        except:
            pass
    
    def get_cn_stock_price(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """获取A股价格数据"""
        if not HAS_AKSHARE:
            return []
        
        cache_key = f"cn_{symbol}_{start_date}_{end_date}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # 转换股票代码格式
            if symbol.startswith('6'):
                ak_symbol = f"sh{symbol}"
            elif symbol.startswith('0') or symbol.startswith('3'):
                ak_symbol = f"sz{symbol}"
            elif symbol in ['SH000001', '000001.SH']:
                ak_symbol = "sh000001"  # 上证指数
            elif symbol in ['SZ399001', '399001.SZ']:
                ak_symbol = "sz399001"  # 深证成指
            else:
                ak_symbol = symbol
            
            # 获取日线数据
            df = ak.stock_zh_a_hist(symbol=ak_symbol.replace('sh', '').replace('sz', ''), 
                                     period="daily",
                                     start_date=start_date.replace('-', ''),
                                     end_date=end_date.replace('-', ''),
                                     adjust="qfq")
            
            prices = []
            for _, row in df.iterrows():
                prices.append({
                    'date': str(row['日期']),
                    'open': float(row['开盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'close': float(row['收盘']),
                    'volume': float(row['成交量']),
                    'change_pct': float(row['涨跌幅'])
                })
            
            self.cache[cache_key] = prices
            self._save_cache()
            return prices
            
        except Exception as e:
            logger.warning(f"获取A股数据失败 {symbol}: {e}")
            return []
    
    def get_us_stock_price(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """获取美股价格数据（优先yfinance，备用akshare）"""
        cache_key = f"us_{symbol}_{start_date}_{end_date}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        prices = []
        
        # 方案 1: yfinance
        if HAS_YFINANCE:
            try:
                # 转换指数代码
                yf_symbol = symbol
                if symbol == 'DJI':
                    yf_symbol = '^DJI'
                elif symbol == 'SPX' or symbol == 'SP500':
                    yf_symbol = '^GSPC'
                elif symbol == 'IXIC' or symbol == 'NASDAQ':
                    yf_symbol = '^IXIC'
                
                ticker = yf.Ticker(yf_symbol)
                df = ticker.history(start=start_date, end=end_date)
                
                prev_close = None
                for date, row in df.iterrows():
                    close = float(row['Close'])
                    change_pct = ((close - prev_close) / prev_close * 100) if prev_close else 0
                    prices.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': close,
                        'volume': float(row['Volume']),
                        'change_pct': change_pct
                    })
                    prev_close = close
                
                if prices:
                    self.cache[cache_key] = prices
                    self._save_cache()
                    return prices
                else:
                    logger.warning(f"yfinance 返回空数据 {symbol} ({start_date} ~ {end_date})")
                    
            except Exception as e:
                logger.warning(f"yfinance 获取失败 {symbol}: {e}")
        
        # 方案 2: akshare 获取美股数据 (备用)
        if HAS_AKSHARE and not prices:
            try:
                df = ak.stock_us_daily(symbol=symbol, adjust="qfq")
                if df is not None and not df.empty:
                    # 筛选日期范围
                    df['date'] = df['date'].astype(str)
                    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
                    df = df[mask]
                    
                    prev_close = None
                    for _, row in df.iterrows():
                        close = float(row['close'])
                        change_pct = ((close - prev_close) / prev_close * 100) if prev_close else 0
                        prices.append({
                            'date': str(row['date']),
                            'open': float(row['open']),
                            'high': float(row['high']),
                            'low': float(row['low']),
                            'close': close,
                            'volume': float(row.get('volume', 0)),
                            'change_pct': change_pct
                        })
                        prev_close = close
                    
                    if prices:
                        self.cache[cache_key] = prices
                        self._save_cache()
                        return prices
                    else:
                        logger.warning(f"akshare 美股返回空数据 {symbol} ({start_date} ~ {end_date})")
            except Exception as e:
                logger.warning(f"akshare 美股获取失败 {symbol}: {e}")
        
        if not prices:
            logger.error(f"所有数据源均无法获取 {symbol} ({start_date} ~ {end_date}), HAS_YFINANCE={HAS_YFINANCE}, HAS_AKSHARE={HAS_AKSHARE}")
        return prices
    
    def get_price(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """自动识别市场并获取价格"""
        # 判断市场
        if symbol.isdigit() or symbol.startswith('SH') or symbol.startswith('SZ'):
            return self.get_cn_stock_price(symbol, start_date, end_date)
        else:
            return self.get_us_stock_price(symbol, start_date, end_date)
    
    def get_price_change(self, symbol: str, date: str, days_after: int = 1) -> Optional[float]:
        """获取指定日期后的价格变化百分比"""
        try:
            start = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            logger.warning(f"日期格式错误: {date}")
            return None
        end = start + timedelta(days=days_after + 5)  # 多取几天防止节假日
        
        prices = self.get_price(symbol, date, end.strftime('%Y-%m-%d'))
        
        if len(prices) < 2:
            logger.warning(f"价格数据不足: {symbol} ({date} ~ {end.strftime('%Y-%m-%d')}), "
                          f"获取到 {len(prices)} 条, HAS_AKSHARE={HAS_AKSHARE}, HAS_YFINANCE={HAS_YFINANCE}")
            return None
        
        # 返回days_after天后的涨跌幅
        if len(prices) > days_after:
            return sum(p['change_pct'] for p in prices[1:days_after+1])
        return prices[-1]['change_pct'] if prices else None

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
                mtime = _parse_timestamp_from_filename(filepath)
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
                logger.warning(f"加载报告失败 {filepath}: {e}")
        
        # 按时间排序
        reports.sort(key=lambda x: x['timestamp'])
        logger.info(f"加载了 {len(reports)} 份历史报告")
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
                mtime = _parse_timestamp_from_filename(filepath)
                if mtime < cutoff:
                    continue
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data['file_path'] = filepath
                data['date'] = mtime.strftime('%Y-%m-%d')
                data['timestamp'] = mtime.isoformat()
                analyses.append(data)
            except Exception as e:
                logger.warning(f"加载周报失败 {filepath}: {e}")
        
        analyses.sort(key=lambda x: x['timestamp'])
        logger.info(f"加载了 {len(analyses)} 份周报分析")
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
                # 使用统一配置阈值
                cfg = _load_backtest_config()
                thresh = cfg['weekly_threshold']
                if actual_change > thresh:
                    actual_dir = '上涨'
                elif actual_change < -thresh:
                    actual_dir = '下跌'
                else:
                    actual_dir = '震荡'
                
                is_correct = (predicted_dir == actual_dir) or \
                            (predicted_dir == '震荡' and abs(actual_change) < cfg['neutral_tolerance'])
                
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
        
        result = {
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_return': total_return,
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': wins / total_trades * 100 if total_trades > 0 else 0,
            'trades': trades  # 返回全部交易记录
        }
        
        # ---- 专业指标增强 ----
        if HAS_METRICS and trades:
            equity_curve = [initial_capital] + [t['capital_after'] for t in trades]
            period_returns = []
            for i in range(1, len(equity_curve)):
                prev = equity_curve[i - 1]
                period_returns.append((equity_curve[i] - prev) / prev if prev else 0)
            
            dd = BacktestMetrics.max_drawdown(equity_curve)
            result['sharpe_ratio'] = BacktestMetrics.sharpe_ratio(period_returns)
            result['sortino_ratio'] = BacktestMetrics.sortino_ratio(period_returns)
            result['max_drawdown_pct'] = dd['max_dd_pct']
            result['calmar_ratio'] = BacktestMetrics.calmar_ratio(total_return, dd['max_dd_pct'])
        
        return result
    
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


# StrategyEvaluator 已移除 -- 功能完全被 BacktestMetrics 覆盖


class WeeklyAnalysisBacktester:
    """周度分析回测器"""
    
    def __init__(self):
        self.weekly_dir = 'data/weekly'
        self.results_file = 'data/weekly_backtest_results.json'
        self.price_fetcher = PriceDataFetcher()
        self.results = self._load_results()
    
    def _load_results(self) -> Dict:
        """加载历史回测结果"""
        try:
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {'verified': [], 'stats': {}}
    
    def _save_results(self):
        """保存回测结果"""
        try:
            os.makedirs(os.path.dirname(self.results_file), exist_ok=True)
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def load_weekly_analyses(self, days: int = 60) -> List[Dict]:
        """加载周报分析"""
        analyses = []
        cutoff = datetime.now() - timedelta(days=days)
        
        files = glob.glob(os.path.join(self.weekly_dir, 'analysis_*.json'))
        
        for filepath in files:
            try:
                mtime = _parse_timestamp_from_filename(filepath)
                if mtime < cutoff:
                    continue
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data['file_path'] = filepath
                data['analysis_date'] = mtime.strftime('%Y-%m-%d')
                analyses.append(data)
            except Exception as e:
                logger.warning(f"加载周报失败 {filepath}: {e}")
                continue
        
        analyses.sort(key=lambda x: x.get('analysis_date', ''))
        logger.info(f"[Weekly] 加载了 {len(analyses)} 份周报分析")
        return analyses
    
    def extract_predictions(self, analysis: Dict) -> List[Dict]:
        """从周报中提取预测"""
        predictions = []
        analysis_date = analysis.get('analysis_date', '')
        
        # 提取股票预测
        for stock in analysis.get('stocks', []):
            symbol = stock.get('symbol', '')
            prediction = stock.get('prediction', '')
            
            # 标准化预测方向
            if '看涨' in prediction or '上涨' in prediction or '买入' in prediction:
                direction = '上涨'
            elif '看跌' in prediction or '下跌' in prediction or '卖出' in prediction:
                direction = '下跌'
            else:
                direction = '震荡'
            
            predictions.append({
                'analysis_date': analysis_date,
                'symbol': symbol,
                'name': stock.get('name', ''),
                'predicted_direction': direction,
                'original_prediction': prediction,
                'reason': stock.get('reason', ''),
                'source': 'weekly_analysis'
            })
        
        return predictions
    
    def verify_prediction(self, prediction: Dict, days_after: int = 5) -> Dict:
        """验证单个预测"""
        symbol = prediction['symbol']
        pred_date = prediction['analysis_date']
        predicted_dir = prediction['predicted_direction']
        
        # 获取价格变化
        actual_change = self.price_fetcher.get_price_change(symbol, pred_date, days_after)
        
        if actual_change is None:
            logger.warning(f"[Weekly] 无法获取价格数据: {symbol} @ {pred_date}")
            return {**prediction, 'verified': False, 'reason': f'无法获取价格数据 ({symbol})'}
        
        # 使用统一配置阈值
        cfg = _load_backtest_config()
        thresh = cfg['weekly_threshold']
        
        if actual_change > thresh:
            actual_dir = '上涨'
        elif actual_change < -thresh:
            actual_dir = '下跌'
        else:
            actual_dir = '震荡'
        
        # 判断是否正确
        is_correct = (predicted_dir == actual_dir) or \
                    (predicted_dir == '震荡' and abs(actual_change) < cfg['neutral_tolerance'])
        
        return {
            **prediction,
            'verified': True,
            'actual_change_pct': round(actual_change, 2),
            'actual_direction': actual_dir,
            'is_correct': is_correct,
            'verify_date': datetime.now().strftime('%Y-%m-%d'),
            'days_after': days_after
        }
    
    def run_backtest(self, days: int = 60, verify_days: int = 5) -> Dict:
        """运行周报回测"""
        logger.info(f"{'='*60}")
        logger.info("周度分析回测")
        logger.info(f"{'='*60}")
        
        # 加载周报
        analyses = self.load_weekly_analyses(days)
        logger.info(f"加载了 {len(analyses)} 份周报")
        
        if not analyses:
            empty_stats = {
                'total_predictions': 0,
                'total_extracted': 0,
                'unverified': 0,
                'accuracy': 0,
                'backtest_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'period_days': days,
                'verify_days': verify_days,
                'note': f'回看 {days} 天内无周报数据'
            }
            self.results['verified'] = []
            self.results['stats'] = empty_stats
            self._save_results()
            return {'error': '无周报数据', 'stats': empty_stats}
        
        # 提取并验证预测
        all_predictions = []
        verified_predictions = []
        price_failures = []  # 诊断：记录价格获取失败的symbol
        skipped_too_recent = 0
        
        for analysis in analyses:
            predictions = self.extract_predictions(analysis)
            all_predictions.extend(predictions)
            
            if not predictions:
                logger.info(f"[Weekly] 文件 {os.path.basename(analysis.get('file_path', '?'))} stocks 为空，跳过")
            
            # 只验证7天前的预测（确保有足够时间验证）
            analysis_date = datetime.strptime(analysis.get('analysis_date', '2000-01-01'), '%Y-%m-%d')
            if datetime.now() - analysis_date > timedelta(days=verify_days + 2):
                for pred in predictions:
                    verified = self.verify_prediction(pred, verify_days)
                    if verified.get('verified'):
                        verified_predictions.append(verified)
                    else:
                        reason = verified.get('reason', '未知')
                        logger.warning(f"[Weekly] 预测验证失败: {pred.get('symbol')} @ {pred.get('analysis_date')} - {reason}")
                        price_failures.append({
                            'symbol': pred.get('symbol'),
                            'date': pred.get('analysis_date'),
                            'reason': reason,
                        })
            else:
                skipped_too_recent += len(predictions)
                if predictions:
                    logger.info(f"[Weekly] 分析日期 {analysis.get('analysis_date')} 距今不足 {verify_days+2} 天，暂不验证 {len(predictions)} 条预测")
        
        logger.info(f"[Weekly] 汇总: 提取 {len(all_predictions)} 条, 已验证 {len(verified_predictions)} 条, "
                    f"价格获取失败 {len(price_failures)} 条, 太新未验证 {skipped_too_recent} 条")
        
        # 计算准确率
        if verified_predictions:
            correct = sum(1 for v in verified_predictions if v.get('is_correct'))
            accuracy = correct / len(verified_predictions) * 100
            
            # 按方向统计
            by_direction = defaultdict(lambda: {'total': 0, 'correct': 0})
            for v in verified_predictions:
                d = v['predicted_direction']
                by_direction[d]['total'] += 1
                if v.get('is_correct'):
                    by_direction[d]['correct'] += 1
            
            for d in by_direction:
                t = by_direction[d]['total']
                c = by_direction[d]['correct']
                by_direction[d]['accuracy'] = round(c / t * 100, 1) if t > 0 else 0
            
            stats = {
                'total_predictions': len(verified_predictions),
                'total_extracted': len(all_predictions),
                'unverified': len(all_predictions) - len(verified_predictions),
                'correct_predictions': correct,
                'accuracy': round(accuracy, 1),
                'by_direction': dict(by_direction),
                'backtest_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'period_days': days,
                'verify_days': verify_days,
                'price_failures': len(price_failures),
                'skipped_too_recent': skipped_too_recent,
                'failed_symbols': list(set(f['symbol'] for f in price_failures))[:20],
            }
        else:
            stats = {
                'total_predictions': 0,
                'total_extracted': len(all_predictions),
                'unverified': len(all_predictions),
                'accuracy': 0,
                'backtest_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'period_days': days,
                'verify_days': verify_days,
                'price_failures': len(price_failures),
                'skipped_too_recent': skipped_too_recent,
                'failed_symbols': list(set(f['symbol'] for f in price_failures))[:20],
                'note': f'共提取 {len(all_predictions)} 条预测: '
                        f'{len(price_failures)} 条价格获取失败, '
                        f'{skipped_too_recent} 条太新未验证'
            }
        
        # ---- 专业指标增强 ----
        if HAS_METRICS and verified_predictions:
            # IC (Information Coefficient)
            pred_scores = []
            act_returns = []
            for v in verified_predictions:
                conf = v.get('confidence', 0.5)
                sign = 1 if v.get('predicted_direction') == '上涨' else -1
                pred_scores.append(conf * sign)
                act_returns.append(v.get('actual_change_pct', v.get('actual_change', 0)))
            
            ic_result = BacktestMetrics.information_coefficient(pred_scores, act_returns)
            stats['ic'] = ic_result['ic']
            stats['ic_significant'] = ic_result['significant']
            
            # 显著性检验
            sig_result = BacktestMetrics.significance_test(
                stats.get('accuracy', 0), len(verified_predictions)
            )
            stats['significance'] = {
                'z_stat': sig_result['z_stat'],
                'p_value': sig_result['p_value'],
                'significant': sig_result['significant'],
            }
        
        # 保存结果
        self.results['verified'] = verified_predictions[-100:]  # 保留最近100条
        self.results['stats'] = stats
        self._save_results()
        
        # 打印结果
        logger.info(f"【回测结果】")
        logger.info(f"  总预测数: {stats.get('total_predictions', 0)}")
        logger.info(f"  准确率: {stats.get('accuracy', 0):.1f}%")
        if stats.get('by_direction'):
            logger.info(f"  按方向:")
            for d, s in stats['by_direction'].items():
                logger.info(f"    {d}: {s['correct']}/{s['total']} ({s['accuracy']:.1f}%)")
        if stats.get('ic') is not None:
            sig_mark = '✓' if stats.get('ic_significant') else '✗'
            logger.info(f"  IC (信息系数): {stats['ic']:.4f} [{sig_mark}显著]")
        if stats.get('significance'):
            sig = stats['significance']
            sig_mark = '✓' if sig['significant'] else '✗'
            logger.info(f"  统计检验: z={sig['z_stat']:.2f}, p={sig['p_value']:.4f} [{sig_mark}显著]")
        
        if stats.get('price_failures', 0) > 0:
            logger.warning(f"  ⚠ 价格获取失败 {stats['price_failures']} 条, "
                          f"失败symbol: {stats.get('failed_symbols', [])}")
        
        return {
            'stats': stats,
            'verified_predictions': verified_predictions,
            'all_predictions': len(all_predictions),
            'price_failures': price_failures[:20],  # 诊断用，最多返回20条
        }
    
    def get_accuracy_report(self) -> Dict:
        """获取准确率报告"""
        return self.results.get('stats', {})


class MonthlyAnalysisBacktester:
    """月度分析回测器"""
    
    def __init__(self):
        self.monthly_dir = 'data/monthly'
        self.results_file = 'data/monthly_backtest_results.json'
        self.price_fetcher = PriceDataFetcher()
        self.results = self._load_results()
    
    def _load_results(self) -> Dict:
        """加载历史回测结果"""
        try:
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {'verified_events': [], 'verified_stocks': [], 'stats': {}}
    
    def _save_results(self):
        """保存回测结果"""
        try:
            os.makedirs(os.path.dirname(self.results_file), exist_ok=True)
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def load_monthly_analyses(self, days: int = 90) -> List[Dict]:
        """加载月度分析"""
        analyses = []
        cutoff = datetime.now() - timedelta(days=days)
        
        files = glob.glob(os.path.join(self.monthly_dir, 'analysis_*.json'))
        
        for filepath in files:
            try:
                mtime = _parse_timestamp_from_filename(filepath)
                if mtime < cutoff:
                    continue
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data['file_path'] = filepath
                data['file_date'] = mtime.strftime('%Y-%m-%d')
                analyses.append(data)
            except Exception as e:
                logger.warning(f"加载月度分析失败 {filepath}: {e}")
                continue
        
        analyses.sort(key=lambda x: x.get('generated_at', ''))
        logger.info(f"[Monthly] 加载了 {len(analyses)} 份月度分析")
        return analyses
    
    def extract_stock_predictions(self, analysis: Dict) -> List[Dict]:
        """从月度分析中提取股票预测"""
        predictions = []
        gen_date = analysis.get('generated_at', '')[:10]
        
        recs = analysis.get('stock_recommendations', {})
        
        # 买入建议 -> 预测上涨
        for stock in recs.get('buy', []):
            predictions.append({
                'analysis_date': gen_date,
                'symbol': stock.get('symbol', ''),
                'name': stock.get('name', ''),
                'predicted_direction': '上涨',
                'target_price': stock.get('target_price', ''),
                'stop_loss': stock.get('stop_loss', ''),
                'reason': stock.get('reason', ''),
                'source': 'monthly_buy'
            })
        
        # 卖出建议 -> 预测下跌
        for stock in recs.get('sell', []):
            predictions.append({
                'analysis_date': gen_date,
                'symbol': stock.get('symbol', ''),
                'name': stock.get('name', ''),
                'predicted_direction': '下跌',
                'reason': stock.get('reason', ''),
                'source': 'monthly_sell'
            })
        
        return predictions
    
    def extract_event_predictions(self, analysis: Dict) -> List[Dict]:
        """从月度分析中提取事件预测"""
        predictions = []
        gen_date = analysis.get('generated_at', '')[:10]
        
        for event in analysis.get('event_analysis', []):
            # 提取预期方向
            impact = event.get('impact', {})
            stocks_impact = impact.get('stocks', '')
            
            if '利多' in stocks_impact or '上涨' in stocks_impact or '积极' in stocks_impact:
                direction = '利多'
            elif '利空' in stocks_impact or '下跌' in stocks_impact or '消极' in stocks_impact:
                direction = '利空'
            else:
                direction = '中性'
            
            predictions.append({
                'analysis_date': gen_date,
                'event_name': event.get('event', ''),
                'event_date': event.get('date', ''),
                'predicted_direction': direction,
                'market_expectation': event.get('market_expectation', ''),
                'scenarios': event.get('scenarios', {}),
                'source': 'monthly_event'
            })
        
        return predictions
    
    def verify_stock_prediction(self, prediction: Dict, days_after: int = 10) -> Dict:
        """验证股票预测"""
        symbol = prediction['symbol']
        pred_date = prediction['analysis_date']
        predicted_dir = prediction['predicted_direction']
        
        actual_change = self.price_fetcher.get_price_change(symbol, pred_date, days_after)
        
        if actual_change is None:
            logger.warning(f"[Monthly] 无法获取价格数据: {symbol} @ {pred_date}")
            return {**prediction, 'verified': False, 'reason': f'无法获取价格数据 ({symbol})'}
        
        # 使用统一配置阈值
        cfg = _load_backtest_config()
        thresh = cfg['monthly_threshold']
        
        if actual_change > thresh:
            actual_dir = '上涨'
        elif actual_change < -thresh:
            actual_dir = '下跌'
        else:
            actual_dir = '震荡'
        
        is_correct = (predicted_dir == actual_dir)
        
        return {
            **prediction,
            'verified': True,
            'actual_change_pct': round(actual_change, 2),
            'actual_direction': actual_dir,
            'is_correct': is_correct,
            'verify_date': datetime.now().strftime('%Y-%m-%d'),
            'days_after': days_after
        }
    
    def verify_event_prediction(self, prediction: Dict) -> Dict:
        """验证事件预测（事件发生后）"""
        event_date = prediction.get('event_date', '')
        
        # 检查事件是否已发生
        if not event_date:
            return {**prediction, 'verified': False, 'reason': '无事件日期'}
        
        try:
            event_dt = datetime.strptime(event_date, '%Y-%m-%d')
            if event_dt > datetime.now():
                return {**prediction, 'verified': False, 'reason': '事件尚未发生'}
        except:
            return {**prediction, 'verified': False, 'reason': '日期格式错误'}
        
        # 获取事件后的市场反应（使用上证指数作为A股代表）
        actual_change = self.price_fetcher.get_price_change('SH000001', event_date, 3)
        
        if actual_change is None:
            # 尝试美股
            actual_change = self.price_fetcher.get_price_change('SPX', event_date, 3)
        
        if actual_change is None:
            return {**prediction, 'verified': False, 'reason': '无法获取市场数据'}
        
        # 使用统一配置阈值
        cfg = _load_backtest_config()
        thresh = cfg['event_threshold']
        
        if actual_change > thresh:
            actual_impact = '利多'
        elif actual_change < -thresh:
            actual_impact = '利空'
        else:
            actual_impact = '中性'
        
        is_correct = (prediction['predicted_direction'] == actual_impact) or \
                    (prediction['predicted_direction'] == '中性' and abs(actual_change) < cfg['neutral_tolerance'])
        
        return {
            **prediction,
            'verified': True,
            'actual_market_change': round(actual_change, 2),
            'actual_impact': actual_impact,
            'is_correct': is_correct,
            'verify_date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def run_backtest(self, days: int = 90) -> Dict:
        """运行月度分析回测"""
        logger.info(f"{'='*60}")
        logger.info("月度分析回测")
        logger.info(f"{'='*60}")
        
        # 加载月度分析
        analyses = self.load_monthly_analyses(days)
        logger.info(f"加载了 {len(analyses)} 份月度分析")
        
        if not analyses:
            empty_stats = {
                'stock_predictions': {
                    'total': 0, 'total_extracted': 0, 'unverified': 0,
                    'correct': 0, 'accuracy': 0
                },
                'event_predictions': {
                    'total': 0, 'total_extracted': 0, 'unverified': 0,
                    'correct': 0, 'accuracy': 0
                },
                'backtest_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'period_days': days,
                'note': f'回看 {days} 天内无月度分析数据'
            }
            self.results['verified_stocks'] = []
            self.results['verified_events'] = []
            self.results['stats'] = empty_stats
            self._save_results()
            return {'error': '无月度分析数据', 'stats': empty_stats}
        
        all_stock_preds = []
        all_event_preds = []
        verified_stocks = []
        verified_events = []
        stock_price_failures = []
        event_failures = []
        skipped_too_recent = 0
        
        for analysis in analyses:
            # 提取预测
            stock_preds = self.extract_stock_predictions(analysis)
            event_preds = self.extract_event_predictions(analysis)
            
            all_stock_preds.extend(stock_preds)
            all_event_preds.extend(event_preds)
            
            logger.info(f"[Monthly] 文件 {os.path.basename(analysis.get('file_path', '?'))}: "
                        f"股票 {len(stock_preds)} 条, 事件 {len(event_preds)} 条")
            
            # 验证（只验证12天前的预测）
            analysis_date = analysis.get('generated_at', '2000-01-01')[:10]
            try:
                analysis_dt = datetime.strptime(analysis_date, '%Y-%m-%d')
                if datetime.now() - analysis_dt > timedelta(days=12):
                    for pred in stock_preds:
                        verified = self.verify_stock_prediction(pred)
                        if verified.get('verified'):
                            verified_stocks.append(verified)
                        else:
                            reason = verified.get('reason', '未知')
                            logger.warning(f"[Monthly] 股票验证失败: {pred.get('symbol')} @ {pred.get('analysis_date')} - {reason}")
                            stock_price_failures.append({
                                'symbol': pred.get('symbol'),
                                'date': pred.get('analysis_date'),
                                'reason': reason,
                            })
                else:
                    skipped_too_recent += len(stock_preds)
                    if stock_preds:
                        logger.info(f"[Monthly] 分析日期 {analysis_date} 距今不足 12 天，暂不验证 {len(stock_preds)} 条股票预测")
            except Exception as e:
                logger.warning(f"[Monthly] 日期解析失败 {analysis_date}: {e}")
            
            # 验证事件预测
            for pred in event_preds:
                verified = self.verify_event_prediction(pred)
                if verified.get('verified'):
                    verified_events.append(verified)
                else:
                    reason = verified.get('reason', '未知')
                    logger.info(f"[Monthly] 事件未验证: {pred.get('event_name')} - {reason}")
                    event_failures.append({
                        'event': pred.get('event_name'),
                        'reason': reason,
                    })
        
        logger.info(f"[Monthly] 汇总: 股票 {len(all_stock_preds)} 提取/{len(verified_stocks)} 验证/{len(stock_price_failures)} 失败, "
                    f"事件 {len(all_event_preds)} 提取/{len(verified_events)} 验证/{len(event_failures)} 失败, "
                    f"太新未验证 {skipped_too_recent}")
        
        # 计算统计
        stats = {
            'stock_predictions': {
                'total': len(verified_stocks),
                'total_extracted': len(all_stock_preds),
                'unverified': len(all_stock_preds) - len(verified_stocks),
                'correct': sum(1 for v in verified_stocks if v.get('is_correct')),
                'accuracy': 0
            },
            'event_predictions': {
                'total': len(verified_events),
                'total_extracted': len(all_event_preds),
                'unverified': len(all_event_preds) - len(verified_events),
                'correct': sum(1 for v in verified_events if v.get('is_correct')),
                'accuracy': 0
            },
            'backtest_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'period_days': days,
            'price_failures': len(stock_price_failures),
            'event_failures': len(event_failures),
            'skipped_too_recent': skipped_too_recent,
            'failed_symbols': list(set(f['symbol'] for f in stock_price_failures))[:20],
        }
        
        if stats['stock_predictions']['total'] > 0:
            stats['stock_predictions']['accuracy'] = round(
                stats['stock_predictions']['correct'] / stats['stock_predictions']['total'] * 100, 1
            )
        
        if stats['event_predictions']['total'] > 0:
            stats['event_predictions']['accuracy'] = round(
                stats['event_predictions']['correct'] / stats['event_predictions']['total'] * 100, 1
            )
        
        # ---- 专业指标增强 ----
        if HAS_METRICS and verified_stocks:
            pred_scores = []
            act_returns = []
            for v in verified_stocks:
                sign = 1 if v.get('predicted_direction') == '上涨' else -1
                pred_scores.append(sign * 0.7)
                act_returns.append(v.get('actual_change_pct', 0))
            
            ic_result = BacktestMetrics.information_coefficient(pred_scores, act_returns)
            stats['stock_predictions']['ic'] = ic_result['ic']
            stats['stock_predictions']['ic_significant'] = ic_result['significant']
            
            sig_result = BacktestMetrics.significance_test(
                stats['stock_predictions']['accuracy'],
                stats['stock_predictions']['total'],
                null_accuracy=50.0  # 二分类(买/卖)基线
            )
            stats['stock_predictions']['significance'] = {
                'z_stat': sig_result['z_stat'],
                'p_value': sig_result['p_value'],
                'significant': sig_result['significant'],
            }
        
        if HAS_METRICS and verified_events:
            sig_result = BacktestMetrics.significance_test(
                stats['event_predictions']['accuracy'],
                stats['event_predictions']['total'],
                null_accuracy=33.33
            )
            stats['event_predictions']['significance'] = {
                'z_stat': sig_result['z_stat'],
                'p_value': sig_result['p_value'],
                'significant': sig_result['significant'],
            }
        
        # 保存结果
        self.results['verified_stocks'] = verified_stocks[-50:]
        self.results['verified_events'] = verified_events[-50:]
        self.results['stats'] = stats
        self._save_results()
        
        # 打印结果
        logger.info(f"【回测结果】")
        logger.info(f"  股票预测准确率: {stats['stock_predictions']['accuracy']:.1f}% ({stats['stock_predictions']['correct']}/{stats['stock_predictions']['total']})")
        if stats['stock_predictions'].get('ic') is not None:
            logger.info(f"  股票IC: {stats['stock_predictions']['ic']:.4f}")
        logger.info(f"  事件预测准确率: {stats['event_predictions']['accuracy']:.1f}% ({stats['event_predictions']['correct']}/{stats['event_predictions']['total']})")
        if stats.get('price_failures', 0) > 0:
            logger.warning(f"  ⚠ 股票价格获取失败 {stats['price_failures']} 条, "
                          f"失败symbol: {stats.get('failed_symbols', [])}")
        if stats.get('event_failures', 0) > 0:
            logger.warning(f"  ⚠ 事件验证失败 {stats['event_failures']} 条")
        
        return {
            'stats': stats,
            'verified_stocks': verified_stocks,
            'verified_events': verified_events,
            'stock_price_failures': stock_price_failures[:20],
            'event_failures': event_failures[:20],
        }
    
    def get_accuracy_report(self) -> Dict:
        """获取准确率报告"""
        return self.results.get('stats', {})


def run_daily_verification(auto_optimize: bool = True):
    """每日验证任务 - 验证过去的预测并自动优化"""
    logger.info(f"{'='*60}")
    logger.info(f"每日预测验证 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*60}")
    
    # 诊断信息收集
    diagnostics = {
        'started_at': datetime.now().isoformat(),
        'environment': {
            'has_akshare': HAS_AKSHARE,
            'has_yfinance': HAS_YFINANCE,
            'has_metrics': HAS_METRICS,
            'has_database': HAS_DATABASE,
        },
        'weekly': {},
        'monthly': {},
        'errors': [],
    }
    
    logger.info(f"[环境检测] akshare={HAS_AKSHARE}, yfinance={HAS_YFINANCE}, "
                f"metrics={HAS_METRICS}, database={HAS_DATABASE}")
    
    # 检查数据文件
    weekly_files = glob.glob('data/weekly/analysis_*.json')
    monthly_files = glob.glob('data/monthly/analysis_*.json')
    logger.info(f"[数据文件] 周报 {len(weekly_files)} 份, 月报 {len(monthly_files)} 份")
    
    # 周报回测
    weekly_bt = WeeklyAnalysisBacktester()
    weekly_result = weekly_bt.run_backtest(days=90, verify_days=5)
    diagnostics['weekly'] = {
        'files_found': len(weekly_files),
        'stats': weekly_result.get('stats', {}),
        'all_predictions': weekly_result.get('all_predictions', 0),
    }
    
    # 月报回测
    monthly_bt = MonthlyAnalysisBacktester()
    monthly_result = monthly_bt.run_backtest(days=180)
    diagnostics['monthly'] = {
        'files_found': len(monthly_files),
        'stats': monthly_result.get('stats', {}),
    }
    
    # 汇总报告
    report = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'weekly': weekly_result.get('stats', {}),
        'monthly': monthly_result.get('stats', {}),
        'diagnostics': diagnostics,
    }
    
    # 使用 BacktestMetrics 生成综合指标
    if HAS_METRICS:
        weekly_verified = weekly_result.get('verified_predictions', [])
        monthly_verified = monthly_result.get('verified_stocks', [])
        all_verified = weekly_verified + monthly_verified
        if all_verified:
            full = BacktestMetrics.full_report(
                predictions=all_verified,
                actuals=all_verified,  # verified 条目已包含 actual_direction
            )
            report['professional_metrics'] = full
    
    # 保存汇总
    os.makedirs('data', exist_ok=True)
    with open('data/backtest_summary.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"回测报告已保存到 data/backtest_summary.json")
    
    # 自动优化
    if auto_optimize:
        logger.info(f"{'='*60}")
        logger.info("自动优化预测策略...")
        logger.info(f"{'='*60}")
        
        try:
            from prediction_optimizer import PredictionOptimizer
            
            optimizer = PredictionOptimizer()
            
            # 加载完整的回测结果
            weekly_full = weekly_bt.results
            monthly_full = monthly_bt.results
            
            # 分析并优化
            analysis = optimizer.analyze_backtest_results(weekly_full, monthly_full)
            
            # 输出优化建议
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                logger.info("【优化建议】")
                for rec in recommendations:
                    logger.info(f"  {rec}")
            
            # 自动应用优化
            opt_result = optimizer.apply_optimizations(analysis, auto_apply=True)
            
            if opt_result['applied']:
                logger.info(f"已自动应用 {len(opt_result['applied'])} 项优化")
                report['optimization'] = {
                    'applied': len(opt_result['applied']),
                    'version': opt_result['new_version'],
                    'changes': [c['key'] for c in opt_result['applied']]
                }
            else:
                logger.info("当前配置已是最优，无需调整")
                report['optimization'] = {'applied': 0, 'message': '无需调整'}
            
            # 更新汇总报告
            with open('data/backtest_summary.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"优化过程出错: {e}")
            report['optimization'] = {'error': str(e)}
    
    return report


# 测试
if __name__ == '__main__':
    print("=== 回测系统测试 ===\n")
    
    # 运行每日验证（包含自动优化）
    run_daily_verification(auto_optimize=True)
    
    print("\n=== 测试完成 ===")
