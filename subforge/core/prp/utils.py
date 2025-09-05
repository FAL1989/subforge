#!/usr/bin/env python3
"""
Utility functions for PRP generation
Contains helper functions for formatting and processing PRP data
"""

from typing import Any, Dict, List


def format_checklist(items: List[str]) -> str:
    """
    Format validation checklist as markdown
    
    Args:
        items: List of checklist items
        
    Returns:
        Formatted markdown checklist
    """
    return "\n".join(f"- [ ] {item}" for item in items)


def format_metrics(metrics: List[str]) -> str:
    """
    Format success metrics as markdown
    
    Args:
        metrics: List of success metrics
        
    Returns:
        Formatted markdown metrics list
    """
    return "\n".join(f"- {metric}" for metric in metrics)


def format_output_spec(spec: Dict[str, Any]) -> str:
    """
    Format output specification as markdown
    
    Args:
        spec: Output specification dictionary
        
    Returns:
        Formatted markdown specification
    """
    lines = []
    for key, value in spec.items():
        if isinstance(value, dict):
            lines.append(f"### {key.replace('_', ' ').title()}")
            for subkey, subvalue in value.items():
                lines.append(f"- **{subkey}**: {subvalue}")
        elif isinstance(value, list):
            lines.append(f"### {key.replace('_', ' ').title()}")
            for item in value:
                lines.append(f"- {item}")
        else:
            lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
    return "\n".join(lines)


def format_analysis_insights(analysis_outputs: Dict[str, Any]) -> str:
    """
    Format analysis outputs for prompt context
    
    Args:
        analysis_outputs: Dictionary of analysis outputs
        
    Returns:
        Formatted string of insights
    """
    if not analysis_outputs:
        return "Analysis in progress - using project profile data"
    
    insights = []
    for key, value in analysis_outputs.items():
        if isinstance(value, dict):
            insights.append(
                f"**{key.replace('_', ' ').title()}**: {len(value)} items identified"
            )
        elif isinstance(value, list):
            preview = ', '.join(map(str, value[:3]))
            if len(value) > 3:
                preview += f" (+{len(value) - 3} more)"
            insights.append(
                f"**{key.replace('_', ' ').title()}**: {preview}"
            )
        else:
            insights.append(f"**{key.replace('_', ' ').title()}**: {value}")
    
    return (
        "\n".join(insights)
        if insights
        else "Standard analysis approach will be used"
    )


def format_project_context(project_profile) -> str:
    """
    Format project profile for prompt context
    
    Args:
        project_profile: ProjectProfile instance
        
    Returns:
        Formatted project context string
    """
    return f"""- **Name**: {project_profile.name}
- **Architecture**: {project_profile.architecture_pattern.value}
- **Complexity**: {project_profile.complexity.value}  
- **Languages**: {', '.join(project_profile.technology_stack.languages)}
- **Frameworks**: {', '.join(project_profile.technology_stack.frameworks)}
- **Team Size**: {project_profile.team_size_estimate}
- **Testing**: {"Comprehensive" if project_profile.has_tests else "Basic"}
- **CI/CD**: {"Integrated" if project_profile.has_ci_cd else "Manual"}"""


def get_architecture_workflow_requirements(architecture) -> str:
    """
    Get architecture-specific workflow requirements
    
    Args:
        architecture: Architecture pattern enum
        
    Returns:
        Formatted workflow requirements string
    """
    if architecture.value == "microservices":
        return """For microservices architecture:
- **Service Development**: Independent service development and testing
- **API Contract Management**: OpenAPI specification and validation
- **Service Integration**: Inter-service communication testing
- **Deployment Coordination**: Independent deployments with dependency management
- **Monitoring & Observability**: Distributed tracing and service health monitoring"""
    
    elif architecture.value == "monolithic":
        return """For monolithic architecture:
- **Module Development**: Feature development within monolithic boundaries
- **Integration Testing**: Comprehensive system-wide testing
- **Database Migrations**: Coordinated schema changes
- **Deployment Strategy**: Blue-green or rolling deployments
- **Performance Monitoring**: System-wide performance and resource monitoring"""
    
    elif architecture.value == "serverless":
        return """For serverless architecture:
- **Function Development**: Isolated function development and testing
- **Event Management**: Event-driven communication patterns
- **API Gateway Configuration**: Request routing and rate limiting
- **Cold Start Optimization**: Performance tuning for lambda functions
- **Distributed Monitoring**: Cross-function tracing and logging"""
    
    elif architecture.value == "jamstack":
        return """For JAMstack architecture:
- **Static Site Generation**: Build-time optimization and caching
- **API Integration**: External service integration and management
- **Edge Functions**: CDN-level compute for dynamic features
- **Content Management**: Headless CMS integration
- **Performance Optimization**: Core Web Vitals and lighthouse scores"""
    
    else:
        return """For standard architecture:
- **Component Development**: Modular development practices
- **Integration Points**: Clear interface definitions and testing
- **Deployment Pipeline**: Straightforward deployment automation
- **Quality Assurance**: Comprehensive testing strategy
- **Monitoring**: Application and system monitoring"""


