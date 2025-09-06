#!/usr/bin/env python3
"""
Performance Test Runner for SubForge
Created: 2025-09-05 17:40 UTC-3 São Paulo

Script to run performance tests with various configurations and generate reports.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


class PerformanceTestRunner:
    """Runner for performance test suites."""
    
    def __init__(self, output_dir: str = "performance_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def run_benchmark_tests(self, groups: List[str] = None) -> Dict[str, Any]:
        """Run benchmark tests for specified groups."""
        cmd = [
            "pytest",
            "tests/test_performance_suite.py",
            "-v",
            "--benchmark-only",
            "--benchmark-json=" + str(self.output_dir / f"benchmark_{self.timestamp}.json"),
            "--benchmark-verbose",
            "--benchmark-sort=mean",
            "--benchmark-columns=min,max,mean,stddev,rounds,iterations"
        ]
        
        if groups:
            for group in groups:
                cmd.extend(["--benchmark-group-by", group])
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "command": " ".join(cmd),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_memory_tests(self) -> Dict[str, Any]:
        """Run memory profiling tests."""
        cmd = [
            "pytest",
            "tests/test_performance_suite.py",
            "-v",
            "-m", "memory",
            "--tb=short"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "command": " ".join(cmd),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_load_tests(self) -> Dict[str, Any]:
        """Run load and stress tests."""
        cmd = [
            "pytest",
            "tests/test_performance_suite.py",
            "-v",
            "-m", "load",
            "--tb=short",
            "--timeout=300"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "command": " ".join(cmd),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_specific_tests(self, test_names: List[str]) -> Dict[str, Any]:
        """Run specific test functions."""
        cmd = [
            "pytest",
            "tests/test_performance_suite.py",
            "-v",
            "--benchmark-only"
        ]
        
        for test in test_names:
            cmd.extend(["-k", test])
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "command": " ".join(cmd),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def generate_report(self, results: Dict[str, Any]) -> None:
        """Generate a performance test report."""
        report_path = self.output_dir / f"report_{self.timestamp}.md"
        
        with open(report_path, 'w') as f:
            f.write("# SubForge Performance Test Report\n\n")
            f.write(f"**Generated**: {datetime.now().isoformat()}\n\n")
            
            for test_type, result in results.items():
                f.write(f"## {test_type.replace('_', ' ').title()}\n\n")
                f.write(f"**Command**: `{result['command']}`\n\n")
                f.write(f"**Status**: {'✅ PASSED' if result['returncode'] == 0 else '❌ FAILED'}\n\n")
                
                if result['returncode'] != 0:
                    f.write("### Errors\n")
                    f.write("```\n")
                    f.write(result['stderr'])
                    f.write("\n```\n\n")
                
                # Extract key metrics from stdout
                if "benchmark" in test_type.lower():
                    f.write("### Benchmark Results\n")
                    # Parse benchmark output
                    lines = result['stdout'].split('\n')
                    for line in lines:
                        if 'test_' in line and ('passed' in line or 'PASSED' in line):
                            f.write(f"- {line.strip()}\n")
                
                f.write("\n---\n\n")
        
        print(f"Report generated: {report_path}")
    
    def run_all_tests(self) -> None:
        """Run all performance test suites."""
        results = {}
        
        # Run different test categories
        print("\n=== Running Benchmark Tests ===")
        results["benchmark_tests"] = self.run_benchmark_tests()
        
        print("\n=== Running Memory Tests ===")
        results["memory_tests"] = self.run_memory_tests()
        
        print("\n=== Running Load Tests ===")
        results["load_tests"] = self.run_load_tests()
        
        # Generate report
        self.generate_report(results)
        
        # Print summary
        print("\n=== Test Summary ===")
        for test_type, result in results.items():
            status = "✅ PASSED" if result['returncode'] == 0 else "❌ FAILED"
            print(f"{test_type}: {status}")
    
    def run_quick_tests(self) -> None:
        """Run a quick subset of performance tests."""
        quick_tests = [
            "test_prp_generation_performance",
            "test_context_creation_performance",
            "test_plugin_loading_performance",
            "test_workflow_lookup_performance"
        ]
        
        print("\n=== Running Quick Performance Tests ===")
        results = {"quick_tests": self.run_specific_tests(quick_tests)}
        
        self.generate_report(results)
        
        # Print summary
        status = "✅ PASSED" if results['quick_tests']['returncode'] == 0 else "❌ FAILED"
        print(f"\nQuick Tests: {status}")


def main():
    """Main entry point for the performance test runner."""
    parser = argparse.ArgumentParser(
        description="Run SubForge performance tests"
    )
    
    parser.add_argument(
        "--mode",
        choices=["all", "quick", "benchmark", "memory", "load"],
        default="quick",
        help="Test mode to run (default: quick)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="performance_results",
        help="Directory to store test results (default: performance_results)"
    )
    
    parser.add_argument(
        "--groups",
        nargs="+",
        help="Specific benchmark groups to run"
    )
    
    parser.add_argument(
        "--tests",
        nargs="+",
        help="Specific test functions to run"
    )
    
    args = parser.parse_args()
    
    runner = PerformanceTestRunner(output_dir=args.output_dir)
    
    if args.mode == "all":
        runner.run_all_tests()
    elif args.mode == "quick":
        runner.run_quick_tests()
    elif args.mode == "benchmark":
        results = {"benchmark": runner.run_benchmark_tests(groups=args.groups)}
        runner.generate_report(results)
    elif args.mode == "memory":
        results = {"memory": runner.run_memory_tests()}
        runner.generate_report(results)
    elif args.mode == "load":
        results = {"load": runner.run_load_tests()}
        runner.generate_report(results)
    elif args.tests:
        results = {"custom": runner.run_specific_tests(args.tests)}
        runner.generate_report(results)


if __name__ == "__main__":
    main()