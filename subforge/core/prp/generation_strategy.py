#!/usr/bin/env python3
"""
Generation Strategy for PRP Generation
Handles the generation phase of factory pattern execution
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..prp_template_loader import PRPTemplateLoader
from .base import BaseStrategy, PRP, PRPType
from .utils import (
    format_analysis_insights,
    format_project_context,
    get_architecture_workflow_requirements,
    get_subagent_output_specification,
    get_subagent_success_metrics,
    get_subagent_validation_checklist,
)


class GenerationStrategy(BaseStrategy):
    """
    Strategy for generating PRPs for factory generation phase
    
    This strategy creates PRPs for different types of subagent generation
    including claude-md, agents, workflows, and other specialized generators.
    """
    
    def __init__(self, workspace_dir: Path, template_loader: Optional[PRPTemplateLoader] = None):
        """
        Initialize generation strategy
        
        Args:
            workspace_dir: Path to workspace directory
            template_loader: Optional template loader for external templates
        """
        super().__init__(workspace_dir)
        self.template_loader = template_loader
        
        # Map of subagent types to their generation methods
        self.subagent_generators = {
            "claude-md-generator": self._generate_claude_md_prompt,
            "agent-generator": self._generate_agent_prompt,
            "workflow-generator": self._generate_workflow_prompt,
            "orchestrator": self._generate_orchestrator_prompt,
        }
    
    def get_required_context_keys(self) -> List[str]:
        """Get required context keys for generation"""
        return [
            "project_profile",
            "context_package",
            "analysis_outputs",
            "subagent_type"
        ]
    
    async def generate(self, context: Dict[str, Any]) -> PRP:
        """
        Generate factory generation PRP
        
        Args:
            context: Must contain project_profile, context_package, 
                    analysis_outputs, and subagent_type
            
        Returns:
            Generated factory generation PRP
        """
        if not self.validate_context(context):
            raise ValueError(f"Missing required context keys: {self.get_required_context_keys()}")
        
        project_profile = context["project_profile"]
        context_package = context["context_package"]
        analysis_outputs = context["analysis_outputs"]
        subagent_type = context["subagent_type"]
        
        prp_id = self.generate_prp_id(f"generation_{subagent_type}")
        
        # Get subagent-specific execution prompt
        execution_prompt = await self._get_subagent_execution_prompt(
            subagent_type, project_profile, context_package, analysis_outputs
        )
        
        # Get subagent-specific components
        validation_checklist = get_subagent_validation_checklist(subagent_type)
        success_metrics = get_subagent_success_metrics(subagent_type)
        output_specification = get_subagent_output_specification(subagent_type)
        
        # Create PRP
        prp = PRP(
            id=prp_id,
            type=PRPType.FACTORY_GENERATION,
            title=f"{subagent_type.replace('-', ' ').title()} Generation for {project_profile.name}",
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
    
    async def _get_subagent_execution_prompt(
        self,
        subagent_type: str,
        project_profile,
        context_package,
        analysis_outputs: Dict[str, Any]
    ) -> str:
        """Get execution prompt for specific subagent type"""
        
        # Use specific generator if available
        if subagent_type in self.subagent_generators:
            generator = self.subagent_generators[subagent_type]
            return await generator(project_profile, context_package, analysis_outputs)
        
        # Otherwise use generic generator
        return await self._generate_generic_prompt(
            subagent_type, project_profile, context_package, analysis_outputs
        )
    
    async def _generate_claude_md_prompt(
        self, project_profile, context_package, analysis_outputs: Dict[str, Any]
    ) -> str:
        """Generate Claude.md specific prompt"""
        
        if self.template_loader:
            try:
                return self.template_loader.render(
                    "claude_md_generator",
                    project_name=project_profile.name,
                    architecture_pattern=project_profile.architecture_pattern.value,
                    complexity=project_profile.complexity.value,
                    languages=project_profile.technology_stack.languages,
                    frameworks=project_profile.technology_stack.frameworks,
                    team_size_estimate=project_profile.team_size_estimate,
                    analysis_insights=format_analysis_insights(analysis_outputs),
                )
            except Exception as e:
                print(f"Template rendering failed: {e}, using embedded template")
        
        # Fallback to embedded template
        return self._get_embedded_claude_md_prompt(project_profile, analysis_outputs)
    
    async def _generate_agent_prompt(
        self, project_profile, context_package, analysis_outputs: Dict[str, Any]
    ) -> str:
        """Generate agent generator specific prompt"""
        
        has_api = any("api" in fw.lower() for fw in project_profile.technology_stack.frameworks)
        
        if self.template_loader:
            try:
                return self.template_loader.render(
                    "agent_generator",
                    architecture_pattern=project_profile.architecture_pattern.value,
                    languages=project_profile.technology_stack.languages,
                    has_tests=project_profile.has_tests,
                    has_api_frameworks=has_api,
                    has_ci_cd=project_profile.has_ci_cd,
                    databases=project_profile.technology_stack.databases,
                    complexity=project_profile.complexity.value,
                    analysis_insights=format_analysis_insights(analysis_outputs),
                )
            except Exception as e:
                print(f"Template rendering failed: {e}, using embedded template")
        
        # Fallback to embedded template
        return self._get_embedded_agent_prompt(project_profile, analysis_outputs, has_api)
    
    async def _generate_workflow_prompt(
        self, project_profile, context_package, analysis_outputs: Dict[str, Any]
    ) -> str:
        """Generate workflow generator specific prompt"""
        
        if self.template_loader:
            try:
                return self.template_loader.render(
                    "workflow_generator",
                    architecture_pattern=project_profile.architecture_pattern.value,
                    team_size_estimate=project_profile.team_size_estimate,
                    languages=project_profile.technology_stack.languages,
                    frameworks=project_profile.technology_stack.frameworks,
                    has_ci_cd=project_profile.has_ci_cd,
                    has_tests=project_profile.has_tests,
                    complexity=project_profile.complexity.value,
                    architecture_workflow_requirements=get_architecture_workflow_requirements(
                        project_profile.architecture_pattern
                    ),
                )
            except Exception as e:
                print(f"Template rendering failed: {e}, using embedded template")
        
        # Fallback to embedded template
        return self._get_embedded_workflow_prompt(project_profile, analysis_outputs)
    
    async def _generate_orchestrator_prompt(
        self, project_profile, context_package, analysis_outputs: Dict[str, Any]
    ) -> str:
        """Generate orchestrator specific prompt"""
        
        if self.template_loader:
            try:
                return self.template_loader.render(
                    "orchestrator",
                    project_name=project_profile.name,
                    complexity=project_profile.complexity.value,
                    team_size_estimate=project_profile.team_size_estimate,
                    architecture_pattern=project_profile.architecture_pattern.value,
                    analysis_insights=format_analysis_insights(analysis_outputs),
                )
            except Exception as e:
                print(f"Template rendering failed: {e}, using embedded template")
        
        # Fallback to embedded template
        return self._get_embedded_orchestrator_prompt(project_profile, analysis_outputs)
    
    async def _generate_generic_prompt(
        self, subagent_type: str, project_profile, context_package, analysis_outputs: Dict[str, Any]
    ) -> str:
        """Generate generic subagent prompt"""
        
        if self.template_loader:
            try:
                return self.template_loader.render(
                    "generic_subagent",
                    subagent_type=subagent_type,
                    project_context=format_project_context(project_profile),
                    architecture_pattern=project_profile.architecture_pattern.value,
                    languages=project_profile.technology_stack.languages,
                    team_size_estimate=project_profile.team_size_estimate,
                    complexity=project_profile.complexity.value,
                    analysis_insights=format_analysis_insights(analysis_outputs),
                )
            except Exception as e:
                print(f"Template rendering failed: {e}, using embedded template")
        
        # Fallback to embedded template
        return self._get_embedded_generic_prompt(subagent_type, project_profile, analysis_outputs)
    
    # Embedded templates for backward compatibility
    
    def _get_embedded_claude_md_prompt(self, project_profile, analysis_outputs: Dict[str, Any]) -> str:
        """Embedded Claude.md generator prompt"""
        return f"""# CLAUDE.md Generation Task

