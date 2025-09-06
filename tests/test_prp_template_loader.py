#!/usr/bin/env python3
"""
Comprehensive test suite for PRP Template Loader
Tests template loading, Jinja2 rendering, and error handling
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from jinja2 import Template, TemplateNotFound, TemplateSyntaxError

from subforge.core.prp_template_loader import PRPTemplateLoader


class TestPRPTemplateLoader:
    """Test suite for PRP Template Loader"""
    
    @pytest.fixture
    def temp_template_dir(self):
        """Create temporary template directory with test templates"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir) / "templates"
            template_dir.mkdir()
            
            # Create test template files
            analysis_template = template_dir / "analysis.yaml"
            analysis_template.write_text("""
# Analysis Template
project: {{ project_name }}
type: {{ analysis_type }}
items:
{% for item in items %}
  - {{ item }}
{% endfor %}
""")
            
            generation_template = template_dir / "generation.yaml"
            generation_template.write_text("""
# Generation Template
subagent: {{ subagent_type | replace('-', ' ') | title }}
context:
  project: {{ project.name }}
  language: {{ project.language }}
{% if features %}
features:
{% for feature in features %}
  - {{ feature }}
{% endfor %}
{% endif %}
""")
            
            validation_template = template_dir / "validation.yaml"
            validation_template.write_text("""
# Validation Template
scope: {{ scope | upper }}
artifacts: {{ artifacts | length }}
{% if metrics %}
metrics:
{% for metric in metrics %}
  - name: {{ metric.name }}
    threshold: {{ metric.threshold }}
{% endfor %}
{% endif %}
""")
            
            # Create invalid template for error testing
            invalid_template = template_dir / "invalid.yaml"
            invalid_template.write_text("""
# Invalid Template
{% for item in items
  - {{ item }}
{% endfor %}
""")
            
            yield template_dir
    
    @pytest.fixture
    def loader(self, temp_template_dir):
        """Create template loader with test templates"""
        return PRPTemplateLoader(temp_template_dir)
    
    def test_initialization_default_directory(self):
        """Test initialization with default template directory"""
        # Mock the default path to exist
        with patch.object(Path, 'exists', return_value=True):
            loader = PRPTemplateLoader()
            assert loader.template_dir.name == "prp"
            assert loader.env is not None
    
    def test_initialization_custom_directory(self, temp_template_dir):
        """Test initialization with custom template directory"""
        loader = PRPTemplateLoader(temp_template_dir)
        assert loader.template_dir == temp_template_dir
        assert loader.env is not None
    
    def test_initialization_nonexistent_directory(self):
        """Test initialization with non-existent directory"""
        with pytest.raises(ValueError, match="Template directory does not exist"):
            PRPTemplateLoader(Path("/nonexistent/directory"))
    
    def test_template_loading_from_files(self, loader):
        """Test loading YAML templates from files"""
        # Load analysis template
        template = loader.load_template("analysis")
        assert template is not None
        assert isinstance(template, Template)
        
        # Load generation template
        template = loader.load_template("generation")
        assert template is not None
        
        # Load validation template
        template = loader.load_template("validation")
        assert template is not None
    
    def test_jinja2_rendering(self, loader):
        """Test template rendering with variables"""
        # Test analysis template rendering
        rendered = loader.render(
            "analysis",
            project_name="TestProject",
            analysis_type="comprehensive",
            items=["item1", "item2", "item3"]
        )
        
        assert "TestProject" in rendered
        assert "comprehensive" in rendered
        assert "item1" in rendered
        assert "item2" in rendered
        assert "item3" in rendered
    
    def test_template_variable_substitution(self, loader):
        """Test complex variable substitution"""
        # Test with nested objects
        project = {
            "name": "MyProject",
            "language": "Python",
            "framework": "FastAPI"
        }
        
        rendered = loader.render(
            "generation",
            subagent_type="agent-generator",
            project=project,
            features=["async", "validation", "authentication"]
        )
        
        assert "Agent Generator" in rendered  # Test title filter
        assert "MyProject" in rendered
        assert "Python" in rendered
        assert "async" in rendered
        assert "validation" in rendered
        assert "authentication" in rendered
    
    def test_template_conditionals(self, loader):
        """Test Jinja2 conditionals in templates"""
        # Render with features
        rendered_with = loader.render(
            "generation",
            subagent_type="test",
            project={"name": "Test", "language": "Python"},
            features=["feature1"]
        )
        assert "features:" in rendered_with
        assert "feature1" in rendered_with
        
        # Render without features
        rendered_without = loader.render(
            "generation",
            subagent_type="test",
            project={"name": "Test", "language": "Python"}
        )
        assert "features:" not in rendered_without
    
    def test_template_loops(self, loader):
        """Test Jinja2 loops in templates"""
        metrics = [
            {"name": "coverage", "threshold": 80},
            {"name": "performance", "threshold": 95},
            {"name": "security", "threshold": 100}
        ]
        
        rendered = loader.render(
            "validation",
            scope="unit",
            artifacts=["file1.py", "file2.py"],
            metrics=metrics
        )
        
        assert "UNIT" in rendered  # Test upper filter
        assert "artifacts: 2" in rendered
        assert "coverage" in rendered
        assert "80" in rendered
        assert "performance" in rendered
        assert "95" in rendered
        assert "security" in rendered
        assert "100" in rendered
    
    def test_template_validation(self, loader):
        """Test template syntax validation"""
        # Valid templates should return True
        assert loader.validate_template("analysis") == True
        assert loader.validate_template("generation") == True
        assert loader.validate_template("validation") == True
        
        # Non-existent template should return False
        assert loader.validate_template("nonexistent") == False
    
    def test_missing_template_handling(self, loader):
        """Test fallback for missing templates"""
        with pytest.raises(TemplateNotFound):
            loader.load_template("nonexistent")
        
        with pytest.raises(TemplateNotFound, match="Template 'nonexistent.yaml' not found"):
            loader.render("nonexistent", test="value")
    
    def test_invalid_template_syntax(self, loader):
        """Test handling of templates with syntax errors"""
        # The invalid template has a syntax error
        with pytest.raises(TemplateSyntaxError):
            loader.load_template("invalid")
    
    def test_template_caching(self, loader):
        """Test template caching mechanism"""
        # Load template twice
        template1 = loader.load_template("analysis")
        template2 = loader.load_template("analysis")
        
        # Jinja2 should cache the compiled template
        # (Both should be the same compiled template object)
        assert template1 is template2
    
    def test_custom_filters(self, loader):
        """Test custom Jinja2 filters"""
        # Test replace filter
        rendered = loader.render(
            "generation",
            subagent_type="test-type-example",
            project={"name": "Test", "language": "Python"}
        )
        assert "Test Type Example" in rendered  # replace + title filters
        
        # Test title filter directly
        template_str = "{{ text | title }}"
        template = loader.env.from_string(template_str)
        result = template.render(text="hello world")
        assert result == "Hello World"
        
        # Test replace filter directly
        template_str = "{{ text | replace('old', 'new') }}"
        template = loader.env.from_string(template_str)
        result = template.render(text="old value")
        assert result == "new value"
    
    def test_multiple_filter_chaining(self, loader):
        """Test chaining multiple filters"""
        template_str = "{{ text | replace('-', ' ') | title }}"
        template = loader.env.from_string(template_str)
        result = template.render(text="test-case-example")
        assert result == "Test Case Example"
    
    def test_template_whitespace_control(self, loader):
        """Test Jinja2 whitespace control"""
        # The loader should be configured to trim blocks and lstrip
        template_str = """
        {%- for item in items -%}
        {{ item }}
        {%- endfor -%}
        """
        template = loader.env.from_string(template_str)
        result = template.render(items=["a", "b", "c"])
        
        # Should have minimal whitespace
        assert result.strip() == "abc"
    
    def test_template_with_default_values(self, loader):
        """Test templates with default values"""
        template_str = "{{ value | default('default_value') }}"
        template = loader.env.from_string(template_str)
        
        # With value
        result = template.render(value="provided")
        assert result == "provided"
        
        # Without value
        result = template.render()
        assert result == "default_value"
    
    def test_template_error_messages(self, loader):
        """Test error message clarity"""
        try:
            loader.load_template("nonexistent_template")
        except TemplateNotFound as e:
            assert "nonexistent_template.yaml" in str(e)
            assert str(loader.template_dir) in str(e)
    
    def test_render_with_missing_variables(self, loader):
        """Test rendering with missing required variables"""
        # Jinja2 by default renders missing variables as empty strings
        rendered = loader.render(
            "analysis",
            project_name="TestProject"
            # Missing: analysis_type and items
        )
        
        assert "TestProject" in rendered
        # Missing variables should be rendered as empty
        assert "type: \n" in rendered or "type:\n" in rendered
    
    def test_template_inheritance(self, temp_template_dir):
        """Test Jinja2 template inheritance"""
        # Create base template
        base_template = temp_template_dir / "base.yaml"
        base_template.write_text("""
# Base Template
{% block header %}
project: {{ project_name }}
{% endblock %}

{% block content %}
Default content
{% endblock %}
""")
        
        # Create child template
        child_template = temp_template_dir / "child.yaml"
        child_template.write_text("""
{% extends "base.yaml" %}

{% block content %}
Custom content for {{ project_name }}
{% endblock %}
""")
        
        loader = PRPTemplateLoader(temp_template_dir)
        rendered = loader.render("child", project_name="TestProject")
        
        assert "TestProject" in rendered
        assert "Custom content for TestProject" in rendered
        assert "Default content" not in rendered
    
    def test_template_includes(self, temp_template_dir):
        """Test Jinja2 template includes"""
        # Create partial template
        partial = temp_template_dir / "partial.yaml"
        partial.write_text("""
# Partial content
- item1: {{ value1 }}
- item2: {{ value2 }}
""")
        
        # Create main template with include
        main_template = temp_template_dir / "main_with_include.yaml"
        main_template.write_text("""
# Main Template
data:
{% include "partial.yaml" %}
""")
        
        loader = PRPTemplateLoader(temp_template_dir)
        rendered = loader.render(
            "main_with_include",
            value1="first",
            value2="second"
        )
        
        assert "item1: first" in rendered
        assert "item2: second" in rendered
    
    def test_template_macros(self, temp_template_dir):
        """Test Jinja2 macros"""
        # Create template with macro
        macro_template = temp_template_dir / "macro_test.yaml"
        macro_template.write_text("""
{% macro render_item(name, value) -%}
{{ name }}: {{ value }}
{%- endmacro %}

items:
{% for item in items %}
  - {{ render_item(item.name, item.value) }}
{% endfor %}
""")
        
        loader = PRPTemplateLoader(temp_template_dir)
        items = [
            {"name": "first", "value": "1"},
            {"name": "second", "value": "2"},
            {"name": "third", "value": "3"}
        ]
        
        rendered = loader.render("macro_test", items=items)
        
        assert "first: 1" in rendered
        assert "second: 2" in rendered
        assert "third: 3" in rendered
    
    def test_template_with_complex_data(self, loader):
        """Test rendering with complex nested data structures"""
        complex_data = {
            "project": {
                "name": "ComplexProject",
                "version": "1.0.0",
                "dependencies": [
                    {"name": "dep1", "version": "1.0"},
                    {"name": "dep2", "version": "2.0"}
                ],
                "config": {
                    "debug": True,
                    "port": 8080,
                    "features": {
                        "auth": True,
                        "cache": False
                    }
                }
            }
        }
        
        template_str = """
Project: {{ project.name }} v{{ project.version }}
Port: {{ project.config.port }}
Auth: {{ project.config.features.auth }}
Dependencies:
{% for dep in project.dependencies %}
  - {{ dep.name }}: {{ dep.version }}
{% endfor %}
"""
        
        template = loader.env.from_string(template_str)
        rendered = template.render(**complex_data)
        
        assert "ComplexProject v1.0.0" in rendered
        assert "Port: 8080" in rendered
        assert "Auth: True" in rendered
        assert "dep1: 1.0" in rendered
        assert "dep2: 2.0" in rendered
    
    def test_concurrent_template_loading(self, loader):
        """Test thread-safe template loading"""
        import concurrent.futures
        
        def load_and_render(template_name):
            template = loader.load_template(template_name)
            return loader.render(
                template_name,
                project_name="Concurrent",
                analysis_type="test",
                items=["a", "b"]
            )
        
        # Load templates concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(load_and_render, "analysis")
                for _ in range(10)
            ]
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All results should be identical
        assert len(results) == 10
        assert all(r == results[0] for r in results)
    
    def test_template_file_watching(self, temp_template_dir):
        """Test template reloading when files change"""
        # Create initial template
        test_template = temp_template_dir / "dynamic.yaml"
        test_template.write_text("Version: 1")
        
        loader = PRPTemplateLoader(temp_template_dir)
        
        # Load and render initial version
        result1 = loader.render("dynamic")
        assert "Version: 1" in result1
        
        # Modify template file
        test_template.write_text("Version: 2")
        
        # Create new loader (Jinja2 doesn't auto-reload by default)
        loader2 = PRPTemplateLoader(temp_template_dir)
        result2 = loader2.render("dynamic")
        assert "Version: 2" in result2


