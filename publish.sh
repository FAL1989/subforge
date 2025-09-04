#!/bin/bash
# SubForge PyPI Publishing Script
# Usage: ./publish.sh [test|prod]

set -e

echo "🚀 SubForge PyPI Publisher"
echo "=========================="

# Check Python and pip
echo "📋 Checking requirements..."
python --version
pip --version

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info

# Install build tools
echo "📦 Installing build tools..."
pip install --upgrade pip setuptools wheel twine build

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Build package
echo "🔨 Building package..."
python -m build

# Check package
echo "✅ Checking package..."
twine check dist/*

# Display package info
echo "📊 Package info:"
ls -la dist/

# Publish based on argument
if [ "$1" = "test" ]; then
    echo "📤 Publishing to Test PyPI..."
    echo "Run: pip install -i https://test.pypi.org/simple/ subforge"
    twine upload --repository testpypi dist/*
elif [ "$1" = "prod" ]; then
    echo "⚠️  Publishing to Production PyPI..."
    echo "This will make the package publicly available!"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        twine upload dist/*
        echo "✅ Published to PyPI!"
        echo "Install with: pip install subforge"
    else
        echo "❌ Publication cancelled"
    fi
else
    echo "📝 Usage: ./publish.sh [test|prod]"
    echo "  test - Publish to Test PyPI"
    echo "  prod - Publish to Production PyPI"
fi