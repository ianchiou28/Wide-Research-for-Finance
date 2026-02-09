"""
Analysis routes blueprint - realtime, backtest, and monthly analysis.
"""
import os
import glob
import json
import logging
import threading
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from web.helpers import (
    safe_filename,
    require_api_key,
    get_realtime_collector,
    get_backtester,
    get_monthly_analyzer,
    parse_timestamp_from_filename,
)

logger = logging.getLogger('web_app')

analysis_bp = Blueprint('analysis', __name__)

# 全局月度分析器实例（用于维持对话状态）
_monthly_analyzer_instance = None

# ---- 异步回测任务状态 ----
_backtest_task = {
    'running': False,
    'started_at': None,
    'finished_at': None,
    'result': None,
    'error': None,
}


def get_monthly_analyzer_instance():
    global _monthly_analyzer_instance
    if _monthly_analyzer_instance is None:
        _monthly_analyzer_instance = get_monthly_analyzer()
    return _monthly_analyzer_instance


@analysis_bp.route('/api/realtime')
def api_realtime():
    """获取实时快讯"""
    collector = get_realtime_collector()
    if not collector:
        return jsonify({'error': '实时采集模块未加载'}), 500

    try:
        data = collector.fetch_all_realtime()
        return jsonify({'data': data, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/backtest/report')
def api_backtest_report():
    """获取回测报告"""
    backtester = get_backtester()
    if not backtester:
        return jsonify({'error': '回测模块未加载'}), 500

    try:
        report = backtester.generate_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/backtest/strategy')
def api_backtest_strategy():
    """回测情绪策略"""
    backtester = get_backtester()
    if not backtester:
        return jsonify({'error': '回测模块未加载'}), 500

    try:
        result = backtester.backtest_sentiment_strategy([])
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== 月度分析 API ==============

@analysis_bp.route('/api/monthly/events')
def api_monthly_events():
    """获取月度重大事件日历"""
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    analyzer = get_monthly_analyzer()
    if not analyzer:
        return jsonify({'error': '月度分析模块未加载'}), 500

    try:
        events = analyzer.get_monthly_events(year, month)
        return jsonify({
            'year': year,
            'month': month,
            'events': events
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/monthly/analysis')
def api_monthly_analysis():
    """获取或生成月度分析"""
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    regenerate = request.args.get('regenerate', 'false').lower() == 'true'

    analyzer = get_monthly_analyzer_instance()
    if not analyzer:
        return jsonify({'error': '月度分析模块未加载'}), 500

    # 获取所有月度分析文件
    monthly_files = glob.glob('data/monthly/analysis_*.json')
    monthly_files.sort(key=lambda f: parse_timestamp_from_filename(f), reverse=True)
    file_names = [os.path.basename(f) for f in monthly_files]

    # 如果请求特定文件
    requested_file = request.args.get('file')
    if requested_file:
        requested_file = safe_filename(requested_file)
        if not requested_file:
            return jsonify({'error': '无效的文件名'}), 400
        file_path = f'data/monthly/{requested_file}'
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['files'] = file_names
                    data['file'] = requested_file
                    analyzer.current_analysis = data  # 设置当前分析用于对话
                    return jsonify(data)
            except Exception as e:
                logger.error(f"读取月度分析文件失败: {e}")
                return jsonify({'error': str(e)}), 500
        return jsonify({'error': '文件不存在'}), 404

    try:
        # 检查是否有当月的分析
        current_month_prefix = f"analysis_{year}{month:02d}"
        existing_analysis = None

        if not regenerate:
            for f in monthly_files:
                if current_month_prefix in f:
                    try:
                        with open(f, 'r', encoding='utf-8') as file:
                            existing_analysis = json.load(file)
                            analyzer.current_analysis = existing_analysis
                        break
                    except:
                        pass

        if existing_analysis and not regenerate:
            existing_analysis['files'] = file_names
            existing_analysis['cached'] = True
            return jsonify(existing_analysis)

        # 生成新分析
        analysis = analyzer.generate_monthly_analysis(year, month)

        if analysis.get('error'):
            return jsonify(analysis), 500

        # 保存
        filename = analyzer.save_analysis(analysis)
        analysis['files'] = [os.path.basename(filename)] + file_names
        analysis['cached'] = False

        return jsonify(analysis)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/monthly/chat', methods=['POST'])
def api_monthly_chat():
    """月度分析对话式追问"""
    data = request.get_json()
    if not data or not data.get('message'):
        return jsonify({'error': '请提供消息内容'}), 400

    analyzer = get_monthly_analyzer_instance()
    if not analyzer:
        return jsonify({'error': '月度分析模块未加载'}), 500

    try:
        # 如果没有当前分析，尝试加载最新的
        if not analyzer.current_analysis:
            latest = analyzer.get_latest_analysis()
            if latest:
                analyzer.current_analysis = latest
            else:
                return jsonify({'error': '请先生成月度分析报告'}), 400

        reply = analyzer.chat(data['message'])
        return jsonify({
            'reply': reply,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/monthly/history')
def api_monthly_history():
    """获取月度分析历史列表"""
    monthly_files = glob.glob('data/monthly/analysis_*.json')
    monthly_files.sort(key=lambda f: parse_timestamp_from_filename(f), reverse=True)

    history = []
    for f in monthly_files:
        try:
            mtime = parse_timestamp_from_filename(f)
            filename = os.path.basename(f)

            # 尝试读取摘要
            summary = ""
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    summary = data.get('summary', '')[:100]
                    month_name = data.get('month', '')
            except:
                month_name = ""

            history.append({
                'file': filename,
                'month': month_name,
                'timestamp': mtime.isoformat(),
                'summary': summary
            })
        except:
            pass

    return jsonify({'data': history})


@analysis_bp.route('/api/monthly/update-event', methods=['POST'])
def api_monthly_update_event():
    """更新事件结果（用于回测）"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供数据'}), 400

    event_id = data.get('event_id')
    actual_result = data.get('actual_result')
    market_reaction = data.get('market_reaction')

    if not all([event_id, actual_result, market_reaction]):
        return jsonify({'error': '请提供完整的事件更新信息'}), 400

    analyzer = get_monthly_analyzer_instance()
    if not analyzer:
        return jsonify({'error': '月度分析模块未加载'}), 500

    try:
        result = analyzer.update_event_result(event_id, actual_result, market_reaction)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ 回测 API ============

@analysis_bp.route('/api/backtest/summary')
def get_backtest_summary():
    """获取回测汇总"""
    try:
        summary_file = 'data/backtest_summary.json'
        if os.path.exists(summary_file):
            with open(summary_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify({'error': '暂无回测数据', 'message': '请先运行回测: python run_backtest.py'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/backtest/weekly')
def get_weekly_backtest():
    """获取周报回测详情"""
    try:
        results_file = 'data/weekly_backtest_results.json'
        if os.path.exists(results_file):
            with open(results_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify({'error': '暂无周报回测数据'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/backtest/monthly')
def get_monthly_backtest():
    """获取月报回测详情"""
    try:
        results_file = 'data/monthly_backtest_results.json'
        if os.path.exists(results_file):
            with open(results_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify({'error': '暂无月报回测数据'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/backtest/run', methods=['POST'])
@require_api_key
def run_backtest():
    """运行回测（异步）- 需要API Key认证"""
    global _backtest_task

    if _backtest_task['running']:
        return jsonify({
            'success': False,
            'message': '回测正在运行中，请稍候',
            'started_at': _backtest_task['started_at'],
        }), 409

    def _run():
        global _backtest_task
        try:
            from backtester import run_daily_verification
            result = run_daily_verification(auto_optimize=True)
            _backtest_task['result'] = result
            _backtest_task['error'] = None
        except Exception as e:
            import traceback
            logger.error(f"Backtest run failed: {e}", exc_info=True)
            _backtest_task['result'] = None
            _backtest_task['error'] = str(e)
            _backtest_task['traceback'] = traceback.format_exc()
        finally:
            _backtest_task['running'] = False
            _backtest_task['finished_at'] = datetime.now().isoformat()

    _backtest_task = {
        'running': True,
        'started_at': datetime.now().isoformat(),
        'finished_at': None,
        'result': None,
        'error': None,
    }

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return jsonify({
        'success': True,
        'message': '回测已启动，请轮询 /api/backtest/status 查看进度',
        'started_at': _backtest_task['started_at'],
    })


@analysis_bp.route('/api/backtest/status')
def get_backtest_status():
    """获取异步回测任务状态（含诊断信息）"""
    status = {
        'running': _backtest_task['running'],
        'started_at': _backtest_task.get('started_at'),
        'finished_at': _backtest_task.get('finished_at'),
        'has_result': _backtest_task.get('result') is not None,
        'error': _backtest_task.get('error'),
    }
    # 如果回测完成且有结果，附上诊断摘要
    result = _backtest_task.get('result')
    if result and isinstance(result, dict):
        diag = result.get('diagnostics', {})
        if diag:
            status['diagnostics'] = {
                'environment': diag.get('environment', {}),
                'weekly_files': diag.get('weekly', {}).get('files_found', 0),
                'monthly_files': diag.get('monthly', {}).get('files_found', 0),
            }
    return jsonify(status)


@analysis_bp.route('/api/backtest/diagnostics')
def get_backtest_diagnostics():
    """获取回测详细诊断信息 - 用于排查问题"""
    try:
        # 1. 从最近一次回测结果获取诊断
        result_diag = None
        result = _backtest_task.get('result')
        if result and isinstance(result, dict):
            result_diag = result.get('diagnostics')

        # 2. 从磁盘读取已保存的回测数据
        disk_data = {}
        for name, path in [
            ('summary', 'data/backtest_summary.json'),
            ('weekly', 'data/weekly_backtest_results.json'),
            ('monthly', 'data/monthly_backtest_results.json'),
        ]:
            if os.path.exists(path):
                try:
                    mtime = os.path.getmtime(path)
                    size = os.path.getsize(path)
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    disk_data[name] = {
                        'exists': True,
                        'size_bytes': size,
                        'modified': datetime.fromtimestamp(mtime).isoformat(),
                        'stats': data.get('stats', data.get('weekly', data.get('monthly', {}))),
                    }
                except Exception as e:
                    disk_data[name] = {'exists': True, 'error': str(e)}
            else:
                disk_data[name] = {'exists': False}

        # 3. 数据文件盘点
        weekly_files = glob.glob('data/weekly/analysis_*.json')
        monthly_files = glob.glob('data/monthly/analysis_*.json')

        # 4. 环境检测
        env_check = {}
        try:
            import akshare
            env_check['akshare'] = {'installed': True, 'version': getattr(akshare, '__version__', '?')}
        except ImportError:
            env_check['akshare'] = {'installed': False}
        try:
            import yfinance
            env_check['yfinance'] = {'installed': True, 'version': getattr(yfinance, '__version__', '?')}
        except ImportError:
            env_check['yfinance'] = {'installed': False}

        # 5. 快速价格获取测试
        price_test = {}
        try:
            from backtester import PriceDataFetcher
            fetcher = PriceDataFetcher()
            test_date = (datetime.now() - __import__('datetime').timedelta(days=10)).strftime('%Y-%m-%d')

            # 测试A股（上证指数）
            cn_change = fetcher.get_price_change('SH000001', test_date, 3)
            price_test['cn_index'] = {
                'symbol': 'SH000001',
                'date': test_date,
                'result': cn_change,
                'success': cn_change is not None,
            }

            # 测试美股
            us_change = fetcher.get_price_change('AAPL', test_date, 3)
            price_test['us_stock'] = {
                'symbol': 'AAPL',
                'date': test_date,
                'result': us_change,
                'success': us_change is not None,
            }
        except Exception as e:
            price_test['error'] = str(e)

        return jsonify({
            'task_status': {
                'running': _backtest_task['running'],
                'started_at': _backtest_task.get('started_at'),
                'finished_at': _backtest_task.get('finished_at'),
                'has_error': _backtest_task.get('error') is not None,
                'error': _backtest_task.get('error'),
                'traceback': _backtest_task.get('traceback'),
            },
            'last_run_diagnostics': result_diag,
            'disk_data': disk_data,
            'data_files': {
                'weekly_count': len(weekly_files),
                'monthly_count': len(monthly_files),
                'weekly_latest': sorted(weekly_files)[-1] if weekly_files else None,
                'monthly_latest': sorted(monthly_files)[-1] if monthly_files else None,
            },
            'environment': env_check,
            'price_test': price_test,
        })
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/backtest/optimization')
def get_optimization_status():
    """获取优化状态"""
    try:
        # 加载优化配置
        config_file = 'data/prediction_config.json'
        history_file = 'data/optimization_history.json'
        report_file = 'data/optimization_report.json'

        result = {
            'config': None,
            'history': None,
            'latest_report': None
        }

        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                result['config'] = json.load(f)

        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 只返回最近10次优化
                result['history'] = {
                    'optimizations': data.get('optimizations', [])[-10:],
                    'total_count': len(data.get('optimizations', []))
                }

        if os.path.exists(report_file):
            with open(report_file, 'r', encoding='utf-8') as f:
                result['latest_report'] = json.load(f)

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/backtest/charts')
def get_backtest_charts():
    """获取回测可视化数据 - 方向偏差/涨跌幅分布/个股胜率/置信度/资金曲线"""
    try:
        from collections import defaultdict, Counter
        import math

        # 1. 加载 verified 数据
        weekly_verified = []
        monthly_verified = []
        for name, path in [
            ('weekly', 'data/weekly_backtest_results.json'),
            ('monthly', 'data/monthly_backtest_results.json'),
        ]:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    vlist = data.get('verified', data.get('verified_stocks', []))
                    if name == 'weekly':
                        weekly_verified = vlist
                    else:
                        monthly_verified = vlist
                except Exception:
                    pass

        all_verified = weekly_verified + monthly_verified
        if not all_verified:
            return jsonify({'error': '暂无已验证的预测数据', 'charts': {}})

        # ========== 图1: 方向偏差 ==========
        pred_dir_counts = Counter()
        actual_dir_counts = Counter()
        confusion = defaultdict(lambda: defaultdict(int))  # confusion[predicted][actual]
        for v in all_verified:
            pd_ = v.get('predicted_direction', '未知')
            ad_ = v.get('actual_direction', '未知')
            pred_dir_counts[pd_] += 1
            actual_dir_counts[ad_] += 1
            confusion[pd_][ad_] += 1

        direction_labels = ['上涨', '下跌', '震荡']
        direction_bias = {
            'predicted': {d: pred_dir_counts.get(d, 0) for d in direction_labels},
            'actual': {d: actual_dir_counts.get(d, 0) for d in direction_labels},
            'confusion': {pd_: dict(acts) for pd_, acts in confusion.items()},
            'total': len(all_verified),
        }

        # ========== 图2: 涨跌幅分布 ==========
        correct_changes = []
        wrong_changes = []
        for v in all_verified:
            change = v.get('actual_change_pct', v.get('actual_change', 0))
            if change is None:
                continue
            if v.get('is_correct'):
                correct_changes.append(round(change, 2))
            else:
                wrong_changes.append(round(change, 2))

        # 生成直方图 bins
        all_changes = correct_changes + wrong_changes
        if all_changes:
            min_c = max(math.floor(min(all_changes)), -30)
            max_c = min(math.ceil(max(all_changes)), 30)
            bin_size = 2
            bins = list(range(min_c, max_c + bin_size, bin_size))
            correct_hist = [0] * (len(bins) - 1)
            wrong_hist = [0] * (len(bins) - 1)
            for c in correct_changes:
                for i in range(len(bins) - 1):
                    if bins[i] <= c < bins[i + 1]:
                        correct_hist[i] += 1
                        break
            for c in wrong_changes:
                for i in range(len(bins) - 1):
                    if bins[i] <= c < bins[i + 1]:
                        wrong_hist[i] += 1
                        break
            bin_labels = [f'{bins[i]}~{bins[i+1]}%' for i in range(len(bins) - 1)]
        else:
            bin_labels, correct_hist, wrong_hist = [], [], []

        return_distribution = {
            'bins': bin_labels,
            'correct': correct_hist,
            'wrong': wrong_hist,
        }

        # ========== 图3: 个股胜率排名 ==========
        symbol_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'name': ''})
        for v in all_verified:
            sym = v.get('symbol', '?')
            symbol_stats[sym]['total'] += 1
            symbol_stats[sym]['name'] = v.get('name', sym)
            if v.get('is_correct'):
                symbol_stats[sym]['correct'] += 1

        # 只取出现>=2次的 symbol，按胜率排序
        sym_ranking = []
        for sym, st in symbol_stats.items():
            if st['total'] >= 2:
                rate = st['correct'] / st['total'] * 100
                sym_ranking.append({
                    'symbol': sym,
                    'name': st['name'],
                    'total': st['total'],
                    'correct': st['correct'],
                    'win_rate': round(rate, 1),
                })
        sym_ranking.sort(key=lambda x: (-x['win_rate'], -x['total']))

        symbol_win_rate = {
            'top': sym_ranking[:15],
            'bottom': list(reversed(sym_ranking[-15:])) if len(sym_ranking) > 15 else [],
        }

        # ========== 图4: 置信度分层效果 ==========
        conf_buckets = {'high': [], 'medium': [], 'low': []}
        for v in all_verified:
            conf = v.get('confidence', 0.5)
            if isinstance(conf, str):
                conf = {'高': 0.8, '中': 0.5, '低': 0.3}.get(conf, 0.5)
            if conf > 0.6:
                conf_buckets['high'].append(v)
            elif conf > 0.3:
                conf_buckets['medium'].append(v)
            else:
                conf_buckets['low'].append(v)

        confidence_strat = {}
        for level, items in conf_buckets.items():
            total = len(items)
            correct = sum(1 for it in items if it.get('is_correct'))
            confidence_strat[level] = {
                'total': total,
                'correct': correct,
                'accuracy': round(correct / total * 100, 1) if total else 0,
            }

        # ========== 图5: 模拟资金曲线 ==========
        capital = 100000
        equity_curve = [{'date': '起始', 'capital': capital, 'trade': ''}]
        sorted_preds = sorted(all_verified, key=lambda x: x.get('analysis_date', ''))
        for v in sorted_preds:
            if v.get('predicted_direction') == '震荡':
                continue
            change = v.get('actual_change_pct', v.get('actual_change', 0))
            if change is None:
                continue
            position = capital * 0.1
            if v.get('predicted_direction') == '上涨':
                pnl = position * (change / 100)
            else:
                pnl = position * (-change / 100)
            capital += pnl
            equity_curve.append({
                'date': v.get('analysis_date', ''),
                'capital': round(capital, 2),
                'trade': f"{v.get('symbol', '?')} {v.get('predicted_direction', '')} {change:+.1f}%",
            })

        # ========== 图6: 按日期准确率趋势 ==========
        date_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
        for v in all_verified:
            d = v.get('analysis_date', '')
            if d:
                date_stats[d]['total'] += 1
                if v.get('is_correct'):
                    date_stats[d]['correct'] += 1
        accuracy_trend = []
        for d in sorted(date_stats.keys()):
            t = date_stats[d]['total']
            c = date_stats[d]['correct']
            accuracy_trend.append({
                'date': d,
                'accuracy': round(c / t * 100, 1) if t else 0,
                'total': t,
                'correct': c,
            })

        return jsonify({
            'charts': {
                'direction_bias': direction_bias,
                'return_distribution': return_distribution,
                'symbol_win_rate': symbol_win_rate,
                'confidence_strat': confidence_strat,
                'equity_curve': equity_curve,
                'accuracy_trend': accuracy_trend,
            }
        })
    except Exception as e:
        logger.error(f"Charts data failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/backtest/optimize', methods=['POST'])
@require_api_key
def run_optimization():
    """手动运行优化 - 需要API Key认证"""
    try:
        from prediction_optimizer import run_optimization as _run_opt
        result = _run_opt()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"Optimization failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