You are the SubForge CLAUDE.md Generator, specialized in creating comprehensive CLAUDE.md files.

## Primary Objective
Generate a complete, project-specific CLAUDE.md file that optimizes Claude Code for this project.

## Project Context
{format_project_context(project_profile)}

## Analysis Insights
{format_analysis_insights(analysis_outputs)}

## Generation Requirements

### 1. **Project Overview Section**
- Clear, concise project description
- Key objectives and goals
- Target users or use cases
- Technology stack summary

### 2. **Build Commands Section**
- Project-specific build commands
- Environment setup instructions
- Testing commands tailored to the project
- Deployment commands if applicable

### 3. **Code Style Section**
- Language-specific style guidelines
- Framework conventions
- Formatting and linting rules
- Documentation standards

### 4. **Architecture Section**
- Architecture guidelines
- Key architectural decisions
- Component interactions
- Scalability considerations

### 5. **Workflow Section**
- Development process definition
- Git workflow recommendations
- Code review process
- Release management

### 6. **Agent Team Configuration**
- List of recommended agents based on analysis
- Agent roles and responsibilities
- Coordination protocols
- Auto-activation rules

## Quality Standards
The generated CLAUDE.md must:
- Be immediately usable without modifications
- Include accurate build commands that work
- Provide clear guidance for all team members
- Integrate seamlessly with existing project structure
- Follow Claude Code best practices"""
    
    def _get_embedded_agent_prompt(
        self, project_profile, analysis_outputs: Dict[str, Any], has_api: bool
    ) -> str:
        """Embedded agent generator prompt"""
        return f"""# Agent Generation Task

