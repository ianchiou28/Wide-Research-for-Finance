"""
测试发送最新报告邮件
"""
import os
import sys
import glob
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.path.append('src')

from email_sender import EmailSender
from email_template import EmailTemplateGenerator


def test_send_email():
    """测试发送邮件"""
    
    # 1. 获取最新的JSON报告
    json_reports = glob.glob('data/reports_json/report_*.json')
    
    if not json_reports:
        print("没有找到JSON报告，尝试生成...")
        # 如果没有JSON报告，可以先运行main.py生成
        return
    
    latest_json = max(json_reports, key=os.path.getctime)
    print(f"使用报告: {latest_json}")
    
    with open(latest_json, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    # 2. 生成HTML邮件
    template_gen = EmailTemplateGenerator()
    html_content = template_gen.generate_email_html(report_data)
    
    # 3. 发送邮件
    sender = EmailSender()
    
    # 生成纯文本备用内容
    text_content = f"财经简报 - {report_data.get('meta', {}).get('generated_at', '')}\n"
    text_content += f"共分析 {report_data.get('meta', {}).get('total_news', 0)} 条新闻"
    
    sender.send(text_content, html_content)
    print("邮件发送完成!")


if __name__ == '__main__':
    test_send_email()
