# backend/app/ai_config.py
"""
AI Configuration Management for Docsmait

This module handles AI-related configuration including:
- Document type prompts
- AI service settings
- Usage tracking
- Model configurations
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from .config import config

logger = logging.getLogger(__name__)

class AIConfig:
    """AI Configuration Management"""
    
    def __init__(self):
        from .config import config
        self.config_file = Path(f"{config.CONFIG_DIR}/ai_config.json")
        self.ensure_config_directory()
        self.load_config()
    
    def ensure_config_directory(self):
        """Ensure config directory exists"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_config(self):
        """Load AI configuration from file or create defaults"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info("AI configuration loaded successfully")
            except Exception as e:
                logger.error(f"Error loading AI config: {e}")
                self.config = self.get_default_config()
                self.save_config()
        else:
            logger.info("Creating default AI configuration")
            self.config = self.get_default_config()
            self.save_config()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("AI configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving AI config: {e}")
            raise
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default AI configuration"""
        return {
            "ai_settings": {
                "ollama_base_url": config.OLLAMA_BASE_URL,
                "default_model": config.GENERAL_PURPOSE_LLM,
                "embedding_model": config.DEFAULT_EMBEDDING_MODEL,
                "ai_timeout": config.AI_TIMEOUT,
                "max_response_length": config.MAX_RESPONSE_LENGTH,
                "ai_context_window": config.AI_CONTEXT_WINDOW,
                "show_prompt": config.SHOW_PROMPT,
                "available_models": config.AVAILABLE_MODELS
            },
            "document_prompts": {
                "planning_documents": {
                    "project_plans": "You are an expert project manager. Help create or improve this project plan document. Focus on: scope definition, timeline, resources, milestones, and risk considerations. Consider the following requirements: [configurable_item]",
                    "quality_plans": "You are a quality assurance expert. Help create or improve this quality plan document. Focus on: quality objectives, processes, responsibilities, metrics, and improvement strategies. Consider the following requirements: [configurable_item]",
                    "risk_assessments": "You are a risk management specialist. Help create or improve this risk assessment document. Focus on: risk identification, probability analysis, impact assessment, mitigation strategies, and monitoring plans. Consider the following requirements: [configurable_item]"
                },
                "process_documents": {
                    "procedures": "You are a process improvement expert. Help create or improve this procedure document. Focus on: clear step-by-step instructions, roles and responsibilities, prerequisites, and quality checkpoints. Consider the following requirements: [configurable_item]",
                    "work_instructions": "You are a technical documentation specialist. Help create or improve this work instruction document. Focus on: detailed task steps, safety considerations, tools required, and quality standards. Consider the following requirements: [configurable_item]",
                    "process_maps": "You are a business process analyst. Help create or improve this process map document. Focus on: process flow, decision points, handoffs, inputs/outputs, and improvement opportunities. Consider the following requirements: [configurable_item]"
                },
                "specifications": {
                    "requirements": "You are a requirements analyst. Help create or improve this requirements document. Focus on: functional requirements, non-functional requirements, acceptance criteria, and traceability. Consider the following requirements: [configurable_item]",
                    "technical_specifications": "You are a technical architect. Help create or improve this technical specification document. Focus on: system architecture, technical design, interfaces, and implementation details. Consider the following requirements: [configurable_item]",
                    "design_documents": "You are a design specialist. Help create or improve this design document. Focus on: design rationale, specifications, constraints, and implementation guidance. Consider the following requirements: [configurable_item]"
                },
                "records": {
                    "test_reports": "You are a test engineer. Help create or improve this test report document. Focus on: test execution results, defect analysis, coverage metrics, and recommendations. Consider the following requirements: [configurable_item]",
                    "audit_reports": "You are an audit specialist. Help create or improve this audit report document. Focus on: findings, compliance status, recommendations, and corrective actions. Consider the following requirements: [configurable_item]",
                    "meeting_minutes": "You are an administrative assistant. Help create or improve these meeting minutes. Focus on: key decisions, action items, attendees, and follow-up tasks. Consider the following requirements: [configurable_item]"
                },
                "templates": {
                    "forms": "You are a forms designer. Help create or improve this form template. Focus on: clear field labels, logical flow, validation requirements, and user experience. Consider the following requirements: [configurable_item]",
                    "checklists": "You are a quality control expert. Help create or improve this checklist template. Focus on: comprehensive coverage, clear criteria, logical sequence, and usability. Consider the following requirements: [configurable_item]",
                    "report_templates": "You are a reporting specialist. Help create or improve this report template. Focus on: structure, key metrics, visualization, and actionable insights. Consider the following requirements: [configurable_item]"
                },
                "policies": {
                    "quality_policy": "You are a quality management expert. Help create or improve this quality policy document. Focus on: policy objectives, scope, responsibilities, and compliance requirements. Consider the following requirements: [configurable_item]",
                    "environmental_policy": "You are an environmental compliance expert. Help create or improve this environmental policy document. Focus on: environmental objectives, commitments, responsibilities, and regulatory compliance. Consider the following requirements: [configurable_item]",
                    "safety_policy": "You are a safety management expert. Help create or improve this safety policy document. Focus on: safety objectives, hazard management, responsibilities, and incident prevention. Consider the following requirements: [configurable_item]"
                },
                "manuals": {
                    "user_manuals": "You are a technical writer. Help create or improve this user manual. Focus on: clear instructions, troubleshooting guides, feature explanations, and user-friendly language. Consider the following requirements: [configurable_item]",
                    "operation_manuals": "You are an operations specialist. Help create or improve this operation manual. Focus on: operational procedures, safety protocols, maintenance schedules, and performance standards. Consider the following requirements: [configurable_item]",
                    "maintenance_guides": "You are a maintenance expert. Help create or improve this maintenance guide. Focus on: preventive maintenance, troubleshooting procedures, spare parts, and safety considerations. Consider the following requirements: [configurable_item]"
                }
            },
            "usage_tracking": {
                "track_usage": config.TRACK_USAGE,
                "track_feedback": config.TRACK_FEEDBACK,
                "log_prompts": config.LOG_PROMPTS,
                "retention_days": config.USAGE_RETENTION_DAYS
            },
            "version": "1.0",
            "last_updated": datetime.now().isoformat()
        }
    
    def get_document_prompt(self, document_type: str, category: str = None) -> str:
        """Get prompt for specific document type"""
        try:
            if category:
                return self.config["document_prompts"].get(category, {}).get(document_type, "")
            else:
                # Search across all categories
                for cat_prompts in self.config["document_prompts"].values():
                    if document_type in cat_prompts:
                        return cat_prompts[document_type]
                return ""
        except Exception as e:
            logger.error(f"Error getting document prompt: {e}")
            return ""
    
    def update_document_prompt(self, document_type: str, prompt: str, category: str = None) -> bool:
        """Update prompt for specific document type"""
        try:
            if category and category in self.config["document_prompts"]:
                self.config["document_prompts"][category][document_type] = prompt
            else:
                # Search across all categories and update
                for cat_name, cat_prompts in self.config["document_prompts"].items():
                    if document_type in cat_prompts:
                        self.config["document_prompts"][cat_name][document_type] = prompt
                        break
                else:
                    # If not found, add to first category or create new
                    if not category:
                        category = "custom"
                        if category not in self.config["document_prompts"]:
                            self.config["document_prompts"][category] = {}
                    self.config["document_prompts"][category][document_type] = prompt
            
            self.config["last_updated"] = datetime.now().isoformat()
            self.save_config()
            return True
        except Exception as e:
            logger.error(f"Error updating document prompt: {e}")
            return False
    
    def get_ai_settings(self) -> Dict[str, Any]:
        """Get AI service settings"""
        return self.config.get("ai_settings", {})
    
    def update_ai_settings(self, settings: Dict[str, Any]) -> bool:
        """Update AI service settings"""
        try:
            self.config["ai_settings"].update(settings)
            self.config["last_updated"] = datetime.now().isoformat()
            self.save_config()
            return True
        except Exception as e:
            logger.error(f"Error updating AI settings: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available AI models"""
        return self.config["ai_settings"].get("available_models", config.AVAILABLE_MODELS)
    
    def get_usage_tracking_settings(self) -> Dict[str, Any]:
        """Get usage tracking settings"""
        return self.config.get("usage_tracking", {})
    
    def log_ai_usage(self, user_id: int, document_type: str, prompt_used: str, 
                     response_length: int, processing_time: float, feedback: Optional[int] = None):
        """Log AI usage for tracking and analytics"""
        if not self.config["usage_tracking"].get("track_usage", False):
            return
        
        usage_data = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "document_type": document_type,
            "prompt_used": prompt_used if self.config["usage_tracking"].get("log_prompts", False) else "logged",
            "response_length": response_length,
            "processing_time": processing_time,
            "feedback": feedback
        }
        
        # In production, this would go to a proper logging system or database
        logger.info(f"AI Usage: {json.dumps(usage_data)}")

# Create global AI config instance
ai_config = AIConfig()