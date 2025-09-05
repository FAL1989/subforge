#!/usr/bin/env python3
"""
Test Setup Validation Script
Validates that all test modules can be imported and basic setup is correct

Created: 2025-09-05 17:50 UTC-3 São Paulo
"""

import sys
import traceback
from pathlib import Path
from typing import List, Tuple


def validate_imports() -> List[Tuple[str, bool, str]]:
    """Validate that all test modules can be imported"""
    results = []
    
    test_modules = [
        "test_phase3_integration",
        "test_performance_benchmarks", 
        "test_architecture_compliance"
    ]
    
    for module_name in test_modules:
        try:
            __import__(module_name)
            results.append((module_name, True, "OK"))
            print(f"✅ {module_name}: Import successful")
        except Exception as e:
            error_msg = str(e)
            results.append((module_name, False, error_msg))
            print(f"❌ {module_name}: Import failed - {error_msg}")
    
    return results


def validate_dependencies() -> List[Tuple[str, bool, str]]:
    """Validate that required dependencies are available"""
    results = []
    
    dependencies = [
        ("pytest", "pytest"),
        ("pytest_benchmark", "pytest-benchmark"),
        ("psutil", "psutil for performance monitoring"),
        ("subforge.core.prp", "PRP module"),
        ("subforge.core.context_engineer", "Context Engineer module"),
        ("subforge.plugins.plugin_manager", "Plugin Manager module")
    ]
    
    for dep_name, description in dependencies:
        try:
            __import__(dep_name)
            results.append((dep_name, True, "Available"))
            print(f"✅ {description}: Available")
        except ImportError as e:
            results.append((dep_name, False, str(e)))
            print(f"❌ {description}: Missing - {e}")
    
    return results


def validate_test_files() -> List[Tuple[str, bool, str]]:
    """Validate that test files exist and have expected structure"""
    results = []
    
    test_files = [
        ("test_phase3_integration.py", "Integration tests"),
        ("test_performance_benchmarks.py", "Performance benchmarks"),
        ("test_architecture_compliance.py", "Architecture tests"),
        ("run_phase3_tests.py", "Test runner script")
    ]
    
    tests_dir = Path(__file__).parent
    
    for filename, description in test_files:
        filepath = tests_dir / filename
        
        if filepath.exists():
            # Check file size (should not be empty)
            if filepath.stat().st_size > 100:
                results.append((filename, True, f"Exists ({filepath.stat().st_size} bytes)"))
                print(f"✅ {description}: File exists and has content")
            else:
                results.append((filename, False, "File too small"))
                print(f"⚠️ {description}: File exists but appears empty")
        else:
            results.append((filename, False, "File not found"))
            print(f"❌ {description}: File not found")
    
    return results


def validate_project_structure() -> List[Tuple[str, bool, str]]:
    """Validate project structure for refactored modules"""
    results = []
    
    project_root = Path(__file__).parent.parent
    
    required_paths = [
        ("subforge/core/prp/__init__.py", "PRP module init"),
        ("subforge/core/prp/base.py", "PRP base classes"),
        ("subforge/core/prp/generator.py", "PRP generator"),
        ("subforge/core/prp/builder.py", "PRP builder"),
        ("subforge/core/context/__init__.py", "Context module init"),
        ("subforge/core/context/types.py", "Context types"),
        ("subforge/core/context/builder.py", "Context builder"),
        ("subforge/core/context/validators.py", "Context validators"),
        ("subforge/plugins/__init__.py", "Plugins module init"),
        ("subforge/plugins/plugin_manager.py", "Plugin manager")
    ]
    
    for rel_path, description in required_paths:
        full_path = project_root / rel_path
        
        if full_path.exists():
            results.append((rel_path, True, "Exists"))
            print(f"✅ {description}: Found")
        else:
            results.append((rel_path, False, "Missing"))
            print(f"❌ {description}: Missing at {rel_path}")
    
    return results


def main():
    """Main validation function"""
    print("🔍 Validating Phase 3 Test Setup")
    print("=" * 50)
    
    all_results = []
    
    # Validate imports
    print("\n📦 Validating Test Module Imports...")
    import_results = validate_imports()
    all_results.extend(import_results)
    
    # Validate dependencies  
    print("\n📋 Validating Dependencies...")
    dep_results = validate_dependencies()
    all_results.extend(dep_results)
    
    # Validate test files
    print("\n📄 Validating Test Files...")
    file_results = validate_test_files()
    all_results.extend(file_results)
    
    # Validate project structure
    print("\n🏗️ Validating Project Structure...")
    structure_results = validate_project_structure()
    all_results.extend(structure_results)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    
    passed = sum(1 for _, success, _ in all_results if success)
    failed = len(all_results) - passed
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/len(all_results)*100:.1f}%")
    
    if failed > 0:
        print("\n❌ FAILED VALIDATIONS:")
        for name, success, message in all_results:
            if not success:
                print(f"   • {name}: {message}")
        
        print("\n💡 RECOMMENDATIONS:")
        print("   1. Install missing dependencies: pip install pytest pytest-benchmark psutil")
        print("   2. Ensure all refactored modules exist in subforge/")
        print("   3. Check that Phase 3 refactoring is complete")
        print("   4. Run tests from project root directory")
        
        return 1
    else:
        print("\n🎉 All validations passed! Ready to run Phase 3 tests.")
        print("\nNext steps:")
        print("   python tests/run_phase3_tests.py")
        print("   python tests/run_phase3_tests.py --quick  # Integration only")
        
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️ Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        traceback.print_exc()
        sys.exit(1)