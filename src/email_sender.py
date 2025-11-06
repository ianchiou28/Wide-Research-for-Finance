import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailSender:
    def __init__(self):
        self.from_email = os.getenv('EMAIL_FROM')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.to_email = os.getenv('EMAIL_TO')
    
    def send(self, report: str):
        """发送邮件报告"""
        if not all([self.from_email, self.password, self.to_email]):
            print("邮件配置不完整，报告已保存到本地")
            self._save_local(report)
            return
        
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        msg['Subject'] = f"财经新闻日报 - {datetime.now().strftime('%Y-%m-%d')}"
        
        msg.attach(MIMEText(report, 'plain', 'utf-8'))
        
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.from_email, self.password)
                server.send_message(msg)
            print("邮件发送成功")
        except Exception as e:
            print(f"邮件发送失败: {e}")
            self._save_local(report)
    
    def _save_local(self, report: str):
        """保存报告到本地"""
        filename = f"data/reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"报告已保存: {filename}")
