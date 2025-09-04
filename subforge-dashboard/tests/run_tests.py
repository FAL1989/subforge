#!/usr/bin/env python3
"""
Test runner script for SubForge Dashboard
Orchestrates backend, frontend, and integration tests
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


class TestRunner:
    """Main test runner for SubForge Dashboard"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_dir = project_root / "backend"
        self.frontend_dir = project_root / "frontend"
        self.tests_dir = project_root / "tests"

        # Track running processes for cleanup
        self.processes: List[subprocess.Popen] = []

        # Test results
        self.results: Dict[str, Any] = {
            "backend": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "frontend": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "integration": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
            "e2e": {"passed": 0, "failed": 0, "skipped": 0, "errors": []},
        }

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            print("\n🛑 Received interrupt signal, cleaning up...")
            self.cleanup()
            sys.exit(1)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def cleanup(self):
        """Clean up running processes"""
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                print(f"Error cleaning up process: {e}")

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")

        # Check Python dependencies
        try:
            subprocess.run(
                [sys.executable, "-c", "import pytest, fastapi, sqlalchemy"],
                check=True,
                capture_output=True,
            )
            print("✅ Python dependencies OK")
        except subprocess.CalledProcessError:
            print(
                "❌ Missing Python dependencies. Run: pip install -r backend/requirements.txt"
            )
            return False

        # Check Node.js dependencies
        try:
            result = subprocess.run(
                ["npm", "--version"], capture_output=True, text=True, check=True
            )
            print(f"✅ npm {result.stdout.strip()} OK")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ npm not found. Please install Node.js")
            return False

        # Check if frontend dependencies are installed
        if not (self.frontend_dir / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            try:
                subprocess.run(["npm", "install"], cwd=self.frontend_dir, check=True)
                print("✅ Frontend dependencies installed")
            except subprocess.CalledProcessError:
                print("❌ Failed to install frontend dependencies")
                return False

        return True

    def run_backend_tests(self, args: argparse.Namespace) -> bool:
        """Run backend tests with pytest"""
        print("\n🐍 Running backend tests...")

        os.chdir(self.tests_dir)

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "backend/",
            "-v",
            "--tb=short",
            f"--maxfail={args.maxfail}",
            "--color=yes",
        ]

        if args.coverage:
            cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html"])

        if args.markers:
            cmd.extend(["-m", args.markers])

        if args.keyword:
            cmd.extend(["-k", args.keyword])

        if args.parallel:
            cmd.extend(["-n", str(args.parallel)])

        if args.verbose:
            cmd.append("-vv")

        try:
            result = subprocess.run(cmd, check=False)
            success = result.returncode == 0

            if success:
                print("✅ Backend tests passed")
            else:
                print("❌ Backend tests failed")
                self.results["backend"]["errors"].append("Backend tests failed")

            return success

        except Exception as e:
            print(f"❌ Error running backend tests: {e}")
            self.results["backend"]["errors"].append(str(e))
            return False

    def run_frontend_tests(self, args: argparse.Namespace) -> bool:
        """Run frontend tests with Jest"""
        print("\n⚛️  Running frontend tests...")

        os.chdir(self.frontend_dir)

        cmd = ["npm", "test", "--"]

        if args.coverage:
            cmd.append("--coverage")

        if args.watch:
            cmd.append("--watch")

        if args.verbose:
            cmd.append("--verbose")

        # Set environment for testing
        env = os.environ.copy()
        env["CI"] = "true"
        env["NODE_ENV"] = "test"

        try:
            result = subprocess.run(cmd, check=False, env=env)
            success = result.returncode == 0

            if success:
                print("✅ Frontend tests passed")
            else:
                print("❌ Frontend tests failed")
                self.results["frontend"]["errors"].append("Frontend tests failed")

            return success

        except Exception as e:
            print(f"❌ Error running frontend tests: {e}")
            self.results["frontend"]["errors"].append(str(e))
            return False

    def start_test_servers(self) -> bool:
        """Start backend and frontend servers for integration/E2E tests"""
        print("🚀 Starting test servers...")

        # Start backend server
        backend_cmd = [
            sys.executable,
            "run.py",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--reload",
            "false",
        ]

        try:
            backend_env = os.environ.copy()
            backend_env["TESTING"] = "true"
            backend_env["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

            backend_process = subprocess.Popen(
                backend_cmd,
                cwd=self.backend_dir,
                env=backend_env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            self.processes.append(backend_process)
            print("✅ Backend server started")

        except Exception as e:
            print(f"❌ Failed to start backend server: {e}")
            return False

        # Start frontend server
        frontend_cmd = ["npm", "run", "dev"]

        try:
            frontend_env = os.environ.copy()
            frontend_env["NODE_ENV"] = "test"
            frontend_env["NEXT_PUBLIC_API_URL"] = "http://localhost:8000"

            frontend_process = subprocess.Popen(
                frontend_cmd,
                cwd=self.frontend_dir,
                env=frontend_env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            self.processes.append(frontend_process)
            print("✅ Frontend server started")

        except Exception as e:
            print(f"❌ Failed to start frontend server: {e}")
            return False

        # Wait for servers to be ready
        print("⏳ Waiting for servers to be ready...")
        time.sleep(10)

        return True

    def run_integration_tests(self, args: argparse.Namespace) -> bool:
        """Run integration tests"""
        print("\n🔗 Running integration tests...")

        os.chdir(self.tests_dir)

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "integration/",
            "-v",
            "--tb=short",
            f"--maxfail={args.maxfail}",
            "--color=yes",
        ]

        if args.markers:
            cmd.extend(["-m", args.markers])

        try:
            result = subprocess.run(cmd, check=False)
            success = result.returncode == 0

            if success:
                print("✅ Integration tests passed")
            else:
                print("❌ Integration tests failed")
                self.results["integration"]["errors"].append("Integration tests failed")

            return success

        except Exception as e:
            print(f"❌ Error running integration tests: {e}")
            self.results["integration"]["errors"].append(str(e))
            return False

    def run_e2e_tests(self, args: argparse.Namespace) -> bool:
        """Run E2E tests with Playwright"""
        print("\n🎭 Running E2E tests...")

        os.chdir(self.tests_dir / "e2e")

        # Install Playwright browsers if needed
        try:
            subprocess.run(
                ["npx", "playwright", "install"], check=True, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Warning: Could not install Playwright browsers: {e}")

        cmd = ["npx", "playwright", "test"]

        if args.headed:
            cmd.append("--headed")

        if args.browser:
            cmd.extend(["--project", args.browser])

        if args.workers:
            cmd.extend(["--workers", str(args.workers)])

        try:
            result = subprocess.run(cmd, check=False)
            success = result.returncode == 0

            if success:
                print("✅ E2E tests passed")
            else:
                print("❌ E2E tests failed")
                self.results["e2e"]["errors"].append("E2E tests failed")

            return success

        except Exception as e:
            print(f"❌ Error running E2E tests: {e}")
            self.results["e2e"]["errors"].append(str(e))
            return False

    def generate_report(self):
        """Generate test report"""
        print("\n📊 Test Results Summary")
        print("=" * 50)

        total_passed = sum(suite["passed"] for suite in self.results.values())
        total_failed = sum(suite["failed"] for suite in self.results.values())
        total_errors = sum(len(suite["errors"]) for suite in self.results.values())

        for suite_name, results in self.results.items():
            status = "✅" if not results["errors"] else "❌"
            print(
                f"{status} {suite_name.capitalize()}: {results['passed']} passed, {results['failed']} failed"
            )

            if results["errors"]:
                for error in results["errors"]:
                    print(f"   ❌ {error}")

        print("=" * 50)
        print(
            f"Total: {total_passed} passed, {total_failed} failed, {total_errors} errors"
        )

        # Save results to file
        report_file = self.tests_dir / "test-results.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"📄 Detailed results saved to {report_file}")

        return total_errors == 0 and total_failed == 0

    def run_all_tests(self, args: argparse.Namespace) -> bool:
        """Run all test suites"""
        self.setup_signal_handlers()

        print("🧪 SubForge Dashboard Test Suite")
        print("=" * 50)

        # Check dependencies
        if not self.check_dependencies():
            return False

        success = True

        try:
            # Run unit tests first (no servers needed)
            if args.backend:
                backend_success = self.run_backend_tests(args)
                success = success and backend_success

            if args.frontend:
                frontend_success = self.run_frontend_tests(args)
                success = success and frontend_success

            # Start servers for integration/E2E tests
            if args.integration or args.e2e:
                if not self.start_test_servers():
                    return False

                if args.integration:
                    integration_success = self.run_integration_tests(args)
                    success = success and integration_success

                if args.e2e:
                    e2e_success = self.run_e2e_tests(args)
                    success = success and e2e_success

        finally:
            self.cleanup()

        # Generate report
        overall_success = self.generate_report()

        return success and overall_success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SubForge Dashboard Test Runner")

    # Test suite selection
    parser.add_argument("--backend", action="store_true", help="Run backend tests")
    parser.add_argument("--frontend", action="store_true", help="Run frontend tests")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests"
    )
    parser.add_argument("--e2e", action="store_true", help="Run E2E tests")
    parser.add_argument("--all", action="store_true", help="Run all test suites")

    # Test options
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage reports"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--markers", "-m", help="Run tests with specific markers")
    parser.add_argument("--keyword", "-k", help="Run tests matching keyword")
    parser.add_argument(
        "--maxfail", type=int, default=5, help="Maximum failures before stopping"
    )
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel")

    # Frontend specific
    parser.add_argument(
        "--watch", action="store_true", help="Watch mode for frontend tests"
    )

    # E2E specific
    parser.add_argument(
        "--headed", action="store_true", help="Run E2E tests in headed mode"
    )
    parser.add_argument("--browser", help="Browser for E2E tests")
    parser.add_argument(
        "--workers", type=int, help="Number of parallel workers for E2E"
    )

    args = parser.parse_args()

    # Default to all tests if none specified
    if not any([args.backend, args.frontend, args.integration, args.e2e]):
        args.all = True

    if args.all:
        args.backend = args.frontend = args.integration = args.e2e = True

    # Find project root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent

    # Run tests
    runner = TestRunner(project_root)
    success = runner.run_all_tests(args)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()