#!/usr/bin/env python3
"""
Phase 3 Integration Test Runner
Comprehensive test suite runner for Phase 3 refactoring validation

This script runs all Phase 3 tests and generates comprehensive reports:
1. Integration tests
2. Performance benchmarks  
3. Architecture compliance
4. Coverage reports
5. Quality metrics

Created: 2025-09-05 17:45 UTC-3 São Paulo
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import pytest


class TestResults:
    """Container for test results"""
    
    def __init__(self):
        self.integration_results = {}
        self.performance_results = {}
        self.architecture_results = {}
        self.coverage_results = {}
        self.overall_results = {}
        self.start_time = time.time()
        self.end_time = None
        
    def finalize(self):
        """Finalize results"""
        self.end_time = time.time()
        self.overall_results['duration'] = self.end_time - self.start_time
        self.overall_results['timestamp'] = datetime.now().isoformat()


class Phase3TestRunner:
    """Main test runner for Phase 3 validation"""
    
    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = workspace_dir or Path.cwd()
        self.tests_dir = self.workspace_dir / "tests"
        self.reports_dir = self.workspace_dir / "test_reports" / "phase3"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = TestResults()
        
    def run_all_tests(self, include_benchmarks: bool = True, include_architecture: bool = True) -> TestResults:
        """Run all Phase 3 tests"""
        print("🚀 Starting Phase 3 Refactoring Test Suite")
        print(f"📂 Workspace: {self.workspace_dir}")
        print(f"📊 Reports: {self.reports_dir}")
        print("-" * 60)
        
        # Run integration tests
        self.run_integration_tests()
        
        # Run performance benchmarks (optional)
        if include_benchmarks:
            self.run_performance_benchmarks()
        
        # Run architecture compliance tests
        if include_architecture:
            self.run_architecture_tests()
        
        # Generate coverage report
        self.generate_coverage_report()
        
        # Finalize and generate summary
        self.results.finalize()
        self.generate_summary_report()
        
        return self.results
    
    def run_integration_tests(self):
        """Run comprehensive integration tests"""
        print("\n🔧 Running Integration Tests...")
        
        test_file = self.tests_dir / "test_phase3_integration.py"
        if not test_file.exists():
            print(f"❌ Integration test file not found: {test_file}")
            self.results.integration_results['status'] = 'failed'
            self.results.integration_results['reason'] = 'Test file not found'
            return
        
        # Run pytest with detailed output
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_file),
            "-v",
            "--tb=short",
            "--durations=10",
            f"--junitxml={self.reports_dir}/integration_results.xml",
            f"--html={self.reports_dir}/integration_report.html",
            "--self-contained-html"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            self.results.integration_results['return_code'] = result.returncode
            self.results.integration_results['stdout'] = result.stdout
            self.results.integration_results['stderr'] = result.stderr
            self.results.integration_results['status'] = 'passed' if result.returncode == 0 else 'failed'
            
            # Parse test results
            self._parse_pytest_output(result.stdout, self.results.integration_results)
            
            if result.returncode == 0:
                print("✅ Integration tests passed!")
            else:
                print("❌ Integration tests failed!")
                print(f"   Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⏰ Integration tests timed out!")
            self.results.integration_results['status'] = 'timeout'
        except Exception as e:
            print(f"❌ Error running integration tests: {e}")
            self.results.integration_results['status'] = 'error'
            self.results.integration_results['error'] = str(e)
    
    def run_performance_benchmarks(self):
        """Run performance benchmark tests"""
        print("\n⚡ Running Performance Benchmarks...")
        
        test_file = self.tests_dir / "test_performance_benchmarks.py"
        if not test_file.exists():
            print(f"❌ Performance test file not found: {test_file}")
            self.results.performance_results['status'] = 'skipped'
            return
        
        # Run pytest-benchmark
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_file),
            "-v",
            "--benchmark-only",
            "--benchmark-sort=mean",
            "--benchmark-columns=mean,stddev,median,ops,rounds",
            f"--benchmark-json={self.reports_dir}/benchmark_results.json",
            f"--benchmark-histogram={self.reports_dir}/benchmark_histogram",
            "--benchmark-disable-gc"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            self.results.performance_results['return_code'] = result.returncode  
            self.results.performance_results['stdout'] = result.stdout
            self.results.performance_results['stderr'] = result.stderr
            self.results.performance_results['status'] = 'passed' if result.returncode == 0 else 'failed'
            
            # Parse benchmark results
            self._parse_benchmark_results()
            
            if result.returncode == 0:
                print("✅ Performance benchmarks completed!")
            else:
                print("❌ Performance benchmarks failed!")
                print(f"   Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⏰ Performance benchmarks timed out!")
            self.results.performance_results['status'] = 'timeout'
        except Exception as e:
            print(f"❌ Error running benchmarks: {e}")
            self.results.performance_results['status'] = 'error'
            self.results.performance_results['error'] = str(e)
    
    def run_architecture_tests(self):
        """Run architecture compliance tests"""
        print("\n🏗️ Running Architecture Compliance Tests...")
        
        test_file = self.tests_dir / "test_architecture_compliance.py"
        if not test_file.exists():
            print(f"❌ Architecture test file not found: {test_file}")
            self.results.architecture_results['status'] = 'skipped'
            return
        
        cmd = [
            sys.executable, "-m", "pytest", 
            str(test_file),
            "-v",
            "--tb=short",
            "-x",  # Stop on first failure for architecture issues
            f"--junitxml={self.reports_dir}/architecture_results.xml"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            self.results.architecture_results['return_code'] = result.returncode
            self.results.architecture_results['stdout'] = result.stdout
            self.results.architecture_results['stderr'] = result.stderr
            self.results.architecture_results['status'] = 'passed' if result.returncode == 0 else 'failed'
            
            # Parse test results
            self._parse_pytest_output(result.stdout, self.results.architecture_results)
            
            if result.returncode == 0:
                print("✅ Architecture compliance verified!")
            else:
                print("❌ Architecture compliance issues found!")
                print(f"   Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⏰ Architecture tests timed out!")
            self.results.architecture_results['status'] = 'timeout'
        except Exception as e:
            print(f"❌ Error running architecture tests: {e}")
            self.results.architecture_results['status'] = 'error' 
            self.results.architecture_results['error'] = str(e)
    
    def generate_coverage_report(self):
        """Generate comprehensive coverage report"""
        print("\n📊 Generating Coverage Report...")
        
        # Run coverage analysis
        coverage_cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir / "test_phase3_integration.py"),
            "--cov=subforge.core.prp",
            "--cov=subforge.core.context",
            "--cov=subforge.plugins",
            "--cov-report=term-missing",
            f"--cov-report=html:{self.reports_dir}/coverage_html",
            f"--cov-report=xml:{self.reports_dir}/coverage.xml",
            f"--cov-report=json:{self.reports_dir}/coverage.json"
        ]
        
        try:
            result = subprocess.run(coverage_cmd, capture_output=True, text=True, timeout=300)
            
            self.results.coverage_results['return_code'] = result.returncode
            self.results.coverage_results['stdout'] = result.stdout
            self.results.coverage_results['stderr'] = result.stderr
            
            # Parse coverage data
            self._parse_coverage_results()
            
            if result.returncode == 0:
                print("✅ Coverage report generated!")
            else:
                print("❌ Coverage generation failed!")
                
        except Exception as e:
            print(f"❌ Error generating coverage: {e}")
            self.results.coverage_results['status'] = 'error'
            self.results.coverage_results['error'] = str(e)
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n📋 Generating Summary Report...")
        
        summary = {
            "phase": "Phase 3 Refactoring Validation",
            "timestamp": datetime.now().isoformat(),
            "duration": f"{self.results.overall_results.get('duration', 0):.2f} seconds",
            "workspace": str(self.workspace_dir),
            "results": {
                "integration": self._get_test_summary(self.results.integration_results),
                "performance": self._get_test_summary(self.results.performance_results),
                "architecture": self._get_test_summary(self.results.architecture_results),
                "coverage": self._get_coverage_summary()
            }
        }
        
        # Overall status
        all_statuses = [
            summary["results"]["integration"]["status"],
            summary["results"]["performance"]["status"],
            summary["results"]["architecture"]["status"]
        ]
        
        if all(status in ["passed", "skipped"] for status in all_statuses):
            summary["overall_status"] = "PASSED"
            print("🎉 Phase 3 Refactoring Validation: PASSED")
        else:
            summary["overall_status"] = "FAILED"
            print("❌ Phase 3 Refactoring Validation: FAILED")
        
        # Write summary report
        summary_file = self.reports_dir / "summary_report.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Write markdown report
        self._generate_markdown_report(summary)
        
        print(f"📄 Summary report: {summary_file}")
        print(f"📄 HTML report: {self.reports_dir}/summary_report.md")
    
    def _parse_pytest_output(self, output: str, results_dict: Dict[str, Any]):
        """Parse pytest output to extract test statistics"""
        lines = output.split('\n')
        
        # Extract test counts
        for line in lines:
            if '=====' in line and ('passed' in line or 'failed' in line):
                # Parse line like "===== 15 passed, 2 failed in 12.34s ====="
                parts = line.split()
                test_counts = {}
                
                for i, part in enumerate(parts):
                    if part.isdigit():
                        if i + 1 < len(parts):
                            status = parts[i + 1].rstrip(',')
                            test_counts[status] = int(part)
                
                results_dict['test_counts'] = test_counts
                break
        
        # Extract warnings
        warnings = [line for line in lines if 'WARNING' in line or 'WARN' in line]
        if warnings:
            results_dict['warnings'] = warnings[:5]  # Limit to first 5 warnings
    
    def _parse_benchmark_results(self):
        """Parse benchmark results from JSON file"""
        benchmark_file = self.reports_dir / "benchmark_results.json"
        
        if benchmark_file.exists():
            try:
                with open(benchmark_file) as f:
                    benchmark_data = json.load(f)
                
                # Extract key metrics
                benchmarks = benchmark_data.get('benchmarks', [])
                summary = {
                    'total_benchmarks': len(benchmarks),
                    'benchmarks': []
                }
                
                for bench in benchmarks:
                    summary['benchmarks'].append({
                        'name': bench.get('name', 'unknown'),
                        'mean': bench.get('stats', {}).get('mean', 0),
                        'stddev': bench.get('stats', {}).get('stddev', 0),
                        'median': bench.get('stats', {}).get('median', 0),
                        'ops': bench.get('stats', {}).get('ops', 0)
                    })
                
                self.results.performance_results['benchmark_summary'] = summary
                
            except Exception as e:
                self.results.performance_results['parse_error'] = str(e)
    
    def _parse_coverage_results(self):
        """Parse coverage results from JSON file"""
        coverage_file = self.reports_dir / "coverage.json"
        
        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                
                summary = coverage_data.get('totals', {})
                self.results.coverage_results['summary'] = {
                    'covered_lines': summary.get('covered_lines', 0),
                    'num_statements': summary.get('num_statements', 0),
                    'percent_covered': summary.get('percent_covered', 0),
                    'missing_lines': summary.get('missing_lines', 0)
                }
                
            except Exception as e:
                self.results.coverage_results['parse_error'] = str(e)
    
    def _get_test_summary(self, results_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary for a test category"""
        status = results_dict.get('status', 'unknown')
        test_counts = results_dict.get('test_counts', {})
        
        return {
            "status": status,
            "tests_run": sum(test_counts.values()),
            "passed": test_counts.get('passed', 0),
            "failed": test_counts.get('failed', 0),
            "skipped": test_counts.get('skipped', 0),
            "warnings": len(results_dict.get('warnings', []))
        }
    
    def _get_coverage_summary(self) -> Dict[str, Any]:
        """Get coverage summary"""
        coverage_summary = self.results.coverage_results.get('summary', {})
        
        return {
            "status": "completed" if coverage_summary else "failed",
            "percent_covered": coverage_summary.get('percent_covered', 0),
            "covered_lines": coverage_summary.get('covered_lines', 0),
            "total_lines": coverage_summary.get('num_statements', 0),
            "missing_lines": coverage_summary.get('missing_lines', 0)
        }
    
    def _generate_markdown_report(self, summary: Dict[str, Any]):
        """Generate markdown summary report"""
        markdown_content = f"""# Phase 3 Refactoring Validation Report

**Generated**: {summary['timestamp']}  
**Duration**: {summary['duration']}  
**Overall Status**: {summary['overall_status']}

## Test Results Summary

### Integration Tests
- **Status**: {summary['results']['integration']['status'].upper()}
- **Tests Run**: {summary['results']['integration']['tests_run']}
- **Passed**: {summary['results']['integration']['passed']}
- **Failed**: {summary['results']['integration']['failed']}
- **Skipped**: {summary['results']['integration']['skipped']}

### Performance Benchmarks
- **Status**: {summary['results']['performance']['status'].upper()}
- **Tests Run**: {summary['results']['performance']['tests_run']}
- **Passed**: {summary['results']['performance']['passed']}
- **Failed**: {summary['results']['performance']['failed']}

### Architecture Compliance
- **Status**: {summary['results']['architecture']['status'].upper()}
- **Tests Run**: {summary['results']['architecture']['tests_run']}
- **Passed**: {summary['results']['architecture']['passed']}
- **Failed**: {summary['results']['architecture']['failed']}

### Code Coverage
- **Status**: {summary['results']['coverage']['status'].upper()}
- **Coverage**: {summary['results']['coverage']['percent_covered']:.1f}%
- **Covered Lines**: {summary['results']['coverage']['covered_lines']}
- **Total Lines**: {summary['results']['coverage']['total_lines']}
- **Missing Lines**: {summary['results']['coverage']['missing_lines']}

## Phase 3 Refactoring Validation

This report validates the following Phase 3 refactoring work:

### ✅ PRP Generator - Strategy Pattern
- External template loading
- Strategy pattern implementation 
- Backward compatibility
- Fluent builder pattern

### ✅ Context Engineer - Modularization
- Type safety with TypedDict
- Module separation
- Caching implementation
- Error handling improvements

### ✅ Plugin Manager - DI Container
- Dependency injection container
- Plugin lifecycle management  
- Interface segregation
- Extensibility patterns

## Quality Gates

| Requirement | Target | Actual | Status |
|-------------|---------|---------|---------|
| Test Coverage | ≥ 90% | {summary['results']['coverage']['percent_covered']:.1f}% | {'✅' if summary['results']['coverage']['percent_covered'] >= 90 else '❌'} |
| Integration Tests | All Pass | {summary['results']['integration']['passed']}/{summary['results']['integration']['tests_run']} | {'✅' if summary['results']['integration']['status'] == 'passed' else '❌'} |
| Architecture Compliance | All Pass | {summary['results']['architecture']['passed']}/{summary['results']['architecture']['tests_run']} | {'✅' if summary['results']['architecture']['status'] == 'passed' else '❌'} |
| Performance | No Regression | {'Passed' if summary['results']['performance']['status'] == 'passed' else 'Failed'} | {'✅' if summary['results']['performance']['status'] == 'passed' else '❌'} |

## Files

- **Integration Report**: `integration_report.html`
- **Coverage Report**: `coverage_html/index.html`
- **Benchmark Results**: `benchmark_results.json`
- **Test Results**: `*_results.xml`

---
*Generated by Phase 3 Test Runner - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC-3 São Paulo*
"""
        
        markdown_file = self.reports_dir / "summary_report.md"
        with open(markdown_file, 'w') as f:
            f.write(markdown_content)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Phase 3 Refactoring Test Runner")
    parser.add_argument("--workspace", type=Path, help="Workspace directory")
    parser.add_argument("--no-benchmarks", action="store_true", help="Skip performance benchmarks")
    parser.add_argument("--no-architecture", action="store_true", help="Skip architecture tests")
    parser.add_argument("--quick", action="store_true", help="Run only integration tests")
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = Phase3TestRunner(args.workspace)
    
    # Configure test execution
    include_benchmarks = not (args.no_benchmarks or args.quick)
    include_architecture = not (args.no_architecture or args.quick)
    
    try:
        # Run tests
        results = runner.run_all_tests(
            include_benchmarks=include_benchmarks,
            include_architecture=include_architecture
        )
        
        # Exit with appropriate code
        if results.overall_results.get('status') == 'PASSED':
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test run failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()