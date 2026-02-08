import os
import sys
from dotenv import load_dotenv
import schedule
import time
from datetime import datetime
import subprocess

sys.path.append('src')
from logger import setup_logger

logger = setup_logger('main')

from collector import DataCollector
from web_scraper import WebScraper
from processor import NLPProcessor
from report_generator import ReportGenerator
from report_generator_v2 import ReportGeneratorV2
from email_sender import EmailSender
from email_template import EmailTemplateGenerator

load_dotenv()

def run_daily_report():
    """执行每日报告生成流程"""
    logger.info(f"{'='*40} 开始生成报告 {'='*40}")
    
    # 1. 数据采集
    logger.info("采集RSS新闻...")
    collector = DataCollector()
    articles = collector.fetch_latest(hours=24, max_per_source=15)
    
    logger.info("爬取官方网站...")
    scraper = WebScraper()
    web_articles = scraper.scrape_all()
    articles.extend(web_articles)

    # 2a. 采集自选股新闻
    web_articles = collector.fetch_stock_specific_news()
    articles.extend(web_articles)
    
    logger.info(f"总计采集 {len(articles)} 条新闻")
    
    if not articles:
        logger.info("无新数据，跳过处理")
        return
    
    # 2. 信息处理
    logger.info("分析新闻内容...")
    processor = NLPProcessor()
    processed = processor.process_batch(articles)
    logger.info(f"成功处理 {len(processed)} 条新闻")
    
    # 3. 生成报告
    logger.info("生成报告...")
    
    # 生成纯文本报告（用于本地保存）
    report_gen = ReportGenerator()
    report_text = report_gen.generate(processed)
    _save_local(report_text)
    
    # 生成结构化报告（用于可视化邮件和前端）
    report_gen_v2 = ReportGeneratorV2()
    report_data = report_gen_v2.generate(processed)
    _save_json(report_data)
    
    # 4. 发送邮件（使用HTML模板）
    logger.info("发送报告...")
    sender = EmailSender()
    
    # 生成HTML邮件并发送
    template_gen = EmailTemplateGenerator()
    html_content = template_gen.generate_email_html(report_data)
    sender.send(report_text, html_content=html_content)
    
    logger.info("报告生成完成")

def _save_local(report: str):
    """保存报告到本地"""
    os.makedirs('data/reports', exist_ok=True)
    filename = f"data/reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8', errors='replace') as f:
        f.write(report)
    logger.info(f"报告已保存: {filename}")

def _save_json(report_data: dict):
    """保存结构化报告为JSON（供前端读取）"""
    import json
    os.makedirs('data/reports_json', exist_ok=True)
    filename = f"data/reports_json/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON报告已保存: {filename}")

def run_weekly_report_script():
    """运行周报分析脚本"""
    logger.info("启动周报分析")
    try:
        subprocess.run([sys.executable, "run_weekly_analysis.py"], check=False)
    except Exception as e:
        logger.error(f"周报分析运行失败: {e}")

def run_monthly_report_script():
    """运行月度分析脚本（每日更新，保持实时性）"""
    logger.info("启动月度分析")
    try:
        subprocess.run([sys.executable, "run_monthly_analysis.py", "--refresh"], check=False)
    except Exception as e:
        logger.error(f"月度分析运行失败: {e}")

def run_backtest_verification():
    """运行回测验证（验证历史预测的准确性）"""
    logger.info("启动回测验证")
    try:
        from src.backtester import run_daily_verification
        result = run_daily_verification()
        
        weekly_acc = result.get('weekly', {}).get('accuracy', 0)
        monthly_stock_acc = result.get('monthly', {}).get('stock_predictions', {}).get('accuracy', 0)
        monthly_event_acc = result.get('monthly', {}).get('event_predictions', {}).get('accuracy', 0)
        
        logger.info(f"回测汇总: 周报={weekly_acc:.1f}% 月报股票={monthly_stock_acc:.1f}% 月报事件={monthly_event_acc:.1f}%")
        
    except Exception as e:
        logger.error(f"回测验证运行失败: {e}")

def main():
    logger.info("Wide Research for Finance - MVP v1.0")
    
    # 检查API密钥
    if not os.getenv('DEEPSEEK_API_KEY'):
        logger.error("未设置 DEEPSEEK_API_KEY，请创建 .env 文件并配置API密钥")
        return
    
    # 服务器环境自动选择模式2
    if os.getenv('DOCKER_ENV') == 'True':
        logger.info("Docker环境检测到，自动启用计划任务")

        # 1. 小时报
        schedule.every().hour.at(":00").do(run_daily_report)

        # 2. 日报（12小时摘要）
        try:
            from daily_summary_main import generate_and_send_summary
            schedule.every().day.at("08:00").do(generate_and_send_summary)
            schedule.every().day.at("20:00").do(generate_and_send_summary)
        except ImportError:
            logger.warning("无法导入 daily_summary_main，跳过摘要生成任务")

        # 3. 周报
        schedule.every().day.at("08:00").do(run_weekly_report_script)
        schedule.every().day.at("20:00").do(run_weekly_report_script)
        
        # 4. 月报（每天早上9点更新，保持实时性）
        # - 自动抓取最新事件
        # - 根据已发生事件修正预测
        # - 更新加减仓建议
        schedule.every().day.at("09:00").do(run_monthly_report_script)
        
        # 5. 回测验证（每天晚上9点，验证历史预测的准确性）
        schedule.every().day.at("21:00").do(run_backtest_verification)

        logger.info("后台运行中，按 Ctrl+C 停止")
        while True:
            schedule.run_pending()
            time.sleep(60)
        return
    else:
        # 选择运行模式
        print("\n运行模式:")
        print("1. 立即执行一次")
        print("2. 每个整点执行（0:00, 1:00, 2:00...）")
        print("3. 每天早上8点执行")
        print("4. 每天8点和20点生成12小时摘要")
        print("5. 立即生成月度分析")
        print("6. 运行回测验证")
        
        choice = input("\n请选择 (1/2/3/4/5/6): ").strip()
    
    if choice == '1':
        run_daily_report()
    elif choice == '2':
        # 在每个整点执行
        schedule.every().hour.at(":00").do(run_daily_report)
        
        next_hour = (datetime.now().hour + 1) % 24
        print(f"\n已设置定时任务：每个整点执行（0:00, 1:00, 2:00...）")
        print(f"下次执行时间：{next_hour:02d}:00")
        print("按 Ctrl+C 停止\n")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    elif choice == '3':
        schedule.every().day.at("08:00").do(run_daily_report)
        print("\n已设置定时任务：每天 08:00 执行")
        print("按 Ctrl+C 停止\n")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    elif choice == '4':
        print("\n请运行: python daily_summary_main.py")
        print("或双击: run_daily_summary.bat")
    elif choice == '5':
        run_monthly_report_script()
    elif choice == '6':
        run_backtest_verification()
    else:
        print("无效选择")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已停止")