You are the SubForge Agent Generator, specialized in creating optimal teams of Claude Code subagents.

## Primary Objective
Generate a complete set of specialized subagents for this {project_profile.architecture_pattern.value} project.

## Project Analysis Summary
{format_analysis_insights(analysis_outputs)}

## Agent Generation Strategy

### 1. **Core Agent Team**
Based on project analysis, generate these essential agents:
- **Backend Developer**: For {', '.join(project_profile.technology_stack.languages)} development
- **Code Reviewer**: For quality assurance and standards compliance
- **Test Engineer**: For {"comprehensive" if project_profile.has_tests else "basic"} testing strategy

### 2. **Specialized Agents**
Based on project characteristics, include:
{"- **API Developer**: For REST/GraphQL API development" if has_api else ""}
{"- **DevOps Engineer**: For CI/CD and deployment" if project_profile.has_ci_cd else ""}
{"- **Database Specialist**: For data modeling and optimization" if project_profile.technology_stack.databases else ""}
{"- **Performance Optimizer**: For complex system optimization" if project_profile.complexity.value == "complex" else ""}

### 3. **Agent Configuration Requirements**

For each generated agent:

#### YAML Frontmatter
```yaml
---
name: agent-name
description: Specific role and expertise
model: opus|sonnet|haiku
tools: [appropriate tools list]
---
```

#### System Prompt Structure
- **Role Definition**: Clear specialization and expertise
- **Project Context**: Technology stack and architecture awareness  
- **Responsibilities**: Specific tasks and domains
- **Coordination**: How agent works with others
- **Quality Standards**: Project-specific standards and practices

## Quality Requirements
Each generated agent must:
- Have a clear, non-overlapping specialization
- Include project-specific knowledge
- Coordinate effectively with other agents
- Follow security best practices
- Be immediately usable in the project context"""
    
    def _get_embedded_workflow_prompt(self, project_profile, analysis_outputs: Dict[str, Any]) -> str:
        """Embedded workflow generator prompt"""
        return f"""# Workflow Generation Task

You are the SubForge Workflow Generator, specialized in creating custom development workflows.

## Primary Objective
Generate comprehensive development workflows for this {project_profile.architecture_pattern.value} project.

