# Phase 3 Integration Test Suite

Comprehensive test suite for validating Phase 3 refactoring work in the SubForge project.

## Overview

This test suite validates three major refactoring components:

1. **PRP Generator** - Strategy Pattern with external templates
2. **Context Engineer** - Modularization and type safety  
3. **Plugin Manager** - DI Container and lifecycle management

## Test Structure

### Core Test Files

- **`test_phase3_integration.py`** - Main integration tests
- **`test_performance_benchmarks.py`** - Performance and memory benchmarks
- **`test_architecture_compliance.py`** - SOLID principles and architecture validation
- **`run_phase3_tests.py`** - Comprehensive test runner with reporting
- **`validate_test_setup.py`** - Setup validation and dependency checking

### Configuration Files

- **`pytest.ini`** - PyTest configuration with coverage settings
- **`README_PHASE3_TESTS.md`** - This documentation file

## Quick Start

### 1. Validate Setup

```bash
# Validate test environment and dependencies
python tests/validate_test_setup.py
```

### 2. Run All Tests

```bash
# Run complete Phase 3 validation suite
python tests/run_phase3_tests.py

# Quick run (integration tests only)
python tests/run_phase3_tests.py --quick

# Skip performance benchmarks
python tests/run_phase3_tests.py --no-benchmarks
```

### 3. View Reports

Reports are generated in `test_reports/phase3/`:
- `summary_report.md` - Human-readable summary
- `integration_report.html` - Detailed integration test results
- `coverage_html/index.html` - Coverage report
- `benchmark_results.json` - Performance benchmark data

## Test Categories

### Integration Tests (`TestPRPRefactoring`, `TestContextRefactoring`, `TestPluginManagerRefactoring`)

**Purpose**: Validate that refactored components work correctly together

**Coverage**:
- PRP Generator strategy pattern implementation
- External template loading and backward compatibility
- Context Engineer modularization and type safety
- Plugin Manager dependency injection and lifecycle
- End-to-end workflow validation

**Example**:
```python
@pytest.mark.asyncio
async def test_full_subforge_workflow(self, workspace_dir, sample_project_profile):
    # 1. Engineer context
    context_engineer = create_context_engineer(workspace_dir)
    context_package = context_engineer.engineer_context(sample_project_profile, ContextLevel.COMPREHENSIVE)
    
    # 2. Generate PRP with strategy pattern
    prp_generator = create_prp_generator(workspace_dir)
    analysis_prp = await prp_generator.generate_prp(PRPType.FACTORY_ANALYSIS, context)
    
    # 3. Execute with plugin manager
    plugin_manager = PluginManager(workspace_dir / "plugins")
    # ... validation continues
```

### Performance Benchmarks (`PerformanceBenchmarks`, `StressTests`)

**Purpose**: Ensure refactoring maintained or improved performance

**Coverage**:
- PRP generation performance baseline
- Context engineering memory usage
- Plugin manager initialization time
- Concurrent operations handling
- Memory leak detection
- Scalability under load

**Quality Gates**:
- PRP generation: < 1 second average
- Context engineering: < 2 seconds comprehensive
- Memory growth: < 50MB for 10 operations
- Cache speedup: > 2x improvement

### Architecture Compliance (`TestSingle*Principle`)

**Purpose**: Validate adherence to SOLID principles and design patterns

**Coverage**:
- Single Responsibility Principle compliance
- Open/Closed Principle with extensible strategies
- Liskov Substitution Principle for interchangeable components
- Interface Segregation Principle for focused interfaces
- Dependency Inversion Principle with abstractions
- Design pattern implementations (Strategy, Builder, Factory)

## Quality Requirements

### Coverage Targets
- **Minimum Coverage**: 85%
- **Target Coverage**: 90%
- **Modules Covered**: 
  - `subforge.core.prp.*`
  - `subforge.core.context.*`
  - `subforge.plugins.*`

### Performance Baselines
- **PRP Generation**: < 1 second average
- **Context Engineering**: < 2 seconds comprehensive
- **Plugin Initialization**: < 0.2 seconds
- **Memory Usage**: < 100MB peak for test operations

### Architecture Requirements
- All files ≤ 300 lines (post-refactoring)
- No `Dict[str, Any]` in public APIs (replaced with TypedDict)
- Abstract base classes for extensibility
- Proper separation of concerns

## Test Execution Modes

### Full Suite
```bash
python tests/run_phase3_tests.py
```
- Integration tests
- Performance benchmarks  
- Architecture compliance
- Coverage analysis
- Comprehensive reporting

