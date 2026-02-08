import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, Optional
from logger import setup_logger

logger = setup_logger('email_sender')


class EmailSender:
    def __init__(self):
        self.from_email = os.getenv('EMAIL_FROM')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.to_email = os.getenv('EMAIL_TO')
    
    def send(self, report: str, html_content: Optional[str] = None):
        """发送邮件报告
        
        Args:
            report: 纯文本报告（作为备用）
            html_content: HTML格式报告（优先使用）
        """
        if not all([self.from_email, self.password, self.to_email]):
            logger.warning("邮件配置不完整，跳过发送")
            return
        
        msg = MIMEMultipart('alternative')
        msg['From'] = self.from_email or ""
        msg['To'] = self.to_email or ""
        msg['Subject'] = f"财经新闻简报 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 添加纯文本版本（作为备用）
        text_part = MIMEText(report, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # 添加HTML版本（优先显示）
        if html_content:
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
        
        try:
            # 支持多种邮箱服务器
            smtp_config = {
                'gmail.com': ('smtp.gmail.com', 465),
                'qq.com': ('smtp.qq.com', 465),
                '163.com': ('smtp.163.com', 465),
                'outlook.com': ('smtp-mail.outlook.com', 587),
                'hotmail.com': ('smtp-mail.outlook.com', 587),
                'foxmail.com': ('smtp.qq.com', 465),
                'yeah.net': ('smtp.yeah.net', 465),
                '126.com': ('smtp.126.com', 465),
            }
            
            domain = self.from_email.split('@')[1] if self.from_email and '@' in self.from_email else 'gmail.com'
            smtp_server, smtp_port = smtp_config.get(domain, ('smtp.gmail.com', 465))
            
            # 允许环境变量覆盖SMTP配置
            smtp_server = os.getenv('SMTP_SERVER', smtp_server)
            smtp_port = int(os.getenv('SMTP_PORT', smtp_port))
            
            logger.info(f"连接 {smtp_server}:{smtp_port}...")
            
            if smtp_port == 587:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                server.starttls()
                server.login(self.from_email or "", self.password or "")
                server.send_message(msg)
                server.quit()
            else:
                with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
                    server.login(self.from_email or "", self.password or "")
                    server.send_message(msg)
            
            logger.info("邮件发送成功")
        except smtplib.SMTPAuthenticationError:
            logger.error("邮件发送失败: 认证失败，请检查邮箱密码/授权码")
        except smtplib.SMTPConnectError:
            logger.error(f"邮件发送失败: 无法连接到 {smtp_server}:{smtp_port}")
        except TimeoutError:
            logger.error(f"邮件发送失败: 连接超时 ({smtp_server}:{smtp_port})")
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
    
    def send_structured_report(self, report_data: Dict[str, Any]):
        """发送结构化报告
        
        Args:
            report_data: 结构化报告数据（来自ReportGeneratorV2）
        """
        try:
            from email_template import EmailTemplateGenerator
            from report_generator_v2 import ReportGeneratorV2
            
            # 生成HTML邮件
            template_gen = EmailTemplateGenerator()
            html_content = template_gen.generate_email_html(report_data)
            
            # 生成纯文本备用
            report_gen = ReportGeneratorV2()
            text_content = report_gen.generate_text_report(report_data)
            
            self.send(text_content, html_content)
        except ImportError as e:
            logger.warning(f"导入模块失败: {e}，回退到纯文本")
            # 回退到纯文本
            if 'meta' in report_data:
                simple_text = f"财经简报 - {report_data['meta'].get('generated_at', '')}\n"
                simple_text += f"共分析 {report_data['meta'].get('total_news', 0)} 条新闻"
                self.send(simple_text)
