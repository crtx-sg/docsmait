# backend/app/user_service.py
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from .database_config import get_db
from .db_models import User
from .auth import get_password_hash, verify_password

class UserService:
    """Service for user management using PostgreSQL/SQLAlchemy"""
    
    def create_user(self, username: str, email: str, password: str, is_admin: bool = False) -> Optional[User]:
        """Create a new user"""
        db = next(get_db())
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()
            
            if existing_user:
                return None
            
            # Check if this is the first user (becomes super admin)
            user_count = db.query(User).count()
            is_super_admin = (user_count == 0)
            
            # Create new user
            user = User(
                username=username,
                email=email,
                password_hash=get_password_hash(password),
                is_admin=is_admin or is_super_admin,  # Super admin is also admin
                is_super_admin=is_super_admin
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return user
            
        except Exception as e:
            db.rollback()
            print(f"Error creating user: {e}")
            return None
        finally:
            db.close()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        db = next(get_db())
        try:
            user = db.query(User).filter(User.email == email).first()
            return user
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
        finally:
            db.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
        finally:
            db.close()
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users for member selection (returns basic info only)"""
        db = next(get_db())
        try:
            users = db.query(User).all()
            user_list = []
            for user in users:
                user_list.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_admin": user.is_admin,
                    "is_super_admin": user.is_super_admin,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                })
            return user_list
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
        finally:
            db.close()
    
    def create_admin_user(self, username: str, email: str, password: str, created_by_user_id: int) -> Optional[User]:
        """Create a new admin user (only allowed by super admin)"""
        db = next(get_db())
        try:
            # Verify creator is super admin
            creator = db.query(User).filter(User.id == created_by_user_id).first()
            if not creator or not creator.is_super_admin:
                return None
            
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()
            
            if existing_user:
                return None
            
            # Create admin user
            user = User(
                username=username,
                email=email,
                password_hash=get_password_hash(password),
                is_admin=True,
                is_super_admin=False
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return user
            
        except Exception as e:
            db.rollback()
            print(f"Error creating admin user: {e}")
            return None
        finally:
            db.close()
    
    def is_super_admin(self, user_id: int) -> bool:
        """Check if user is super admin"""
        user = self.get_user_by_id(user_id)
        return user.is_super_admin if user else False
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin (includes super admin)"""
        user = self.get_user_by_id(user_id)
        return user.is_admin if user else False
    
    def update_user_admin_status(self, user_id: int, is_admin: bool, updated_by_user_id: int) -> bool:
        """Update user admin status (only allowed by super admin)"""
        db = next(get_db())
        try:
            # Verify updater is super admin
            updater = db.query(User).filter(User.id == updated_by_user_id).first()
            if not updater or not updater.is_super_admin:
                return False
            
            # Get target user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Cannot change super admin status
            if user.is_super_admin:
                return False
            
            user.is_admin = is_admin
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Error updating user admin status: {e}")
            return False
        finally:
            db.close()

# Create global instance
user_service = UserService()