## Project Workflow Context
- **Architecture**: {project_profile.architecture_pattern.value}
- **Team Size**: {project_profile.team_size_estimate}
- **Tech Stack**: {', '.join(project_profile.technology_stack.languages)}
- **CI/CD**: {"Integrated" if project_profile.has_ci_cd else "Manual"}
- **Testing**: {"Comprehensive" if project_profile.has_tests else "Basic"}

## Workflow Generation Requirements

### 1. **Development Workflows**
Create workflows for:
- **Feature Development**: End-to-end feature implementation
- **Bug Fix Workflow**: Rapid response and resolution  
- **Code Review Process**: Quality assurance and knowledge sharing
- **Testing Strategy**: Architecture-appropriate testing
- **Release Management**: Deployment process

### 2. **Architecture-Specific Patterns**
{get_architecture_workflow_requirements(project_profile.architecture_pattern)}

### 3. **Quality Gates**
Define measurable quality checkpoints:
- Code commit gates
- Pull request gates
- Pre-deployment gates
- Post-deployment gates

### 4. **Automation Commands**
Generate project-specific commands for common tasks

### 5. **Agent Coordination Workflows**
Design how agents work together effectively

## Output Requirements
Generate comprehensive workflow documentation including:
- Step-by-step process definitions
- Executable commands and scripts
- Quality gate specifications  
- Agent coordination protocols
- Emergency procedures and rollback plans"""
    
    def _get_embedded_orchestrator_prompt(self, project_profile, analysis_outputs: Dict[str, Any]) -> str:
        """Embedded orchestrator prompt"""
        return f"""# Orchestrator Configuration Task

You are the SubForge Orchestrator Generator, specialized in creating orchestration configurations.

## Primary Objective
Generate orchestration configuration for coordinating multiple agents in this {project_profile.complexity.value} project.

## Project Context
{format_project_context(project_profile)}

## Analysis Insights
{format_analysis_insights(analysis_outputs)}

## Orchestration Requirements

### 1. **Task Distribution Strategy**
- Define how tasks are distributed among agents
- Set up parallel execution patterns
- Configure task dependencies

### 2. **Resource Management**
- Agent allocation strategies
- Load balancing approaches
- Resource optimization techniques

### 3. **Communication Patterns**
- Inter-agent communication protocols
- Event-driven coordination
- State synchronization methods

### 4. **Error Handling**
- Failure detection mechanisms
- Recovery procedures
- Rollback strategies

### 5. **Monitoring & Metrics**
- Performance tracking
- Success rate monitoring
- Bottleneck identification

## Quality Requirements
The orchestration configuration must:
- Enable efficient parallel execution
- Prevent deadlocks and race conditions
- Provide clear error recovery paths
- Scale with project complexity
- Integrate with existing workflows"""
    
    def _get_embedded_generic_prompt(
        self, subagent_type: str, project_profile, analysis_outputs: Dict[str, Any]
    ) -> str:
        """Embedded generic subagent prompt"""
        return f"""# {subagent_type.replace('-', ' ').title()} Generation Task

You are a SubForge factory subagent specialized in {subagent_type.replace('-', ' ')}.

## Project Context
{format_project_context(project_profile)}

## Analysis Context  
{format_analysis_insights(analysis_outputs)}

## Generation Objectives
Generate high-quality, project-specific configurations that:
- Align with {project_profile.architecture_pattern.value} architecture
- Support {', '.join(project_profile.technology_stack.languages)} development
- Scale for {project_profile.team_size_estimate} team members
- Meet {project_profile.complexity.value} complexity requirements

## Quality Standards
Ensure all outputs:
- Are immediately usable without modification
- Follow project-specific conventions
- Integrate seamlessly with other components
- Include comprehensive documentation
- Meet established quality criteria"""
    
    def validate(self, prp: PRP) -> bool:
        """
        Validate generation PRP
        
        Args:
            prp: PRP to validate
            
        Returns:
            True if valid
        """
        if not super().validate(prp):
            return False
        
        # Additional validation for generation
        if prp.type != PRPType.FACTORY_GENERATION:
            return False
        
        # Ensure generation-specific requirements
        if not prp.output_specification:
            return False
        
        return True