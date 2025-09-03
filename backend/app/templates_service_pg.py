# backend/app/templates_service_pg.py
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from .database_config import get_db
from .db_models import Template, User

class TemplatesService:
    """Service for managing templates using PostgreSQL/SQLAlchemy"""
    
    def create_template(self, name: str, description: str, document_type: str, 
                       content: str, tags: List[str], created_by: int) -> Dict[str, Any]:
        """Create a new template"""
        db = next(get_db())
        try:
            # Input validation
            if not name or not name.strip():
                return {"success": False, "error": "Template name is required"}
            
            if len(name.strip()) > 200:
                return {"success": False, "error": "Template name must be 200 characters or less"}
            
            # Check if template name already exists
            existing_template = db.query(Template).filter(Template.name == name.strip()).first()
            if existing_template:
                return {"success": False, "error": "Template name already exists"}
            
            # Create template
            template_id = str(uuid.uuid4())
            template = Template(
                id=template_id,
                name=name.strip(),
                description=description,
                document_type=self._normalize_document_type(document_type),
                content=content,
                tags=tags,  # SQLAlchemy will handle JSON serialization
                created_by=created_by,
                status="active"
            )
            db.add(template)
            db.commit()
            
            return {
                "success": True,
                "template_id": template_id,
                "message": "Template created successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error creating template: {e}")
            return {"success": False, "error": f"Error creating template: {str(e)}"}
        finally:
            db.close()
    
    def _normalize_document_type(self, document_type: str) -> str:
        """Convert frontend document type format to database format"""
        mapping = {
            "planning_documents": "Planning Documents",
            "process_documents": "Process Documents", 
            "specifications": "Specifications",
            "records": "Records",
            "templates": "Templates",
            "policies": "Policies",
            "manuals": "Manuals"
        }
        return mapping.get(document_type, document_type)
    
    def list_templates(self, status: Optional[str] = None, 
                      document_type: Optional[str] = None,
                      created_by: Optional[int] = None) -> List[Dict[str, Any]]:
        """List templates with optional filtering"""
        db = next(get_db())
        try:
            query = db.query(Template).options(
                joinedload(Template.creator),
                joinedload(Template.approver_user)
            )
            
            if status:
                query = query.filter(Template.status == status)
            if document_type:
                # Normalize document type for database query
                normalized_doc_type = self._normalize_document_type(document_type)
                query = query.filter(Template.document_type == normalized_doc_type)
            if created_by:
                query = query.filter(Template.created_by == created_by)
            
            templates_db = query.order_by(Template.created_at.desc()).all()
            
            templates = []
            for template in templates_db:
                templates.append({
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "document_type": template.document_type,
                    "content": template.content,
                    "tags": template.tags or [],
                    "version": template.version or "1.0",
                    "status": template.status,
                    "created_by": template.created_by,
                    "created_by_username": template.creator.username if template.creator else None,
                    "created_at": template.created_at.isoformat() if template.created_at else None,
                    "updated_at": template.updated_at.isoformat() if template.updated_at else None,
                    "approved_by": template.approved_by,
                    "approved_by_username": template.approver_user.username if template.approver_user else None,
                    "approved_at": template.approved_at.isoformat() if template.approved_at else None
                })
            
            return templates
            
        except Exception as e:
            print(f"Error listing templates: {e}")
            return []
        finally:
            db.close()
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID"""
        db = next(get_db())
        try:
            template = db.query(Template).options(
                joinedload(Template.creator),
                joinedload(Template.approver_user)
            ).filter(Template.id == template_id).first()
            
            if not template:
                return None
            
            return {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "document_type": template.document_type,
                "content": template.content,
                "tags": template.tags or [],
                "version": template.version or "1.0",
                "status": template.status,
                "created_by": template.created_by,
                "created_by_username": template.creator.username if template.creator else None,
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None,
                "approved_by": template.approved_by,
                "approved_by_username": template.approver_user.username if template.approver_user else None,
                "approved_at": template.approved_at.isoformat() if template.approved_at else None
            }
            
        except Exception as e:
            print(f"Error getting template: {e}")
            return None
        finally:
            db.close()
    
    def get_document_types(self) -> List[str]:
        """Get available document types"""
        return [
            "planning_documents",
            "process_documents", 
            "specifications",
            "records",
            "templates",
            "policies",
            "manuals"
        ]
    
    # Placeholder methods for other functionality
    def update_template(self, template_id: str, user_id: int, name: str, 
                       description: str, document_type: str, content: str, 
                       tags: List[str], status: str = None) -> Dict[str, Any]:
        """Update an existing template (creator only)"""
        db = next(get_db())
        try:
            # Input validation
            if not name or not name.strip():
                return {"success": False, "error": "Template name is required"}
            
            if len(name.strip()) > 200:
                return {"success": False, "error": "Template name must be 200 characters or less"}
            
            # Get the template
            template = db.query(Template).filter(Template.id == template_id).first()
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # Check if user is the creator or admin
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            if template.created_by != user_id and not user.is_admin:
                return {"success": False, "error": "Only the template creator or admin can update this template"}
            
            # Check if new name conflicts with existing template (excluding current one)
            if name.strip() != template.name:
                existing_template = db.query(Template).filter(
                    Template.name == name.strip(),
                    Template.id != template_id
                ).first()
                if existing_template:
                    return {"success": False, "error": "Template name already exists"}
            
            # Store original status for comparison
            original_status = template.status
            
            # Update template fields
            if name:
                template.name = name.strip()
            if description is not None:
                template.description = description
            if document_type:
                template.document_type = self._normalize_document_type(document_type)
            if content:
                template.content = content
            if tags is not None:
                template.tags = tags
            if status:
                template.status = status
            
            # Increment version if content changed
            if content and template.content != content:
                current_version = template.version or "1.0"
                try:
                    parts = current_version.split('.')
                    if len(parts) >= 2:
                        major = int(parts[0])
                        minor = int(parts[1])
                        template.version = f"{major}.{minor + 1}"
                    else:
                        template.version = "1.1"
                except (ValueError, IndexError):
                    template.version = "1.1"
            
            db.commit()
            
            # Check if template was approved and update KB
            if status == "approved" and original_status != "approved":
                updated_template = self.get_template_by_id(template_id)
                if updated_template:
                    self._update_knowledge_base(updated_template)
            
            return {
                "success": True,
                "template_id": template_id,
                "version": template.version,
                "message": "Template updated successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error updating template: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}
        finally:
            db.close()
    
    def delete_template(self, template_id: str, user_id: int) -> Dict[str, Any]:
        """Delete a template (creator or admin only)"""
        db = next(get_db())
        try:
            # Get the template
            template = db.query(Template).filter(Template.id == template_id).first()
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # Check if user is the creator or admin
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}
            
            if template.created_by != user_id and not user.is_admin:
                return {"success": False, "error": "Only the template creator or admin can delete this template"}
            
            # Delete the template
            db.delete(template)
            db.commit()
            
            return {
                "success": True,
                "message": "Template deleted successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error deleting template: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}
        finally:
            db.close()
    
    def request_approval(self, **kwargs) -> Dict[str, Any]:
        return {"success": False, "error": "Request approval not implemented yet"}
    
    def respond_to_approval(self, **kwargs) -> Dict[str, Any]:
        return {"success": False, "error": "Respond to approval not implemented yet"}
    
    def get_pending_approvals(self, user_id: int) -> List[Dict[str, Any]]:
        return []
    
    def _update_knowledge_base(self, template: Dict[str, Any]) -> None:
        """Update knowledge base when template is approved"""
        try:
            from .kb_service_pg import kb_service
            
            # Create collection name based on document type
            collection_name = template['document_type'].replace(' ', '_').lower()
            
            # Prepare filename and content
            filename = f"template_{template['name'].replace(' ', '_').lower()}_v{template['version']}.md"
            
            # Create content with metadata
            content = f"""# Template: {template['name']}

