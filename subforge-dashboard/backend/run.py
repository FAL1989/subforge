#!/usr/bin/env python3
"""
Development server runner for SubForge Dashboard Backend
"""

import uvicorn
import argparse
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings


def main():
    """Main entry point for development server"""
    parser = argparse.ArgumentParser(description="SubForge Dashboard Backend Development Server")
    parser.add_argument("--host", default=None, help="Host to bind to")
    parser.add_argument("--port", type=int, default=None, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default=None, help="Log level")
    parser.add_argument("--env", default="development", help="Environment (development/production/testing)")
    
    args = parser.parse_args()
    
    # Set environment
    os.environ["ENVIRONMENT"] = args.env
    
    # Get settings
    settings = get_settings()
    
    # Use command line args or fall back to settings
    host = args.host or settings.HOST
    port = args.port or settings.PORT
    reload = args.reload or settings.RELOAD
    log_level = args.log_level or settings.LOG_LEVEL.lower()
    
    print(f"🚀 Starting SubForge Dashboard Backend")
    print(f"   Environment: {args.env}")
    print(f"   Host: {host}:{port}")
    print(f"   Reload: {reload}")
    print(f"   Log Level: {log_level}")
    print(f"   Debug: {settings.DEBUG}")
    print()
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True,
        app_dir=str(Path(__file__).parent)
    )


if __name__ == "__main__":
    main()