### Quick Validation
```bash
python tests/run_phase3_tests.py --quick
```
- Integration tests only
- Basic coverage report
- Fast feedback (~2 minutes)

### Custom Execution
```bash
# Integration tests only
pytest tests/test_phase3_integration.py -v

# Benchmarks only
pytest tests/test_performance_benchmarks.py --benchmark-only

# Architecture only
pytest tests/test_architecture_compliance.py -x
```

## Interpreting Results

### Success Criteria

**PASSED** - All requirements met:
- ✅ Integration tests: All pass
- ✅ Performance: No regression 
- ✅ Architecture: SOLID compliance
- ✅ Coverage: ≥ 90%

**FAILED** - Requirements not met:
- ❌ Any integration test fails
- ❌ Performance regression detected
- ❌ Architecture violations found  
- ❌ Coverage below 85%

### Common Issues

**Import Errors**:
```bash
# Validate setup first
python tests/validate_test_setup.py

# Install missing dependencies
pip install pytest pytest-benchmark psutil
```

**Module Not Found**:
```bash
# Ensure SubForge is installed in development mode
pip install -e . --break-system-packages

# Check project structure
ls -la subforge/core/prp/
ls -la subforge/core/context/
ls -la subforge/plugins/
```

**Performance Issues**:
- Check if running in resource-constrained environment
- Disable other applications during benchmarking
- Use `--no-benchmarks` to skip performance tests

**Architecture Violations**:
- Review SOLID principles compliance
- Check for proper abstraction usage
- Validate design pattern implementations

## Extending Tests

### Adding New Test Cases

```python
# Add to test_phase3_integration.py
class TestNewFeature:
    """Test new Phase 3 feature"""
    
    def test_new_functionality(self, workspace_dir):
        """Test new functionality"""
        # Arrange
        # Act  
        # Assert
        pass
```

### Adding Benchmarks

```python
# Add to test_performance_benchmarks.py
def test_new_performance_benchmark(self, benchmark):
    """Benchmark new functionality"""
    def operation_to_benchmark():
        # Implementation
        pass
    
    result = benchmark(operation_to_benchmark)
    assert result is not None
```

### Adding Architecture Tests

```python
# Add to test_architecture_compliance.py
def test_new_architecture_requirement(self):
    """Test new architecture requirement"""
    # Validate design patterns
    # Check principle compliance
    pass
```

## Reporting

### Generated Reports

1. **`summary_report.md`** - Executive summary with pass/fail status
2. **`integration_report.html`** - Detailed test results with stack traces
3. **`coverage_html/index.html`** - Interactive coverage report
4. **`benchmark_results.json`** - Performance metrics and trends
5. **Various XML files** - CI/CD integration format

### Report Structure

```
test_reports/
└── phase3/
    ├── summary_report.md           # Main summary
    ├── summary_report.json         # Machine-readable summary  
    ├── integration_report.html     # Detailed integration results
    ├── integration_results.xml     # JUnit format
    ├── architecture_results.xml    # JUnit format
    ├── coverage_html/              # Interactive coverage
    │   └── index.html
    ├── coverage.xml                # Coverage XML
    ├── coverage.json               # Coverage JSON
    ├── benchmark_results.json      # Benchmark data
    └── benchmark_histogram.svg     # Performance visualization
```

## Troubleshooting

### Common Error Solutions

**"ModuleNotFoundError: No module named 'subforge'"**:
```bash
cd /path/to/Claude-subagents
pip install -e . --break-system-packages
```

**"pytest: command not found"**:
```bash
pip install pytest pytest-benchmark pytest-html pytest-cov
```

**"Permission denied" on test scripts**:
```bash
chmod +x tests/run_phase3_tests.py tests/validate_test_setup.py
```

**Tests timeout or hang**:
- Check for infinite loops in refactored code
- Reduce test iterations with `--quick` mode
- Monitor system resources during execution

### Getting Help

1. **Validate setup**: `python tests/validate_test_setup.py`
2. **Check logs**: Review detailed error output in reports
3. **Run individual tests**: Use pytest directly for debugging
4. **Check dependencies**: Ensure all required modules are installed

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Phase 3 Tests
on: [push, pull_request]

jobs:
  test-phase3:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -e . --break-system-packages
          pip install pytest pytest-benchmark pytest-html pytest-cov
      
      - name: Validate test setup
        run: python tests/validate_test_setup.py
      
      - name: Run Phase 3 tests
        run: python tests/run_phase3_tests.py
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: phase3-test-reports
          path: test_reports/phase3/
```

---

*Phase 3 Integration Test Suite - Created 2025-09-05 17:55 UTC-3 São Paulo*