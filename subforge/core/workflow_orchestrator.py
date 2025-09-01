#!/usr/bin/env python3
"""
SubForge Workflow Orchestrator
Coordinates the multi-phase subagent factory workflow based on proven patterns
"""

import asyncio
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

from .project_analyzer import ProjectAnalyzer, ProjectProfile


class WorkflowPhase(Enum):
    REQUIREMENTS = "requirements"
    ANALYSIS = "analysis"
    SELECTION = "selection"
    GENERATION = "generation"
    INTEGRATION = "integration"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"


class PhaseStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseResult:
    """Result from executing a workflow phase"""
    phase: WorkflowPhase
    status: PhaseStatus
    duration: float
    outputs: Dict[str, Any]
    errors: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "phase": self.phase.value,
            "status": self.status.value,
            "duration": self.duration,
            "outputs": self.outputs,
            "errors": self.errors,
            "metadata": self.metadata
        }


@dataclass
class WorkflowContext:
    """Context object that flows through all workflow phases"""
    project_id: str
    user_request: str
    project_path: str
    communication_dir: Path
    phase_results: Dict[WorkflowPhase, PhaseResult]
    project_profile: Optional[ProjectProfile]
    template_selections: Dict[str, Any]
    generated_configurations: Dict[str, Any]
    deployment_plan: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "project_id": self.project_id,
            "user_request": self.user_request,
            "project_path": self.project_path,
            "communication_dir": str(self.communication_dir),
            "phase_results": {phase.value: result.to_dict() for phase, result in self.phase_results.items()},
            "project_profile": self.project_profile.to_dict() if self.project_profile else None,
            "template_selections": self.template_selections,
            "generated_configurations": self.generated_configurations,
            "deployment_plan": self.deployment_plan
        }