**Version:** {template['version']}
**Status:** {template['status']}
**Document Type:** {template['document_type']}
**Description:** {template['description']}
**Tags:** {', '.join(template['tags']) if template['tags'] else 'None'}
**Created by:** {template['created_by_username']}
**Created on:** {template['created_at']}

## Template Content

{template['content']}
"""
            
            # Prepare metadata for Qdrant payload
            metadata = {
                "template_id": template['id'],
                "template_name": template['name'],
                "version": template['version'],
                "status": template['status'],
                "document_type": template['document_type'],
                "created_by": template['created_by_username'],
                "tags": template['tags']
            }
            
            # Add to knowledge base
            result = kb_service.add_text_to_collection(
                collection_name=collection_name,
                text_content=content,
                filename=filename,
                metadata=metadata
            )
            
            if result.get("success"):
                print(f"✅ Template '{template['name']}' added to knowledge base collection '{collection_name}'")
            else:
                print(f"❌ Failed to add template to KB: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Error updating knowledge base for template: {e}")

    def export_to_pdf(self, template_id: str, include_metadata: bool) -> Dict[str, Any]:
        """Export template to PDF format"""
        try:
            # Get template
            template = self.get_template_by_id(template_id)
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # Try to generate PDF using various methods
            try:
                # Method 1: Try using weasyprint (if available)
                import weasyprint
                from weasyprint import HTML, CSS
                from io import BytesIO
                import base64
                
                # Create HTML content
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>{template['name']}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                        h1, h2, h3 {{ color: #333; }}
                        .metadata {{ background: #f5f5f5; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                        .content {{ margin-top: 20px; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                        pre {{ background: #f8f8f8; padding: 10px; border-radius: 4px; }}
                        code {{ background: #f0f0f0; padding: 2px 4px; border-radius: 3px; }}
                    </style>
                </head>
                <body>
                """
                
                if include_metadata:
                    html_content += f"""
                    <div class="metadata">
                        <h2>Template Information</h2>
                        <p><strong>Name:</strong> {template['name']}</p>
                        <p><strong>Description:</strong> {template['description']}</p>
                        <p><strong>Document Type:</strong> {template['document_type'].replace('_', ' ').title()}</p>
                        <p><strong>Version:</strong> {template['version']}</p>
                        <p><strong>Status:</strong> {template['status'].title()}</p>
                        <p><strong>Created by:</strong> {template['created_by_username']}</p>
                        <p><strong>Created on:</strong> {template['created_at'][:10]}</p>
                        {f"<p><strong>Tags:</strong> {', '.join(template['tags'])}</p>" if template['tags'] else ""}
                    </div>
                    """
                
                # Convert markdown to HTML
                import markdown
                md_content = markdown.markdown(template['content'], extensions=['tables', 'fenced_code'])
                
                html_content += f"""
                    <div class="content">
                        <h1>Template Content</h1>
                        {md_content}
                    </div>
                </body>
                </html>
                """
                
                # Generate PDF
                pdf_buffer = BytesIO()
                HTML(string=html_content).write_pdf(pdf_buffer)
                pdf_buffer.seek(0)
                
                # Encode as base64 for JSON response
                pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
                
                return {
                    "success": True, 
                    "pdf_data": pdf_base64,
                    "filename": f"{template['name'].replace(' ', '_')}_v{template['version']}.pdf",
                    "content_type": "application/pdf"
                }
                
            except ImportError:
                # Method 2: Fallback to simple HTML export if weasyprint not available
                import base64
                
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>{template['name']}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                        h1, h2, h3 {{ color: #333; }}
                        .metadata {{ background: #f5f5f5; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <h1>{template['name']}</h1>
                """
                
                if include_metadata:
                    html_content += f"""
                    <div class="metadata">
                        <h2>Template Information</h2>
                        <p><strong>Description:</strong> {template['description']}</p>
                        <p><strong>Document Type:</strong> {template['document_type'].replace('_', ' ').title()}</p>
                        <p><strong>Version:</strong> {template['version']}</p>
                        <p><strong>Status:</strong> {template['status'].title()}</p>
                        <p><strong>Created by:</strong> {template['created_by_username']}</p>
                        <p><strong>Created on:</strong> {template['created_at'][:10]}</p>
                    </div>
                    """
                
                # Simple markdown-like conversion
                content = template['content']
                content = content.replace('\n# ', '\n<h1>').replace('\n## ', '\n<h2>').replace('\n### ', '\n<h3>')
                content = content.replace('**', '<strong>').replace('**', '</strong>')
                content = content.replace('*', '<em>').replace('*', '</em>')
                content = content.replace('\n', '<br>')
                
                html_content += f"""
                    <div class="content">
                        <h2>Template Content</h2>
                        {content}
                    </div>
                </body>
                </html>
                """
                
                # Return HTML as fallback
                html_base64 = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
                
                return {
                    "success": True,
                    "html_data": html_base64,
                    "filename": f"{template['name'].replace(' ', '_')}_v{template['version']}.html",
                    "content_type": "text/html",
                    "message": "PDF library not available. Generated HTML export instead."
                }
                
        except Exception as e:
            return {"success": False, "error": f"Export failed: {str(e)}"}

# Create global instance
templates_service = TemplatesService()