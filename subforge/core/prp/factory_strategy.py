#!/usr/bin/env python3
"""
Factory Analysis Strategy for PRP Generation
Handles the analysis phase of factory pattern execution
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..prp_template_loader import PRPTemplateLoader
from .base import BaseStrategy, PRP, PRPType
from .utils import format_analysis_insights, format_project_context


class FactoryAnalysisStrategy(BaseStrategy):
    """
    Strategy for generating PRPs for factory analysis phase
    
    This strategy creates comprehensive analysis PRPs that examine project
    structure, technology stack, and requirements to guide subsequent
    factory generation phases.
    """
    
    def __init__(self, workspace_dir: Path, template_loader: Optional[PRPTemplateLoader] = None):
        """
        Initialize factory analysis strategy
        
        Args:
            workspace_dir: Path to workspace directory
            template_loader: Optional template loader for external templates
        """
        super().__init__(workspace_dir)
        self.template_loader = template_loader
    
    def get_required_context_keys(self) -> List[str]:
        """Get required context keys for factory analysis"""
        return [
            "project_profile",
            "context_package",
            "user_request"
        ]
    
    async def generate(self, context: Dict[str, Any]) -> PRP:
        """
        Generate factory analysis PRP
        
        Args:
            context: Must contain project_profile, context_package, and user_request
            
        Returns:
            Generated factory analysis PRP
        """
        if not self.validate_context(context):
            raise ValueError(f"Missing required context keys: {self.get_required_context_keys()}")
        
        project_profile = context["project_profile"]
        context_package = context["context_package"]
        user_request = context["user_request"]
        
        prp_id = self.generate_prp_id("analysis")
        
        # Generate execution prompt
        execution_prompt = await self._generate_execution_prompt(
            project_profile, context_package, user_request
        )
        
        # Create validation checklist
        validation_checklist = self._create_validation_checklist()
        
        # Create success metrics
        success_metrics = self._create_success_metrics()
        
        # Create output specification
        output_specification = self._create_output_specification()
        
        # Create PRP
        prp = PRP(
            id=prp_id,
            type=PRPType.FACTORY_ANALYSIS,
            title=f"Factory Analysis for {project_profile.name}",
            context_package=context_package,
            execution_prompt=execution_prompt,
            validation_checklist=validation_checklist,
            success_metrics=success_metrics,
            output_specification=output_specification,
            created_at=datetime.now(),
        )
        
        # Save PRP
        self.save_prp(prp)
        
        return prp
    
    async def _generate_execution_prompt(
        self, project_profile, context_package, user_request: str
    ) -> str:
        """Generate execution prompt for factory analysis"""
        
        if self.template_loader:
            try:
                return self.template_loader.render(
                    "factory_analysis",
                    user_request=user_request,
                    languages=project_profile.technology_stack.languages,
                    frameworks=project_profile.technology_stack.frameworks,
                    architecture_pattern=project_profile.architecture_pattern.value,
                    complexity=project_profile.complexity.value,
                    team_size_estimate=project_profile.team_size_estimate,
                    has_ci_cd=project_profile.has_ci_cd,
                    has_tests=project_profile.has_tests,
                )
            except Exception as e:
                print(f"Template rendering failed: {e}, using embedded template")
        
        # Fallback to embedded template
        return self._get_embedded_prompt(project_profile, context_package, user_request)
    
    def _get_embedded_prompt(self, project_profile, context_package, user_request: str) -> str:
        """Get embedded factory analysis prompt"""
        return f"""# Factory Analysis Task

You are the SubForge Project Analyzer, a specialized agent responsible for deep project analysis and requirement gathering.

## Primary Objective
Perform comprehensive analysis of the project to enable optimal factory configuration generation.

## User Request Context
**Original Request**: {user_request}

## Analysis Framework

### 1. **Project Structure Analysis**
- Examine the complete project directory structure
- Identify entry points, configuration files, and key modules
- Map dependencies and relationships between components
- Document any unusual or project-specific patterns

### 2. **Technology Stack Deep Dive**
- Validate detected technologies: {', '.join(project_profile.technology_stack.languages)}
- Identify specific versions and configurations
- Analyze framework usage patterns: {', '.join(project_profile.technology_stack.frameworks)}
- Document build tools, package managers, and deployment tools

### 3. **Architecture Pattern Verification**
- Confirm architecture pattern: {project_profile.architecture_pattern.value}
- Identify architectural boundaries and interfaces
- Map data flow and communication patterns
- Document scalability and performance considerations

### 4. **Team and Workflow Analysis**
- Assess project complexity: {project_profile.complexity.value}
- Recommend team size: Currently estimated at {project_profile.team_size_estimate}
- Identify collaboration patterns and tools
- Analyze development workflow requirements

### 5. **Integration Requirements**
- CI/CD integration needs: {"Required" if project_profile.has_ci_cd else "Not detected"}
- Testing strategy requirements: {"Comprehensive" if project_profile.has_tests else "Basic"}
- Deployment and monitoring needs
- Security and compliance considerations

## Required Analysis Outputs

### Project Analysis Document
Create comprehensive `project_analysis.md` with:
- **Executive Summary**: Key findings and recommendations
- **Technical Architecture**: Detailed architecture documentation  
- **Technology Stack**: Complete stack with versions and usage patterns
- **Development Workflow**: Recommended processes and tools
- **Team Recommendations**: Optimal team composition and size
- **Integration Plan**: CI/CD, monitoring, and deployment strategy
- **Quality Standards**: Testing, security, and performance requirements

### Requirements Refinement
Based on analysis, refine the original user request with:
- Specific technical requirements discovered
- Architecture-specific considerations
- Team collaboration needs
- Quality and compliance requirements
- Timeline and complexity estimates

## Context Integration
Leverage the provided context package to:
- Use relevant examples from similar projects
- Apply proven patterns for the detected architecture
- Reference best practices for the technology stack
- Validate recommendations against success criteria

## Quality Gates
Before completing analysis, ensure:
- All major project components are documented
- Technology stack is comprehensively analyzed
- Architecture pattern is validated with evidence
- Team and workflow recommendations are specific
- Integration requirements are clearly defined

This analysis will serve as the foundation for all subsequent factory phases."""
    
    def _create_validation_checklist(self) -> List[str]:
        """Create validation checklist for factory analysis"""
        return [
            "Project structure is completely mapped and documented",
            "All technologies are identified with specific versions",
            "Architecture pattern is validated with concrete evidence",
            "Team size and workflow recommendations are specific",
            "Integration requirements are clearly documented",
            "Quality standards are defined and measurable",
            "Analysis provides clear guidance for template selection",
            "All findings are backed by project evidence",
            "Dependencies and external services are identified",
            "Security considerations are addressed",
            "Performance requirements are documented",
            "Scalability needs are assessed",
        ]
    
    def _create_success_metrics(self) -> List[str]:
        """Create success metrics for factory analysis"""
        return [
            "Analysis completion time < 3 minutes",
            "All major project components identified",
            "Technology stack accuracy > 95%",
            "Architecture pattern correctly classified",
            "Actionable team recommendations provided",
            "Clear template selection criteria established",
            "Integration points fully documented",
            "Quality requirements clearly defined",
            "Risk assessment completed",
            "Workflow recommendations are executable",
        ]
    
    def _create_output_specification(self) -> Dict[str, Any]:
        """Create output specification for factory analysis"""
        return {
            "required_files": {
                "project_analysis.md": "Comprehensive project analysis document",
                "requirements_refined.md": "Enhanced requirements based on analysis",
                "template_criteria.json": "Criteria for template selection",
                "architecture_map.md": "Visual and textual architecture documentation",
            },
            "analysis_sections": [
                "executive_summary",
                "technical_architecture",
                "technology_stack",
                "workflow_analysis",
                "team_structure",
                "integration_requirements",
                "quality_standards",
                "risk_assessment",
            ],
            "analysis_depth": "comprehensive",
            "documentation_level": "detailed",
            "evidence_required": True,
            "recommendations_specificity": "high",
            "validation_requirements": {
                "code_samples": "Include relevant code examples",
                "configuration_files": "Reference actual project configs",
                "dependency_analysis": "Full dependency tree documentation",
            }
        }
    
    def validate(self, prp: PRP) -> bool:
        """
        Validate factory analysis PRP
        
        Args:
            prp: PRP to validate
            
        Returns:
            True if valid
        """
        if not super().validate(prp):
            return False
        
        # Additional validation for factory analysis
        if prp.type != PRPType.FACTORY_ANALYSIS:
            return False
        
        # Ensure analysis-specific requirements
        if not prp.output_specification.get("required_files"):
            return False
        
        if len(prp.validation_checklist) < 8:
            return False
        
        return True