# backend/app/settings_service.py
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from .database_config import get_db
from .db_models import SystemSetting

class SettingsService:
    """Service for managing system settings"""
    
    def get_setting(self, key: str, default_value: Any = None) -> Any:
        """Get a setting value by key"""
        db = next(get_db())
        try:
            setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
            if setting and setting.value is not None:
                # Try to parse as JSON, fall back to string
                try:
                    return json.loads(setting.value)
                except (json.JSONDecodeError, TypeError):
                    return setting.value
            return default_value
        except Exception as e:
            print(f"Error getting setting {key}: {e}")
            return default_value
        finally:
            db.close()
    
    def set_setting(self, key: str, value: Any, category: str = "general", 
                   description: str = "", updated_by: Optional[int] = None) -> bool:
        """Set a setting value"""
        db = next(get_db())
        try:
            # Convert value to JSON string if it's not a simple string
            if isinstance(value, (dict, list, bool, int, float)):
                value_str = json.dumps(value)
            else:
                value_str = str(value) if value is not None else None
            
            # Check if setting exists
            setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
            
            if setting:
                # Update existing setting
                setting.value = value_str
                setting.category = category
                setting.description = description
                setting.updated_by = updated_by
            else:
                # Create new setting
                setting = SystemSetting(
                    key=key,
                    value=value_str,
                    category=category,
                    description=description,
                    updated_by=updated_by
                )
                db.add(setting)
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error setting {key}: {e}")
            return False
        finally:
            db.close()
    
    def get_category_settings(self, category: str) -> Dict[str, Any]:
        """Get all settings for a specific category"""
        db = next(get_db())
        try:
            settings = db.query(SystemSetting).filter(SystemSetting.category == category).all()
            result = {}
            for setting in settings:
                try:
                    result[setting.key] = json.loads(setting.value) if setting.value else None
                except (json.JSONDecodeError, TypeError):
                    result[setting.key] = setting.value
            return result
        except Exception as e:
            print(f"Error getting category settings {category}: {e}")
            return {}
        finally:
            db.close()
    
    def get_smtp_settings(self) -> Dict[str, Any]:
        """Get SMTP settings with defaults"""
        smtp_settings = self.get_category_settings("smtp")
        
        # Provide defaults
        defaults = {
            "server_name": "",
            "port": 25,
            "username": "",
            "password": "",
            "auth_method": "normal_password",
            "connection_security": "STARTTLS",
            "enabled": False
        }
        
        # Merge with database values
        for key, default_value in defaults.items():
            if f"smtp_{key}" not in smtp_settings:
                smtp_settings[f"smtp_{key}"] = default_value
        
        # Convert to expected format (remove smtp_ prefix)
        result = {}
        for key, value in smtp_settings.items():
            if key.startswith("smtp_"):
                result[key[5:]] = value  # Remove 'smtp_' prefix
        
        return result
    
    def update_smtp_settings(self, settings: Dict[str, Any], updated_by: Optional[int] = None) -> bool:
        """Update SMTP settings"""
        try:
            for key, value in settings.items():
                success = self.set_setting(
                    key=f"smtp_{key}",
                    value=value,
                    category="smtp",
                    description=f"SMTP {key} setting",
                    updated_by=updated_by
                )
                if not success:
                    return False
            return True
        except Exception as e:
            print(f"Error updating SMTP settings: {e}")
            return False

# Global settings service instance
settings_service = SettingsService()