# backend/app/records_service.py
"""
Records Service

This service provides comprehensive record management capabilities for
Supplier Management, Parts & Inventory, Lab Equipment Calibration,
Customer Complaints, and Non-Conformances per ISO 13485 and FDA requirements.
"""

import uuid
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from .database_config import get_db
from .db_models import (
    Supplier, PartsInventory, LabEquipmentCalibration, 
    CustomerComplaint, NonConformance, User
)
from .activity_log_service import activity_log_service


class RecordsService:
    """Service for managing all records modules"""
    
    # ========== Supplier Management ==========
    
    def create_supplier(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplier record"""
        db = next(get_db())
        try:
            # Check for existing supplier name
            existing = db.query(Supplier).filter(
                Supplier.supplier_name == data.get('supplier_name')
            ).first()
            
            if existing:
                return {"success": False, "error": "Supplier name already exists"}
            
            supplier = Supplier(
                supplier_name=data.get('supplier_name'),
                address=data.get('address'),
                contact_person=data.get('contact_person'),
                contact_email=data.get('contact_email'),
                contact_phone=data.get('contact_phone'),
                approval_status=data.get('approval_status'),
                risk_level=data.get('risk_level'),
                certification_status=data.get('certification_status'),
                last_audit_date=self._parse_date(data.get('last_audit_date')),
                next_audit_date=self._parse_date(data.get('next_audit_date')),
                performance_rating=data.get('performance_rating'),
                on_time_delivery_rate=data.get('on_time_delivery_rate'),
                quality_rating=data.get('quality_rating'),
                contract_details=data.get('contract_details')
            )
            
            db.add(supplier)
            db.commit()
            
            # Log activity
            activity_log_service.log_activity(
                user_id=user_id,
                action=activity_log_service.ACTIONS['CREATE'],
                resource_type='supplier',
                resource_id=str(supplier.supplier_id),
                resource_name=supplier.supplier_name,
                description=f"Created supplier: {supplier.supplier_name}",
                db=db
            )
            
            return {
                "success": True,
                "supplier_id": supplier.supplier_id,
                "message": "Supplier created successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error creating supplier: {e}")
            return {"success": False, "error": f"Failed to create supplier: {str(e)}"}
        finally:
            db.close()
    
    def get_suppliers(self, user_id: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all suppliers with optional filtering"""
        db = next(get_db())
        try:
            query = db.query(Supplier)
            
            if filters:
                if filters.get('approval_status'):
                    query = query.filter(Supplier.approval_status == filters['approval_status'])
                if filters.get('risk_level'):
                    query = query.filter(Supplier.risk_level == filters['risk_level'])
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        or_(
                            Supplier.supplier_name.ilike(search_term),
                            Supplier.contact_person.ilike(search_term)
                        )
                    )
            
            suppliers = query.order_by(desc(Supplier.created_at)).all()
            return [self._supplier_to_dict(supplier) for supplier in suppliers]
            
        except Exception as e:
            print(f"Error getting suppliers: {e}")
            return []
        finally:
            db.close()
    
    def update_supplier(self, user_id: int, supplier_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update supplier record"""
        db = next(get_db())
        try:
            supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
            
            if not supplier:
                return {"success": False, "error": "Supplier not found"}
            
            # Update fields
            for field, value in data.items():
                if field in ['last_audit_date', 'next_audit_date']:
                    value = self._parse_date(value)
                if hasattr(supplier, field):
                    setattr(supplier, field, value)
            
            db.commit()
            
            # Log activity
            activity_log_service.log_activity(
                user_id=user_id,
                action=activity_log_service.ACTIONS['UPDATE'],
                resource_type='supplier',
                resource_id=str(supplier.supplier_id),
                resource_name=supplier.supplier_name,
                description=f"Updated supplier: {supplier.supplier_name}",
                db=db
            )
            
            return {"success": True, "message": "Supplier updated successfully"}
            
        except Exception as e:
            db.rollback()
            print(f"Error updating supplier: {e}")
            return {"success": False, "error": f"Failed to update supplier: {str(e)}"}
        finally:
            db.close()
    
    # ========== Parts & Inventory Management ==========
    
    def create_parts_inventory(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new parts inventory record"""
        db = next(get_db())
        try:
            # Check for existing part number
            existing = db.query(PartsInventory).filter(
                PartsInventory.part_number == data.get('part_number')
            ).first()
            
            if existing:
                return {"success": False, "error": "Part number already exists"}
            
            part = PartsInventory(
                part_number=data.get('part_number'),
                description=data.get('description'),
                udi=data.get('udi'),
                lot_number=data.get('lot_number'),
                serial_number=data.get('serial_number'),
                supplier_id=data.get('supplier_id'),
                quantity_in_stock=data.get('quantity_in_stock'),
                minimum_stock_level=data.get('minimum_stock_level'),
                location=data.get('location'),
                expiration_date=self._parse_date(data.get('expiration_date')),
                status=data.get('status'),
                received_date=self._parse_date(data.get('received_date')),
                cost=data.get('cost')
            )
            
            db.add(part)
            db.commit()
            
            # Log activity
            activity_log_service.log_activity(
                user_id=user_id,
                action=activity_log_service.ACTIONS['CREATE'],
                resource_type='parts_inventory',
                resource_id=str(part.part_id),
                resource_name=part.part_number,
                description=f"Created parts inventory: {part.part_number}",
                db=db
            )
            
            return {
                "success": True,
                "part_id": part.part_id,
                "message": "Parts inventory created successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error creating parts inventory: {e}")
            return {"success": False, "error": f"Failed to create parts inventory: {str(e)}"}
        finally:
            db.close()
    
    def get_parts_inventory(self, user_id: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all parts inventory with optional filtering"""
        db = next(get_db())
        try:
            query = db.query(PartsInventory)
            
            if filters:
                if filters.get('status'):
                    query = query.filter(PartsInventory.status == filters['status'])
                if filters.get('supplier_id'):
                    query = query.filter(PartsInventory.supplier_id == filters['supplier_id'])
                if filters.get('low_stock'):
                    query = query.filter(PartsInventory.quantity_in_stock <= PartsInventory.minimum_stock_level)
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        or_(
                            PartsInventory.part_number.ilike(search_term),
                            PartsInventory.description.ilike(search_term)
                        )
                    )
            
            parts = query.order_by(desc(PartsInventory.created_at)).all()
            return [self._parts_to_dict(part) for part in parts]
            
        except Exception as e:
            print(f"Error getting parts inventory: {e}")
            return []
        finally:
            db.close()
    
    # ========== Lab Equipment Calibration ==========
    
    def create_lab_equipment(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lab equipment calibration record"""
        db = next(get_db())
        try:
            equipment = LabEquipmentCalibration(
                equipment_name=data.get('equipment_name'),
                serial_number=data.get('serial_number'),
                location=data.get('location'),
                calibration_frequency=data.get('calibration_frequency'),
                last_calibration_date=self._parse_date(data.get('last_calibration_date')),
                next_calibration_date=self._parse_date(data.get('next_calibration_date')),
                calibration_status=data.get('calibration_status'),
                technician=data.get('technician'),
                standards_used=data.get('standards_used'),
                results=data.get('results'),
                adjustment_made=data.get('adjustment_made', False),
                compliance_notes=data.get('compliance_notes')
            )
            
            db.add(equipment)
            db.commit()
            
            # Log activity
            activity_log_service.log_activity(
                user_id=user_id,
                action=activity_log_service.ACTIONS['CREATE'],
                resource_type='lab_equipment',
                resource_id=str(equipment.equipment_id),
                resource_name=equipment.equipment_name,
                description=f"Created lab equipment: {equipment.equipment_name}",
                db=db
            )
            
            return {
                "success": True,
                "equipment_id": equipment.equipment_id,
                "message": "Lab equipment record created successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error creating lab equipment: {e}")
            return {"success": False, "error": f"Failed to create lab equipment: {str(e)}"}
        finally:
            db.close()
    
    def get_lab_equipment(self, user_id: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all lab equipment with optional filtering"""
        db = next(get_db())
        try:
            query = db.query(LabEquipmentCalibration)
            
            if filters:
                if filters.get('calibration_status'):
                    query = query.filter(LabEquipmentCalibration.calibration_status == filters['calibration_status'])
                if filters.get('due_soon'):
                    # Equipment due for calibration in next 30 days
                    from datetime import timedelta
                    due_date = datetime.now().date() + timedelta(days=30)
                    query = query.filter(LabEquipmentCalibration.next_calibration_date <= due_date)
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        or_(
                            LabEquipmentCalibration.equipment_name.ilike(search_term),
                            LabEquipmentCalibration.serial_number.ilike(search_term)
                        )
                    )
            
            equipment = query.order_by(desc(LabEquipmentCalibration.created_at)).all()
            return [self._lab_equipment_to_dict(eq) for eq in equipment]
            
        except Exception as e:
            print(f"Error getting lab equipment: {e}")
            return []
        finally:
            db.close()
    
    # ========== Customer Complaints ==========
    
    def create_customer_complaint(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer complaint record"""
        db = next(get_db())
        try:
            complaint = CustomerComplaint(
                received_date=self._parse_date(data.get('received_date')),
                complainant_name=data.get('complainant_name'),
                complainant_contact=data.get('complainant_contact'),
                product_id=data.get('product_id'),
                lot_number=data.get('lot_number'),
                serial_number=data.get('serial_number'),
                complaint_description=data.get('complaint_description'),
                investigation_details=data.get('investigation_details'),
                root_cause=data.get('root_cause'),
                corrective_action=data.get('corrective_action'),
                response_date=self._parse_date(data.get('response_date')),
                mdr_reportable=data.get('mdr_reportable', False),
                status=data.get('status', 'Open')
            )
            
            db.add(complaint)
            db.commit()
            
            # Log activity
            activity_log_service.log_activity(
                user_id=user_id,
                action=activity_log_service.ACTIONS['CREATE'],
                resource_type='customer_complaint',
                resource_id=str(complaint.complaint_id),
                resource_name=f"Complaint #{complaint.complaint_id}",
                description=f"Created customer complaint from {complaint.complainant_name}",
                db=db
            )
            
            return {
                "success": True,
                "complaint_id": complaint.complaint_id,
                "message": "Customer complaint created successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error creating customer complaint: {e}")
            return {"success": False, "error": f"Failed to create customer complaint: {str(e)}"}
        finally:
            db.close()
    
    def get_customer_complaints(self, user_id: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all customer complaints with optional filtering"""
        db = next(get_db())
        try:
            query = db.query(CustomerComplaint)
            
            if filters:
                if filters.get('status'):
                    query = query.filter(CustomerComplaint.status == filters['status'])
                if filters.get('mdr_reportable'):
                    query = query.filter(CustomerComplaint.mdr_reportable == True)
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        or_(
                            CustomerComplaint.complainant_name.ilike(search_term),
                            CustomerComplaint.product_id.ilike(search_term),
                            CustomerComplaint.complaint_description.ilike(search_term)
                        )
                    )
            
            complaints = query.order_by(desc(CustomerComplaint.created_at)).all()
            return [self._complaint_to_dict(complaint) for complaint in complaints]
            
        except Exception as e:
            print(f"Error getting customer complaints: {e}")
            return []
        finally:
            db.close()
    
    # ========== Non-Conformances ==========
    
    def create_non_conformance(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new non-conformance record"""
        db = next(get_db())
        try:
            nc = NonConformance(
                detection_date=self._parse_date(data.get('detection_date')),
                description=data.get('description'),
                product_process_involved=data.get('product_process_involved'),
                severity=data.get('severity'),
                risk_level=data.get('risk_level'),
                root_cause=data.get('root_cause'),
                corrective_action=data.get('corrective_action'),
                preventive_action=data.get('preventive_action'),
                responsible_person=data.get('responsible_person'),
                disposition=data.get('disposition'),
                status=data.get('status', 'Open'),
                closure_date=self._parse_date(data.get('closure_date'))
            )
            
            db.add(nc)
            db.commit()
            
            # Log activity
            activity_log_service.log_activity(
                user_id=user_id,
                action=activity_log_service.ACTIONS['CREATE'],
                resource_type='non_conformance',
                resource_id=str(nc.nc_id),
                resource_name=f"NC #{nc.nc_id}",
                description=f"Created non-conformance: {nc.description[:50]}{'...' if len(nc.description) > 50 else ''}",
                db=db
            )
            
            return {
                "success": True,
                "nc_id": nc.nc_id,
                "message": "Non-conformance created successfully"
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error creating non-conformance: {e}")
            return {"success": False, "error": f"Failed to create non-conformance: {str(e)}"}
        finally:
            db.close()
    
    def get_non_conformances(self, user_id: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get all non-conformances with optional filtering"""
        db = next(get_db())
        try:
            query = db.query(NonConformance)
            
            if filters:
                if filters.get('status'):
                    query = query.filter(NonConformance.status == filters['status'])
                if filters.get('severity'):
                    query = query.filter(NonConformance.severity == filters['severity'])
                if filters.get('risk_level'):
                    query = query.filter(NonConformance.risk_level == filters['risk_level'])
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        or_(
                            NonConformance.description.ilike(search_term),
                            NonConformance.product_process_involved.ilike(search_term)
                        )
                    )
            
            ncs = query.order_by(desc(NonConformance.created_at)).all()
            return [self._nc_to_dict(nc) for nc in ncs]
            
        except Exception as e:
            print(f"Error getting non-conformances: {e}")
            return []
        finally:
            db.close()
    
    # ========== Helper Methods ==========
    
    def _parse_date(self, date_str: str) -> date:
        """Parse date string to date object"""
        if not date_str:
            return None
        try:
            if isinstance(date_str, str):
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            elif isinstance(date_str, date):
                return date_str
            return None
        except:
            return None
    
    def _supplier_to_dict(self, supplier: Supplier) -> Dict[str, Any]:
        """Convert Supplier model to dictionary"""
        return {
            "supplier_id": supplier.supplier_id,
            "supplier_name": supplier.supplier_name,
            "address": supplier.address,
            "contact_person": supplier.contact_person,
            "contact_email": supplier.contact_email,
            "contact_phone": supplier.contact_phone,
            "approval_status": supplier.approval_status,
            "risk_level": supplier.risk_level,
            "certification_status": supplier.certification_status,
            "last_audit_date": supplier.last_audit_date.isoformat() if supplier.last_audit_date else None,
            "next_audit_date": supplier.next_audit_date.isoformat() if supplier.next_audit_date else None,
            "performance_rating": float(supplier.performance_rating) if supplier.performance_rating else None,
            "on_time_delivery_rate": float(supplier.on_time_delivery_rate) if supplier.on_time_delivery_rate else None,
            "quality_rating": float(supplier.quality_rating) if supplier.quality_rating else None,
            "contract_details": supplier.contract_details,
            "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
            "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None
        }
    
    def _parts_to_dict(self, part: PartsInventory) -> Dict[str, Any]:
        """Convert PartsInventory model to dictionary"""
        return {
            "part_id": part.part_id,
            "part_number": part.part_number,
            "description": part.description,
            "udi": part.udi,
            "lot_number": part.lot_number,
            "serial_number": part.serial_number,
            "supplier_id": part.supplier_id,
            "supplier_name": part.supplier.supplier_name if part.supplier else None,
            "quantity_in_stock": part.quantity_in_stock,
            "minimum_stock_level": part.minimum_stock_level,
            "location": part.location,
            "expiration_date": part.expiration_date.isoformat() if part.expiration_date else None,
            "status": part.status,
            "received_date": part.received_date.isoformat() if part.received_date else None,
            "cost": float(part.cost) if part.cost else None,
            "created_at": part.created_at.isoformat() if part.created_at else None,
            "updated_at": part.updated_at.isoformat() if part.updated_at else None
        }
    
    def _lab_equipment_to_dict(self, equipment: LabEquipmentCalibration) -> Dict[str, Any]:
        """Convert LabEquipmentCalibration model to dictionary"""
        return {
            "equipment_id": equipment.equipment_id,
            "equipment_name": equipment.equipment_name,
            "serial_number": equipment.serial_number,
            "location": equipment.location,
            "calibration_frequency": equipment.calibration_frequency,
            "last_calibration_date": equipment.last_calibration_date.isoformat() if equipment.last_calibration_date else None,
            "next_calibration_date": equipment.next_calibration_date.isoformat() if equipment.next_calibration_date else None,
            "calibration_status": equipment.calibration_status,
            "technician": equipment.technician,
            "standards_used": equipment.standards_used,
            "results": equipment.results,
            "adjustment_made": equipment.adjustment_made,
            "compliance_notes": equipment.compliance_notes,
            "created_at": equipment.created_at.isoformat() if equipment.created_at else None,
            "updated_at": equipment.updated_at.isoformat() if equipment.updated_at else None
        }
    
    def _complaint_to_dict(self, complaint: CustomerComplaint) -> Dict[str, Any]:
        """Convert CustomerComplaint model to dictionary"""
        return {
            "complaint_id": complaint.complaint_id,
            "received_date": complaint.received_date.isoformat() if complaint.received_date else None,
            "complainant_name": complaint.complainant_name,
            "complainant_contact": complaint.complainant_contact,
            "product_id": complaint.product_id,
            "lot_number": complaint.lot_number,
            "serial_number": complaint.serial_number,
            "complaint_description": complaint.complaint_description,
            "investigation_details": complaint.investigation_details,
            "root_cause": complaint.root_cause,
            "corrective_action": complaint.corrective_action,
            "response_date": complaint.response_date.isoformat() if complaint.response_date else None,
            "mdr_reportable": complaint.mdr_reportable,
            "status": complaint.status,
            "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
            "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None
        }
    
    def _nc_to_dict(self, nc: NonConformance) -> Dict[str, Any]:
        """Convert NonConformance model to dictionary"""
        return {
            "nc_id": nc.nc_id,
            "detection_date": nc.detection_date.isoformat() if nc.detection_date else None,
            "description": nc.description,
            "product_process_involved": nc.product_process_involved,
            "severity": nc.severity,
            "risk_level": nc.risk_level,
            "root_cause": nc.root_cause,
            "corrective_action": nc.corrective_action,
            "preventive_action": nc.preventive_action,
            "responsible_person": nc.responsible_person,
            "disposition": nc.disposition,
            "status": nc.status,
            "closure_date": nc.closure_date.isoformat() if nc.closure_date else None,
            "created_at": nc.created_at.isoformat() if nc.created_at else None,
            "updated_at": nc.updated_at.isoformat() if nc.updated_at else None
        }


# Create global service instance
records_service = RecordsService()