def get_subagent_validation_checklist(subagent_type: str) -> List[str]:
    """
    Get validation checklist for specific subagent type
    
    Args:
        subagent_type: Type of subagent
        
    Returns:
        List of validation checklist items
    """
    common_checks = [
        "Output files are generated in correct locations",
        "All generated content is syntactically valid",
        "Configuration integrates with existing project structure",
        "Documentation is comprehensive and accurate",
    ]
    
    specific_checks = {
        "claude-md-generator": [
            "CLAUDE.md follows proper structure and format",
            "Build commands are executable and accurate",
            "Agent team configuration is appropriate",
            "All project-specific sections are included",
        ],
        "agent-generator": [
            "All agents have valid YAML frontmatter",
            "Agent roles are clearly defined and non-overlapping",
            "Tool assignments are appropriate and secure",
            "System prompts are project-specific",
        ],
        "workflow-generator": [
            "Workflows are appropriate for project architecture",
            "Quality gates are measurable and enforceable",
            "Commands are executable and tested",
            "Agent coordination is clearly defined",
        ],
        "orchestrator": [
            "Orchestration patterns match project complexity",
            "Parallel execution strategies are well-defined",
            "Resource allocation is optimized",
            "Error handling and recovery procedures are documented",
        ],
    }
    
    return common_checks + specific_checks.get(subagent_type, [])


def get_subagent_success_metrics(subagent_type: str) -> List[str]:
    """
    Get success metrics for specific subagent type
    
    Args:
        subagent_type: Type of subagent
        
    Returns:
        List of success metrics
    """
    metrics_map = {
        "claude-md-generator": [
            "CLAUDE.md generation time < 30 seconds",
            "Build commands execute successfully",
            "Configuration accuracy > 95%",
            "No manual corrections required",
        ],
        "agent-generator": [
            "All agents generated within 60 seconds",
            "Agent specialization clarity score > 90%",
            "Tool assignment accuracy > 95%",
            "No configuration conflicts detected",
        ],
        "workflow-generator": [
            "Workflow generation time < 45 seconds",
            "All commands are executable",
            "Quality gates are comprehensive",
            "Agent coordination is well-defined",
        ],
        "orchestrator": [
            "Orchestration setup time < 20 seconds",
            "Parallel execution efficiency > 80%",
            "Zero deadlocks or race conditions",
            "Clear task dependency resolution",
        ],
    }
    
    return metrics_map.get(subagent_type, [
        "Generation completed within expected timeframe",
        "Output quality meets standards",
        "Integration successful with existing components",
    ])


def get_subagent_output_specification(subagent_type: str) -> Dict[str, Any]:
    """
    Get output specification for specific subagent type
    
    Args:
        subagent_type: Type of subagent
        
    Returns:
        Output specification dictionary
    """
    specs = {
        "claude-md-generator": {
            "primary_output": "CLAUDE.md",
            "location": "project_root",
            "format": "markdown",
            "sections_required": [
                "project_overview",
                "build_commands",
                "code_style",
                "architecture",
                "workflow",
                "agent_team",
            ],
            "customization_level": "high",
        },
        "agent-generator": {
            "primary_output": "agent_configurations",
            "location": ".claude/agents/",
            "format": "yaml_frontmatter_markdown",
            "agents_count": "variable_based_on_analysis",
            "customization_level": "high",
        },
        "workflow-generator": {
            "primary_output": "workflow_documentation",
            "location": "workflows/",
            "format": "markdown",
            "includes": ["processes", "commands", "quality_gates", "coordination"],
            "customization_level": "architecture_specific",
        },
        "orchestrator": {
            "primary_output": "orchestration_config",
            "location": ".claude/orchestration/",
            "format": "yaml",
            "includes": ["task_definitions", "dependencies", "execution_strategies"],
            "customization_level": "complexity_based",
        },
    }
    
    return specs.get(subagent_type, {
        "primary_output": f"{subagent_type}_configuration",
        "format": "markdown",
        "customization_level": "standard",
    })