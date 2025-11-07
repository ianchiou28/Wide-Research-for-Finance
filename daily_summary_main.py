import os
import sys
from dotenv import load_dotenv
import schedule
import time
from datetime import datetime

sys.path.append('src')
from daily_summary import DailySummary
from email_sender import EmailSender

load_dotenv()

def generate_and_send_summary():
    """生成并发送12小时摘要"""
    print(f"\n{'='*60}")
    print(f"生成12小时摘要 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        # 生成摘要
        summary_gen = DailySummary()
        summary = summary_gen.generate_12h_summary()
        
        # 保存摘要
        summary_gen.save_summary(summary)
        
        # 打印摘要
        print(summary)
        
        # 发送邮件
        sender = EmailSender()
        sender.send(summary)
        
        print(f"\n{'='*60}")
        print("摘要生成完成")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ 生成摘要失败: {e}")

def main():
    print("Wide Research for Finance - 每日摘要系统")
    print("="*60)
    
    print("\n运行模式:")
    print("1. 立即生成一次摘要")
    print("2. 每天早上8点和晚上8点自动生成")
    
    choice = input("\n请选择 (1/2): ").strip()
    
    if choice == '1':
        generate_and_send_summary()
    elif choice == '2':
        # 设置定时任务
        schedule.every().day.at("08:00").do(generate_and_send_summary)
        schedule.every().day.at("20:00").do(generate_and_send_summary)
        
        print("\n已设置定时任务：")
        print("- 每天 08:00 生成早间摘要")
        print("- 每天 20:00 生成晚间摘要")
        print("按 Ctrl+C 停止\n")
        
        # 立即执行一次
        generate_and_send_summary()
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        print("无效选择")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已停止")
