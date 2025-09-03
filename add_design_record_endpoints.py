#!/usr/bin/env python3
"""
Script to add all Design Record API endpoints to main.py
"""

# FMEA Analysis endpoints
fmea_endpoints = '''
# ================================
# DESIGN RECORD - FMEA ANALYSIS
# ================================

@app.get("/design-record/fmea")
def get_fmea_analyses(
    project_id: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Get FMEA analyses for a project"""
    from .db_models import FMEAAnalysis, ProjectMember, User
    
    try:
        query = db.query(FMEAAnalysis).options(
            joinedload(FMEAAnalysis.creator),
            joinedload(FMEAAnalysis.project)
        )
        
        if project_id:
            # Check if user has access to this project
            is_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            ).first()
            
            user = db.query(User).filter(User.id == user_id).first()
            if not is_member and not (user and (user.is_admin or user.is_super_admin)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to project FMEA analyses"
                )
            
            query = query.filter(FMEAAnalysis.project_id == project_id)
        
        fmeas = query.order_by(FMEAAnalysis.fmea_id).all()
        
        result = []
        for fmea in fmeas:
            result.append({
                "id": fmea.id,
                "fmea_id": fmea.fmea_id,
                "fmea_type": fmea.fmea_type,
                "analysis_level": fmea.analysis_level,
                "hierarchy_level": fmea.hierarchy_level,
                "element_id": fmea.element_id,
                "element_function": fmea.element_function,
                "performance_standards": fmea.performance_standards,
                "fmea_team": fmea.fmea_team,
                "analysis_date": str(fmea.analysis_date) if fmea.analysis_date else None,
                "review_status": fmea.review_status,
                "failure_modes": fmea.failure_modes,
                "project_id": fmea.project_id,
                "created_by": fmea.creator.username if fmea.creator else "Unknown",
                "created_at": fmea.created_at.isoformat() if fmea.created_at else None,
                "updated_at": fmea.updated_at.isoformat() if fmea.updated_at else None
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch FMEA analyses: {str(e)}"
        )

@app.post("/design-record/fmea")
def create_fmea_analysis(
    fmea_data: dict,
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Create a new FMEA analysis"""
    from .db_models import FMEAAnalysis, ProjectMember, User
    import uuid
    from datetime import datetime
    
    try:
        project_id = fmea_data.get("project_id")
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id is required")
        
        # Check if user has access to this project
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not is_member and not (user and (user.is_admin or user.is_super_admin)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to create FMEA analyses in this project"
            )
        
        # Check if FMEA ID already exists in this project
        existing_fmea = db.query(FMEAAnalysis).filter(
            FMEAAnalysis.project_id == project_id,
            FMEAAnalysis.fmea_id == fmea_data.get("fmea_id")
        ).first()
        
        if existing_fmea:
            raise HTTPException(
                status_code=400, 
                detail=f"FMEA ID '{fmea_data.get('fmea_id')}' already exists in this project"
            )
        
        # Parse analysis date
        analysis_date = None
        if fmea_data.get("analysis_date"):
            analysis_date = datetime.strptime(fmea_data.get("analysis_date"), "%Y-%m-%d").date()
        
        # Create new FMEA analysis
        fmea_id = str(uuid.uuid4())
        fmea = FMEAAnalysis(
            id=fmea_id,
            project_id=project_id,
            fmea_id=fmea_data.get("fmea_id"),
            fmea_type=fmea_data.get("fmea_type"),
            analysis_level=fmea_data.get("analysis_level"),
            hierarchy_level=fmea_data.get("hierarchy_level"),
            element_id=fmea_data.get("element_id"),
            element_function=fmea_data.get("element_function"),
            performance_standards=fmea_data.get("performance_standards"),
            fmea_team=fmea_data.get("fmea_team", []),
            analysis_date=analysis_date,
            review_status=fmea_data.get("review_status", "draft"),
            failure_modes=fmea_data.get("failure_modes", []),
            created_by=user_id
        )
        
        db.add(fmea)
        db.commit()
        db.refresh(fmea)
        
        return {
            "success": True,
            "fmea_id": fmea_id,
            "message": f"FMEA {fmea.fmea_id} created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create FMEA analysis: {str(e)}"
        )
'''

