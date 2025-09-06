---
name: SubForge CI/CD Pipeline
description: GitHub Actions workflow: SubForge CI/CD Pipeline
source: .github/workflows/ci.yml
---

# Subforge Ci/Cd Pipeline Workflow

## Description
GitHub Actions workflow: SubForge CI/CD Pipeline

## Source
Extracted from: `.github/workflows/ci.yml`



## Steps
1. Set up Python ${{ matrix.python-version }}
2. Cache pip packages
3. Install dependencies (`./scripts/install.sh`)
4. Run tests with coverage
5. Upload coverage to Codecov
6. Set up Python
7. Install linting tools (`./scripts/install.sh`)
8. Run Black
9. Run Ruff
10. Run Flake8
11. Set up Python
12. Install build tools (`./scripts/install.sh`)
13. Build package
14. Check package
15. Upload artifacts
16. Set up Python
17. Download artifacts
18. Publish to Test PyPI
19. Publish to PyPI

## Usage
This workflow runs automatically in CI/CD

## Related Commands
- `./scripts/install.sh` - SubForge - Local Development Installation Script
- `./scripts/install.sh` - SubForge - Local Development Installation Script
- `./scripts/install.sh` - SubForge - Local Development Installation Script

## Notes
- This workflow runs on GitHub Actions
- Complex workflow with 19 steps