class TestPRPTemplateLoaderIntegration:
    """Integration tests for template loader with PRP system"""
    
    @pytest.fixture
    def complete_template_dir(self):
        """Create a complete set of PRP templates"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir)
            
            # Create all PRP template types
            templates = {
                "factory_analysis": """
# Factory Analysis PRP
project: {{ project.name }}
complexity: {{ project.complexity }}
request: {{ user_request }}

## Analysis Scope
{% for scope in analysis_scopes %}
- {{ scope }}
{% endfor %}

## Expected Outputs
{{ output_specification | default('Standard analysis outputs') }}
""",
                "factory_generation": """
# Factory Generation PRP
subagent_type: {{ subagent_type }}
project: {{ project.name }}

## Generation Context
{% if analysis_outputs %}
Previous Analysis:
{% for key, value in analysis_outputs.items() %}
  {{ key }}: {{ value }}
{% endfor %}
{% endif %}

## Templates to Generate
{% for template in templates_to_generate %}
- {{ template }}
{% endfor %}
""",
                "validation": """
# Validation PRP
scope: {{ validation_scope }}
project: {{ project.name }}

## Artifacts to Validate
{% for artifact in artifacts %}
- {{ artifact }}
{% endfor %}

## Validation Criteria
{% for criterion in criteria %}
- {{ criterion }}
{% endfor %}
""",
            }
            
            for name, content in templates.items():
                (template_dir / f"{name}.yaml").write_text(content)
            
            yield template_dir
    
    def test_complete_prp_workflow(self, complete_template_dir):
        """Test loading and rendering all PRP template types"""
        loader = PRPTemplateLoader(complete_template_dir)
        
        # Test factory analysis template
        analysis_result = loader.render(
            "factory_analysis",
            project={"name": "TestProject", "complexity": "high"},
            user_request="Create comprehensive agents",
            analysis_scopes=["architecture", "requirements", "constraints"],
            output_specification="Detailed agent specifications"
        )
        assert "TestProject" in analysis_result
        assert "high" in analysis_result
        assert "architecture" in analysis_result
        
        # Test factory generation template
        generation_result = loader.render(
            "factory_generation",
            subagent_type="agent-generator",
            project={"name": "TestProject"},
            analysis_outputs={"agents": ["frontend", "backend"], "count": 2},
            templates_to_generate=["agent.md", "config.yaml"]
        )
        assert "agent-generator" in generation_result
        assert "frontend" in generation_result
        assert "agent.md" in generation_result
        
        # Test validation template
        validation_result = loader.render(
            "validation",
            validation_scope="comprehensive",
            project={"name": "TestProject"},
            artifacts=["agent1.md", "workflow1.py"],
            criteria=["syntax", "completeness", "consistency"]
        )
        assert "comprehensive" in validation_result
        assert "agent1.md" in validation_result
        assert "syntax" in validation_result


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])