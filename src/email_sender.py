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
            print("邮件配置不完整")
            # self._save_local(report)
            return
        
        msg = MIMEMultipart()
        msg['From'] = self.from_email or ""
        msg['To'] = self.to_email or ""
        msg['Subject'] = f"财经新闻日报 - {datetime.now().strftime('%Y-%m-%d')}"
        
        msg.attach(MIMEText(report, 'plain', 'utf-8'))
        
        try:
            # 支持多种邮箱服务器
            smtp_config = {
                'gmail.com': ('smtp.gmail.com', 465),
                'qq.com': ('smtp.qq.com', 465),
                '163.com': ('smtp.163.com', 465),
                'outlook.com': ('smtp-mail.outlook.com', 587),
                'hotmail.com': ('smtp-mail.outlook.com', 587)
            }
            
            domain = self.from_email.split('@')[1] if self.from_email and '@' in self.from_email else 'gmail.com'
            smtp_server, smtp_port = smtp_config.get(domain, ('smtp.gmail.com', 465))
            
            if smtp_port == 587:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(self.from_email or "", self.password or "")
                server.send_message(msg)
                server.quit()
            else:
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(self.from_email or "", self.password or "")
                    server.send_message(msg)
            
            print("✅ 邮件发送成功")
            # self._save_local(report)
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            print("提示: 请检查 .env 文件中的邮箱配置")
            # self._save_local(report)
