# backend/app/audit_service.py
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, and_
from datetime import datetime, date
import uuid

from .db_models import Audit, Finding, CorrectiveAction, User, Project, ProjectMember
from .models import (
    AuditCreate, AuditUpdate, AuditResponse,
    FindingCreate, FindingUpdate, FindingResponse,
    CorrectiveActionCreate, CorrectiveActionUpdate, CorrectiveActionResponse
)
from .email_service import email_service

class AuditService:
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_audit_number(self) -> str:
        """Generate unique audit number in format AUD-YYYY-NNNN"""
        year = datetime.now().year
        count = self.db.query(Audit).filter(
            func.extract('year', Audit.created_at) == year
        ).count()
        return f"AUD-{year}-{count + 1:04d}"
    
    def generate_finding_number(self, audit_id: str) -> str:
        """Generate unique finding number within audit"""
        count = self.db.query(Finding).filter(Finding.audit_id == audit_id).count()
        return f"F{count + 1:03d}"
    
    def generate_action_number(self, finding_id: str) -> str:
        """Generate unique action number within finding"""
        count = self.db.query(CorrectiveAction).filter(CorrectiveAction.finding_id == finding_id).count()
        return f"CA{count + 1:03d}"
    
    # === AUDIT CRUD ===
    
    def create_audit(self, audit_data: AuditCreate, current_user_id: int) -> AuditResponse:
        """Create new audit"""
        audit_id = str(uuid.uuid4())
        audit_number = self.generate_audit_number()
        
        audit = Audit(
            id=audit_id,
            audit_number=audit_number,
            title=audit_data.title,
            audit_type=audit_data.audit_type,
            scope=audit_data.scope,
            planned_start_date=datetime.strptime(audit_data.planned_start_date, "%Y-%m-%d").date(),
            planned_end_date=datetime.strptime(audit_data.planned_end_date, "%Y-%m-%d").date(),
            lead_auditor=audit_data.lead_auditor,
            audit_team=audit_data.audit_team,
            auditee_department=audit_data.auditee_department,
            compliance_standard=audit_data.compliance_standard,
            project_id=audit_data.project_id,
            created_by=current_user_id
        )
        
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        
        # Send email notifications for audit scheduling
        try:
            # Get project and stakeholder details
            project = self.db.query(Project).filter(Project.id == audit_data.project_id).first()
            project_name = project.name if project else "Unknown Project"
            
            # Get lead auditor details
            lead_auditor = self.db.query(User).filter(User.id == audit_data.lead_auditor).first()
            auditor_username = lead_auditor.username if lead_auditor else "Unknown Auditor"
            
            # Get audit team usernames
            audit_team_usernames = []
            for team_member_id in audit_data.audit_team:
                team_member = self.db.query(User).filter(User.id == team_member_id).first()
                if team_member:
                    audit_team_usernames.append(team_member.username)
            
            # Get stakeholder emails (project members + audit team + lead auditor)
            stakeholder_emails = []
            
            # Add project members
            project_members = self.db.query(ProjectMember).options(
                joinedload(ProjectMember.user)
            ).filter(ProjectMember.project_id == audit_data.project_id).all()
            
            for member in project_members:
                if member.user and member.user.email:
                    stakeholder_emails.append(member.user.email)
            
            # Add audit team emails
            if lead_auditor and lead_auditor.email:
                stakeholder_emails.append(lead_auditor.email)
                
            for team_member_id in audit_data.audit_team:
                team_member = self.db.query(User).filter(User.id == team_member_id).first()
                if team_member and team_member.email:
                    stakeholder_emails.append(team_member.email)
            
            # Remove duplicates
            stakeholder_emails = list(set(stakeholder_emails))
            
            # Send audit schedule notification
            if stakeholder_emails:
                email_service.send_audit_schedule_notification(
                    project_name=project_name,
                    audit_title=audit_data.title,
                    audit_type=audit_data.audit_type,
                    scope=audit_data.scope,
                    department=audit_data.auditee_department,
                    planned_start_date=audit_data.planned_start_date,
                    planned_end_date=audit_data.planned_end_date,
                    auditor_username=auditor_username,
                    audit_team_usernames=audit_team_usernames,
                    stakeholder_emails=stakeholder_emails
                )
        except Exception as e:
            print(f"Failed to send audit schedule notification emails: {e}")
            # Don't fail audit creation if email fails
        
        return self._audit_to_response(audit)
    
    def get_audits(self, project_id: Optional[str] = None, status: Optional[str] = None) -> List[AuditResponse]:
        """Get all audits with optional filtering"""
        query = self.db.query(Audit).options(
            joinedload(Audit.lead_auditor_user),
            joinedload(Audit.creator),
            joinedload(Audit.project)
        )
        
        if project_id:
            query = query.filter(Audit.project_id == project_id)
        if status:
            query = query.filter(Audit.status == status)
            
        audits = query.order_by(desc(Audit.created_at)).all()
        return [self._audit_to_response(audit) for audit in audits]
    
    def get_audit(self, audit_id: str) -> Optional[AuditResponse]:
        """Get single audit by ID"""
        audit = self.db.query(Audit).options(
            joinedload(Audit.lead_auditor_user),
            joinedload(Audit.creator),
            joinedload(Audit.project)
        ).filter(Audit.id == audit_id).first()
        
        return self._audit_to_response(audit) if audit else None
    
    def update_audit(self, audit_id: str, audit_data: AuditUpdate) -> Optional[AuditResponse]:
        """Update existing audit"""
        audit = self.db.query(Audit).filter(Audit.id == audit_id).first()
        if not audit:
            return None
        
        for field, value in audit_data.dict(exclude_unset=True).items():
            if field in ["planned_start_date", "planned_end_date", "actual_start_date", "actual_end_date"] and value:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            setattr(audit, field, value)
        
        self.db.commit()
        self.db.refresh(audit)
        return self._audit_to_response(audit)
    
    def delete_audit(self, audit_id: str) -> bool:
        """Delete audit and all related data"""
        audit = self.db.query(Audit).filter(Audit.id == audit_id).first()
        if not audit:
            return False
        
        self.db.delete(audit)
        self.db.commit()
        return True
    
    # === FINDING CRUD ===
    
    def create_finding(self, finding_data: FindingCreate, current_user_id: int) -> FindingResponse:
        """Create new finding"""
        finding_id = str(uuid.uuid4())
        finding_number = self.generate_finding_number(finding_data.audit_id)
        
        finding = Finding(
            id=finding_id,
            audit_id=finding_data.audit_id,
            finding_number=finding_number,
            title=finding_data.title,
            description=finding_data.description,
            severity=finding_data.severity,
            category=finding_data.category,
            clause_reference=finding_data.clause_reference,
            evidence=finding_data.evidence,
            root_cause=finding_data.root_cause,
            immediate_action=finding_data.immediate_action,
            identified_by=current_user_id,
            identified_date=datetime.strptime(finding_data.identified_date, "%Y-%m-%d").date(),
            due_date=datetime.strptime(finding_data.due_date, "%Y-%m-%d").date() if finding_data.due_date else None
        )
        
        self.db.add(finding)
        self.db.commit()
        self.db.refresh(finding)
        
        return self._finding_to_response(finding)
    
    def get_findings(self, audit_id: Optional[str] = None, status: Optional[str] = None) -> List[FindingResponse]:
        """Get findings with optional filtering"""
        query = self.db.query(Finding).options(
            joinedload(Finding.identifier),
            joinedload(Finding.verifier)
        )
        
        if audit_id:
            query = query.filter(Finding.audit_id == audit_id)
        if status:
            query = query.filter(Finding.status == status)
            
        findings = query.order_by(desc(Finding.created_at)).all()
        return [self._finding_to_response(finding) for finding in findings]
    
    def get_finding(self, finding_id: str) -> Optional[FindingResponse]:
        """Get single finding by ID"""
        finding = self.db.query(Finding).options(
            joinedload(Finding.identifier),
            joinedload(Finding.verifier)
        ).filter(Finding.id == finding_id).first()
        
        return self._finding_to_response(finding) if finding else None
    
    def update_finding(self, finding_id: str, finding_data: FindingUpdate) -> Optional[FindingResponse]:
        """Update existing finding"""
        finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            return None
        
        # Store original status for KB check
        original_status = finding.status
        
        for field, value in finding_data.dict(exclude_unset=True).items():
            if field in ["identified_date", "due_date", "closed_date", "verified_date"] and value:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            setattr(finding, field, value)
        
        self.db.commit()
        self.db.refresh(finding)
        
        # Check if finding was closed and update KB
        if finding_data.status == "closed" and original_status != "closed":
            updated_finding = self.get_finding(finding_id)
            if updated_finding:
                self._update_finding_knowledge_base(updated_finding)
        
        return self._finding_to_response(finding)
    
    def delete_finding(self, finding_id: str) -> bool:
        """Delete finding and all related corrective actions"""
        finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            return False
        
        self.db.delete(finding)
        self.db.commit()
        return True
    
    # === CORRECTIVE ACTION CRUD ===
    
    def create_corrective_action(self, action_data: CorrectiveActionCreate, current_user_id: int) -> CorrectiveActionResponse:
        """Create new corrective action"""
        action_id = str(uuid.uuid4())
        action_number = self.generate_action_number(action_data.finding_id)
        
        action = CorrectiveAction(
            id=action_id,
            finding_id=action_data.finding_id,
            action_number=action_number,
            description=action_data.description,
            responsible_person=action_data.responsible_person,
            target_date=datetime.strptime(action_data.target_date, "%Y-%m-%d").date(),
            priority=action_data.priority,
            resources_required=action_data.resources_required,
            success_criteria=action_data.success_criteria
        )
        
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        
        return self._action_to_response(action)
    
    def get_corrective_actions(self, finding_id: Optional[str] = None, status: Optional[str] = None) -> List[CorrectiveActionResponse]:
        """Get corrective actions with optional filtering"""
        query = self.db.query(CorrectiveAction).options(
            joinedload(CorrectiveAction.responsible_user),
            joinedload(CorrectiveAction.verifier)
        )
        
        if finding_id:
            query = query.filter(CorrectiveAction.finding_id == finding_id)
        if status:
            query = query.filter(CorrectiveAction.status == status)
            
        actions = query.order_by(desc(CorrectiveAction.created_at)).all()
        return [self._action_to_response(action) for action in actions]
    
    def get_corrective_action(self, action_id: str) -> Optional[CorrectiveActionResponse]:
        """Get single corrective action by ID"""
        action = self.db.query(CorrectiveAction).options(
            joinedload(CorrectiveAction.responsible_user),
            joinedload(CorrectiveAction.verifier)
        ).filter(CorrectiveAction.id == action_id).first()
        
        return self._action_to_response(action) if action else None
    
    def update_corrective_action(self, action_id: str, action_data: CorrectiveActionUpdate) -> Optional[CorrectiveActionResponse]:
        """Update existing corrective action"""
        action = self.db.query(CorrectiveAction).filter(CorrectiveAction.id == action_id).first()
        if not action:
            return None
        
        for field, value in action_data.dict(exclude_unset=True).items():
            if field in ["target_date", "actual_completion_date", "effectiveness_verified_date"] and value:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            setattr(action, field, value)
        
        self.db.commit()
        self.db.refresh(action)
        return self._action_to_response(action)
    
    def delete_corrective_action(self, action_id: str) -> bool:
        """Delete corrective action"""
        action = self.db.query(CorrectiveAction).filter(CorrectiveAction.id == action_id).first()
        if not action:
            return False
        
        self.db.delete(action)
        self.db.commit()
        return True
    
    # === HELPER METHODS ===
    
    def _audit_to_response(self, audit: Audit) -> AuditResponse:
        """Convert Audit DB model to response model"""
        # Get usernames for audit team
        team_users = self.db.query(User).filter(User.id.in_(audit.audit_team or [])).all()
        team_usernames = [user.username for user in team_users]
        
        # Count findings
        findings_count = self.db.query(Finding).filter(Finding.audit_id == audit.id).count()
        open_findings_count = self.db.query(Finding).filter(
            and_(Finding.audit_id == audit.id, Finding.status == "open")
        ).count()
        
        return AuditResponse(
            id=audit.id,
            audit_number=audit.audit_number,
            title=audit.title,
            audit_type=audit.audit_type,
            scope=audit.scope,
            planned_start_date=audit.planned_start_date.isoformat(),
            planned_end_date=audit.planned_end_date.isoformat(),
            actual_start_date=audit.actual_start_date.isoformat() if audit.actual_start_date else None,
            actual_end_date=audit.actual_end_date.isoformat() if audit.actual_end_date else None,
            status=audit.status,
            lead_auditor=audit.lead_auditor,
            lead_auditor_username=audit.lead_auditor_user.username,
            audit_team=audit.audit_team or [],
            audit_team_usernames=team_usernames,
            auditee_department=audit.auditee_department,
            compliance_standard=audit.compliance_standard,
            overall_rating=audit.overall_rating,
            project_id=audit.project_id,
            project_name=audit.project.name,
            created_by=audit.created_by,
            created_by_username=audit.creator.username,
            created_at=audit.created_at.isoformat(),
            updated_at=audit.updated_at.isoformat(),
            findings_count=findings_count,
            open_findings_count=open_findings_count
        )
    
    def _finding_to_response(self, finding: Finding) -> FindingResponse:
        """Convert Finding DB model to response model"""
        # Count corrective actions
        actions_count = self.db.query(CorrectiveAction).filter(CorrectiveAction.finding_id == finding.id).count()
        
        return FindingResponse(
            id=finding.id,
            audit_id=finding.audit_id,
            finding_number=finding.finding_number,
            title=finding.title,
            description=finding.description,
            severity=finding.severity,
            category=finding.category,
            clause_reference=finding.clause_reference,
            evidence=finding.evidence,
            status=finding.status,
            root_cause=finding.root_cause,
            immediate_action=finding.immediate_action,
            identified_by=finding.identified_by,
            identified_by_username=finding.identifier.username,
            identified_date=finding.identified_date.isoformat(),
            due_date=finding.due_date.isoformat() if finding.due_date else None,
            closed_date=finding.closed_date.isoformat() if finding.closed_date else None,
            verified_by=finding.verified_by,
            verified_by_username=finding.verifier.username if finding.verifier else None,
            verified_date=finding.verified_date.isoformat() if finding.verified_date else None,
            created_at=finding.created_at.isoformat(),
            updated_at=finding.updated_at.isoformat(),
            corrective_actions_count=actions_count
        )
    
    def _action_to_response(self, action: CorrectiveAction) -> CorrectiveActionResponse:
        """Convert CorrectiveAction DB model to response model"""
        return CorrectiveActionResponse(
            id=action.id,
            finding_id=action.finding_id,
            action_number=action.action_number,
            description=action.description,
            responsible_person=action.responsible_person,
            responsible_person_username=action.responsible_user.username,
            target_date=action.target_date.isoformat(),
            actual_completion_date=action.actual_completion_date.isoformat() if action.actual_completion_date else None,
            status=action.status,
            effectiveness_check=action.effectiveness_check,
            effectiveness_verified_by=action.effectiveness_verified_by,
            effectiveness_verified_by_username=action.verifier.username if action.verifier else None,
            effectiveness_verified_date=action.effectiveness_verified_date.isoformat() if action.effectiveness_verified_date else None,
            priority=action.priority,
            resources_required=action.resources_required,
            success_criteria=action.success_criteria,
            created_at=action.created_at.isoformat(),
            updated_at=action.updated_at.isoformat()
        )
    
    def _update_finding_knowledge_base(self, finding_data) -> None:
        """Update knowledge base when audit finding is closed"""
        try:
            from .kb_service_pg import kb_service
            
            # Get project name from audit
            audit = self.db.query(Audit).options(
                joinedload(Audit.project)
            ).filter(Audit.id == finding_data.audit_id).first()
            
            if not audit or not audit.project:
                print("No project found for audit finding KB integration")
                return
            
            project_name = audit.project.name
            collection_name = project_name.replace(' ', '_').lower()
            
            # Create filename for the audit finding
            audit_finding = f"audit_finding_{finding_data.finding_number}_{finding_data.title}"
            filename = f"{audit_finding.replace(' ', '_').lower()}.md"
            
            # Create content with finding details
            content = f"""# Audit Finding: {finding_data.title}

**Finding Number:** {finding_data.finding_number}
**Audit:** {audit.audit_number} - {audit.title}
**Status:** {finding_data.status}
**Severity:** {finding_data.severity}
**Category:** {finding_data.category}

## Description
{finding_data.description}

## Evidence
{finding_data.evidence or 'No evidence provided'}

## Root Cause
{finding_data.root_cause or 'Root cause not identified'}

## Immediate Action
{finding_data.immediate_action or 'No immediate action specified'}

## Compliance Details
- **Standard:** {audit.compliance_standard}
- **Clause Reference:** {finding_data.clause_reference or 'Not specified'}
- **Identified Date:** {finding_data.identified_date}
- **Closed Date:** {finding_data.closed_date or 'Not closed'}
- **Identified By:** {finding_data.identified_by_username}
{f"- **Verified By:** {finding_data.verified_by_username}" if finding_data.verified_by_username else ""}

## Audit Context
- **Department:** {audit.auditee_department}
- **Lead Auditor:** {audit.lead_auditor_username}
- **Audit Type:** {audit.audit_type}
- **Scope:** {audit.scope}
"""
            
            # Prepare metadata for Qdrant payload
            metadata = {
                "finding_id": finding_data.id,
                "finding_number": finding_data.finding_number,
                "audit_id": finding_data.audit_id,
                "audit_number": audit.audit_number,
                "project_name": project_name,
                "audit_finding": audit_finding,
                "severity": finding_data.severity,
                "category": finding_data.category,
                "compliance_standard": audit.compliance_standard,
                "status": finding_data.status,
                "closed_date": finding_data.closed_date
            }
            
            # Add to knowledge base
            result = kb_service.add_text_to_collection(
                collection_name=collection_name,
                text_content=content,
                filename=filename,
                metadata=metadata
            )
            
            if result.get("success"):
                print(f"✅ Audit finding '{audit_finding}' added to knowledge base collection '{collection_name}'")
            else:
                print(f"❌ Failed to add audit finding to KB: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"Error updating knowledge base for audit finding: {e}")