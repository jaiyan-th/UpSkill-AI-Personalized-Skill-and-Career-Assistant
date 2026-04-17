"""
Email Service for UpSkill AI
Handles all email notifications with HTML templates and non-blocking delivery
"""

import smtplib
import os
import logging
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """
    Production-ready email service with:
    - HTML email templates
    - Non-blocking async sending
    - Error handling and logging
    - Support for multiple email types
    """
    
    def __init__(self):
        self.host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("EMAIL_PORT", "587"))
        self.user = os.getenv("EMAIL_USER", "")
        self.password = os.getenv("EMAIL_PASS", "")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "UpSkill AI")
        self.enabled = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
        
        if not self.user or not self.password:
            logger.warning("Email credentials not configured. Email notifications will be disabled.")
            self.enabled = False
    
    def _send_email_sync(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None):
        """
        Internal method to send email synchronously
        Should not be called directly - use send_email() instead
        """
        if not self.enabled:
            logger.info(f"Email disabled. Would have sent: {subject} to {to_email}")
            return
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.user}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully: {subject} to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            # Don't raise - email failures should not break the application
    
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None):
        """
        Send email asynchronously (non-blocking) on traditional servers,
        or synchronously on Vercel (serverless environments freeze background threads).
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML content of the email
            text_body: Plain text fallback (optional)
        """
        if os.getenv("VERCEL"):
            # Serverless environments freeze background threads after the response is returned.
            # We must send the email synchronously here.
            self._send_email_sync(to_email, subject, html_body, text_body)
        else:
            # Traditional server: Send in background thread to avoid blocking API response
            thread = threading.Thread(
                target=self._send_email_sync,
                args=(to_email, subject, html_body, text_body)
            )
            thread.daemon = True
            thread.start()
    
    def send_welcome_email(self, user_name: str, user_email: str):
        """
        Send welcome email after successful registration
        """
        subject = "Welcome to UpSkill AI 🚀"
        
        html_body = self._get_welcome_template(user_name)
        text_body = f"""
Hi {user_name},

Welcome to UpSkill AI!

You can now:
✓ Analyze your resume with AI
✓ Practice mock interviews
✓ Get personalized skill recommendations
✓ Track your career growth

Let's get you hired! 🚀

Best regards,
The UpSkill AI Team
        """.strip()
        
        self.send_email(user_email, subject, html_body, text_body)
    
    def send_login_alert(self, user_name: str, user_email: str, login_time: Optional[datetime] = None):
        """
        Send login alert email after successful login
        """
        if login_time is None:
            login_time = datetime.now()
        
        subject = "New Login Detected 🔐"
        
        html_body = self._get_login_alert_template(user_name, login_time)
        text_body = f"""
Hi {user_name},

You have successfully logged into UpSkill AI.

Login Time: {login_time.strftime('%B %d, %Y at %I:%M %p')}

If this wasn't you, please reset your password immediately.

Best regards,
UpSkill AI Security Team
        """.strip()
        
        self.send_email(user_email, subject, html_body, text_body)
    
    def send_verification_email(self, user_name: str, user_email: str, verification_code: str):
        """
        Send email verification code
        """
        subject = "Verify Your Email - UpSkill AI"
        
        html_body = self._get_verification_template(user_name, verification_code)
        text_body = f"""
Hi {user_name},

Please verify your email address using the code below:

Verification Code: {verification_code}

This code will expire in 15 minutes.

Best regards,
The UpSkill AI Team
        """.strip()
        
        self.send_email(user_email, subject, html_body, text_body)
    
    def send_password_reset_email(self, user_name: str, user_email: str, reset_code: str):
        """
        Send password reset email
        """
        subject = "Reset Your Password - UpSkill AI"
        
        html_body = self._get_password_reset_template(user_name, reset_code)
        text_body = f"""
Hi {user_name},

You requested to reset your password. Use the code below:

Reset Code: {reset_code}

This code will expire in 15 minutes.

If you didn't request this, please ignore this email.

Best regards,
UpSkill AI Security Team
        """.strip()
        
        self.send_email(user_email, subject, html_body, text_body)
    
    # ==================== HTML TEMPLATES ====================
    
    def _get_base_template(self, content: str) -> str:
        """Base HTML template with styling"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UpSkill AI</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f7fa; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 700;">
                                🚀 UpSkill AI
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #e0e7ff; font-size: 16px;">
                                Your AI-Powered Career Assistant
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            {content}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 10px 0; color: #64748b; font-size: 14px;">
                                © 2026 UpSkill AI. All rights reserved.
                            </p>
                            <p style="margin: 0; color: #94a3b8; font-size: 12px;">
                                This email was sent to you because you registered on UpSkill AI.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """.strip()
    
    def _get_welcome_template(self, user_name: str) -> str:
        """Welcome email HTML template"""
        content = f"""
            <h2 style="margin: 0 0 20px 0; color: #1e293b; font-size: 24px;">
                Hi {user_name}! 👋
            </h2>
            
            <p style="margin: 0 0 20px 0; color: #475569; font-size: 16px; line-height: 1.6;">
                Welcome to <strong>UpSkill AI</strong>! We're excited to help you accelerate your career growth.
            </p>
            
            <div style="background-color: #f1f5f9; border-radius: 8px; padding: 25px; margin: 25px 0;">
                <h3 style="margin: 0 0 15px 0; color: #334155; font-size: 18px;">
                    🎯 What You Can Do Now:
                </h3>
                <ul style="margin: 0; padding-left: 20px; color: #475569; font-size: 15px; line-height: 1.8;">
                    <li><strong>Analyze Your Resume</strong> - Get AI-powered insights and improvements</li>
                    <li><strong>Practice Interviews</strong> - Mock interviews with real-time feedback</li>
                    <li><strong>Skill Gap Analysis</strong> - Discover what skills you need to learn</li>
                    <li><strong>Career Recommendations</strong> - Personalized learning paths</li>
                    <li><strong>Track Progress</strong> - Monitor your growth over time</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="#" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Get Started Now 🚀
                </a>
            </div>
            
            <p style="margin: 25px 0 0 0; color: #64748b; font-size: 14px; line-height: 1.6;">
                Need help? Reply to this email or check out our <a href="#" style="color: #667eea; text-decoration: none;">Help Center</a>.
            </p>
            
            <p style="margin: 20px 0 0 0; color: #475569; font-size: 15px;">
                Best regards,<br>
                <strong>The UpSkill AI Team</strong>
            </p>
        """
        return self._get_base_template(content)
    
    def _get_login_alert_template(self, user_name: str, login_time: datetime) -> str:
        """Login alert HTML template"""
        formatted_time = login_time.strftime('%B %d, %Y at %I:%M %p')
        
        content = f"""
            <h2 style="margin: 0 0 20px 0; color: #1e293b; font-size: 24px;">
                Hi {user_name}! 🔐
            </h2>
            
            <p style="margin: 0 0 20px 0; color: #475569; font-size: 16px; line-height: 1.6;">
                We detected a new login to your UpSkill AI account.
            </p>
            
            <div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 8px; padding: 20px; margin: 25px 0;">
                <p style="margin: 0 0 10px 0; color: #166534; font-size: 15px; font-weight: 600;">
                    ✓ Login Successful
                </p>
                <p style="margin: 0; color: #15803d; font-size: 14px;">
                    <strong>Time:</strong> {formatted_time}
                </p>
            </div>
            
            <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; border-radius: 8px; padding: 20px; margin: 25px 0;">
                <p style="margin: 0 0 10px 0; color: #991b1b; font-size: 15px; font-weight: 600;">
                    ⚠️ Wasn't You?
                </p>
                <p style="margin: 0 0 15px 0; color: #b91c1c; font-size: 14px;">
                    If you didn't log in, please secure your account immediately.
                </p>
                <a href="#" style="display: inline-block; background-color: #ef4444; color: #ffffff; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: 600; font-size: 14px;">
                    Reset Password Now
                </a>
            </div>
            
            <p style="margin: 25px 0 0 0; color: #64748b; font-size: 14px; line-height: 1.6;">
                For security tips, visit our <a href="#" style="color: #667eea; text-decoration: none;">Security Center</a>.
            </p>
            
            <p style="margin: 20px 0 0 0; color: #475569; font-size: 15px;">
                Best regards,<br>
                <strong>UpSkill AI Security Team</strong>
            </p>
        """
        return self._get_base_template(content)
    
    def _get_verification_template(self, user_name: str, verification_code: str) -> str:
        """Email verification HTML template"""
        content = f"""
            <h2 style="margin: 0 0 20px 0; color: #1e293b; font-size: 24px;">
                Hi {user_name}! 📧
            </h2>
            
            <p style="margin: 0 0 20px 0; color: #475569; font-size: 16px; line-height: 1.6;">
                Please verify your email address to complete your registration.
            </p>
            
            <div style="background-color: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 8px; padding: 30px; margin: 25px 0; text-align: center;">
                <p style="margin: 0 0 15px 0; color: #64748b; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">
                    Your Verification Code
                </p>
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; font-size: 32px; font-weight: 700; letter-spacing: 8px; padding: 20px; border-radius: 8px; display: inline-block;">
                    {verification_code}
                </div>
                <p style="margin: 15px 0 0 0; color: #94a3b8; font-size: 13px;">
                    This code expires in 15 minutes
                </p>
            </div>
            
            <p style="margin: 25px 0 0 0; color: #64748b; font-size: 14px; line-height: 1.6;">
                If you didn't create an account, you can safely ignore this email.
            </p>
            
            <p style="margin: 20px 0 0 0; color: #475569; font-size: 15px;">
                Best regards,<br>
                <strong>The UpSkill AI Team</strong>
            </p>
        """
        return self._get_base_template(content)
    
    def _get_password_reset_template(self, user_name: str, reset_code: str) -> str:
        """Password reset HTML template"""
        content = f"""
            <h2 style="margin: 0 0 20px 0; color: #1e293b; font-size: 24px;">
                Hi {user_name}! 🔑
            </h2>
            
            <p style="margin: 0 0 20px 0; color: #475569; font-size: 16px; line-height: 1.6;">
                You requested to reset your password. Use the code below to proceed.
            </p>
            
            <div style="background-color: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 8px; padding: 30px; margin: 25px 0; text-align: center;">
                <p style="margin: 0 0 15px 0; color: #64748b; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">
                    Your Reset Code
                </p>
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; font-size: 32px; font-weight: 700; letter-spacing: 8px; padding: 20px; border-radius: 8px; display: inline-block;">
                    {reset_code}
                </div>
                <p style="margin: 15px 0 0 0; color: #94a3b8; font-size: 13px;">
                    This code expires in 15 minutes
                </p>
            </div>
            
            <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 8px; padding: 20px; margin: 25px 0;">
                <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.6;">
                    <strong>⚠️ Security Notice:</strong> If you didn't request a password reset, please ignore this email and ensure your account is secure.
                </p>
            </div>
            
            <p style="margin: 20px 0 0 0; color: #475569; font-size: 15px;">
                Best regards,<br>
                <strong>UpSkill AI Security Team</strong>
            </p>
        """
        return self._get_base_template(content)


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create email service singleton"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
