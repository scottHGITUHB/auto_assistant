import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = config.SMTP_HOST
        self.smtp_port = config.SMTP_PORT
        self.smtp_user = config.SMTP_USER
        self.smtp_password = config.SMTP_PASSWORD
        self.smtp_to = config.SMTP_TO
    
    def is_configured(self):
        """检查邮件配置是否完整"""
        return all([
            self.smtp_host,
            self.smtp_user,
            self.smtp_password,
            self.smtp_to
        ])
    
    async def send_email(self, subject, content, to_email=None):
        """发送邮件"""
        try:
            if not self.is_configured():
                logger.error("[ERROR] Email configuration is incomplete")
                return False
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = to_email or self.smtp_to
            msg['Subject'] = subject
            
            # 添加邮件内容
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 连接SMTP服务器并发送
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"[INFO] Email sent successfully: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to send email: {e}")
            return False
    
    async def send_reminder_email(self, reminder_content, remind_time):
        """发送提醒邮件"""
        subject = f"[智能助理] 提醒: {reminder_content}"
        content = f"""
您好，

这是来自智能助理的提醒：

提醒内容: {reminder_content}
提醒时间: {remind_time}

请记得处理相关事项。

---
智能助理
        """
        return await self.send_email(subject, content)

email_service = EmailService()