#!/usr/bin/env python3
"""
Verification script for SubForge Dashboard Backend setup
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def check_imports():
    """Check if all required modules can be imported"""
    print("🔍 Checking imports...")
    
    try:
        # Core imports
        import fastapi
        import uvicorn
        import sqlalchemy
        import pydantic
        import alembic
        print("✅ Core dependencies imported successfully")
        
        # Application imports
        from app.main import app
        from app.core.config import settings
        from app.models import Agent, Task, Workflow, SystemMetrics
        from app.schemas import AgentCreate, TaskCreate, WorkflowCreate
        from app.websocket.manager import websocket_manager
        print("✅ Application modules imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def check_configuration():
    """Check configuration"""
    print("\n🔧 Checking configuration...")
    
    try:
        from app.core.config import settings
        
        print(f"   App Name: {settings.APP_NAME}")
        print(f"   Version: {settings.APP_VERSION}")
        print(f"   Debug: {settings.DEBUG}")
        print(f"   Host: {settings.HOST}:{settings.PORT}")
        print(f"   Database URL: {settings.DATABASE_URL}")
        print(f"   File Watcher: {settings.ENABLE_FILE_WATCHER}")
        
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def check_database():
    """Check database setup"""
    print("\n🗄️  Checking database setup...")
    
    try:
        from app.database.session import engine, async_engine
        from app.database.base import Base
        from app.models import Agent, Task, Workflow, SystemMetrics
        
        # Check if models are registered
        tables = list(Base.metadata.tables.keys())
        expected_tables = ['agents', 'tasks', 'workflows', 'system_metrics']
        
        print(f"   Registered tables: {tables}")
        
        for table in expected_tables:
            if table in tables:
                print(f"   ✅ {table} table registered")
            else:
                print(f"   ❌ {table} table missing")
                return False
        
        print("✅ Database models configured correctly")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_api_routes():
    """Check API routes"""
    print("\n🛣️  Checking API routes...")
    
    try:
        from app.main import app
        
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(f"{route.methods} {route.path}")
        
        expected_routes = [
            '/health', '/api/v1/agents', '/api/v1/tasks', 
            '/api/v1/workflows', '/api/v1/system/status', '/ws'
        ]
        
        print(f"   Total routes: {len(routes)}")
        
        for expected in expected_routes:
            found = any(expected in route for route in routes)
            if found:
                print(f"   ✅ {expected} route found")
            else:
                print(f"   ❌ {expected} route missing")
        
        print("✅ API routes configured correctly")
        return True
    except Exception as e:
        print(f"❌ API routes error: {e}")
        return False

def check_file_structure():
    """Check file structure"""
    print("\n📁 Checking file structure...")
    
    required_files = [
        "app/main.py",
        "app/core/config.py",
        "app/models/__init__.py",
        "app/schemas/__init__.py",
        "app/api/v1/__init__.py",
        "app/websocket/manager.py",
        "requirements.txt",
        "alembic.ini",
        "alembic/env.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} missing")
            all_exist = False
    
    if all_exist:
        print("✅ File structure is complete")
    else:
        print("❌ Some required files are missing")
    
    return all_exist

def main():
    """Main verification function"""
    print("🚀 SubForge Dashboard Backend Setup Verification")
    print("=" * 50)
    
    checks = [
        check_imports,
        check_configuration,
        check_database,
        check_api_routes,
        check_file_structure
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All checks passed! ({passed}/{total})")
        print("\n✨ Your SubForge Dashboard Backend is ready!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure")
        print("2. Run: python run.py --reload")
        print("3. Visit: http://localhost:8000/docs")
        return True
    else:
        print(f"⚠️  Some checks failed. ({passed}/{total})")
        print("\n🔧 Please fix the issues above before running the backend.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)