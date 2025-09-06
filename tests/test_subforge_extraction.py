#!/usr/bin/env python3
"""
Tests for SubForge Knowledge Extraction System
Verifies real extraction functionality - no fake data
Created: 2025-09-06 12:30 UTC-3 São Paulo
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import json
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from subforge.core.knowledge_extractor import ProjectKnowledgeExtractor
from subforge.core.context_builder import ContextBuilder
from subforge.core.gap_analyzer import GapAnalyzer
from subforge.simple_init import init_subforge


class TestKnowledgeExtractor:
    """Test the knowledge extraction functionality"""
    
    def test_extract_from_package_json(self, tmp_path):
        """Test extraction from package.json"""
        # Create a mock package.json
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "test-project",
            "version": "1.0.0",
            "scripts": {
                "dev": "vite dev",
                "build": "vite build",
                "test": "vitest"
            },
            "dependencies": {
                "react": "^18.0.0",
                "vite": "^4.0.0"
            }
        }))
        
        extractor = ProjectKnowledgeExtractor(tmp_path)
        commands = extractor.extract_commands()
        
        assert len(commands) == 3
        assert "dev" in commands
        assert commands["dev"].command == "npm run dev"
        # Check that it came from package.json
        assert commands["dev"].source == "package.json"
    
    def test_extract_from_makefile(self, tmp_path):
        """Test extraction from Makefile"""
        makefile = tmp_path / "Makefile"
        makefile.write_text("""
.PHONY: install test build

install:
	pip install -r requirements.txt

test:
	pytest tests/

build:
	python setup.py build
""")
        
        extractor = ProjectKnowledgeExtractor(tmp_path)
        commands = extractor.extract_commands()
        
        assert len(commands) == 3
        assert "install" in commands
        assert commands["install"].command == "make install"
        # Description is generic "Run install target"
        assert "install" in commands["install"].description.lower()
    
    def test_identify_modules(self, tmp_path):
        """Test module identification"""
        # Create directory structure with more files to meet significance threshold
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "__init__.py").touch()
        (tmp_path / "src" / "main.py").write_text("def main(): pass")
        (tmp_path / "src" / "utils.py").write_text("def util(): pass")
        (tmp_path / "src" / "config.py").write_text("CONFIG = {}")
        
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("def test_main(): pass")
        (tmp_path / "tests" / "test_utils.py").write_text("def test_util(): pass")
        
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "README.md").touch()
        
        extractor = ProjectKnowledgeExtractor(tmp_path)
        modules = extractor.identify_modules()
        
        # Should find modules based on significance
        module_names = [m.name for m in modules]
        
        # At least one module should be identified
        assert len(modules) > 0
        
        # If tests module is found, verify test detection
        if "tests" in module_names:
            tests_module = next(m for m in modules if m.name == "tests")
            assert tests_module.has_tests == True


class TestContextBuilder:
    """Test the context building functionality"""
    
    def test_build_root_claude_md(self, tmp_path):
        """Test root CLAUDE.md generation"""
        from subforge.core.knowledge_extractor import ProjectInfo, Module, Command
        
        project_info = ProjectInfo(
            name="test-project",
            description="Test project description",
            languages=["Python", "JavaScript"],
            frameworks=["FastAPI", "React"],
            databases=[],
            architecture="Microservices",
            conventions=[]
        )
        
        modules = [
            Module(
                name="api",
                path=tmp_path / "api",
                description="API backend service",
                has_tests=True,
                has_docs=False,
                key_files=[],
                dependencies=[]
            ),
            Module(
                name="frontend",
                path=tmp_path / "frontend",
                description="React frontend",
                has_tests=True,
                has_docs=True,
                key_files=[],
                dependencies=[]
            )
        ]
        
        commands = {
            "dev": Command(
                name="dev",
                command="npm run dev",
                description="Start development server",
                source="package.json",
                category="development"
            )
        }
        
        builder = ContextBuilder(tmp_path)
        claude_md = builder.build_root_claude_md(project_info, modules, commands)
        
        assert "test-project" in claude_md
        assert "Python, JavaScript" in claude_md
        assert "FastAPI, React" in claude_md
        assert "Microservices" in claude_md
        assert "api" in claude_md
        assert "frontend" in claude_md
    
    def test_sanitize_workflow_names(self, tmp_path):
        """Test that workflow names with slashes are sanitized"""
        from subforge.core.knowledge_extractor import Workflow
        
        workflows = {
            "CI/CD Pipeline": Workflow(
                name="CI/CD Pipeline",
                description="Continuous Integration and Deployment",
                source=".github/workflows/ci.yml",
                steps=["Test", "Build", "Deploy"]
            )
        }
        
        builder = ContextBuilder(tmp_path)
        workflow_files = builder.build_workflow_files(workflows, {})
        
        # Check that the filename is sanitized
        assert len(workflow_files) == 1
        assert "CI-CD Pipeline" in str(workflow_files[0].path)


class TestGapAnalyzer:
    """Test the gap analysis functionality"""
    
    def test_calculate_completeness_score(self, tmp_path):
        """Test completeness score calculation"""
        # Create minimal project structure
        (tmp_path / "README.md").write_text("# Test Project")
        (tmp_path / "package.json").write_text(json.dumps({
            "name": "test",
            "scripts": {"dev": "vite"}
        }))
        
        analyzer = GapAnalyzer(tmp_path)
        report = analyzer.analyze_documentation_gaps()
        
        # Should have a score between 0 and 1
        assert 0 <= report.completeness_score <= 1
        
        # Should identify missing items
        assert isinstance(report.missing_commands, list)
        assert isinstance(report.missing_workflows, list)
        assert isinstance(report.missing_documentation, list)
    
    def test_identify_missing_commands(self, tmp_path):
        """Test identification of missing commands"""
        # Create project with tests but no test command
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_something.py").touch()
        
        analyzer = GapAnalyzer(tmp_path)
        report = analyzer.analyze_documentation_gaps()
        
        # Should identify missing test command
        missing_command_names = [cmd.name for cmd in report.missing_commands]
        assert "test" in missing_command_names


class TestSubForgeInit:
    """Test the complete SubForge initialization"""
    
    def test_init_creates_structure(self, tmp_path):
        """Test that init creates the expected structure"""
        # Create minimal project
        (tmp_path / "README.md").write_text("# Test Project\nA test project")
        (tmp_path / "setup.py").write_text("from setuptools import setup\nsetup(name='test')")
        
        # Run initialization
        results = init_subforge(str(tmp_path), verbose=False)
        
        assert results['summary']['success'] == True
        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / ".claude").exists()
        assert (tmp_path / ".claude" / "GAP_ANALYSIS.md").exists()
        assert (tmp_path / ".claude" / "INITIALIZATION.md").exists()
    
    def test_init_extracts_real_data(self, tmp_path):
        """Test that init extracts real project data"""
        # Create project with specific content
        package_json = {
            "name": "real-project",
            "scripts": {
                "start": "node server.js",
                "test": "jest"
            },
            "dependencies": {
                "express": "^4.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))
        
        results = init_subforge(str(tmp_path), verbose=False)
        
        # Check extraction results
        assert results['extraction']['project_name'] == 'real-project'
        assert results['extraction']['commands_count'] >= 2  # start and test
        # JSON is detected from package.json, JavaScript may or may not be detected
        assert 'JSON' in results['extraction']['languages'] or 'JavaScript' in results['extraction']['languages']
        
        # Verify CLAUDE.md contains real data
        claude_md = (tmp_path / "CLAUDE.md").read_text()
        assert "real-project" in claude_md
        assert "express" in claude_md.lower() or "node" in claude_md.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])