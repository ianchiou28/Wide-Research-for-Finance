"""
Analysis routes blueprint - realtime, backtest, and monthly analysis.
"""
import os
import glob
import json
import logging
import threading
from datetime import datetime

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
            logger.error(f"Backtest run failed: {e}", exc_info=True)
            _backtest_task['result'] = None
            _backtest_task['error'] = str(e)
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
    """获取异步回测任务状态"""
    return jsonify({
        'running': _backtest_task['running'],
        'started_at': _backtest_task.get('started_at'),
        'finished_at': _backtest_task.get('finished_at'),
        'has_result': _backtest_task.get('result') is not None,
        'error': _backtest_task.get('error'),
    })


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
