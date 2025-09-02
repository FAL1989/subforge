#!/usr/bin/env python3
"""
Simple backend startup script for testing Socket.IO connection
"""

import uvicorn
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Run without the problematic imports
    uvicorn.run(
        "app.main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )