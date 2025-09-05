#!/usr/bin/env python3
"""
PRP Template Loader - Manages external Jinja2 templates for PRP generation
"""

from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound


class PRPTemplateLoader:
    """
    Manages loading and rendering of PRP templates using Jinja2
    
    This class provides a clean interface for loading external YAML templates
    with Jinja2 variable substitution, enabling maintainable and reusable
    prompt generation.
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the template loader with the templates directory
        
        Args:
            template_dir: Path to templates directory. If None, uses default location
        """
        if template_dir is None:
            # Default to subforge/templates/prp directory
            template_dir = Path(__file__).parent.parent / "templates" / "prp"
        
        if not template_dir.exists():
            raise ValueError(f"Template directory does not exist: {template_dir}")
        
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        # Register custom filters
        self._register_custom_filters()
    
    def _register_custom_filters(self):
        """Register custom Jinja2 filters for template processing"""
        
        def replace_filter(value: str, old: str, new: str) -> str:
            """Replace substring in string"""
            return value.replace(old, new)
        
        def title_filter(value: str) -> str:
            """Convert string to title case"""
            return value.title()
        
        self.env.filters['replace'] = replace_filter
        self.env.filters['title'] = title_filter
    
    def load_template(self, name: str) -> Template:
        """
        Load a template by name
        
        Args:
            name: Template name (without .yaml extension)
            
        Returns:
            Jinja2 Template object
            
        Raises:
            TemplateNotFound: If template doesn't exist
        """
        try:
            return self.env.get_template(f"{name}.yaml")
        except TemplateNotFound as e:
            raise TemplateNotFound(
                f"Template '{name}.yaml' not found in {self.template_dir}"
            ) from e
    
    def render(self, template_name: str, **kwargs) -> str:
        """
        Load and render a template with given variables
        
        Args:
            template_name: Name of template to render
            **kwargs: Variables to pass to template
            
        Returns:
            Rendered template as string
        """
        template = self.load_template(template_name)
        return template.render(**kwargs)
    
    def validate_template(self, name: str) -> bool:
        """
        Check if a template exists and is valid
        
        Args:
            name: Template name to validate
            
        Returns:
            True if template exists and is valid
        """
        try:
            self.load_template(name)
            return True
        except TemplateNotFound:
            return False
    
    def list_templates(self) -> list[str]:
        """
        List all available template names
        
        Returns:
            List of template names (without extensions)
        """
        templates = []
        for template_file in self.template_dir.glob("*.yaml"):
            templates.append(template_file.stem)
        return sorted(templates)
    
    def get_template_variables(self, name: str) -> set[str]:
        """
        Extract all variables used in a template
        
        Args:
            name: Template name
            
        Returns:
            Set of variable names used in template
        """
        template = self.load_template(name)
        ast = self.env.parse(template.source)
        return {node.name for node in ast.find_all(self.env.get('Name'))}


def create_template_loader(template_dir: Optional[Path] = None) -> PRPTemplateLoader:
    """
    Factory function to create PRPTemplateLoader instance
    
    Args:
        template_dir: Optional path to templates directory
        
    Returns:
        Configured PRPTemplateLoader instance
    """
    return PRPTemplateLoader(template_dir)