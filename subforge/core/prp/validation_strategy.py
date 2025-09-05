#!/usr/bin/env python3
"""
Validation Strategy for PRP Generation
Handles validation and quality assurance phases
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..prp_template_loader import PRPTemplateLoader
from .base import BaseStrategy, PRP, PRPType
from .utils import format_project_context


class ValidationStrategy(BaseStrategy):
    """
    Strategy for generating validation PRPs
    
    This strategy creates PRPs focused on validation, quality assurance,
    and comprehensive testing of generated artifacts.
    """
    
    def __init__(self, workspace_dir: Path, template_loader: Optional[PRPTemplateLoader] = None):
        """
        Initialize validation strategy
        
        Args:
            workspace_dir: Path to workspace directory
            template_loader: Optional template loader for external templates
        """
        super().__init__(workspace_dir)
        self.template_loader = template_loader
    
    def get_required_context_keys(self) -> List[str]:
        """Get required context keys for validation"""
        return [
            "project_profile",
            "context_package",
            "validation_scope",
            "artifacts_to_validate"
        ]
    
    async def generate(self, context: Dict[str, Any]) -> PRP:
        """
        Generate validation PRP
        
        Args:
            context: Must contain project_profile, context_package,
                    validation_scope, and artifacts_to_validate
            
        Returns:
            Generated validation PRP
        """
        if not self.validate_context(context):
            raise ValueError(f"Missing required context keys: {self.get_required_context_keys()}")
        
        project_profile = context["project_profile"]
        context_package = context["context_package"]
        validation_scope = context["validation_scope"]
        artifacts = context["artifacts_to_validate"]
        
        prp_id = self.generate_prp_id(f"validation_{validation_scope}")
        
        # Generate execution prompt
        execution_prompt = await self._generate_execution_prompt(
            project_profile, validation_scope, artifacts
        )
        
        # Create validation checklist
        validation_checklist = self._create_validation_checklist(validation_scope, artifacts)
        
        # Create success metrics
        success_metrics = self._create_success_metrics(validation_scope)
        
        # Create output specification
        output_specification = self._create_output_specification(validation_scope)
        
        # Create PRP
        prp = PRP(
            id=prp_id,
            type=PRPType.VALIDATION_COMPREHENSIVE,
            title=f"Comprehensive Validation for {validation_scope.title()} - {project_profile.name}",
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
        self, project_profile, validation_scope: str, artifacts: List[str]
    ) -> str:
        """Generate execution prompt for validation"""
        
        if self.template_loader:
            try:
                return self.template_loader.render(
                    "validation_comprehensive",
                    project_context=format_project_context(project_profile),
                    validation_scope=validation_scope,
                    artifacts_to_validate=artifacts,
                    architecture_pattern=project_profile.architecture_pattern.value,
                    complexity=project_profile.complexity.value,
                )
            except Exception as e:
                print(f"Template rendering failed: {e}, using embedded template")
        
        # Fallback to embedded template
        return self._get_embedded_prompt(project_profile, validation_scope, artifacts)
    
    def _get_embedded_prompt(
        self, project_profile, validation_scope: str, artifacts: List[str]
    ) -> str:
        """Get embedded validation prompt"""
        artifacts_list = "\n".join(f"- {artifact}" for artifact in artifacts)
        
        return f"""# Comprehensive Validation Task

You are the SubForge Validation Specialist, responsible for comprehensive quality assurance and validation.

## Primary Objective
Perform thorough validation of generated artifacts to ensure they meet all quality standards and project requirements.

## Validation Scope
**Focus Area**: {validation_scope.replace('_', ' ').title()}

## Artifacts to Validate
{artifacts_list}

## Project Context
{format_project_context(project_profile)}

## Validation Framework

### 1. **Syntax and Structure Validation**
- Verify all files have correct syntax for their languages
- Check file structure and organization
- Validate configuration file formats
- Ensure proper encoding and line endings

### 2. **Functional Validation**
- Test that all generated commands execute correctly
- Verify integrations work as expected
- Check that dependencies are properly declared
- Validate API contracts and interfaces

### 3. **Quality Standards Validation**
- Code quality and maintainability checks
- Documentation completeness and accuracy
- Security best practices compliance
- Performance considerations validation

### 4. **Integration Validation**
- Verify compatibility with existing codebase
- Check for conflicts with current configurations
- Validate cross-component interactions
- Ensure smooth workflow integration

### 5. **Architecture Compliance**
- Confirm alignment with {project_profile.architecture_pattern.value} patterns
- Validate architectural boundaries
- Check scalability considerations
- Verify separation of concerns

## Validation Requirements

### Automated Checks
Implement automated validation for:
- Syntax validation using appropriate linters
- Unit test execution where applicable
- Configuration schema validation
- Dependency resolution checks

### Manual Review Points
Document areas requiring manual validation:
- Business logic correctness
- User experience considerations
- Documentation clarity
- Edge case handling

