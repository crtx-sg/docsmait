# backend/app/project_export_service.py
"""
Project Document Export Service

This service handles the comprehensive export of all project-related documents
into organized ZIP or TAR archives for regulatory compliance and delivery.
"""

import os
import io
import zipfile
import tarfile
import tempfile
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from sqlalchemy.orm import Session
from .database_config import get_db
from .db_models import Project, Document, ProjectMember, User
from .documents_service import documents_service
from .audit_service import AuditService
from .code_review_service import CodeReviewService


class ProjectExportService:
    """Service for exporting comprehensive project documentation packages"""
    
    def __init__(self):
        # Services will be initialized with db session when needed
        pass
    
    def export_project_documents(
        self, 
        project_id: int, 
        export_config: Dict[str, Any],
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Export comprehensive project documentation package
        
        Args:
            project_id: Project ID to export
            export_config: Export configuration with inclusion flags
            user_id: User requesting the export
            db: Database session
            
        Returns:
            Dict with export results and file information
        """
        try:
            print(f"DEBUG: Starting export for project_id={project_id}, user_id={user_id}")
            print(f"DEBUG: Export config: {export_config}")
            
            # Validate project access
            project = self._get_project_with_access_check(project_id, user_id, db)
            if not project:
                return {"success": False, "error": "Project not found or access denied"}
            
            print(f"DEBUG: Access granted for project: {project.name}")
            
            # Create temporary directory for export files
            with tempfile.TemporaryDirectory() as temp_dir:
                export_dir = Path(temp_dir) / f"project_{project.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                export_dir.mkdir(parents=True, exist_ok=True)
                
                export_stats = {
                    "document_count": 0,
                    "review_count": 0,
                    "code_review_count": 0,
                    "design_record_count": 0,
                    "audit_report_count": 0,
                    "total_files": 0,
                    "file_size_mb": 0.0
                }
                
                # Export each module based on configuration
                if export_config.get("include_documents", False):
                    print("DEBUG: Exporting documents...")
                    docs_count = self._export_approved_documents(project_id, export_dir, db)
                    export_stats["document_count"] = docs_count
                    print(f"DEBUG: Exported {docs_count} documents")
                
                if export_config.get("include_reviews", False):
                    print("DEBUG: Exporting reviews...")
                    reviews_count = self._export_project_reviews(project_id, export_dir, db)
                    export_stats["review_count"] = reviews_count
                    print(f"DEBUG: Exported {reviews_count} reviews")
                
                if export_config.get("include_code_reviews", False):
                    print("DEBUG: Exporting code reviews...")
                    code_reviews_count = self._export_code_reviews(project_id, export_dir, db)
                    export_stats["code_review_count"] = code_reviews_count
                    print(f"DEBUG: Exported {code_reviews_count} code reviews")
                
                if export_config.get("include_design_record", False):
                    print("DEBUG: Exporting design record...")
                    design_count = self._export_design_record(project_id, export_dir, db)
                    export_stats["design_record_count"] = design_count
                    print(f"DEBUG: Exported {design_count} design records")
                
                if export_config.get("include_audit_report", False):
                    print("DEBUG: Exporting audit reports...")
                    audit_count = self._export_audit_reports(project_id, export_dir, db)
                    export_stats["audit_report_count"] = audit_count
                    print(f"DEBUG: Exported {audit_count} audit reports")
                
                # Add metadata if requested
                if export_config.get("include_metadata", True):
                    self._create_export_metadata(project, export_config, export_stats, export_dir)
                
                # Calculate total files and size
                export_stats["total_files"] = sum([
                    export_stats["document_count"],
                    export_stats["review_count"], 
                    export_stats["code_review_count"],
                    export_stats["design_record_count"],
                    export_stats["audit_report_count"]
                ])
                
                print(f"DEBUG: Total files to export: {export_stats['total_files']}")
                
                # Check if export directory has any content
                has_content = any(export_dir.iterdir()) if export_dir.exists() else False
                print(f"DEBUG: Export directory has content: {has_content}")
                
                if not has_content:
                    # Create at least the metadata file if no other content
                    print("DEBUG: No content found, creating minimal export with metadata only")
                    if export_config.get("include_metadata", True):
                        self._create_export_metadata(project, export_config, export_stats, export_dir)
                    else:
                        # Create a simple info file
                        info_path = export_dir / "no_content_info.txt"
                        with open(info_path, "w", encoding="utf-8") as f:
                            f.write(f"No exportable content found for project: {project.name}\n")
                            f.write(f"Export requested on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write("This may be because:\n")
                            f.write("- No approved documents exist\n")
                            f.write("- No completed reviews exist\n") 
                            f.write("- Export modules are not properly configured\n")
                
                # Create archive
                archive_format = export_config.get("archive_format", "zip")
                archive_path = self._create_archive(export_dir, archive_format, temp_dir)
                
                if archive_path and archive_path.exists():
                    # Calculate file size
                    export_stats["file_size_mb"] = archive_path.stat().st_size / (1024 * 1024)
                    print(f"DEBUG: Archive created successfully, size: {export_stats['file_size_mb']:.2f} MB")
                    
                    # Read archive content for download
                    with open(archive_path, "rb") as f:
                        archive_content = f.read()
                    
                    return {
                        "success": True,
                        "archive_content": archive_content,
                        "filename": archive_path.name,
                        "mime_type": "application/zip" if archive_format == "zip" else "application/gzip",
                        **export_stats
                    }
                else:
                    print("DEBUG: Failed to create archive")
                    return {"success": False, "error": "Failed to create archive"}
        
        except Exception as e:
            return {"success": False, "error": f"Export failed: {str(e)}"}
    
    def _get_project_with_access_check(self, project_id: int, user_id: int, db: Session) -> Optional[Project]:
        """Verify user has access to project"""
        try:
            # Convert project_id to int if it's a string
            if isinstance(project_id, str):
                project_id = int(project_id)
            
            print(f"DEBUG: Checking access for project_id={project_id}, user_id={user_id}")
            
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                print(f"DEBUG: Project {project_id} not found in database")
                return None
            
            print(f"DEBUG: Found project: {project.name}")
            
            # Check if user is project member or admin
            is_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            ).first()
            
            if is_member:
                print(f"DEBUG: User {user_id} is a member of project {project_id}")
                return project
            
            # Check if user is admin
            user = db.query(User).filter(User.id == user_id).first()
            if user and (user.is_admin or user.is_super_admin):
                print(f"DEBUG: User {user_id} has admin access")
                return project
            
            print(f"DEBUG: User {user_id} has no access to project {project_id}")
            return None
            
        except Exception as e:
            print(f"DEBUG: Error in access check: {str(e)}")
            return None
    
    def _export_approved_documents(self, project_id: int, export_dir: Path, db: Session) -> int:
        """Export all approved documents as PDFs"""
        docs_dir = export_dir / "01_Documents"
        docs_dir.mkdir(exist_ok=True, parents=True)
        
        print(f"DEBUG: Looking for approved documents for project {project_id}")
        
        # Get approved documents for project
        documents = db.query(Document).filter(
            Document.project_id == project_id,
            Document.status == "approved"
        ).all()
        
        print(f"DEBUG: Found {len(documents)} approved documents")
        
        # Also check for any documents (not just approved) for debugging
        all_documents = db.query(Document).filter(Document.project_id == project_id).all()
        print(f"DEBUG: Total documents in project: {len(all_documents)}")
        for doc in all_documents:
            print(f"DEBUG: Document: {doc.name}, Status: {doc.status}")
        
        count = 0
        for doc in documents:
            try:
                print(f"DEBUG: Generating PDF for document: {doc.name}")
                pdf_content = self._generate_document_pdf(doc)
                if pdf_content:
                    safe_name = self._safe_filename(doc.name)
                    pdf_path = docs_dir / f"{safe_name}.pdf"
                    
                    with open(pdf_path, "wb") as f:
                        f.write(pdf_content)
                    print(f"DEBUG: Successfully exported document: {safe_name}.pdf")
                    count += 1
                else:
                    print(f"DEBUG: Failed to generate PDF for document: {doc.name}")
            except Exception as e:
                print(f"ERROR: Error exporting document {doc.name}: {e}")
        
        # Create document index
        if documents:
            self._create_document_index(documents, docs_dir)
        
        print(f"DEBUG: Document export completed, exported {count} documents")
        return count
    
    def _export_project_reviews(self, project_id: int, export_dir: Path, db: Session) -> int:
        """Export all project reviews as PDFs"""
        reviews_dir = export_dir / "02_Project_Reviews"
        reviews_dir.mkdir(exist_ok=True)
        
        # This would integrate with the actual reviews service
        # For now, create a placeholder
        count = 0
        
        try:
            # Placeholder for actual review export logic
            # This would call the reviews service to get completed reviews
            reviews_pdf = self._generate_reviews_summary_pdf(project_id, db)
            if reviews_pdf:
                pdf_path = reviews_dir / "project_reviews_summary.pdf"
                with open(pdf_path, "wb") as f:
                    f.write(reviews_pdf)
                count = 1
        except Exception as e:
            print(f"Error exporting reviews: {e}")
        
        return count
    
    def _export_code_reviews(self, project_id: int, export_dir: Path, db: Session) -> int:
        """Export all code reviews as PDFs"""
        code_dir = export_dir / "03_Code_Reviews"
        code_dir.mkdir(exist_ok=True)
        
        count = 0
        try:
            # Get code reviews from code review service
            from .code_review_service import CodeReviewService
            code_review_service = CodeReviewService(db)
            code_reviews = code_review_service.get_project_code_reviews(project_id, db)
            
            for review in code_reviews:
                if review.get("status") == "approved":
                    pdf_content = self._generate_code_review_pdf(review)
                    if pdf_content:
                        safe_name = self._safe_filename(f"code_review_{review.get('id', 'unknown')}")
                        pdf_path = code_dir / f"{safe_name}.pdf"
                        
                        with open(pdf_path, "wb") as f:
                            f.write(pdf_content)
                        count += 1
        except Exception as e:
            print(f"Error exporting code reviews: {e}")
        
        return count
    
    def _export_design_record(self, project_id: int, export_dir: Path, db: Session) -> int:
        """Export complete design record as PDF"""
        design_dir = export_dir / "04_Design_Record"
        design_dir.mkdir(exist_ok=True)
        
        try:
            # Generate comprehensive design record PDF
            design_record_pdf = self._generate_design_record_pdf(project_id, db)
            if design_record_pdf:
                pdf_path = design_dir / "complete_design_record.pdf"
                with open(pdf_path, "wb") as f:
                    f.write(design_record_pdf)
                return 1
        except Exception as e:
            print(f"Error exporting design record: {e}")
        
        return 0
    
    def _export_audit_reports(self, project_id: int, export_dir: Path, db: Session) -> int:
        """Export audit reports as PDFs"""
        audit_dir = export_dir / "05_Audit_Reports"
        audit_dir.mkdir(exist_ok=True)
        
        try:
            # Get latest audit report
            from .audit_service import AuditService
            audit_service = AuditService(db)
            audit_reports = audit_service.get_project_audits(project_id, db)
            
            if audit_reports:
                # Export the most recent audit
                latest_audit = audit_reports[0] if audit_reports else None
                if latest_audit:
                    audit_pdf = self._generate_audit_report_pdf(latest_audit)
                    if audit_pdf:
                        pdf_path = audit_dir / f"audit_report_{latest_audit.get('id', 'latest')}.pdf"
                        with open(pdf_path, "wb") as f:
                            f.write(audit_pdf)
                        return 1
        except Exception as e:
            print(f"Error exporting audit reports: {e}")
        
        return 0
    
    def _generate_document_pdf(self, document: Document) -> Optional[bytes]:
        """Generate PDF from document content"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=TA_CENTER
            )
            story.append(Paragraph(document.name, title_style))
            story.append(Spacer(1, 20))
            
            # Metadata table
            metadata = [
                ['Document Type:', document.document_type.replace('_', ' ').title()],
                ['Status:', document.status.title()],
                ['Version:', f"v{document.version}"],
                ['Created:', document.created_at.strftime("%Y-%m-%d %H:%M")],
                ['Last Modified:', document.updated_at.strftime("%Y-%m-%d %H:%M")],
            ]
            
            metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
            metadata_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(metadata_table)
            story.append(Spacer(1, 30))
            
            # Content
            if document.content:
                content_paragraphs = document.content.split('\n')
                for para in content_paragraphs:
                    if para.strip():
                        story.append(Paragraph(para, styles['Normal']))
                        story.append(Spacer(1, 12))
            else:
                story.append(Paragraph("No content available", styles['Italic']))
            
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        
        except Exception as e:
            print(f"Error generating PDF for document {document.name}: {e}")
            return None
    
    def _generate_reviews_summary_pdf(self, project_id: int, db: Session) -> Optional[bytes]:
        """Generate PDF summary of project reviews"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            story.append(Paragraph("Project Reviews Summary", styles['Title']))
            story.append(Spacer(1, 30))
            
            # Placeholder content - would integrate with actual reviews service
            story.append(Paragraph("Project Review Documentation", styles['Heading1']))
            story.append(Spacer(1, 20))
            
            story.append(Paragraph(
                "This section contains all completed project reviews including requirements reviews, "
                "design reviews, and approval workflows.", 
                styles['Normal']
            ))
            
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        
        except Exception as e:
            print(f"Error generating reviews summary PDF: {e}")
            return None
    
    def _generate_code_review_pdf(self, code_review: Dict[str, Any]) -> Optional[bytes]:
        """Generate PDF from code review data"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            story.append(Paragraph(f"Code Review: {code_review.get('title', 'Unknown')}", styles['Title']))
            story.append(Spacer(1, 20))
            
            # Review details
            story.append(Paragraph(f"Status: {code_review.get('status', 'Unknown')}", styles['Normal']))
            story.append(Paragraph(f"Reviewer: {code_review.get('reviewer', 'Unknown')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Comments
            if code_review.get('comments'):
                story.append(Paragraph("Review Comments:", styles['Heading2']))
                story.append(Paragraph(code_review['comments'], styles['Normal']))
            
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        
        except Exception as e:
            print(f"Error generating code review PDF: {e}")
            return None
    
    def _generate_design_record_pdf(self, project_id: int, db: Session) -> Optional[bytes]:
        """Generate comprehensive design record PDF"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Get project info
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return None
            
            # Title page
            story.append(Paragraph("Complete Design Record", styles['Title']))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Project: {project.name}", styles['Heading1']))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(PageBreak())
            
            # Table of Contents
            story.append(Paragraph("Table of Contents", styles['Heading1']))
            toc_items = [
                "1. Requirements Management",
                "2. Risk Analysis & FMEA", 
                "3. Design Artifacts",
                "4. Test Documentation",
                "5. Compliance Evidence",
                "6. Traceability Matrix"
            ]
            for item in toc_items:
                story.append(Paragraph(item, styles['Normal']))
            story.append(PageBreak())
            
            # Content sections - integrate with actual design record service
            for section in ["Requirements", "Risk Analysis", "Design", "Testing", "Compliance"]:
                story.append(Paragraph(f"{section} Documentation", styles['Heading1']))
                story.append(Spacer(1, 20))
                story.append(Paragraph(
                    f"This section contains all {section.lower()} documentation for the project.", 
                    styles['Normal']
                ))
                story.append(Spacer(1, 30))
            
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        
        except Exception as e:
            print(f"Error generating design record PDF: {e}")
            return None
    
    def _generate_audit_report_pdf(self, audit_data: Dict[str, Any]) -> Optional[bytes]:
        """Generate PDF from audit data"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            story.append(Paragraph(f"Audit Report: {audit_data.get('title', 'Unknown')}", styles['Title']))
            story.append(Spacer(1, 20))
            
            # Audit details
            story.append(Paragraph(f"Audit Type: {audit_data.get('audit_type', 'Unknown')}", styles['Normal']))
            story.append(Paragraph(f"Status: {audit_data.get('status', 'Unknown')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Findings
            if audit_data.get('findings'):
                story.append(Paragraph("Audit Findings:", styles['Heading2']))
                story.append(Paragraph(str(audit_data['findings']), styles['Normal']))
            
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        
        except Exception as e:
            print(f"Error generating audit report PDF: {e}")
            return None
    
    def _create_export_metadata(
        self, 
        project: Project, 
        export_config: Dict[str, Any], 
        export_stats: Dict[str, Any], 
        export_dir: Path
    ):
        """Create README.txt with export metadata"""
        readme_path = export_dir / "README.txt"
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"PROJECT DOCUMENT EXPORT\n")
            f.write(f"{'=' * 50}\n\n")
            f.write(f"Project Name: {project.name}\n")
            f.write(f"Project Description: {project.description or 'No description'}\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"EXPORT CONTENTS:\n")
            f.write(f"{'-' * 20}\n")
            if export_config.get("include_documents"):
                f.write(f"✓ Documents: {export_stats['document_count']} files\n")
            if export_config.get("include_reviews"):
                f.write(f"✓ Project Reviews: {export_stats['review_count']} files\n")
            if export_config.get("include_code_reviews"):
                f.write(f"✓ Code Reviews: {export_stats['code_review_count']} files\n")
            if export_config.get("include_design_record"):
                f.write(f"✓ Design Record: {export_stats['design_record_count']} files\n")
            if export_config.get("include_audit_report"):
                f.write(f"✓ Audit Reports: {export_stats['audit_report_count']} files\n")
            
            f.write(f"\nTOTAL FILES: {export_stats['total_files']}\n\n")
            
            f.write(f"FOLDER STRUCTURE:\n")
            f.write(f"{'-' * 20}\n")
            f.write(f"01_Documents/          - Approved project documents\n")
            f.write(f"02_Project_Reviews/    - Completed project reviews\n")
            f.write(f"03_Code_Reviews/       - Approved code reviews\n")
            f.write(f"04_Design_Record/      - Complete design record\n")
            f.write(f"05_Audit_Reports/      - Latest audit reports\n\n")
            
            f.write(f"Generated by Docsmait Document Management System\n")
            f.write(f"© {datetime.now().year} Coherentix Labs\n")
    
    def _create_document_index(self, documents: List[Document], docs_dir: Path):
        """Create CSV index of exported documents"""
        index_path = docs_dir / "document_index.csv"
        
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("Document Name,Type,Status,Version,Created Date,File Name\n")
            for doc in documents:
                safe_name = self._safe_filename(doc.name)
                f.write(f'"{doc.name}","{doc.document_type}","{doc.status}","{doc.version}","{doc.created_at.strftime("%Y-%m-%d")}","{safe_name}.pdf"\n')
    
    def _create_archive(self, source_dir: Path, archive_format: str, output_dir: str) -> Optional[Path]:
        """Create ZIP or TAR archive of export directory"""
        try:
            archive_name = f"{source_dir.name}.{archive_format}"
            archive_path = Path(output_dir) / archive_name
            
            if archive_format.lower() == "zip":
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in source_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(source_dir.parent)
                            zipf.write(file_path, arcname)
            
            elif archive_format.lower() in ["tar.gz", "tgz"]:
                with tarfile.open(archive_path, 'w:gz') as tarf:
                    tarf.add(source_dir, arcname=source_dir.name)
            
            else:
                print(f"Unsupported archive format: {archive_format}")
                return None
            
            return archive_path
        
        except Exception as e:
            print(f"Error creating archive: {e}")
            return None
    
    def _safe_filename(self, filename: str) -> str:
        """Create safe filename for filesystem"""
        # Remove or replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_. "
        safe_name = "".join(c if c in safe_chars else "_" for c in filename)
        # Remove excessive spaces and underscores
        safe_name = " ".join(safe_name.split())
        safe_name = safe_name.replace(" ", "_")
        # Limit length
        return safe_name[:100]


# Create global service instance
project_export_service = ProjectExportService()