# Design Artifacts endpoints
design_endpoints = '''
# ================================
# DESIGN RECORD - DESIGN ARTIFACTS
# ================================

@app.get("/design-record/design")
def get_design_artifacts(
    project_id: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Get design artifacts for a project"""
    from .db_models import DesignArtifact, ProjectMember, User
    
    try:
        query = db.query(DesignArtifact).options(
            joinedload(DesignArtifact.creator),
            joinedload(DesignArtifact.project)
        )
        
        if project_id:
            # Check if user has access to this project
            is_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            ).first()
            
            user = db.query(User).filter(User.id == user_id).first()
            if not is_member and not (user and (user.is_admin or user.is_super_admin)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to project design artifacts"
                )
            
            query = query.filter(DesignArtifact.project_id == project_id)
        
        designs = query.order_by(DesignArtifact.design_id).all()
        
        result = []
        for design in designs:
            result.append({
                "id": design.id,
                "design_id": design.design_id,
                "design_title": design.design_title,
                "design_type": design.design_type,
                "design_description": design.design_description,
                "implementation_approach": design.implementation_approach,
                "architecture_diagrams": design.architecture_diagrams,
                "interface_definitions": design.interface_definitions,
                "design_patterns": design.design_patterns,
                "technology_stack": design.technology_stack,
                "project_id": design.project_id,
                "created_by": design.creator.username if design.creator else "Unknown",
                "created_at": design.created_at.isoformat() if design.created_at else None,
                "updated_at": design.updated_at.isoformat() if design.updated_at else None
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch design artifacts: {str(e)}"
        )

@app.post("/design-record/design")
def create_design_artifact(
    design_data: dict,
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Create a new design artifact"""
    from .db_models import DesignArtifact, ProjectMember, User
    import uuid
    
    try:
        project_id = design_data.get("project_id")
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id is required")
        
        # Check if user has access to this project
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not is_member and not (user and (user.is_admin or user.is_super_admin)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to create design artifacts in this project"
            )
        
        # Check if design ID already exists in this project
        existing_design = db.query(DesignArtifact).filter(
            DesignArtifact.project_id == project_id,
            DesignArtifact.design_id == design_data.get("design_id")
        ).first()
        
        if existing_design:
            raise HTTPException(
                status_code=400, 
                detail=f"Design ID '{design_data.get('design_id')}' already exists in this project"
            )
        
        # Create new design artifact
        design_id = str(uuid.uuid4())
        design = DesignArtifact(
            id=design_id,
            project_id=project_id,
            design_id=design_data.get("design_id"),
            design_title=design_data.get("design_title"),
            design_type=design_data.get("design_type"),
            design_description=design_data.get("design_description"),
            implementation_approach=design_data.get("implementation_approach"),
            architecture_diagrams=design_data.get("architecture_diagrams", []),
            interface_definitions=design_data.get("interface_definitions", []),
            design_patterns=design_data.get("design_patterns", []),
            technology_stack=design_data.get("technology_stack", []),
            created_by=user_id
        )
        
        db.add(design)
        db.commit()
        db.refresh(design)
        
        return {
            "success": True,
            "design_id": design_id,
            "message": f"Design {design.design_id} created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create design artifact: {str(e)}"
        )
'''

# Test Artifacts endpoints
test_endpoints = '''
# ================================
# DESIGN RECORD - TEST ARTIFACTS
# ================================

@app.get("/design-record/tests")
def get_test_artifacts(
    project_id: Optional[str] = Query(None),
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Get test artifacts for a project"""
    from .db_models import TestArtifact, ProjectMember, User
    
    try:
        query = db.query(TestArtifact).options(
            joinedload(TestArtifact.creator),
            joinedload(TestArtifact.project)
        )
        
        if project_id:
            # Check if user has access to this project
            is_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            ).first()
            
            user = db.query(User).filter(User.id == user_id).first()
            if not is_member and not (user and (user.is_admin or user.is_super_admin)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to project test artifacts"
                )
            
            query = query.filter(TestArtifact.project_id == project_id)
        
        tests = query.order_by(TestArtifact.test_id).all()
        
        result = []
        for test in tests:
            result.append({
                "id": test.id,
                "test_id": test.test_id,
                "test_title": test.test_title,
                "test_type": test.test_type,
                "test_objective": test.test_objective,
                "acceptance_criteria": test.acceptance_criteria,
                "test_environment": test.test_environment,
                "test_execution": test.test_execution,
                "coverage_metrics": test.coverage_metrics,
                "project_id": test.project_id,
                "created_by": test.creator.username if test.creator else "Unknown",
                "created_at": test.created_at.isoformat() if test.created_at else None,
                "updated_at": test.updated_at.isoformat() if test.updated_at else None
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch test artifacts: {str(e)}"
        )

@app.post("/design-record/tests")
def create_test_artifact(
    test_data: dict,
    user_id: int = Depends(auth.verify_token),
    db: Session = Depends(get_db)
):
    """Create a new test artifact"""
    from .db_models import TestArtifact, ProjectMember, User
    import uuid
    
    try:
        project_id = test_data.get("project_id")
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id is required")
        
        # Check if user has access to this project
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not is_member and not (user and (user.is_admin or user.is_super_admin)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to create test artifacts in this project"
            )
        
        # Check if test ID already exists in this project
        existing_test = db.query(TestArtifact).filter(
            TestArtifact.project_id == project_id,
            TestArtifact.test_id == test_data.get("test_id")
        ).first()
        
        if existing_test:
            raise HTTPException(
                status_code=400, 
                detail=f"Test ID '{test_data.get('test_id')}' already exists in this project"
            )
        
        # Create new test artifact
        test_id = str(uuid.uuid4())
        test = TestArtifact(
            id=test_id,
            project_id=project_id,
            test_id=test_data.get("test_id"),
            test_title=test_data.get("test_title"),
            test_type=test_data.get("test_type"),
            test_objective=test_data.get("test_objective"),
            acceptance_criteria=test_data.get("acceptance_criteria"),
            test_environment=test_data.get("test_environment"),
            test_execution=test_data.get("test_execution"),
            coverage_metrics=test_data.get("coverage_metrics"),
            created_by=user_id
        )
        
        db.add(test)
        db.commit()
        db.refresh(test)
        
        return {
            "success": True,
            "test_id": test_id,
            "message": f"Test {test.test_id} created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test artifact: {str(e)}"
        )
'''

print("Endpoint templates created. Use these to add to main.py manually or via append operations.")