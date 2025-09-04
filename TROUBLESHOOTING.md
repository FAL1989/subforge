# SubForge Troubleshooting Guide

**Created**: 2025-09-04 15:44 UTC-3 São Paulo  
**Version**: 2.0.0  
**Coverage**: Comprehensive issue resolution for Claude-subagents

This guide covers all common issues, their root causes, solutions, and prevention strategies for SubForge development and deployment.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)  
3. [Runtime Issues](#runtime-issues)
4. [Integration Issues](#integration-issues)
5. [Debug Techniques](#debug-techniques)
6. [FAQ - Top 20 Questions](#faq---top-20-questions)
7. [Performance Optimization](#performance-optimization)
8. [Emergency Recovery](#emergency-recovery)

---

## Installation Issues

### 1.1 ModuleNotFoundError: subforge

**Problem**: Python cannot find the SubForge module

#### Root Cause
- SubForge not installed in current environment
- Virtual environment not activated  
- Incorrect Python path configuration
- Package installed in different Python version

#### Solutions

**Solution 1: Install SubForge (Recommended)**
```bash
# From PyPI (if available)
pip install subforge

# From source (development)
cd /path/to/Claude-subagents
pip install -e . --break-system-packages

# With optional dependencies
pip install -e .[dev] --break-system-packages
```

**Solution 2: Fix Python Path**
```bash
# Check current Python
which python
python --version

# Verify installation
python -c "import subforge; print(subforge.__file__)"

# Add to PYTHONPATH if needed
export PYTHONPATH="/path/to/Claude-subagents:$PYTHONPATH"
```

**Solution 3: Virtual Environment Fix**
```bash
# Create new environment
python -m venv subforge_env
source subforge_env/bin/activate  # Linux/Mac
# OR
subforge_env\Scripts\activate     # Windows

# Install SubForge
pip install -e /path/to/Claude-subagents
```

#### Prevention
- Always use virtual environments
- Install SubForge in editable mode for development
- Check Python version compatibility (>=3.8)

### 1.2 Permission Errors

**Problem**: Permission denied when installing or running SubForge

#### Root Cause
- Insufficient permissions for system-wide installation
- Read-only filesystem
- Package conflicts with system packages

#### Solutions

**Solution 1: User Installation**
```bash
# Install for current user only
pip install --user -e /path/to/Claude-subagents

# Update PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Solution 2: Use Virtual Environment**
```bash
# Create and activate virtual environment
python -m venv ~/.subforge_env
source ~/.subforge_env/bin/activate
pip install -e /path/to/Claude-subagents
```

**Solution 3: Fix Directory Permissions**
```bash
# Fix project directory permissions
sudo chown -R $USER:$USER /path/to/Claude-subagents
chmod -R 755 /path/to/Claude-subagents
```

#### Prevention
- Always use virtual environments for Python projects
- Avoid system-wide installations unless necessary
- Check directory permissions before installation

### 1.3 Python Version Conflicts

**Problem**: SubForge requires Python 3.8+ but older version is active

#### Root Cause
- System has multiple Python versions
- Wrong Python version in PATH
- Virtual environment using wrong Python

#### Solutions

**Solution 1: Use Specific Python Version**
```bash
# Check available Python versions
ls /usr/bin/python*

# Create venv with specific version
python3.12 -m venv subforge_env
python3.11 -m venv subforge_env  # or any 3.8+
```

**Solution 2: Update Default Python**
```bash
# Using update-alternatives (Ubuntu/Debian)
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1
sudo update-alternatives --config python

# Using pyenv (cross-platform)
pyenv install 3.12.0
pyenv global 3.12.0
```

**Solution 3: Docker Alternative**
```bash
# Use Docker with Python 3.12
docker run -it --rm -v $(pwd):/workspace python:3.12 bash
cd /workspace
pip install -e .
```

#### Prevention
- Use pyenv for Python version management
- Specify Python version in virtual environment creation
- Document required Python version in README

### 1.4 Dependency Conflicts

**Problem**: Conflicting package versions or missing dependencies

#### Root Cause
- Conflicting package versions in environment
- Missing optional dependencies
- Outdated package versions

#### Solutions

**Solution 1: Clean Environment**
```bash
# Remove existing environment
rm -rf venv/ subforge_env/

# Create fresh environment
python -m venv fresh_env
source fresh_env/bin/activate
pip install -e . --break-system-packages
```

**Solution 2: Resolve Conflicts**
```bash
# Check for conflicts
pip check

# Upgrade all packages
pip install --upgrade pip setuptools wheel

# Install with specific versions
pip install typer==0.9.0 rich==13.0.0
```

**Solution 3: Use Requirements Lock File**
```bash
# Generate requirements lock
pip freeze > requirements.lock

# Install from lock file
pip install -r requirements.lock
```

#### Prevention
- Use requirements.lock files for consistent environments
- Regularly update dependencies
- Use dependabot or similar tools for dependency management

---

## Configuration Issues

### 2.1 Agent Not Found Errors

**Problem**: `@agent-name` not found when trying to call specific agents

#### Root Cause
- SubForge not initialized in project
- Agent configuration files missing
- Incorrect agent names
- Corrupted .claude/agents/ directory

#### Solutions

**Solution 1: Initialize SubForge**
```bash
# Navigate to project root
cd /path/to/your/project

# Initialize SubForge
python -m subforge.simple_cli init --request "Describe your project needs"

# Verify agents created
ls .claude/agents/
```

**Solution 2: Manual Agent Verification**
```bash
# Check agent directory structure
find .claude/agents/ -name "*.md" -type f

# List available agents
python -m subforge.simple_cli status

# Check CLAUDE.md configuration
cat CLAUDE.md | grep -A5 -B5 "@"
```

**Solution 3: Recreate Agents**
```bash
# Backup existing configuration
cp -r .claude .claude.backup

# Reinitialize with fresh agents
python -m subforge.simple_cli init --request "Fresh start with [your requirements]"
```

#### Prevention
- Always run `subforge init` in new projects
- Use `subforge status` to verify agent availability
- Keep .claude/ directory in version control

### 2.2 Template Loading Failures

**Problem**: Cannot load or find agent templates

#### Root Cause
- Missing template files
- Incorrect template path configuration
- Template syntax errors
- Package data not installed correctly

#### Solutions

**Solution 1: Verify Template Installation**
```bash
# Check template location
python -c "
import subforge
import os
template_path = os.path.join(os.path.dirname(subforge.__file__), 'templates')
print(f'Template path: {template_path}')
print('Templates:', os.listdir(template_path) if os.path.exists(template_path) else 'NOT FOUND')
"
```

**Solution 2: Reinstall with Templates**
```bash
# Reinstall SubForge ensuring templates are included
pip uninstall subforge -y
pip install -e . --break-system-packages

# Verify templates are included
python -c "import pkg_resources; print(pkg_resources.resource_listdir('subforge', 'templates'))"
```

**Solution 3: Manual Template Verification**
```bash
# Find templates in source
find /path/to/Claude-subagents -name "*.md" -path "*/templates/*"

# Check MANIFEST.in includes templates
cat MANIFEST.in | grep template
```

#### Prevention
- Include templates in MANIFEST.in
- Test template loading in CI/CD
- Use package data configuration in setup.py/pyproject.toml

### 2.3 CLAUDE.md Syntax Errors

**Problem**: CLAUDE.md configuration file has syntax issues

#### Root Cause
- Invalid Markdown syntax
- Missing required sections
- Incorrect agent references
- Character encoding issues

#### Solutions

**Solution 1: Validate CLAUDE.md Syntax**
```bash
# Check basic syntax
python -c "
import markdown
with open('CLAUDE.md', 'r', encoding='utf-8') as f:
    content = f.read()
    try:
        markdown.markdown(content)
        print('✅ Valid Markdown syntax')
    except Exception as e:
        print(f'❌ Syntax error: {e}')
"
```

**Solution 2: Regenerate CLAUDE.md**
```bash
# Backup current file
cp CLAUDE.md CLAUDE.md.backup

# Generate fresh configuration
python -m subforge.simple_cli init --request "Regenerate configuration"

# Compare differences
diff CLAUDE.md.backup CLAUDE.md
```

**Solution 3: Fix Common Issues**
```bash
# Check for common issues
grep -n "^# " CLAUDE.md  # Verify heading levels
grep -n "@" CLAUDE.md     # Verify agent references
grep -n "```" CLAUDE.md   # Verify code blocks are closed

# Fix encoding issues
iconv -f ISO-8859-1 -t UTF-8 CLAUDE.md > CLAUDE.md.fixed
mv CLAUDE.md.fixed CLAUDE.md
```

#### Prevention
- Use consistent Markdown formatting
- Validate CLAUDE.md in CI/CD pipeline
- Use UTF-8 encoding consistently

### 2.4 Path Resolution Problems

**Problem**: SubForge cannot find project files or directories

#### Root Cause
- Relative vs absolute path confusion
- Symbolic links not resolved
- Case sensitivity issues (Windows/Mac)
- Missing directory permissions

#### Solutions

**Solution 1: Use Absolute Paths**
```bash
# Always use absolute paths for SubForge operations
PROJECT_ROOT=$(realpath .)
python -m subforge.simple_cli init --project-root "$PROJECT_ROOT"
```

**Solution 2: Fix Path Resolution**
```bash
# Resolve symbolic links
cd $(readlink -f /path/to/project)

# Check current directory
pwd
ls -la

# Verify SubForge can access
python -c "
from pathlib import Path
import os
print(f'Current dir: {os.getcwd()}')
print(f'Accessible: {os.access(\".\", os.R_OK | os.W_OK)}')
print(f'Contents: {list(Path(\".\").iterdir())[:10]}')
"
```

**Solution 3: Fix Permissions**
```bash
# Fix directory permissions
find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;

# Fix ownership if needed
sudo chown -R $USER:$USER .
```

#### Prevention
- Use absolute paths in scripts and configuration
- Test on different operating systems
- Document any special path requirements

---

## Runtime Issues

### 3.1 Memory/Performance Problems

**Problem**: SubForge consumes excessive memory or runs slowly

#### Root Cause
- Large project analysis without pagination
- Memory leaks in long-running processes
- Inefficient parallel execution
- Excessive logging or debugging

#### Solutions

**Solution 1: Monitor Resource Usage**
```bash
# Monitor memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
print(f'CPU: {process.cpu_percent()}%')
"

# Use system monitoring
top -p $(pgrep -f subforge)
```

**Solution 2: Optimize Configuration**
```bash
# Reduce parallel workers
export SUBFORGE_MAX_WORKERS=2

# Enable memory-efficient mode
export SUBFORGE_MEMORY_EFFICIENT=true

# Limit analysis depth
python -m subforge.simple_cli analyze --max-depth 3
```

**Solution 3: Profile Performance**
```bash
# Profile SubForge execution
python -m cProfile -o profile.stats -m subforge.simple_cli init
python -c "
import pstats
stats = pstats.Stats('profile.stats')
stats.sort_stats('cumulative').print_stats(20)
"
```

#### Prevention
- Set resource limits in CI/CD
- Regular performance regression testing
- Monitor memory usage patterns

### 3.2 Parallel Execution Failures

**Problem**: Parallel agent execution fails or hangs

#### Root Cause
- Race conditions between agents
- Shared resource conflicts
- Deadlocks in async operations
- Insufficient system resources

#### Solutions

**Solution 1: Disable Parallel Execution**
```bash
# Use serial execution for debugging
python -m subforge.simple_cli init --serial-only

# Or set environment variable
export SUBFORGE_PARALLEL_DISABLED=true
python -m subforge.simple_cli init
```

**Solution 2: Debug Parallel Issues**
```bash
# Enable detailed async debugging
export PYTHONDEVMODE=1
export SUBFORGE_DEBUG_ASYNC=true

# Run with verbose logging
python -m subforge.simple_cli init --verbose
```

**Solution 3: Adjust Resource Limits**
```bash
# Limit concurrent operations
export SUBFORGE_MAX_CONCURRENT=2

# Increase timeout values
export SUBFORGE_ASYNC_TIMEOUT=300

# Use resource monitoring
ulimit -v 2097152  # Limit memory to 2GB
```

#### Prevention
- Test parallel execution in CI/CD
- Use proper async/await patterns
- Implement resource locking for shared resources

### 3.3 Test Failures

**Problem**: pytest runs fail with various errors

#### Root Cause
- Missing test dependencies
- Environment-specific test failures
- Race conditions in async tests
- Incorrect test configuration

#### Solutions

**Solution 1: Install Test Dependencies**
```bash
# Install development dependencies
pip install -e .[dev]

# Install specific test requirements
pip install pytest pytest-asyncio pytest-cov

# Verify test discovery
python -m pytest --collect-only tests/
```

**Solution 2: Fix Async Test Issues**
```bash
# Run tests with proper async handling
python -m pytest tests/ -v --asyncio-mode=auto

# Debug specific async tests
python -m pytest tests/test_async.py -v -s --tb=long
```

**Solution 3: Environment-Specific Fixes**
```bash
# Run tests in isolation
python -m pytest tests/ --forked

# Skip problematic tests
python -m pytest tests/ -k "not slow and not integration"

# Use specific test configuration
python -m pytest -c pytest.ini tests/
```

#### Prevention
- Pin test dependencies in requirements
- Use proper async test patterns
- Run tests in multiple environments

### 3.4 Coverage Reporting Issues

**Problem**: Test coverage reports are incorrect or missing

#### Root Cause
- Coverage tool not configured properly
- Source code not instrumented
- Parallel execution affecting coverage
- Missing coverage configuration

#### Solutions

**Solution 1: Configure Coverage Properly**
```bash
# Install coverage tools
pip install coverage pytest-cov

# Run with coverage
python -m pytest tests/ --cov=subforge --cov-report=html --cov-report=term

# Generate manual coverage report
coverage run -m pytest tests/
coverage report -m
coverage html
```

**Solution 2: Fix Coverage Configuration**
```bash
# Check coverage configuration
cat .coveragerc

# Create proper configuration
cat > .coveragerc << EOF
[run]
source = subforge
branch = true
omit = 
    */tests/*
    */venv/*
    */env/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
EOF
```

**Solution 3: Debug Coverage Issues**
```bash
# Debug coverage data
coverage debug sys
coverage debug data

# Combine coverage data from parallel runs
coverage combine
coverage report
```

#### Prevention
- Include coverage configuration in project
- Test coverage collection in CI/CD
- Use consistent coverage tools across environments

---

## Integration Issues

### 4.1 Git Conflicts

**Problem**: Git merge conflicts with SubForge-generated files

#### Root Cause
- Multiple developers running SubForge
- Generated files in version control
- Inconsistent agent configurations
- Merge conflicts in CLAUDE.md

#### Solutions

**Solution 1: Proper Git Configuration**
```bash
# Add to .gitignore
echo "
# SubForge temporary files
.subforge/
*.pyc
__pycache__/
.coverage
htmlcov/
.pytest_cache/
" >> .gitignore

# Keep only essential files in git
git rm --cached .subforge/ -r
git commit -m "Remove SubForge temp files from tracking"
```

**Solution 2: Resolve Merge Conflicts**
```bash
# Check conflict status
git status

# Resolve CLAUDE.md conflicts
git checkout --theirs CLAUDE.md  # Use their version
# OR
git checkout --ours CLAUDE.md    # Use your version
# OR
git mergetool CLAUDE.md          # Manual resolution

# Regenerate after resolution
python -m subforge.simple_cli update
```

**Solution 3: Standardize Team Configuration**
```bash
# Create team template
python -m subforge.simple_cli init --template team-standard

# Share configuration
git add CLAUDE.md .claude/agents/
git commit -m "Standardize SubForge configuration"
```

#### Prevention
- Standardize SubForge configuration across team
- Use .gitignore for temporary files
- Document SubForge workflow in team guidelines

### 4.2 CI/CD Pipeline Failures

**Problem**: SubForge operations fail in CI/CD environments

#### Root Cause
- Missing dependencies in CI environment
- Different Python versions
- Missing environment variables
- Insufficient permissions

#### Solutions

**Solution 1: Fix CI Configuration**
```yaml
# GitHub Actions example
name: SubForge CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v --cov=subforge
    
    - name: Test SubForge initialization
      run: |
        python -m subforge.simple_cli init --request "Test project"
        python -m subforge.simple_cli status
```

**Solution 2: Environment Variables**
```bash
# Set required environment variables in CI
export PYTHONPATH="${GITHUB_WORKSPACE}:$PYTHONPATH"
export SUBFORGE_CI_MODE=true
export SUBFORGE_QUIET=true

# Use secrets for sensitive configuration
export SUBFORGE_API_KEY="${{ secrets.SUBFORGE_API_KEY }}"
```

**Solution 3: Containerized CI**
```dockerfile
# Dockerfile for CI
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

CMD ["python", "-m", "pytest", "tests/"]
```

#### Prevention
- Test CI configuration locally with act or similar tools
- Pin dependency versions in CI
- Use matrix builds for multiple Python versions

### 4.3 Docker/Container Issues

**Problem**: SubForge doesn't work properly in Docker containers

#### Root Cause
- Missing system dependencies
- File permission issues
- Path mounting problems
- Resource constraints

#### Solutions

**Solution 1: Proper Dockerfile**
```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 subforge
RUN chown -R subforge:subforge /workspace
USER subforge

# Set entrypoint
ENTRYPOINT ["python", "-m", "subforge.simple_cli"]
```

**Solution 2: Docker Compose Configuration**
```yaml
version: '3.8'
services:
  subforge:
    build: .
    volumes:
      - .:/workspace
      - /workspace/.subforge  # Exclude temp files
    environment:
      - PYTHONPATH=/workspace
      - SUBFORGE_DOCKER_MODE=true
    user: "1000:1000"
```

**Solution 3: Fix Permission Issues**
```bash
# Run with correct user mapping
docker run --rm -it \
  -v $(pwd):/workspace \
  -u $(id -u):$(id -g) \
  subforge:latest init
```

#### Prevention
- Test Docker builds locally
- Use multi-stage builds for smaller images
- Document container usage patterns

### 4.4 IDE Integration Problems

**Problem**: SubForge doesn't work properly with VS Code, PyCharm, etc.

#### Root Cause
- IDE using wrong Python interpreter
- Missing environment activation
- Incorrect project configuration
- Plugin conflicts

#### Solutions

**Solution 1: VS Code Configuration**
```json
// .vscode/settings.json
{
    "python.defaultInterpreter": "./venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        ".subforge/": true,
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

**Solution 2: PyCharm Configuration**
```bash
# Set Python interpreter
# File → Settings → Project → Python Interpreter
# Choose: /path/to/venv/bin/python

# Configure test runner
# File → Settings → Tools → Python Integrated Tools
# Default test runner: pytest
```

**Solution 3: Environment Activation**
```bash
# Ensure IDE uses activated environment
source venv/bin/activate
code .  # Launch VS Code from activated environment

# Or configure terminal integration
echo 'source venv/bin/activate' >> ~/.bashrc
```

#### Prevention
- Document IDE setup in project README
- Include IDE configuration files in project
- Test setup with fresh IDE installations

---

## Debug Techniques

### 5.1 Verbose Logging

**Problem**: Need detailed information about SubForge operations

#### Solutions

**Enable Debug Logging**
```bash
# Environment variable approach
export SUBFORGE_DEBUG=true
export SUBFORGE_LOG_LEVEL=DEBUG
python -m subforge.simple_cli init

# Command line approach
python -m subforge.simple_cli init --verbose --debug

# Python logging configuration
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import subforge
# Now run SubForge operations
"
```

**Custom Logging Configuration**
```python
# debug_config.py
import logging
import sys

def setup_debug_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('subforge_debug.log')
        ]
    )
    
    # Enable specific loggers
    logging.getLogger('subforge').setLevel(logging.DEBUG)
    logging.getLogger('asyncio').setLevel(logging.INFO)

if __name__ == '__main__':
    setup_debug_logging()
```

### 5.2 Debug Mode

**Problem**: Need to inspect SubForge internal state

#### Solutions

**Interactive Debug Mode**
```python
# debug_session.py
import asyncio
from subforge.core.workflow_orchestrator import WorkflowOrchestrator
from subforge.core.project_analyzer import ProjectAnalyzer

async def debug_session():
    analyzer = ProjectAnalyzer()
    orchestrator = WorkflowOrchestrator()
    
    # Set breakpoints and inspect
    import pdb; pdb.set_trace()
    
    # Analyze project
    context = await analyzer.analyze_project(".", "Debug session")
    print(f"Analysis result: {context}")
    
    # Debug workflow execution
    result = await orchestrator.execute_workflow(".", "Debug workflow", context)
    return result

# Run debug session
asyncio.run(debug_session())
```

**Debug with Environment Variables**
```bash
# Enable all debug features
export SUBFORGE_DEBUG=true
export SUBFORGE_DEBUG_ASYNC=true
export SUBFORGE_DEBUG_WORKFLOW=true
export SUBFORGE_DEBUG_AGENTS=true
export PYTHONDEVMODE=1

# Run with debug enabled
python -m subforge.simple_cli init --request "Debug test"
```

### 5.3 Stack Trace Analysis

**Problem**: Need to analyze error stack traces effectively

#### Solutions

**Enhanced Stack Trace Collection**
```python
# enhanced_traceback.py
import traceback
import sys
from pathlib import Path

def detailed_exception_handler(exc_type, exc_value, exc_traceback):
    """Enhanced exception handler with context"""
    print("=== DETAILED EXCEPTION ANALYSIS ===")
    print(f"Exception Type: {exc_type.__name__}")
    print(f"Exception Value: {exc_value}")
    print()
    
    print("=== STACK TRACE ===")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    print()
    
    print("=== LOCAL VARIABLES ===")
    tb = exc_traceback
    while tb is not None:
        frame = tb.tb_frame
        print(f"\nFrame: {frame.f_code.co_filename}:{tb.tb_lineno} in {frame.f_code.co_name}")
        for var_name, var_value in frame.f_locals.items():
            if not var_name.startswith('__'):
                try:
                    print(f"  {var_name} = {repr(var_value)[:100]}")
                except:
                    print(f"  {var_name} = <unable to represent>")
        tb = tb.tb_next

# Install enhanced handler
sys.excepthook = detailed_exception_handler
```

**Stack Trace with Context**
```bash
# Environment for better tracebacks
export PYTHONDEVMODE=1
export PYTHONASYNCIODEBUG=1

# Run with full traceback
python -u -m subforge.simple_cli init 2>&1 | tee error_log.txt

# Analyze with external tools
python -c "
import re
with open('error_log.txt') as f:
    content = f.read()
    
# Extract stack traces
traces = re.findall(r'Traceback.*?(?=\n\n|\nSubForge|\Z)', content, re.DOTALL)
for i, trace in enumerate(traces):
    print(f'=== TRACE {i+1} ===')
    print(trace)
    print()
"
```

### 5.4 Performance Profiling

**Problem**: Need to identify performance bottlenecks

#### Solutions

**CPU Profiling**
```bash
# Profile with cProfile
python -m cProfile -o subforge.prof -m subforge.simple_cli init

# Analyze profile
python -c "
import pstats
stats = pstats.Stats('subforge.prof')
stats.sort_stats('cumulative').print_stats(20)
print('\n=== Top functions by time ===')
stats.sort_stats('time').print_stats(10)
"
```

**Memory Profiling**
```bash
# Install memory profiler
pip install memory-profiler psutil

# Profile memory usage
python -m memory_profiler -m subforge.simple_cli init

# Continuous memory monitoring
python -c "
import psutil
import time
import subprocess
import threading

def monitor_memory():
    process = subprocess.Popen(['python', '-m', 'subforge.simple_cli', 'init'])
    pid = process.pid
    
    with open('memory_usage.log', 'w') as f:
        while process.poll() is None:
            try:
                p = psutil.Process(pid)
                memory_mb = p.memory_info().rss / 1024 / 1024
                f.write(f'{time.time()},{memory_mb}\n')
                f.flush()
                time.sleep(0.1)
            except psutil.NoSuchProcess:
                break
    
    process.wait()

monitor_memory()
"
```

**Async Profiling**
```python
# async_profiler.py
import asyncio
import time
import functools

def async_profile(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end = time.perf_counter()
            print(f"{func.__name__} took {end - start:.3f} seconds")
    return wrapper

# Apply to SubForge functions
from subforge.core.workflow_orchestrator import WorkflowOrchestrator

# Monkey patch for profiling
original_execute = WorkflowOrchestrator.execute_workflow
WorkflowOrchestrator.execute_workflow = async_profile(original_execute)
```

---

## FAQ - Top 20 Questions

### Q1: How do I know if SubForge is properly installed?

**Answer:**
```bash
# Quick installation check
python -c "import subforge; print(f'SubForge {subforge.__version__} installed at {subforge.__file__}')"

# Verify CLI availability
python -m subforge.simple_cli --help

# Check templates
python -c "import subforge.templates; print('Templates available')"
```

### Q2: Why doesn't `@agent-name` work in my project?

**Answer:**
The agent doesn't exist. Run initialization first:
```bash
python -m subforge.simple_cli init --request "Your project description"
ls .claude/agents/  # Verify agents were created
```

### Q3: How do I fix "No module named 'subforge'" errors?

**Answer:**
Install SubForge in editable mode:
```bash
cd /path/to/Claude-subagents
pip install -e . --break-system-packages
```

### Q4: Why is SubForge running slowly?

**Answer:**
Check resource usage and optimize:
```bash
# Monitor resources
top -p $(pgrep -f subforge)

# Reduce parallelization
export SUBFORGE_MAX_WORKERS=2

# Use memory-efficient mode
export SUBFORGE_MEMORY_EFFICIENT=true
```

### Q5: How do I debug SubForge agent creation?

**Answer:**
Enable debug mode:
```bash
export SUBFORGE_DEBUG=true
python -m subforge.simple_cli init --verbose
```

### Q6: What files should I commit to Git?

**Answer:**
```bash
# Commit these
git add CLAUDE.md .claude/agents/

# Don't commit these (add to .gitignore)
echo ".subforge/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
```

### Q7: How do I update existing agents?

**Answer:**
```bash
# Update all agents with new context
python -m subforge.simple_cli update

# Or reinitialize completely
python -m subforge.simple_cli init --request "Updated requirements"
```

### Q8: Why do tests fail in CI/CD?

**Answer:**
Common issues and fixes:
```yaml
# In your CI configuration
- name: Install SubForge
  run: pip install -e .[dev]

- name: Run tests with proper async handling
  run: python -m pytest tests/ --asyncio-mode=auto
```

### Q9: How do I handle memory errors?

**Answer:**
```bash
# Limit memory usage
ulimit -v 2097152  # 2GB limit

# Use smaller batch sizes
export SUBFORGE_BATCH_SIZE=10

# Enable garbage collection
export PYTHONDEBUG=gc
```

### Q10: What Python versions are supported?

**Answer:**
SubForge requires Python 3.8 or higher. Check compatibility:
```bash
python --version  # Should be 3.8+
python -c "import sys; print(sys.version_info >= (3, 8))"
```

### Q11: How do I fix template loading errors?

**Answer:**
```bash
# Verify template installation
python -c "import pkg_resources; print(pkg_resources.resource_listdir('subforge', 'templates'))"

# Reinstall if needed
pip install -e . --force-reinstall
```

### Q12: Why doesn't parallel execution work?

**Answer:**
```bash
# Check if parallel executor is available
python -c "
try:
    from subforge.orchestration.parallel_executor import ParallelExecutor
    print('✅ Parallel executor available')
except ImportError as e:
    print(f'❌ Parallel executor not available: {e}')
"

# Use serial mode as fallback
python -m subforge.simple_cli init --serial-only
```

### Q13: How do I handle permission errors?

**Answer:**
```bash
# Fix ownership
sudo chown -R $USER:$USER /path/to/project

# Fix permissions
chmod -R 755 /path/to/project

# Use user installation
pip install --user -e .
```

### Q14: What environment variables does SubForge use?

**Answer:**
```bash
# Common environment variables
export SUBFORGE_DEBUG=true          # Enable debug logging
export SUBFORGE_MAX_WORKERS=4       # Parallel worker limit
export SUBFORGE_MEMORY_EFFICIENT=true  # Memory optimization
export SUBFORGE_QUIET=true          # Suppress non-error output
export SUBFORGE_CI_MODE=true        # CI/CD optimizations
```

### Q15: How do I profile SubForge performance?

**Answer:**
```bash
# CPU profiling
python -m cProfile -o profile.stats -m subforge.simple_cli init

# Memory profiling
pip install memory-profiler
python -m memory_profiler -m subforge.simple_cli init
```

### Q16: Why do I get "Agent not responding" errors?

**Answer:**
```bash
# Check agent configuration
cat .claude/agents/agent-name.md

# Verify CLAUDE.md syntax
python -m py_compile CLAUDE.md  # Should not error

# Regenerate agents
python -m subforge.simple_cli init --force
```

### Q17: How do I handle Docker containerization?

**Answer:**
```dockerfile
FROM python:3.12-slim
WORKDIR /workspace
COPY . .
RUN pip install -e .
USER 1000:1000
ENTRYPOINT ["python", "-m", "subforge.simple_cli"]
```

### Q18: What are the resource requirements?

**Answer:**
- **Minimum**: 512MB RAM, Python 3.8+
- **Recommended**: 2GB RAM, Python 3.11+, SSD storage
- **Heavy usage**: 4GB+ RAM, multiple CPU cores

### Q19: How do I contribute to SubForge development?

**Answer:**
```bash
# Development setup
git clone https://github.com/FAL1989/subforge
cd subforge
pip install -e .[dev]

# Run tests
python -m pytest tests/ -v

# Code quality checks
flake8 subforge/
black subforge/
```

### Q20: Where can I get more help?

**Answer:**
- **Documentation**: Check README.md and docs/
- **Issues**: https://github.com/FAL1989/subforge/issues
- **Discussions**: GitHub Discussions
- **Debug logs**: Look in .subforge/errors/ directory

---

## Performance Optimization

### 7.1 Memory Optimization

**Strategies for reducing memory usage:**

```bash
# Environment variables for memory efficiency
export SUBFORGE_MEMORY_EFFICIENT=true
export SUBFORGE_BATCH_SIZE=10
export SUBFORGE_CACHE_SIZE=50

# Python memory optimization
export PYTHONOPTIMIZE=1
export PYTHONOSPRANDOMHASH=1

# Garbage collection tuning
python -c "
import gc
gc.set_threshold(700, 10, 10)  # More frequent GC
"
```

**Code-level optimizations:**
```python
# memory_optimizer.py
import gc
import weakref
from functools import lru_cache

class MemoryOptimizer:
    def __init__(self):
        self.weak_refs = weakref.WeakKeyDictionary()
    
    @lru_cache(maxsize=128)
    def cached_analysis(self, project_path: str):
        # Cached project analysis
        pass
    
    def cleanup_memory(self):
        gc.collect()
        self.cached_analysis.cache_clear()
```

### 7.2 CPU Optimization

**Parallel execution tuning:**

```bash
# Optimal worker count (usually CPU cores)
export SUBFORGE_MAX_WORKERS=$(nproc)

# Enable async optimizations
export SUBFORGE_ASYNC_OPTIMIZE=true

# CPU affinity (Linux)
taskset -c 0-3 python -m subforge.simple_cli init
```

### 7.3 I/O Optimization

**File system optimization:**

```bash
# Use faster filesystem (tmpfs for temp files)
mkdir /tmp/subforge_workspace
export SUBFORGE_TEMP_DIR=/tmp/subforge_workspace

# Enable async I/O
export SUBFORGE_ASYNC_IO=true

# Batch file operations
export SUBFORGE_BATCH_IO=true
```

### 7.4 Network Optimization

**For network-dependent operations:**

```bash
# Connection pooling
export SUBFORGE_CONNECTION_POOL_SIZE=10

# Timeout optimization
export SUBFORGE_CONNECT_TIMEOUT=30
export SUBFORGE_READ_TIMEOUT=120

# Retry configuration
export SUBFORGE_MAX_RETRIES=3
export SUBFORGE_RETRY_DELAY=1
```

---

## Emergency Recovery

### 8.1 Complete System Reset

**When everything is broken:**

```bash
#!/bin/bash
# emergency_reset.sh

echo "🚨 Emergency SubForge Reset"

# 1. Backup current state
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp -r .claude backups/$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
cp CLAUDE.md backups/$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true

# 2. Clean temporary files
rm -rf .subforge/
rm -rf __pycache__/
find . -name "*.pyc" -delete

# 3. Reset virtual environment
deactivate 2>/dev/null || true
rm -rf venv/ env/ subforge_env/

# 4. Fresh installation
python -m venv fresh_env
source fresh_env/bin/activate
pip install -e /path/to/Claude-subagents --break-system-packages

# 5. Verify installation
python -c "import subforge; print(f'✅ SubForge {subforge.__version__} ready')"

# 6. Fresh initialization
python -m subforge.simple_cli init --request "Emergency reset initialization"

echo "✅ Emergency reset complete"
```

### 8.2 Partial Recovery

**When some components work:**

```bash
# Check what's working
python -c "
import sys
try:
    import subforge
    print('✅ SubForge module available')
    print(f'Version: {subforge.__version__}')
    print(f'Location: {subforge.__file__}')
except ImportError:
    print('❌ SubForge module not found')
    sys.exit(1)

try:
    from subforge.core.project_analyzer import ProjectAnalyzer
    print('✅ Core modules available')
except ImportError as e:
    print(f'❌ Core modules broken: {e}')

try:
    from subforge.simple_cli import main
    print('✅ CLI available')
except ImportError as e:
    print(f'❌ CLI broken: {e}')
"

# Fix specific components
if [ $? -eq 0 ]; then
    echo "Attempting partial recovery..."
    python -m subforge.simple_cli status
    python -m subforge.simple_cli update
fi
```

### 8.3 Data Recovery

**Recovering lost configurations:**

```bash
# Find backup configurations
find . -name "CLAUDE.md*" -o -name "*.backup"
find backups/ -name "CLAUDE.md" 2>/dev/null

# Restore from git history
git log --oneline --name-only | grep -E "(CLAUDE\.md|\.claude/)"
git show HEAD~1:CLAUDE.md > CLAUDE.md.recovered

# Recover from .subforge directory
find .subforge/ -name "*.json" -exec grep -l "agents" {} \;
```

### 8.4 Diagnostic Report

**Generate comprehensive diagnostic information:**

```bash
#!/bin/bash
# diagnostic_report.sh

echo "# SubForge Diagnostic Report"
echo "Generated: $(date)"
echo

echo "## System Information"
echo "- OS: $(uname -a)"
echo "- Python: $(python --version)"
echo "- PWD: $(pwd)"
echo

echo "## SubForge Status"
python -c "
try:
    import subforge
    print(f'- Version: {subforge.__version__}')
    print(f'- Location: {subforge.__file__}')
    
    # Check core components
    from subforge.core import project_analyzer
    print('- ✅ Core modules working')
    
    from subforge import simple_cli
    print('- ✅ CLI working')
    
except Exception as e:
    print(f'- ❌ Error: {e}')
"

echo
echo "## Project Status"
echo "- Git status: $(git status --porcelain | wc -l) modified files"
echo "- CLAUDE.md exists: $([ -f CLAUDE.md ] && echo 'Yes' || echo 'No')"
echo "- Agents directory: $([ -d .claude/agents ] && echo 'Yes' || echo 'No')"
if [ -d .claude/agents ]; then
    echo "- Agent count: $(find .claude/agents -name '*.md' | wc -l)"
fi

echo
echo "## Recent Errors"
if [ -d .subforge/errors ]; then
    echo "Error files found:"
    ls -la .subforge/errors/ | tail -5
else
    echo "No error directory found"
fi

echo
echo "## Environment Variables"
env | grep -i subforge | head -10

echo
echo "## Recent Commands"
history | grep -i subforge | tail -5
```

---

## Contact and Support

For additional support:
- **GitHub Issues**: https://github.com/FAL1989/subforge/issues
- **Documentation**: README.md and project documentation
- **Emergency Recovery**: Use the scripts provided in this troubleshooting guide

**Remember**: When in doubt, start with a clean virtual environment and fresh SubForge installation.

---

*Last Updated: 2025-09-04 15:44 UTC-3 São Paulo*  
*Version: 2.0.0*  
*Status: Comprehensive troubleshooting coverage*