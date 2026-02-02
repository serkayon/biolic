import smtplib
import secrets
import string
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailService:
    """Production-grade Email Service (Zoho SMTP)"""
    
    def __init__(self):
        self.smtp_server = "smtp.zoho.com"
        self.smtp_port = 587
        self.sender_email = os.getenv('EMAIL_USER')
        self.sender_password = os.getenv('EMAIL_PASSWORD')
        self.timeout = 60  # seconds
    
    def is_configured(self):
        return bool(self.sender_email and self.sender_password)
    
    # =========================
    # Secure OTP generator
    # =========================
    def generate_otp(self, length=6):
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    # =========================
    # Send OTP Email
    # =========================
    def send_otp_email(self, recipient_email, otp):
        if not self.is_configured():
            logger.error("Email service not configured")
            return False, "Email service not configured"
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = "Email Verification - OTP Code"
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            text = f"""
Hello,

Your OTP for verification is: {otp}

This OTP is valid for 5 minutes.
Do not share this code with anyone.

If you did not request this, ignore this email.

- License System
"""
            
            html = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <div style="max-width:600px;margin:auto;padding:20px">
      <h2>Email Verification</h2>
      <p>Your OTP code:</p>
      <div style="background:#f0f0f0;padding:20px;text-align:center;border-radius:6px">
        <h1 style="letter-spacing:6px">{otp}</h1>
      </div>
      <p><b>Valid for 5 minutes.</b></p>
      <p style="font-size:12px;color:#888">Do not share this OTP.</p>
      <hr>
      <p style="font-size:12px;color:#aaa">License System Team</p>
    </div>
  </body>
</html>
"""
            
            message.attach(MIMEText(text, "plain"))
            message.attach(MIMEText(html, "html"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(
                    self.sender_email,
                    recipient_email,
                    message.as_string()
                )
            
            logger.info(f"OTP sent to {recipient_email}")
            return True, "OTP sent successfully"
        
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed")
            return False, "Email authentication failed"
        
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False, "SMTP error"
        
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False, "Email sending failed"

# Singleton instance
email_service = EmailService()

