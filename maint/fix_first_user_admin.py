#!/usr/bin/env python3
"""
Script to fix admin status for the first user in the system
"""

import requests
import json
import sys
import os
from datetime import datetime

# Import centralized configuration
try:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(parent_dir)
    from config.environments import config
    BACKEND_URL = config.backend_url
except ImportError:
    # Fallback for when centralized config is not available
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def fix_first_user_admin():
    """Fix admin status for the first user via API"""
    
    print("🔍 Checking first user admin status via API...")
    
    try:
        # Try to get users endpoint (this might not exist, but let's check)
        # We'll need to create an endpoint or use direct database access
        
        print("⚠️  Note: This requires direct database access or admin API endpoint")
        print("🔧 Please run one of these solutions:")
        print()
        print("**Option 1 - If you have Docker access:**")
        print("docker exec -it <postgres_container_name> psql -U docsmait_user -d docsmait")
        print("Then run: UPDATE users SET is_admin=true, is_super_admin=true WHERE id=(SELECT MIN(id) FROM users);")
        print()
        print("**Option 2 - If you have database client:**")
        print("Connect to your PostgreSQL database and run:")
        print("UPDATE users SET is_admin=true, is_super_admin=true WHERE username='sganesh';")
        print()
        print("**Option 3 - Check container name:**")
        print("Run: docker ps | grep postgres")
        print("Then use the container name with Option 1")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_first_user_admin()