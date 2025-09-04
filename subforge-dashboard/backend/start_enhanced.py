#!/usr/bin/env python3
"""
Enhanced SubForge Dashboard Backend Startup Script
"""

import subprocess
import sys
from pathlib import Path
from typing import List

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path is set
from app.core.config import settings


class ServiceManager:
    """Manages the startup and coordination of backend services"""

    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.redis_process = None
        self.celery_worker_process = None
        self.fastapi_process = None

    def check_redis_connection(self) -> bool:
        """Check if Redis is available"""
        try:
            import redis

            client = redis.from_url(settings.REDIS_URL)
            client.ping()
            return True
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False

    def start_redis_server(self) -> bool:
        """Start Redis server if not running"""
        if self.check_redis_connection():
            print("✅ Redis server is already running")
            return True

        try:
            print("🚀 Starting Redis server...")
            self.redis_process = subprocess.Popen(
                ["redis-server", "--port", "6379"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Wait a moment for Redis to start
            import time

            time.sleep(2)

            if self.check_redis_connection():
                print("✅ Redis server started successfully")
                return True
            else:
                print("❌ Redis server failed to start")
                return False

        except FileNotFoundError:
            print("❌ Redis server not found. Please install Redis:")
            print("   Ubuntu/Debian: sudo apt-get install redis-server")
            print("   macOS: brew install redis")
            print("   Windows: https://redis.io/download")
            return False
        except Exception as e:
            print(f"❌ Error starting Redis server: {e}")
            return False

    def start_celery_worker(self) -> bool:
        """Start Celery worker for background tasks"""
        if not settings.ENABLE_BACKGROUND_TASKS:
            print("⏭️  Background tasks disabled, skipping Celery worker")
            return True

        try:
            print("🚀 Starting Celery worker...")
            self.celery_worker_process = subprocess.Popen(
                [
                    "celery",
                    "-A",
                    "app.services.background_tasks.celery_app",
                    "worker",
                    "--loglevel=info",
                    "--pool=solo" if sys.platform == "win32" else "--pool=prefork",
                    "--concurrency=2",
                ]
            )

            print("✅ Celery worker started successfully")
            return True

        except FileNotFoundError:
            print("❌ Celery not found. Install with: pip install celery")
            return False
        except Exception as e:
            print(f"❌ Error starting Celery worker: {e}")
            return False

    def start_fastapi_server(self) -> bool:
        """Start FastAPI server"""
        try:
            print("🚀 Starting FastAPI server...")

            # Ensure uploads directory exists
            upload_dir = project_root / settings.UPLOAD_DIR
            upload_dir.mkdir(exist_ok=True)

            # Start FastAPI with uvicorn
            cmd = [
                "uvicorn",
                "app.main:app",
                "--host",
                settings.HOST,
                "--port",
                str(settings.PORT),
                "--log-level",
                settings.LOG_LEVEL.lower(),
            ]

            if settings.RELOAD:
                cmd.append("--reload")

            self.fastapi_process = subprocess.Popen(cmd)
            print(
                f"✅ FastAPI server started on http://{settings.HOST}:{settings.PORT}"
            )
            return True

        except Exception as e:
            print(f"❌ Error starting FastAPI server: {e}")
            return False

    def start_all_services(self) -> bool:
        """Start all required services"""
        print("🌟 Starting Enhanced SubForge Dashboard Backend")
        print("=" * 50)

        # Check and start Redis
        if not self.start_redis_server():
            return False

        # Start Celery worker
        if not self.start_celery_worker():
            print("⚠️  Continuing without background tasks...")

        # Start FastAPI server
        if not self.start_fastapi_server():
            return False

        print("\n🎉 All services started successfully!")
        print("\nService URLs:")
        print(f"  • API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
        print(f"  • API v1: http://{settings.HOST}:{settings.PORT}/api/v1")
        print(f"  • API v2: http://{settings.HOST}:{settings.PORT}/api/v2")
        print(f"  • WebSocket v1: ws://{settings.HOST}:{settings.PORT}/ws")
        print(f"  • WebSocket v2: ws://{settings.HOST}:{settings.PORT}/ws/v2")
        print("\nPress Ctrl+C to stop all services")

        return True

    def stop_all_services(self):
        """Stop all services"""
        print("\n🛑 Stopping services...")

        for process in [
            self.fastapi_process,
            self.celery_worker_process,
            self.redis_process,
        ]:
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"✅ Service stopped")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"⚡ Service force-killed")
                except Exception as e:
                    print(f"⚠️  Error stopping service: {e}")

        print("👋 All services stopped")

    def wait_for_services(self):
        """Wait for services to run"""
        try:
            if self.fastapi_process:
                self.fastapi_process.wait()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all_services()


def main():
    """Main startup function"""
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)

    # Check if required packages are installed
    try:
        pass
    except ImportError as e:
        print(f"❌ Required package missing: {e}")
        print("Install with: pip install -r requirements.txt")
        sys.exit(1)

    # Create and start service manager
    service_manager = ServiceManager()

    try:
        if service_manager.start_all_services():
            service_manager.wait_for_services()
        else:
            print("❌ Failed to start services")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️  Shutdown requested")
        service_manager.stop_all_services()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        service_manager.stop_all_services()
        sys.exit(1)


if __name__ == "__main__":
    main()