"""
Publish Document Service

Service for publishing content from Design Records, Audit, and Issues as Documents
that can be processed through the standard Document workflow.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from .database_config import get_db
from .documents_service_v2 import DocumentsServiceV2
from .activity_log_service import ActivityLogService


class PublishDocumentService:
    """Service for publishing various content types as Documents"""
    
    def __init__(self):
        self.documents_service = DocumentsServiceV2()
        self.activity_service = ActivityLogService()
    
    def publish_design_record_as_document(
        self, 
        project_id: str, 
        project_name: str,
        report_type: str, 
        compliance_standard: str,
        markdown_content: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Publish Design Record report as a Document
        
        Args:
            project_id: Project ID for the design record
            project_name: Project name for document naming
            report_type: Type of design record report
            compliance_standard: Compliance standard used
            markdown_content: Pre-generated markdown content
            user_id: User creating the document
            
        Returns:
            Dict with success status and document details
        """
        try:
            # Generate timestamped document name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_project_name = project_name.replace(" ", "_")
            clean_report_type = report_type.replace(" ", "_")
            document_name = f"DesignRecord_{clean_report_type}_{clean_project_name}_{timestamp}"
            
            # Enhance markdown content with metadata
            enhanced_content = f"""# {report_type} - {project_name}

**Document Type**: Design Record Report  
**Project**: {project_name}  
**Compliance Standard**: {compliance_standard}  
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Published by**: User ID {user_id}

---

{markdown_content}

---

*This document was automatically generated from Design Record data and published to the Document workflow for review and approval.*
"""
            
            # Create document using Documents service
            result = self.documents_service.create_document(
                name=document_name,
                document_type="Design Record Report",
                content=enhanced_content,
                project_id=project_id,
                user_id=user_id
            )
            
            if result["success"]:
                # Log the publishing activity
                self.activity_service.log_document_created(
                    user_id=user_id,
                    document_id=result["document_id"],
                    document_name=document_name,
                    project_id=project_id
                )
                
                return {
                    "success": True,
                    "document_id": result["document_id"],
                    "document_name": document_name,
                    "message": f"Design Record '{report_type}' successfully published as document"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create document: {result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error publishing design record as document: {str(e)}"
            }
    
    def publish_issues_as_document(
        self,
        project_id: str,
        project_name: str, 
        markdown_content: str,
        user_id: int,
        total_issues: int = 0
    ) -> Dict[str, Any]:
        """
        Publish Issues report as a Document
        
        Args:
            project_id: Project ID for the issues
            project_name: Project name for document naming
            markdown_content: Pre-generated markdown content
            user_id: User creating the document
            total_issues: Number of issues in the report
            
        Returns:
            Dict with success status and document details
        """
        try:
            # Generate timestamped document name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_project_name = project_name.replace(" ", "_")
            document_name = f"IssuesReport_{clean_project_name}_{timestamp}"
            
            # Enhance markdown content with metadata
            enhanced_content = f"""# Issues Report - {project_name}

**Document Type**: Issues Report  
**Project**: {project_name}  
**Total Issues**: {total_issues}  
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Published by**: User ID {user_id}

---

{markdown_content}

---

*This document was automatically generated from Issues data and published to the Document workflow for review and approval.*
"""
            
            # Create document using Documents service
            result = self.documents_service.create_document(
                name=document_name,
                document_type="Issues Report",
                content=enhanced_content,
                project_id=project_id,
                user_id=user_id
            )
            
            if result["success"]:
                # Log the publishing activity
                self.activity_service.log_document_created(
                    user_id=user_id,
                    document_id=result["document_id"],
                    document_name=document_name,
                    project_id=project_id
                )
                
                return {
                    "success": True,
                    "document_id": result["document_id"],
                    "document_name": document_name,
                    "message": f"Issues report successfully published as document"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create document: {result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error publishing issues as document: {str(e)}"
            }
    
    def publish_audit_as_document(
        self,
        project_id: str,
        project_name: str,
        audit_id: str,
        audit_title: str,
        markdown_content: str,
        user_id: int,
        findings_count: int = 0,
        actions_count: int = 0
    ) -> Dict[str, Any]:
        """
        Publish Audit report as a Document
        
        Args:
            project_id: Project ID for the audit
            project_name: Project name for document naming
            audit_id: Audit ID
            audit_title: Audit title
            markdown_content: Pre-generated markdown content
            user_id: User creating the document
            findings_count: Number of findings in the audit
            actions_count: Number of corrective actions
            
        Returns:
            Dict with success status and document details
        """
        try:
            # Generate timestamped document name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_project_name = project_name.replace(" ", "_")
            clean_audit_title = audit_title.replace(" ", "_")
            document_name = f"AuditReport_{clean_audit_title}_{clean_project_name}_{timestamp}"
            
            # Enhance markdown content with metadata
            enhanced_content = f"""# Audit Report - {audit_title}

**Document Type**: Audit Report  
**Project**: {project_name}  
**Audit ID**: {audit_id}  
**Findings Count**: {findings_count}  
**Corrective Actions**: {actions_count}  
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Published by**: User ID {user_id}

---

{markdown_content}

---

*This document was automatically generated from Audit data and published to the Document workflow for review and approval.*
"""
            
            # Create document using Documents service
            result = self.documents_service.create_document(
                name=document_name,
                document_type="Audit Report",
                content=enhanced_content,
                project_id=project_id,
                user_id=user_id
            )
            
            if result["success"]:
                # Log the publishing activity
                self.activity_service.log_document_created(
                    user_id=user_id,
                    document_id=result["document_id"],
                    document_name=document_name,
                    project_id=project_id
                )
                
                return {
                    "success": True,
                    "document_id": result["document_id"],
                    "document_name": document_name,
                    "message": f"Audit report '{audit_title}' successfully published as document"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create document: {result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error publishing audit as document: {str(e)}"
            }