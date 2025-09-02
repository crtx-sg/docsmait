# backend/app/email_service.py
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from .user_service import user_service
from .settings_service import settings_service
import logging

logger = logging.getLogger(__name__)

class EmailNotificationService:
    def __init__(self):
        self.smtp_settings = self._load_smtp_settings()
        
    def _load_smtp_settings(self) -> Dict[str, Any]:
        """Load SMTP settings from database"""
        return settings_service.get_smtp_settings()
    
    def update_smtp_settings(self, settings: Dict[str, Any], updated_by: Optional[int] = None) -> bool:
        """Update SMTP settings"""
        try:
            success = settings_service.update_smtp_settings(settings, updated_by)
            if success:
                self.smtp_settings = self._load_smtp_settings()  # Reload settings
            return success
        except Exception as e:
            logger.error(f"Failed to update SMTP settings: {e}")
            return False
    
    def _create_smtp_connection(self):
        """Create SMTP connection based on settings"""
        if not self.smtp_settings.get("enabled", False):
            raise Exception("Email notifications are disabled")
            
        server = smtplib.SMTP(
            self.smtp_settings["server_name"],
            self.smtp_settings["port"]
        )
        
        if self.smtp_settings["connection_security"] == "STARTTLS":
            server.starttls(context=ssl.create_default_context())
        elif self.smtp_settings["connection_security"] == "SSL":
            server = smtplib.SMTP_SSL(
                self.smtp_settings["server_name"],
                self.smtp_settings["port"],
                context=ssl.create_default_context()
            )
        
        if self.smtp_settings["username"] and self.smtp_settings["password"]:
            server.login(
                self.smtp_settings["username"],
                self.smtp_settings["password"]
            )
            
        return server
    
    def _send_email(self, to_emails: List[str], subject: str, body: str, html_body: Optional[str] = None):
        """Send email using configured SMTP settings"""
        try:
            if not self.smtp_settings.get("enabled", False):
                logger.info(f"Email notifications disabled. Would send: {subject} to {to_emails}")
                return True
                
            server = self._create_smtp_connection()
            
            for to_email in to_emails:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = self.smtp_settings["username"]
                msg["To"] = to_email
                
                # Add plain text part
                text_part = MIMEText(body, "plain")
                msg.attach(text_part)
                
                # Add HTML part if provided
                if html_body:
                    html_part = MIMEText(html_body, "html")
                    msg.attach(html_part)
                
                server.sendmail(
                    self.smtp_settings["username"],
                    to_email,
                    msg.as_string()
                )
            
            server.quit()
            logger.info(f"Successfully sent email '{subject}' to {len(to_emails)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email '{subject}': {e}")
            return False
    
    def _get_user_email(self, user_id: int) -> Optional[str]:
        """Get user email by user ID"""
        try:
            user = user_service.get_user_by_id(user_id)
            return user.email if user else None
        except Exception as e:
            logger.error(f"Failed to get user email for user_id {user_id}: {e}")
            return None
    
    def _get_user_username(self, user_id: int) -> Optional[str]:
        """Get username by user ID"""
        try:
            user = user_service.get_user_by_id(user_id)
            return user.username if user else None
        except Exception as e:
            logger.error(f"Failed to get username for user_id {user_id}: {e}")
            return None
    
    def send_project_member_welcome(self, member_user_id: int, project_name: str, added_by_user_id: int):
        """Send welcome email when new member is added to project"""
        try:
            member_email = self._get_user_email(member_user_id)
            member_username = self._get_user_username(member_user_id)
            
            if not member_email or not member_username:
                logger.error(f"Could not find email/username for user_id {member_user_id}")
                return False
            
            subject = f"Welcome to Project: {project_name}"
            
            body = f"""Welcome {member_username}! You are assigned to Project {project_name}.

You now have access to:
- Project documents and templates
- Collaboration tools
- Review workflows

Login to the system to start collaborating on this project.

Best regards,
Docsmait Team"""
            
            html_body = f"""
            <html>
            <body>
                <h2>Welcome to Project: {project_name}</h2>
                <p>Hello {member_username}!</p>
                <p>You have been assigned to Project <strong>{project_name}</strong>.</p>
                
                <h3>You now have access to:</h3>
                <ul>
                    <li>Project documents and templates</li>
                    <li>Collaboration tools</li>
                    <li>Review workflows</li>
                </ul>
                
                <p>Login to the system to start collaborating on this project.</p>
                
                <p>Best regards,<br>Docsmait Team</p>
            </body>
            </html>
            """
            
            return self._send_email([member_email], subject, body, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send project welcome email: {e}")
            return False
    
    def send_review_notification(self, document_name: str, reviewer_user_id: int, status: str, comments: str = "", next_status: str = ""):
        """Send notification when review status changes"""
        try:
            reviewer_email = self._get_user_email(reviewer_user_id)
            reviewer_username = self._get_user_username(reviewer_user_id)
            
            if not reviewer_email or not reviewer_username:
                logger.error(f"Could not find email/username for reviewer_id {reviewer_user_id}")
                return False
            
            subject = f"Document Review Update: {document_name}"
            
            status_messages = {
                "request_review": "A document has been submitted for your review",
                "needs_review": "A document requires additional review",
                "approved": "Document review has been completed"
            }
            
            body = f"""Document Review Notification

The {document_name}
Reviewed by {reviewer_username}
{comments if comments else 'No comments provided'}
Status: {status_messages.get(status, status)}"""
            
            if next_status:
                body += f"\nMoved to {next_status}"
                
            body += f"""

Please login to the system to view the full details.

Best regards,
Docsmait Team"""
            
            html_body = f"""
            <html>
            <body>
                <h2>Document Review Update</h2>
                <p><strong>Document:</strong> {document_name}</p>
                <p><strong>Reviewed by:</strong> {reviewer_username}</p>
                <p><strong>Status:</strong> {status_messages.get(status, status)}</p>
                
                {f'<p><strong>Comments:</strong><br>{comments}</p>' if comments else ''}
                {f'<p><strong>Moved to:</strong> {next_status}</p>' if next_status else ''}
                
                <p>Please login to the system to view the full details.</p>
                
                <p>Best regards,<br>Docsmait Team</p>
            </body>
            </html>
            """
            
            return self._send_email([reviewer_email], subject, body, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send review notification: {e}")
            return False
    
    def send_document_workflow_notification(self, project_name: str, document_name: str, file_name: str, status: str, stakeholder_emails: List[str]):
        """Send notification for document workflow status change"""
        try:
            if not stakeholder_emails:
                logger.warning("No stakeholder emails provided for document workflow notification")
                return False
            
            subject = f"Document Status Update: {document_name}"
            
            body = f"""Document Workflow Notification

Project name: {project_name}
Document Name: {file_name}
Status: {status}

The document status has been updated. Please login to the system for more details.

Best regards,
Docsmait Team"""
            
            html_body = f"""
            <html>
            <body>
                <h2>Document Workflow Update</h2>
                <p><strong>Project:</strong> {project_name}</p>
                <p><strong>Document:</strong> {file_name}</p>
                <p><strong>Status:</strong> {status}</p>
                
                <p>The document status has been updated. Please login to the system for more details.</p>
                
                <p>Best regards,<br>Docsmait Team</p>
            </body>
            </html>
            """
            
            return self._send_email(stakeholder_emails, subject, body, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send document workflow notification: {e}")
            return False
    
    def send_code_review_notification(self, project_name: str, pull_request_title: str, summary_comment: str, review_status: str, reviewer_emails: List[str]):
        """Send notification for code review"""
        try:
            if not reviewer_emails:
                logger.warning("No reviewer emails provided for code review notification")
                return False
            
            subject = f"Code Review: {pull_request_title}"
            
            body = f"""Code Review Notification

Project name: {project_name}
Pull Request: {pull_request_title}
Summary Comment: {summary_comment if summary_comment else 'No summary provided'}
Review Status: {review_status}

Please login to the system to review the code changes.

Best regards,
Docsmait Team"""
            
            html_body = f"""
            <html>
            <body>
                <h2>Code Review Required</h2>
                <p><strong>Project:</strong> {project_name}</p>
                <p><strong>Pull Request:</strong> {pull_request_title}</p>
                <p><strong>Summary:</strong> {summary_comment if summary_comment else 'No summary provided'}</p>
                <p><strong>Status:</strong> {review_status}</p>
                
                <p>Please login to the system to review the code changes.</p>
                
                <p>Best regards,<br>Docsmait Team</p>
            </body>
            </html>
            """
            
            return self._send_email(reviewer_emails, subject, body, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send code review notification: {e}")
            return False
    
    def send_audit_schedule_notification(self, project_name: str, audit_title: str, audit_type: str, scope: str, department: str, planned_start_date: str, planned_end_date: str, auditor_username: str, audit_team_usernames: List[str], stakeholder_emails: List[str]):
        """Send notification when audit is scheduled"""
        try:
            if not stakeholder_emails:
                logger.warning("No stakeholder emails provided for audit schedule notification")
                return False
            
            subject = f"Audit Scheduled: {audit_title}"
            
            audit_team_str = ", ".join(audit_team_usernames) if audit_team_usernames else "Not assigned"
            
            body = f"""Audit Schedule Notification

Audit {audit_title} is scheduled.
Type: {audit_type}
Scope: {scope}
Department: {department}
Planned Start Date: {planned_start_date}
Planned End Date: {planned_end_date}
Auditor: {auditor_username}
Audit Team: {audit_team_str}

Project: {project_name}

Please prepare accordingly and login to the system for more details.

Best regards,
Docsmait Team"""
            
            html_body = f"""
            <html>
            <body>
                <h2>Audit Scheduled: {audit_title}</h2>
                <p>An audit has been scheduled for project <strong>{project_name}</strong>.</p>
                
                <h3>Audit Details:</h3>
                <ul>
                    <li><strong>Type:</strong> {audit_type}</li>
                    <li><strong>Scope:</strong> {scope}</li>
                    <li><strong>Department:</strong> {department}</li>
                    <li><strong>Planned Start Date:</strong> {planned_start_date}</li>
                    <li><strong>Planned End Date:</strong> {planned_end_date}</li>
                    <li><strong>Lead Auditor:</strong> {auditor_username}</li>
                    <li><strong>Audit Team:</strong> {audit_team_str}</li>
                </ul>
                
                <p>Please prepare accordingly and login to the system for more details.</p>
                
                <p>Best regards,<br>Docsmait Team</p>
            </body>
            </html>
            """
            
            return self._send_email(stakeholder_emails, subject, body, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send audit schedule notification: {e}")
            return False

# Global email service instance
email_service = EmailNotificationService()