class SubagentExecutor:
    """Handles execution of individual subagents within phases"""
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.available_subagents = self._discover_subagents()
    
    def _discover_subagents(self) -> Dict[str, Path]:
        """Discover available subagent templates"""
        subagents = {}
        
        if self.templates_dir.exists():
            for template_file in self.templates_dir.glob("*.md"):
                subagent_name = template_file.stem
                subagents[subagent_name] = template_file
        
        return subagents
    
    async def execute_subagent(self, subagent_name: str, context: WorkflowContext, 
                              phase: WorkflowPhase, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific subagent with given inputs"""
        print(f"    🤖 Executing subagent: {subagent_name}")
        
        if subagent_name not in self.available_subagents:
            raise ValueError(f"Subagent '{subagent_name}' not found in templates")
        
        # For now, this is a simulation - in real implementation, this would
        # invoke the actual Claude Code subagent via MCP or Claude API
        
        # Simulate different execution times and outputs based on subagent type
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # Generate mock outputs based on subagent type and phase
        outputs = self._generate_mock_outputs(subagent_name, phase, inputs, context)
        
        return outputs
    
    def _generate_mock_outputs(self, subagent_name: str, phase: WorkflowPhase, 
                              inputs: Dict[str, Any], context: WorkflowContext) -> Dict[str, Any]:
        """Generate mock outputs for testing - replace with actual subagent execution"""
        
        base_outputs = {
            "subagent": subagent_name,
            "phase": phase.value,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        
        if phase == WorkflowPhase.ANALYSIS:
            if subagent_name == "project-analyzer":
                return {
                    **base_outputs,
                    "analysis_report": f"Comprehensive analysis of {context.project_path}",
                    "technology_stack": context.project_profile.technology_stack.to_dict() if context.project_profile else {},
                    "complexity_assessment": "medium",
                    "recommendations": ["Use React for frontend", "Implement CI/CD pipeline"]
                }
        
        elif phase == WorkflowPhase.SELECTION:
            if subagent_name == "template-selector":
                return {
                    **base_outputs,
                    "selected_templates": [
                        {"name": "frontend-developer", "score": 0.95, "reason": "React project detected"},
                        {"name": "backend-developer", "score": 0.87, "reason": "API endpoints found"},
                        {"name": "code-reviewer", "score": 1.0, "reason": "Always recommended"}
                    ],
                    "template_customizations": {
                        "frontend-developer": {"framework": "react", "typescript": True},
                        "backend-developer": {"framework": "fastapi", "database": "postgresql"}
                    }
                }
        
        elif phase == WorkflowPhase.GENERATION:
            generation_outputs = {
                "claude-md-generator": {
                    **base_outputs,
                    "claude_md_content": self._generate_claude_md_content(context),
                    "custom_commands": ["/test-all", "/deploy", "/review-code"],
                    "workflow_rules": ["Auto-activate frontend dev for .tsx files", "Require review before merge"]
                },
                "agent-generator": {
                    **base_outputs,
                    "generated_agents": [
                        {"name": "frontend-developer", "customized": True, "tools": ["read", "write", "bash"]},
                        {"name": "backend-developer", "customized": True, "tools": ["read", "write", "bash", "grep"]}
                    ],
                    "agent_configurations": "Specialized configurations for detected tech stack"
                },
                "workflow-generator": {
                    **base_outputs,
                    "workflows": [
                        {"name": "feature-development", "steps": ["analyze", "implement", "test", "review"]},
                        {"name": "bug-fix", "steps": ["diagnose", "fix", "test", "deploy"]}
                    ],
                    "commands": {
                        "/test-all": "Run comprehensive test suite",
                        "/deploy-staging": "Deploy to staging environment", 
                        "/review-pr": "Automated PR review process"
                    }
                }
            }
            return generation_outputs.get(subagent_name, base_outputs)
        
        elif phase == WorkflowPhase.VALIDATION:
            if subagent_name == "deployment-validator":
                return {
                    **base_outputs,
                    "validation_results": {
                        "syntax_check": "passed",
                        "semantic_check": "passed",
                        "security_check": "passed",
                        "integration_check": "passed"
                    },
                    "deployment_readiness": True,
                    "rollback_plan": "Automated rollback to previous configuration available"
                }
        
        return base_outputs
    
    def _generate_claude_md_content(self, context: WorkflowContext) -> str:
        """Generate sample CLAUDE.md content"""
        project_name = Path(context.project_path).name
        tech_stack = context.project_profile.technology_stack if context.project_profile else None
        
        return f"""# {project_name}

## Project Overview
{context.user_request}

## Technology Stack
Languages: {', '.join(tech_stack.languages) if tech_stack else 'Not detected'}
Frameworks: {', '.join(tech_stack.frameworks) if tech_stack else 'Not detected'}

## Available Subagents
- @frontend-developer - UI/UX development and optimization
- @backend-developer - Server-side logic and API development  
- @code-reviewer - Code quality and best practices enforcement

## Workflow Commands
- /test-all - Run comprehensive test suite
- /deploy-staging - Deploy to staging environment
- /review-code - Comprehensive code review

## Development Guidelines
- Follow project coding standards
- Write tests for all new features
- Use semantic commit messages
- Request code review before merging

Generated by SubForge v1.0 🚀
"""


class WorkflowOrchestrator:
    """
    Main orchestrator that coordinates the entire SubForge workflow
    Based on proven patterns from AI Agent Factory
    """
    
    def __init__(self, templates_dir: Optional[Path] = None, workspace_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or Path(__file__).parent.parent / "templates"
        self.workspace_dir = workspace_dir or Path.cwd() / ".subforge"
        self.workspace_dir.mkdir(exist_ok=True)
        
        self.project_analyzer = ProjectAnalyzer()
        self.subagent_executor = SubagentExecutor(self.templates_dir)
        
        # Define workflow phases with their subagents
        self.phase_definitions = {
            WorkflowPhase.REQUIREMENTS: {
                "subagents": [],  # Manual phase - user input
                "parallel": False,
                "description": "Gather and clarify requirements"
            },
            WorkflowPhase.ANALYSIS: {
                "subagents": ["project-analyzer"],
                "parallel": False,
                "description": "Deep project analysis and understanding"
            },
            WorkflowPhase.SELECTION: {
                "subagents": ["template-selector"],
                "parallel": False,
                "description": "Intelligent template selection and matching"
            },
            WorkflowPhase.GENERATION: {
                "subagents": ["claude-md-generator", "agent-generator", "workflow-generator"],
                "parallel": True,
                "description": "Parallel generation of configurations"
            },
            WorkflowPhase.INTEGRATION: {
                "subagents": [],  # Handled by orchestrator
                "parallel": False,
                "description": "Integration of generated components"
            },
            WorkflowPhase.VALIDATION: {
                "subagents": ["deployment-validator"],
                "parallel": False,
                "description": "Comprehensive validation and testing"
            },
            WorkflowPhase.DEPLOYMENT: {
                "subagents": [],  # Handled by orchestrator
                "parallel": False,
                "description": "Final deployment and configuration"
            }
        }
    
    async def execute_workflow(self, user_request: str, project_path: str) -> WorkflowContext:
        """
        Main workflow execution method
        Orchestrates all phases from requirements to deployment
        """
        print(f"🚀 Starting SubForge workflow for: {Path(project_path).name}")
        print(f"📝 Request: {user_request}")
        print("="*60)
        
        # Initialize workflow context
        context = self._initialize_context(user_request, project_path)
        
        try:
            # Execute each phase in sequence
            for phase in WorkflowPhase:
                print(f"\n🔄 Phase {phase.value.upper()}: {self.phase_definitions[phase]['description']}")
                
                phase_result = await self._execute_phase(phase, context)
                context.phase_results[phase] = phase_result
                
                if phase_result.status == PhaseStatus.FAILED:
                    print(f"❌ Phase {phase.value} failed. Stopping workflow.")
                    break
                
                print(f"✅ Phase {phase.value} completed in {phase_result.duration:.2f}s")
            
            # Final workflow summary
            self._print_workflow_summary(context)
            
            # Save workflow context
            await self._save_workflow_context(context)
            
            return context
            
        except Exception as e:
            print(f"💥 Workflow execution failed: {e}")
            # TODO: Implement proper error recovery
            raise
    
    def _initialize_context(self, user_request: str, project_path: str) -> WorkflowContext:
        """Initialize workflow context with basic information"""
        project_id = f"subforge_{int(datetime.now().timestamp())}"
        communication_dir = self.workspace_dir / project_id
        communication_dir.mkdir(parents=True, exist_ok=True)
        
        return WorkflowContext(
            project_id=project_id,
            user_request=user_request,
            project_path=str(Path(project_path).resolve()),
            communication_dir=communication_dir,
            phase_results={},
            project_profile=None,
            template_selections={},
            generated_configurations={},
            deployment_plan={}
        )
    
    async def _execute_phase(self, phase: WorkflowPhase, context: WorkflowContext) -> PhaseResult:
        """Execute a specific workflow phase"""
        start_time = asyncio.get_event_loop().time()
        phase_def = self.phase_definitions[phase]
        
        try:
            # Create phase-specific directory
            phase_dir = context.communication_dir / phase.value
            phase_dir.mkdir(exist_ok=True)
            
            outputs = {}
            errors = []
            
            if phase == WorkflowPhase.REQUIREMENTS:
                outputs = await self._handle_requirements_phase(context)
            
            elif phase == WorkflowPhase.ANALYSIS:
                outputs = await self._handle_analysis_phase(context, phase_dir)
            
            elif phase == WorkflowPhase.SELECTION:
                outputs = await self._handle_selection_phase(context, phase_dir)
            
            elif phase == WorkflowPhase.GENERATION:
                outputs = await self._handle_generation_phase(context, phase_dir)
            
            elif phase == WorkflowPhase.INTEGRATION:
                outputs = await self._handle_integration_phase(context, phase_dir)
            
            elif phase == WorkflowPhase.VALIDATION:
                outputs = await self._handle_validation_phase(context, phase_dir)
            
            elif phase == WorkflowPhase.DEPLOYMENT:
                outputs = await self._handle_deployment_phase(context, phase_dir)
            
            duration = asyncio.get_event_loop().time() - start_time
            
            return PhaseResult(
                phase=phase,
                status=PhaseStatus.COMPLETED,
                duration=duration,
                outputs=outputs,
                errors=errors,
                metadata={"subagents": phase_def["subagents"]}
            )
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            return PhaseResult(
                phase=phase,
                status=PhaseStatus.FAILED,
                duration=duration,
                outputs={},
                errors=[str(e)],
                metadata={}
            )
    
    async def _handle_requirements_phase(self, context: WorkflowContext) -> Dict[str, Any]:
        """Handle requirements gathering phase"""
        # In a real implementation, this might involve interactive prompts
        # or additional clarifying questions
        return {
            "requirements_confirmed": True,
            "user_request": context.user_request,
            "project_path": context.project_path
        }
    
    async def _handle_analysis_phase(self, context: WorkflowContext, phase_dir: Path) -> Dict[str, Any]:
        """Handle project analysis phase"""
        print("    🔍 Running comprehensive project analysis...")
        
        # Run project analysis
        context.project_profile = await self.project_analyzer.analyze_project(context.project_path)
        
        # Save analysis to markdown file
        analysis_file = phase_dir / "project_analysis.md"
        with open(analysis_file, 'w') as f:
            f.write(self._format_analysis_markdown(context.project_profile))
        
        return {
            "project_profile": context.project_profile.to_dict(),
            "analysis_file": str(analysis_file)
        }
    
    async def _handle_selection_phase(self, context: WorkflowContext, phase_dir: Path) -> Dict[str, Any]:
        """Handle template selection phase"""
        print("    🎯 Selecting optimal templates...")
        
        # Mock template selection - in real implementation would use ML-based selector
        if context.project_profile:
            selected_templates = context.project_profile.recommended_subagents
        else:
            selected_templates = ["code-reviewer"]
        
        context.template_selections = {
            "selected_templates": selected_templates,
            "selection_reasons": {
                template: f"Selected for {template} capabilities" for template in selected_templates
            }
        }
        
        # Save selection to markdown file
        selection_file = phase_dir / "template_selection.md"
        with open(selection_file, 'w') as f:
            f.write(self._format_selection_markdown(context.template_selections))
        
        return context.template_selections
    
    async def _handle_generation_phase(self, context: WorkflowContext, phase_dir: Path) -> Dict[str, Any]:
        """Handle parallel generation phase"""
        print("    ⚡ Running parallel generation...")
        
        # Execute generation subagents in parallel
        generation_tasks = []
        for subagent_name in self.phase_definitions[WorkflowPhase.GENERATION]["subagents"]:
            task = self.subagent_executor.execute_subagent(
                subagent_name, 
                context, 
                WorkflowPhase.GENERATION,
                {"templates": context.template_selections}
            )
            generation_tasks.append(task)
        
        # Wait for all generation tasks to complete
        results = await asyncio.gather(*generation_tasks, return_exceptions=True)
        
        # Process results
        outputs = {}
        for i, result in enumerate(results):
            subagent_name = self.phase_definitions[WorkflowPhase.GENERATION]["subagents"][i]
            if isinstance(result, Exception):
                outputs[f"{subagent_name}_error"] = str(result)
            else:
                outputs[subagent_name] = result
                
                # Save individual results to files
                result_file = phase_dir / f"{subagent_name}_output.md"
                with open(result_file, 'w') as f:
                    f.write(json.dumps(result, indent=2))
        
        context.generated_configurations = outputs
        return outputs
    
    async def _handle_integration_phase(self, context: WorkflowContext, phase_dir: Path) -> Dict[str, Any]:
        """Handle integration of generated components"""
        print("    🔗 Integrating generated components...")
        
        # Mock integration logic
        integration_result = {
            "claude_md_integrated": True,
            "subagents_integrated": True,
            "workflows_integrated": True,
            "conflicts_resolved": 0
        }
        
        return integration_result
    
    async def _handle_validation_phase(self, context: WorkflowContext, phase_dir: Path) -> Dict[str, Any]:
        """Handle validation phase"""
        print("    ✅ Validating generated configuration...")
        
        # Execute validation subagent
        validation_result = await self.subagent_executor.execute_subagent(
            "deployment-validator",
            context,
            WorkflowPhase.VALIDATION,
            {"configurations": context.generated_configurations}
        )
        
        return validation_result
    
    async def _handle_deployment_phase(self, context: WorkflowContext, phase_dir: Path) -> Dict[str, Any]:
        """Handle final deployment phase"""
        print("    🚀 Deploying configuration...")
        
        # Mock deployment logic
        deployment_result = {
            "configuration_deployed": True,
            "subagents_activated": len(context.template_selections.get("selected_templates", [])),
            "deployment_location": str(Path(context.project_path) / ".claude"),
            "success": True
        }
        
        context.deployment_plan = deployment_result
        return deployment_result
    
    def _format_analysis_markdown(self, profile: ProjectProfile) -> str:
        """Format project analysis as markdown"""
        return f"""# Project Analysis Report

## Project: {profile.name}
**Path**: {profile.path}
**Architecture**: {profile.architecture_pattern.value}
**Complexity**: {profile.complexity.value}
**Team Size**: {profile.team_size_estimate}

## Technology Stack
- **Languages**: {', '.join(profile.technology_stack.languages)}
- **Frameworks**: {', '.join(profile.technology_stack.frameworks)}
- **Databases**: {', '.join(profile.technology_stack.databases)}
- **Tools**: {', '.join(profile.technology_stack.tools)}

## Recommended Subagents
{chr(10).join(f'- {agent}' for agent in profile.recommended_subagents)}

## Project Metrics
- **Files**: {profile.file_count:,}
- **Lines of Code**: {profile.lines_of_code:,}
- **Has Tests**: {'Yes' if profile.has_tests else 'No'}
- **Has CI/CD**: {'Yes' if profile.has_ci_cd else 'No'}
- **Has Docker**: {'Yes' if profile.has_docker else 'No'}

Generated by SubForge Project Analyzer
"""
    
    def _format_selection_markdown(self, selections: Dict[str, Any]) -> str:
        """Format template selections as markdown"""
        selected = selections.get("selected_templates", [])
        reasons = selections.get("selection_reasons", {})
        
        content = "# Template Selection Report\n\n"
        content += f"**Selected Templates**: {len(selected)}\n\n"
        
        for template in selected:
            reason = reasons.get(template, "Standard selection")
            content += f"## {template}\n"
            content += f"**Reason**: {reason}\n\n"
        
        content += "Generated by SubForge Template Selector\n"
        return content
    
    def _print_workflow_summary(self, context: WorkflowContext):
        """Print final workflow summary"""
        print("\n" + "="*60)
        print("📋 SUBFORGE WORKFLOW SUMMARY")
        print("="*60)
        
        total_duration = sum(result.duration for result in context.phase_results.values())
        completed_phases = sum(1 for result in context.phase_results.values() 
                             if result.status == PhaseStatus.COMPLETED)
        
        print(f"Project: {Path(context.project_path).name}")
        print(f"Workflow ID: {context.project_id}")
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Phases Completed: {completed_phases}/{len(context.phase_results)}")
        
        if context.project_profile:
            print(f"Detected Stack: {', '.join(context.project_profile.technology_stack.languages)}")
            print(f"Complexity: {context.project_profile.complexity.value}")
        
        selected_templates = context.template_selections.get("selected_templates", [])
        print(f"Generated Subagents: {len(selected_templates)}")
        for template in selected_templates:
            print(f"  • {template}")
        
        print(f"Configuration saved to: {context.communication_dir}")
        print("🎉 SubForge workflow completed successfully!")
    
    async def _save_workflow_context(self, context: WorkflowContext):
        """Save complete workflow context for future reference"""
        context_file = context.communication_dir / "workflow_context.json"
        
        with open(context_file, 'w') as f:
            json.dump(context.to_dict(), f, indent=2, default=str)
        
        print(f"💾 Workflow context saved: {context_file}")


# CLI interface for testing
async def main():
    """Main CLI interface for testing the workflow orchestrator"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python workflow_orchestrator.py <project_path> [user_request]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    user_request = sys.argv[2] if len(sys.argv) > 2 else "Set up development environment with best practices"
    
    orchestrator = WorkflowOrchestrator()
    
    try:
        context = await orchestrator.execute_workflow(user_request, project_path)
        print(f"\n✨ Workflow completed! Check results in: {context.communication_dir}")
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())