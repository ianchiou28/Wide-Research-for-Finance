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
    rss_count = len(articles)
    
    print("\n2. 爬取官方网站...")
    scraper = WebScraper()
    web_articles = scraper.scrape_all()
    web_count = len(web_articles)
    articles.extend(web_articles)

    # 2a. 采集自选股新闻
    stock_articles = collector.fetch_stock_specific_news()
    stock_count = len(stock_articles)
    articles.extend(stock_articles)
    
    print(f"\n   📊 采集统计:")
    print(f"      - RSS源: {rss_count} 条")
    print(f"      - 网页爬取: {web_count} 条")
    print(f"      - 自选股: {stock_count} 条")
    print(f"      - 总计: {len(articles)} 条")
    
    if not articles:
        print("\n   ⚠️ 无新数据！可能原因:")
        print("      1. 网络问题导致RSS/爬虫超时")
        print("      2. 所有新闻都因时间过滤被排除")
        print("      3. 网站结构变化导致爬取失败")
        print("   跳过本次报告生成")
        return
    
    # 2. 信息处理
    print("\n3. 分析新闻内容...")
    processor = NLPProcessor()
    processed = processor.process_batch(articles)
    print(f"   成功处理 {len(processed)} 条新闻")
    
    if not processed:
        print("\n   ⚠️ AI处理后无有效新闻！可能原因:")
        print("      1. DeepSeek API调用失败（检查API密钥和余额）")
        print("      2. AI认为所有新闻都不值得分析")
        print("      3. JSON解析失败")
        print("   将跳过本次报告生成")
        return
    
    # 3. 生成报告
    print("\n4. 生成报告...")
    
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

def run_monthly_report_script():
    """运行月度分析脚本（每日更新，保持实时性）"""
    print(f"\n启动月度分析 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        # --refresh 强制刷新事件日历，确保获取最新信息
        subprocess.run([sys.executable, "run_monthly_analysis.py", "--refresh"], check=False)
    except Exception as e:
        print(f"月度分析运行失败: {e}")

def run_backtest_verification():
    """运行回测验证（验证历史预测的准确性）"""
    print(f"\n启动回测验证 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        from src.backtester import run_daily_verification
        result = run_daily_verification()
        
        # 打印汇总
        weekly_acc = result.get('weekly', {}).get('accuracy', 0)
        monthly_stock_acc = result.get('monthly', {}).get('stock_predictions', {}).get('accuracy', 0)
        monthly_event_acc = result.get('monthly', {}).get('event_predictions', {}).get('accuracy', 0)
        
        print(f"\n📊 回测汇总:")
        print(f"   周报预测准确率: {weekly_acc:.1f}%")
        print(f"   月报股票预测准确率: {monthly_stock_acc:.1f}%")
        print(f"   月报事件预测准确率: {monthly_event_acc:.1f}%")
        
    except Exception as e:
        print(f"回测验证运行失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("Wide Research for Finance - MVP v1.0")
    print("="*60)
    
    # 检查API密钥
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("错误: 未设置 DEEPSEEK_API_KEY")
        print("请创建 .env 文件并配置API密钥")
        return
    
    # 服务器环境自动选择模式2
    if os.getenv('DOCKER_ENV') == 'True':
        print("Docker环境检测到，自动启用计划任务：")
        print("- 每小时整点生成小时报 (run_daily_report)")
        print("- 每天 08:00 和 20:00 生成12小时摘要")
        print("- 每天 08:00 和 20:00 运行周报分析")
        print("- 每天 09:00 更新月度分析（事件日历+预测修正）")
        print("- 每天 21:00 运行回测验证（验证预测准确率）")

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
        
        # 4. 月报（每天早上9点更新，保持实时性）
        # - 自动抓取最新事件
        # - 根据已发生事件修正预测
        # - 更新加减仓建议
        schedule.every().day.at("09:00").do(run_monthly_report_script)
        
        # 5. 回测验证（每天晚上9点，验证历史预测的准确性）
        schedule.every().day.at("21:00").do(run_backtest_verification)

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
