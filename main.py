import os
import sys
from dotenv import load_dotenv
import schedule
import time
from datetime import datetime
import subprocess

sys.path.append('src')
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
    print(f"\n{'='*60}")
    print(f"开始生成报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 1. 数据采集
    print("1. 采集RSS新闻...")
    collector = DataCollector()
    articles = collector.fetch_latest(hours=24, max_per_source=15)
    
    print("\n2. 爬取官方网站...")
    scraper = WebScraper()
    web_articles = scraper.scrape_all()
    articles.extend(web_articles)

    # 2a. 采集自选股新闻
    web_articles = collector.fetch_stock_specific_news()
    articles.extend(web_articles)
    
    print(f"\n   总计采集 {len(articles)} 条新闻")
    
    if not articles:
        print("   无新数据，跳过处理")
        return
    
    # 2. 信息处理
    print("\n3. 分析新闻内容...")
    processor = NLPProcessor()
    processed = processor.process_batch(articles)
    print(f"   成功处理 {len(processed)} 条新闻")
    
    # 3. 生成报告
    print("4. 生成报告...")
    
    # 生成纯文本报告（用于本地保存）
    report_gen = ReportGenerator()
    report_text = report_gen.generate(processed)
    _save_local(report_text)
    
    # 生成结构化报告（用于可视化邮件和前端）
    report_gen_v2 = ReportGeneratorV2()
    report_data = report_gen_v2.generate(processed)
    _save_json(report_data)
    
    # 4. 发送邮件（使用HTML模板）
    print("5. 发送报告...")
    sender = EmailSender()
    
    # 生成HTML邮件并发送
    template_gen = EmailTemplateGenerator()
    html_content = template_gen.generate_email_html(report_data)
    sender.send(report_text, html_content=html_content)
    
    print(f"\n{'='*60}")
    print("报告生成完成")
    print(f"{'='*60}\n")

def _save_local(report: str):
    """保存报告到本地"""
    os.makedirs('data/reports', exist_ok=True)
    filename = f"data/reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8', errors='replace') as f:
        f.write(report)
    try:
        print(f"报告已保存: {filename}")
    except:
        print(f"Report saved: {filename}")

def _save_json(report_data: dict):
    """保存结构化报告为JSON（供前端读取）"""
    import json
    os.makedirs('data/reports_json', exist_ok=True)
    filename = f"data/reports_json/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    try:
        print(f"JSON报告已保存: {filename}")
    except:
        print(f"JSON report saved: {filename}")

def run_weekly_report_script():
    """运行周报分析脚本"""
    print(f"\n启动周报分析 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        subprocess.run([sys.executable, "run_weekly_analysis.py"], check=False)
    except Exception as e:
        print(f"周报分析运行失败: {e}")

def main():
    print("Wide Research for Finance - MVP v1.0")
    print("="*60)
    
    # 检查API密钥
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("错误: 未设置 DEEPSEEK_API_KEY")
        print("请创建 .env 文件并配置API密钥")
        return
    
    # Docker环境自动选择模式2
    if os.getenv('DOCKER_ENV') == 'True':
        print("Docker环境检测到，自动启用计划任务：")
        print("- 每小时整点生成小时报 (run_daily_report)")
        print("- 每天 08:00 和 20:00 生成12小时摘要")
        print("- 每天 08:00 和 20:00 运行周报分析")

        # 1. 小时报
        schedule.every().hour.at(":00").do(run_daily_report)

        # 2. 日报（12小时摘要）
        try:
            from daily_summary_main import generate_and_send_summary
            schedule.every().day.at("08:00").do(generate_and_send_summary)
            schedule.every().day.at("20:00").do(generate_and_send_summary)
        except ImportError:
            print("警告: 无法导入 daily_summary_main，跳过摘要生成任务")

        # 3. 周报
        schedule.every().day.at("08:00").do(run_weekly_report_script)
        schedule.every().day.at("20:00").do(run_weekly_report_script)

        print("后台运行中，按 Ctrl+C 停止\n")
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
        
        choice = input("\n请选择 (1/2/3/4): ").strip()
    
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
    else:
        print("无效选择")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已停止")
