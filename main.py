import os
import sys
from dotenv import load_dotenv
import schedule
import time
from datetime import datetime

sys.path.append('src')
from collector import DataCollector
from web_scraper import WebScraper
from processor import NLPProcessor
from report_generator import ReportGenerator
from email_sender import EmailSender

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
    report_gen = ReportGenerator()
    report = report_gen.generate(processed)
    
    # 4. 发送邮件
    print("5. 发送报告...")
    sender = EmailSender()
    sender.send(report)
    
    print(f"\n{'='*60}")
    print("报告生成完成")
    print(f"{'='*60}\n")

def main():
    print("Wide Research for Finance - MVP v1.0")
    print("="*60)
    
    # 检查API密钥
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("错误: 未设置 DEEPSEEK_API_KEY")
        print("请创建 .env 文件并配置API密钥")
        return
    
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
        for hour in range(24):
            schedule.every().day.at(f"{hour:02d}:00").do(run_daily_report)
        
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