### Regression Testing
Ensure no existing functionality is broken:
- Run existing test suites
- Verify backward compatibility
- Check for unintended side effects
- Validate migration paths

## Output Requirements

### Validation Report
Create comprehensive `validation_report.md` with:
- **Executive Summary**: Overall validation status
- **Detailed Findings**: Item-by-item validation results
- **Issues Identified**: Problems found with severity levels
- **Recommendations**: Fixes and improvements needed
- **Quality Metrics**: Quantitative quality measurements

### Issue Tracking
For each issue found:
- Clear description of the problem
- Severity level (critical, major, minor)
- Suggested fix or workaround
- Impact assessment
- Priority recommendation

## Quality Gates
Before marking validation complete:
- All critical issues must be resolved
- Major issues must have mitigation plans
- Test coverage meets minimum thresholds
- Documentation is complete and accurate
- Security checks pass without warnings"""
    
    def _create_validation_checklist(self, scope: str, artifacts: List[str]) -> List[str]:
        """Create validation checklist based on scope and artifacts"""
        base_checks = [
            "All artifacts exist and are accessible",
            "File permissions are correctly set",
            "No syntax errors in any generated files",
            "All configurations are valid and complete",
            "Documentation is comprehensive and accurate",
        ]
        
        scope_specific = {
            "full_project": [
                "Project builds successfully",
                "All tests pass without errors",
                "No security vulnerabilities detected",
                "Performance benchmarks meet requirements",
                "Deployment procedures validated",
            ],
            "agents": [
                "Agent configurations have valid YAML frontmatter",
                "Agent roles are clearly defined",
                "Tool assignments are appropriate",
                "No overlapping responsibilities",
                "Coordination protocols are clear",
            ],
            "workflows": [
                "All workflow commands are executable",
                "Quality gates are measurable",
                "Process flows are logical",
                "Error handling is comprehensive",
                "Automation scripts work correctly",
            ],
            "configuration": [
                "All configuration files are valid",
                "Environment variables are documented",
                "Secrets management is secure",
                "Dependencies are properly declared",
                "Version constraints are appropriate",
            ],
        }
        
        specific_checks = scope_specific.get(scope, [
            "Scope-specific validation completed",
            "Quality standards met",
            "Integration points verified",
        ])
        
        # Add artifact-specific checks
        artifact_checks = [f"{artifact} validated successfully" for artifact in artifacts[:3]]
        
        return base_checks + specific_checks + artifact_checks
    
    def _create_success_metrics(self, scope: str) -> List[str]:
        """Create success metrics for validation"""
        base_metrics = [
            "Validation completed within allocated time",
            "Zero critical issues remaining",
            "All automated tests passing",
            "Documentation accuracy > 95%",
        ]
        
        scope_metrics = {
            "full_project": [
                "Build success rate = 100%",
                "Test coverage > 80%",
                "Performance within 10% of targets",
                "Security scan shows no high-risk issues",
            ],
            "agents": [
                "All agents properly configured",
                "Agent specialization clarity > 90%",
                "Tool assignment accuracy = 100%",
                "No configuration conflicts",
            ],
            "workflows": [
                "All workflows executable",
                "Process efficiency improved > 20%",
                "Quality gate coverage = 100%",
                "Automation success rate > 95%",
            ],
            "configuration": [
                "Configuration validity = 100%",
                "No missing dependencies",
                "Environment setup time < 5 minutes",
                "Zero configuration conflicts",
            ],
        }
        
        return base_metrics + scope_metrics.get(scope, [
            "Scope objectives achieved",
            "Quality targets met",
        ])
    
    def _create_output_specification(self, scope: str) -> Dict[str, Any]:
        """Create output specification for validation"""
        return {
            "primary_output": "validation_report.md",
            "location": "validation/",
            "format": "markdown",
            "report_sections": [
                "executive_summary",
                "validation_methodology",
                "detailed_findings",
                "issues_and_recommendations",
                "quality_metrics",
                "next_steps",
            ],
            "supporting_files": {
                "validation_log.txt": "Detailed validation execution log",
                "issues.json": "Structured issue tracking data",
                "metrics.json": "Quantitative validation metrics",
            },
            "validation_scope": scope,
            "severity_levels": ["critical", "major", "minor", "informational"],
            "resolution_tracking": True,
            "automated_checks": {
                "syntax": "Language-specific linters",
                "security": "Security scanning tools",
                "performance": "Performance profiling",
                "tests": "Test suite execution",
            }
        }
    
    def validate(self, prp: PRP) -> bool:
        """
        Validate validation PRP (meta!)
        
        Args:
            prp: PRP to validate
            
        Returns:
            True if valid
        """
        if not super().validate(prp):
            return False
        
        # Additional validation for validation PRPs
        if prp.type != PRPType.VALIDATION_COMPREHENSIVE:
            return False
        
        # Ensure validation-specific requirements
        if not prp.output_specification.get("report_sections"):
            return False
        
        if not prp.output_specification.get("severity_levels"):
            return False
        
        return True