#!/usr/bin/env python3
"""
Gap Analyzer for SubForge
Identifies what's missing in existing project documentation and configuration
Suggests what needs to be created or documented
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field

from .knowledge_extractor import (
    ProjectInfo, Command, Workflow, Module, Architecture,
    ProjectKnowledgeExtractor
)


@dataclass
class MissingCommand:
    """Represents a command that should exist but doesn't"""
    name: str
    suggested_command: str
    reason: str
    priority: str  # high, medium, low


@dataclass
class MissingWorkflow:
    """Represents a workflow that should exist but doesn't"""
    name: str
    description: str
    suggested_steps: List[str]
    reason: str
    priority: str


@dataclass
class MissingDocumentation:
    """Represents missing documentation"""
    file: str
    description: str
    priority: str
    template: Optional[str] = None


@dataclass
class AgentSuggestion:
    """Suggestion for an agent that should be created"""
    name: str
    reason: str
    focus_area: str
    suggested_tools: List[str]
    priority: str


@dataclass
class GapReport:
    """Complete gap analysis report"""
    missing_commands: List[MissingCommand]
    missing_workflows: List[MissingWorkflow]
    missing_documentation: List[MissingDocumentation]
    suggested_agents: List[AgentSuggestion]
    configuration_issues: List[str]
    improvement_suggestions: List[str]
    completeness_score: float  # 0-1 score of how complete the project is


class GapAnalyzer:
    """
    Analyzes project gaps and suggests improvements
    Identifies what's missing from documentation and configuration
    """
    
    def __init__(self, project_path: str = None):
        """Initialize with project path"""
        self.project_path = Path(project_path or os.getcwd())
        self.extractor = ProjectKnowledgeExtractor(project_path)
        
    def analyze_documentation_gaps(self) -> GapReport:
        """
        Comprehensive gap analysis of project documentation
        """
        # Extract current state
        project_info = self.extractor.extract_project_info()
        commands = self.extractor.extract_commands()
        workflows = self.extractor.extract_workflows()
        modules = self.extractor.identify_modules()
        
        # Analyze gaps
        missing_commands = self.analyze_command_gaps(commands, project_info, modules)
        missing_workflows = self.analyze_workflow_gaps(workflows, project_info, commands)
        missing_docs = self.analyze_documentation_files()
        suggested_agents = self.suggest_agents_needed(modules, project_info)
        config_issues = self.analyze_configuration_issues(project_info)
        improvements = self.suggest_improvements(project_info, commands, workflows, modules)
        
        # Calculate completeness score
        score = self.calculate_completeness_score(
            project_info, commands, workflows, modules,
            missing_commands, missing_workflows, missing_docs
        )
        
        return GapReport(
            missing_commands=missing_commands,
            missing_workflows=missing_workflows,
            missing_documentation=missing_docs,
            suggested_agents=suggested_agents,
            configuration_issues=config_issues,
            improvement_suggestions=improvements,
            completeness_score=score
        )
    
    def analyze_command_gaps(self, 
                            existing_commands: Dict[str, Command],
                            project_info: ProjectInfo,
                            modules: List[Module]) -> List[MissingCommand]:
        """
        Identify commands that should exist but don't
        """
        missing = []
        existing_names = set(existing_commands.keys())
        existing_categories = set(cmd.category for cmd in existing_commands.values())
        
        # Check for essential commands by category
        
        # Development commands
        if 'dev' not in existing_categories:
            if 'JavaScript' in project_info.languages or 'TypeScript' in project_info.languages:
                if not any('dev' in name.lower() or 'start' in name.lower() for name in existing_names):
                    missing.append(MissingCommand(
                        name='dev',
                        suggested_command='npm run dev or npm start',
                        reason='No development server command found',
                        priority='high'
                    ))
            elif 'Python' in project_info.languages:
                if 'FastAPI' in project_info.frameworks:
                    missing.append(MissingCommand(
                        name='dev',
                        suggested_command='uvicorn main:app --reload',
                        reason='No FastAPI dev server command found',
                        priority='high'
                    ))
                elif 'Django' in project_info.frameworks:
                    missing.append(MissingCommand(
                        name='dev',
                        suggested_command='python manage.py runserver',
                        reason='No Django dev server command found',
                        priority='high'
                    ))
        
        # Test commands
        if 'test' not in existing_categories:
            if project_info.languages:
                missing.append(MissingCommand(
                    name='test',
                    suggested_command=self._suggest_test_command(project_info),
                    reason='No test command found',
                    priority='high'
                ))
        
        # Build commands
        if 'build' not in existing_categories:
            if any(fw in project_info.frameworks for fw in ['React', 'Vue', 'Angular', 'Next.js']):
                missing.append(MissingCommand(
                    name='build',
                    suggested_command='npm run build',
                    reason='Frontend project without build command',
                    priority='medium'
                ))
        
        # Lint commands
        if 'lint' not in existing_categories:
            if project_info.languages:
                lint_cmd = self._suggest_lint_command(project_info)
                if lint_cmd:
                    missing.append(MissingCommand(
                        name='lint',
                        suggested_command=lint_cmd,
                        reason='No linting command found',
                        priority='medium'
                    ))
        
        # Database commands
        if project_info.databases and 'database' not in existing_categories:
            if not any('migrate' in name.lower() or 'db' in name.lower() for name in existing_names):
                missing.append(MissingCommand(
                    name='migrate',
                    suggested_command=self._suggest_database_command(project_info),
                    reason='Database project without migration commands',
                    priority='medium'
                ))
        
        # Docker commands
        if (self.project_path / 'docker-compose.yml').exists():
            if not any('docker' in name.lower() or 'compose' in name.lower() for name in existing_names):
                missing.append(MissingCommand(
                    name='docker-up',
                    suggested_command='docker-compose up',
                    reason='Docker Compose file exists but no commands',
                    priority='medium'
                ))
        
        # Module-specific test commands
        for module in modules:
            if module.has_tests and not module.test_command:
                module_test_name = f"test-{module.name}"
                if module_test_name not in existing_names:
                    missing.append(MissingCommand(
                        name=module_test_name,
                        suggested_command=f"npm run test -- {module.path.relative_to(self.project_path)}",
                        reason=f"Module {module.name} has tests but no test command",
                        priority='low'
                    ))
        
        return missing
    
    def analyze_workflow_gaps(self,
                            existing_workflows: Dict[str, Workflow],
                            project_info: ProjectInfo,
                            commands: Dict[str, Command]) -> List[MissingWorkflow]:
        """
        Identify workflows that should exist but don't
        """
        missing = []
        existing_names = set(existing_workflows.keys())
        
        # Check for essential workflows
        
        # Development workflow
        if 'development' not in existing_names and 'dev' not in existing_names:
            dev_steps = self._generate_development_workflow_steps(commands)
            if dev_steps:
                missing.append(MissingWorkflow(
                    name='development',
                    description='Standard development workflow',
                    suggested_steps=dev_steps,
                    reason='No development workflow documented',
                    priority='high'
                ))
        
        # PR/Contribution workflow
        if not any('pr' in name.lower() or 'pull' in name.lower() or 'contribut' in name.lower() 
                  for name in existing_names):
            pr_steps = [
                'Fork repository (if external contributor)',
                'Create feature branch',
                'Make changes',
                'Run tests locally',
                'Commit with descriptive message',
                'Push to branch',
                'Create pull request',
                'Address review feedback'
            ]
            missing.append(MissingWorkflow(
                name='pull-request',
                description='Pull request submission workflow',
                suggested_steps=pr_steps,
                reason='No PR/contribution workflow documented',
                priority='high'
            ))
        
        # Release workflow
        if not any('release' in name.lower() or 'deploy' in name.lower() for name in existing_names):
            if any(cmd.category == 'deploy' for cmd in commands.values()):
                release_steps = self._generate_release_workflow_steps(commands)
                missing.append(MissingWorkflow(
                    name='release',
                    description='Release and deployment workflow',
                    suggested_steps=release_steps,
                    reason='Has deploy commands but no release workflow',
                    priority='medium'
                ))
        
        # Testing workflow
        if 'testing' not in existing_names and 'test' not in existing_names:
            if any(cmd.category == 'test' for cmd in commands.values()):
                test_steps = self._generate_test_workflow_steps(commands)
                missing.append(MissingWorkflow(
                    name='testing',
                    description='Complete testing workflow',
                    suggested_steps=test_steps,
                    reason='Has test commands but no testing workflow',
                    priority='medium'
                ))
        
        # Hotfix workflow
        if not any('hotfix' in name.lower() or 'emergency' in name.lower() for name in existing_names):
            if project_info.architecture in ['Microservices', 'Monolithic'] and len(commands) > 10:
                hotfix_steps = [
                    'Identify critical issue',
                    'Create hotfix branch from production',
                    'Apply minimal fix',
                    'Test fix thoroughly',
                    'Deploy to staging',
                    'Verify in staging',
                    'Deploy to production',
                    'Create follow-up ticket for proper fix'
                ]
                missing.append(MissingWorkflow(
                    name='hotfix',
                    description='Emergency hotfix workflow',
                    suggested_steps=hotfix_steps,
                    reason='Production project without hotfix workflow',
                    priority='low'
                ))
        
        return missing
    
    def analyze_documentation_files(self) -> List[MissingDocumentation]:
        """
        Check for missing documentation files
        """
        missing = []
        
        # Check for README
        if not self._file_exists(['README.md', 'README.rst', 'README.txt']):
            missing.append(MissingDocumentation(
                file='README.md',
                description='Main project documentation',
                priority='high',
                template=self._generate_readme_template()
            ))
        
        # Check for CONTRIBUTING
        if not self._file_exists(['CONTRIBUTING.md', 'CONTRIBUTING.rst']):
            if (self.project_path / '.github').exists():  # Likely open source
                missing.append(MissingDocumentation(
                    file='CONTRIBUTING.md',
                    description='Contribution guidelines',
                    priority='high',
                    template=self._generate_contributing_template()
                ))
        
        # Check for LICENSE
        if not self._file_exists(['LICENSE', 'LICENSE.md', 'LICENSE.txt']):
            if (self.project_path / '.github').exists():  # Likely open source
                missing.append(MissingDocumentation(
                    file='LICENSE',
                    description='License file',
                    priority='high',
                    template='Choose appropriate license from https://choosealicense.com/'
                ))
        
        # Check for CHANGELOG
        if not self._file_exists(['CHANGELOG.md', 'CHANGELOG.rst', 'HISTORY.md']):
            if self._is_mature_project():
                missing.append(MissingDocumentation(
                    file='CHANGELOG.md',
                    description='Version history and changes',
                    priority='medium',
                    template=self._generate_changelog_template()
                ))
        
        # Check for API documentation
        if self._has_api() and not self._file_exists(['API.md', 'docs/API.md', 'docs/api.md']):
            missing.append(MissingDocumentation(
                file='docs/API.md',
                description='API endpoint documentation',
                priority='high',
                template=self._generate_api_doc_template()
            ))
        
        # Check for architecture documentation
        if self._is_complex_project() and not self._file_exists(['ARCHITECTURE.md', 'docs/ARCHITECTURE.md']):
            missing.append(MissingDocumentation(
                file='docs/ARCHITECTURE.md',
                description='System architecture documentation',
                priority='medium',
                template=self._generate_architecture_template()
            ))
        
        # Check for .env.example
        if self._file_exists(['.env']) and not self._file_exists(['.env.example', '.env.sample']):
            missing.append(MissingDocumentation(
                file='.env.example',
                description='Environment variables template',
                priority='high',
                template='Copy .env and remove sensitive values'
            ))
        
        return missing
    
    def suggest_agents_needed(self, modules: List[Module], project_info: ProjectInfo) -> List[AgentSuggestion]:
        """
        Suggest agents based on project structure and modules
        """
        suggestions = []
        existing_agents = self._get_existing_agents()
        
        # Module-based agents
        for module in modules:
            agent_name = f"{module.name}-specialist"
            if agent_name not in existing_agents:
                tools = self._determine_agent_tools(module)
                suggestions.append(AgentSuggestion(
                    name=agent_name,
                    reason=f"Module {module.name} needs specialized agent",
                    focus_area=module.description,
                    suggested_tools=tools,
                    priority='high' if module.has_tests else 'medium'
                ))
        
        # Framework/technology specific agents
        
        # API agent
        if any(fw in project_info.frameworks for fw in ['FastAPI', 'Express', 'Flask', 'Django']):
            if 'api-specialist' not in existing_agents:
                suggestions.append(AgentSuggestion(
                    name='api-specialist',
                    reason='Project has API framework',
                    focus_area='API endpoints, middleware, request handling',
                    suggested_tools=['Read', 'Write', 'Edit', 'Bash', 'Grep'],
                    priority='high'
                ))
        
        # Database agent
        if project_info.databases:
            if 'database-specialist' not in existing_agents:
                suggestions.append(AgentSuggestion(
                    name='database-specialist',
                    reason='Project uses databases',
                    focus_area='Database schema, queries, migrations, optimization',
                    suggested_tools=['Read', 'Write', 'Edit', 'Bash'],
                    priority='high'
                ))
        
        # Frontend agent
        if any(fw in project_info.frameworks for fw in ['React', 'Vue', 'Angular', 'Svelte']):
            if 'frontend-specialist' not in existing_agents:
                suggestions.append(AgentSuggestion(
                    name='frontend-specialist',
                    reason='Project has frontend framework',
                    focus_area='UI components, state management, styling',
                    suggested_tools=['Read', 'Write', 'Edit', 'Bash', 'Grep'],
                    priority='high'
                ))
        
        # Testing agent
        if any(fw in project_info.frameworks for fw in ['Jest', 'pytest', 'Mocha', 'Cypress']):
            if 'test-specialist' not in existing_agents:
                suggestions.append(AgentSuggestion(
                    name='test-specialist',
                    reason='Project has testing framework',
                    focus_area='Test creation, test coverage, test automation',
                    suggested_tools=['Read', 'Write', 'Edit', 'Bash'],
                    priority='medium'
                ))
        
        # DevOps agent
        if self._has_ci_cd() or self._has_docker():
            if 'devops-specialist' not in existing_agents:
                suggestions.append(AgentSuggestion(
                    name='devops-specialist',
                    reason='Project has CI/CD or containerization',
                    focus_area='Build pipelines, deployment, infrastructure',
                    suggested_tools=['Read', 'Write', 'Edit', 'Bash', 'Grep'],
                    priority='medium'
                ))
        
        # Performance agent for large projects
        if self._is_complex_project():
            if 'performance-specialist' not in existing_agents:
                suggestions.append(AgentSuggestion(
                    name='performance-specialist',
                    reason='Complex project needs performance optimization',
                    focus_area='Performance profiling, optimization, caching',
                    suggested_tools=['Read', 'Write', 'Edit', 'Bash', 'Grep'],
                    priority='low'
                ))
        
        # Security agent for production projects
        if self._is_production_project():
            if 'security-specialist' not in existing_agents:
                suggestions.append(AgentSuggestion(
                    name='security-specialist',
                    reason='Production project needs security focus',
                    focus_area='Security audits, vulnerability fixes, best practices',
                    suggested_tools=['Read', 'Grep', 'Bash'],
                    priority='medium'
                ))
        
        # Always suggest a coordinator for multi-module projects
        if len(modules) > 2 and 'project-coordinator' not in existing_agents:
            suggestions.append(AgentSuggestion(
                name='project-coordinator',
                reason='Multi-module project needs coordination',
                focus_area='Cross-module integration, architecture decisions',
                suggested_tools=['Read', 'Write', 'Edit', 'Bash', 'Grep', 'Glob'],
                priority='high'
            ))
        
        return suggestions
    
    def analyze_configuration_issues(self, project_info: ProjectInfo) -> List[str]:
        """
        Identify configuration issues
        """
        issues = []
        
        # Check for missing gitignore
        if not (self.project_path / '.gitignore').exists():
            issues.append("Missing .gitignore file - sensitive files may be committed")
        
        # Check for exposed secrets
        env_file = self.project_path / '.env'
        if env_file.exists():
            gitignore = self.project_path / '.gitignore'
            if gitignore.exists():
                with open(gitignore, 'r') as f:
                    gitignore_content = f.read()
                    if '.env' not in gitignore_content:
                        issues.append(".env file not in .gitignore - secrets may be exposed")
        
        # Check for missing package manager lock files
        if (self.project_path / 'package.json').exists():
            if not (self.project_path / 'package-lock.json').exists() and \
               not (self.project_path / 'yarn.lock').exists() and \
               not (self.project_path / 'pnpm-lock.yaml').exists():
                issues.append("Missing package lock file - dependency versions not locked")
        
        if (self.project_path / 'requirements.txt').exists():
            # Check if versions are pinned
            with open(self.project_path / 'requirements.txt', 'r') as f:
                content = f.read()
                if '==' not in content and '>=' not in content:
                    issues.append("Python dependencies not version-pinned")
        
        # Check for missing linting configuration
        if 'JavaScript' in project_info.languages or 'TypeScript' in project_info.languages:
            if not self._file_exists(['.eslintrc.json', '.eslintrc.js', '.eslintrc.yml']):
                issues.append("No ESLint configuration for JavaScript/TypeScript project")
        
        if 'Python' in project_info.languages:
            if not self._file_exists(['.flake8', 'setup.cfg', 'pyproject.toml', '.ruff.toml']):
                issues.append("No Python linting configuration")
        
        # Check for missing editor configuration
        if not (self.project_path / '.editorconfig').exists():
            issues.append("Missing .editorconfig - inconsistent coding styles possible")
        
        # Check for missing CI/CD configuration
        if self._is_mature_project() and not self._has_ci_cd():
            issues.append("No CI/CD configuration detected")
        
        # Check for missing pre-commit hooks
        if self._is_mature_project():
            if not self._file_exists(['.pre-commit-config.yaml', '.husky']):
                issues.append("No pre-commit hooks configured")
        
        return issues
    
    def suggest_improvements(self,
                            project_info: ProjectInfo,
                            commands: Dict[str, Command],
                            workflows: Dict[str, Workflow],
                            modules: List[Module]) -> List[str]:
        """
        Suggest general improvements for the project
        """
        suggestions = []
        
        # Testing improvements
        test_commands = [cmd for cmd in commands.values() if cmd.category == 'test']
        if not test_commands:
            suggestions.append("Add automated testing to improve code quality")
        elif len(test_commands) == 1:
            suggestions.append("Consider separating unit tests from integration tests")
        
        # Documentation improvements
        if not (self.project_path / 'docs').exists():
            if self._is_complex_project():
                suggestions.append("Create a docs/ directory for detailed documentation")
        
        # Module organization
        if len(modules) == 0 and self._is_mature_project():
            suggestions.append("Consider organizing code into logical modules")
        elif len(modules) > 10:
            suggestions.append("Consider consolidating some modules for better maintainability")
        
        # Command organization
        if len(commands) > 20:
            suggestions.append("Consider using a task runner (Make, Just, etc.) to organize commands")
        
        # Workflow automation
        if len(workflows) < 3 and len(commands) > 10:
            suggestions.append("Document more workflows to standardize processes")
        
        # Container suggestions
        if not self._has_docker() and self._is_complex_project():
            suggestions.append("Consider containerizing the application with Docker")
        
        # Monitoring and logging
        if self._is_production_project():
            if not self._has_monitoring():
                suggestions.append("Add monitoring and observability tools")
            if not self._has_structured_logging():
                suggestions.append("Implement structured logging for better debugging")
        
        # Performance suggestions
        if 'React' in project_info.frameworks:
            suggestions.append("Consider implementing code splitting and lazy loading")
        
        if project_info.databases:
            suggestions.append("Ensure database queries are optimized with proper indexing")
        
        # Security suggestions
        if self._has_api():
            suggestions.append("Implement rate limiting and API authentication")
            suggestions.append("Add input validation and sanitization")
        
        # Development experience
        if not self._file_exists(['.vscode/settings.json', '.idea']):
            suggestions.append("Add IDE configuration for consistent development experience")
        
        return suggestions
    
    def calculate_completeness_score(self,
                                    project_info: ProjectInfo,
                                    commands: Dict[str, Command],
                                    workflows: Dict[str, Workflow],
                                    modules: List[Module],
                                    missing_commands: List[MissingCommand],
                                    missing_workflows: List[MissingWorkflow],
                                    missing_docs: List[MissingDocumentation]) -> float:
        """
        Calculate a completeness score for the project (0-1)
        """
        score = 0.0
        max_score = 0.0
        
        # Documentation score (30%)
        max_score += 30
        if self._file_exists(['README.md', 'README.rst']):
            score += 10
        if self._file_exists(['CONTRIBUTING.md']) or not self._is_open_source():
            score += 5
        if self._file_exists(['LICENSE']) or not self._is_open_source():
            score += 5
        if len(missing_docs) == 0:
            score += 10
        elif len(missing_docs) < 3:
            score += 5
        
        # Commands score (20%)
        max_score += 20
        if commands:
            score += 10
            if len(missing_commands) == 0:
                score += 10
            elif len(missing_commands) < 3:
                score += 5
        
        # Workflows score (15%)
        max_score += 15
        if workflows:
            score += 7
            if len(missing_workflows) == 0:
                score += 8
            elif len(missing_workflows) < 2:
                score += 4
        
        # Testing score (15%)
        max_score += 15
        if any(cmd.category == 'test' for cmd in commands.values()):
            score += 10
        if any(module.has_tests for module in modules):
            score += 5
        
        # Configuration score (10%)
        max_score += 10
        if (self.project_path / '.gitignore').exists():
            score += 3
        if self._has_linting_config():
            score += 3
        if self._has_ci_cd():
            score += 4
        
        # Architecture score (10%)
        max_score += 10
        if project_info.architecture != 'Unknown':
            score += 5
        if modules:
            score += 5
        
        return score / max_score if max_score > 0 else 0.0
    
    # Helper methods
    
    def _file_exists(self, filenames: List[str]) -> bool:
        """Check if any of the files exist"""
        for filename in filenames:
            if (self.project_path / filename).exists():
                return True
        return False
    
    def _get_existing_agents(self) -> Set[str]:
        """Get list of existing agents"""
        agents = set()
        agents_dir = self.project_path / '.claude' / 'agents'
        if agents_dir.exists():
            for agent_file in agents_dir.glob('*.md'):
                agents.add(agent_file.stem)
        return agents
    
    def _suggest_test_command(self, project_info: ProjectInfo) -> str:
        """Suggest appropriate test command"""
        if 'Jest' in project_info.frameworks:
            return 'npm test'
        elif 'pytest' in project_info.frameworks:
            return 'pytest'
        elif 'Mocha' in project_info.frameworks:
            return 'npm test'
        elif 'JavaScript' in project_info.languages:
            return 'npm test'
        elif 'Python' in project_info.languages:
            return 'python -m pytest or python -m unittest'
        else:
            return 'Add appropriate test command'
    
    def _suggest_lint_command(self, project_info: ProjectInfo) -> Optional[str]:
        """Suggest appropriate lint command"""
        if 'JavaScript' in project_info.languages or 'TypeScript' in project_info.languages:
            return 'npm run lint or eslint .'
        elif 'Python' in project_info.languages:
            return 'flake8 or ruff check'
        elif 'Ruby' in project_info.languages:
            return 'rubocop'
        elif 'Go' in project_info.languages:
            return 'go fmt ./...'
        return None
    
    def _suggest_database_command(self, project_info: ProjectInfo) -> str:
        """Suggest database command"""
        if 'Django' in project_info.frameworks:
            return 'python manage.py migrate'
        elif 'SQLAlchemy' in project_info.frameworks:
            return 'alembic upgrade head'
        elif 'Prisma' in project_info.frameworks:
            return 'npx prisma migrate dev'
        elif 'TypeORM' in project_info.frameworks:
            return 'npm run typeorm migration:run'
        else:
            return 'Add database migration command'
    
    def _generate_development_workflow_steps(self, commands: Dict[str, Command]) -> List[str]:
        """Generate development workflow steps"""
        steps = []
        
        # Find relevant commands
        setup_cmd = next((cmd for cmd in commands.values() if cmd.category == 'setup'), None)
        dev_cmd = next((cmd for cmd in commands.values() if cmd.category == 'dev'), None)
        test_cmd = next((cmd for cmd in commands.values() if cmd.category == 'test'), None)
        
        if setup_cmd:
            steps.append(f"Install dependencies: {setup_cmd.command}")
        else:
            steps.append("Install project dependencies")
        
        if dev_cmd:
            steps.append(f"Start development: {dev_cmd.command}")
        else:
            steps.append("Start development environment")
        
        steps.append("Make code changes")
        
        if test_cmd:
            steps.append(f"Run tests: {test_cmd.command}")
        else:
            steps.append("Test your changes")
        
        steps.append("Commit changes with descriptive message")
        
        return steps
    
    def _generate_release_workflow_steps(self, commands: Dict[str, Command]) -> List[str]:
        """Generate release workflow steps"""
        steps = [
            "Update version number",
            "Update CHANGELOG.md",
            "Run all tests",
            "Build production assets"
        ]
        
        # Find deploy command
        deploy_cmd = next((cmd for cmd in commands.values() if cmd.category == 'deploy'), None)
        if deploy_cmd:
            steps.append(f"Deploy: {deploy_cmd.command}")
        else:
            steps.append("Deploy to production")
        
        steps.extend([
            "Verify deployment",
            "Create git tag",
            "Update documentation"
        ])
        
        return steps
    
    def _generate_test_workflow_steps(self, commands: Dict[str, Command]) -> List[str]:
        """Generate test workflow steps"""
        steps = []
        test_commands = [cmd for cmd in commands.values() if cmd.category == 'test']
        
        for cmd in test_commands[:5]:
            steps.append(f"{cmd.description}: {cmd.command}")
        
        if not steps:
            steps = [
                "Run unit tests",
                "Run integration tests",
                "Check code coverage",
                "Run linting"
            ]
        
        return steps
    
    def _determine_agent_tools(self, module: Module) -> List[str]:
        """Determine tools for an agent"""
        tools = ['Read', 'Write', 'Edit']
        
        if module.has_tests:
            tools.append('Bash')
        
        if module.name in ['api', 'server', 'backend', 'frontend']:
            tools.extend(['Bash', 'Grep'])
        
        return list(dict.fromkeys(tools))  # Remove duplicates
    
    def _is_mature_project(self) -> bool:
        """Check if project is mature"""
        # Check for git history
        git_dir = self.project_path / '.git'
        if git_dir.exists():
            try:
                import subprocess
                result = subprocess.run(
                    ['git', 'rev-list', '--count', 'HEAD'],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    commit_count = int(result.stdout.strip())
                    return commit_count > 50
            except:
                pass
        
        # Check file count as fallback
        file_count = sum(1 for _ in self.project_path.rglob('*') if _.is_file())
        return file_count > 20
    
    def _is_complex_project(self) -> bool:
        """Check if project is complex"""
        file_count = sum(1 for _ in self.project_path.rglob('*') if _.is_file())
        return file_count > 100
    
    def _is_production_project(self) -> bool:
        """Check if project is likely in production"""
        return (self._has_ci_cd() and 
                self._has_docker() and 
                self._is_mature_project())
    
    def _is_open_source(self) -> bool:
        """Check if project is likely open source"""
        return (self.project_path / '.github').exists() or \
               (self.project_path / '.gitlab').exists()
    
    def _has_api(self) -> bool:
        """Check if project has API"""
        project_info = self.extractor.extract_project_info()
        return any(fw in project_info.frameworks 
                  for fw in ['FastAPI', 'Express', 'Flask', 'Django', 'NestJS'])
    
    def _has_ci_cd(self) -> bool:
        """Check if project has CI/CD"""
        return self._file_exists([
            '.github/workflows',
            '.gitlab-ci.yml',
            'Jenkinsfile',
            '.circleci/config.yml',
            '.travis.yml'
        ])
    
    def _has_docker(self) -> bool:
        """Check if project uses Docker"""
        return self._file_exists(['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml'])
    
    def _has_linting_config(self) -> bool:
        """Check if project has linting configuration"""
        return self._file_exists([
            '.eslintrc.json', '.eslintrc.js',
            '.prettierrc', '.prettierrc.json',
            '.flake8', '.ruff.toml',
            '.rubocop.yml'
        ])
    
    def _has_monitoring(self) -> bool:
        """Check if project has monitoring"""
        # This is a simplified check
        return False  # Would need to check for specific monitoring tools
    
    def _has_structured_logging(self) -> bool:
        """Check if project has structured logging"""
        # This is a simplified check
        return False  # Would need to analyze code for logging patterns
    
    def _generate_readme_template(self) -> str:
        """Generate README template"""
        return """# Project Name

## Description
Brief description of what this project does.

## Installation
```bash
# Installation commands
```

## Usage
```bash
# Usage examples
```

## Development
See CONTRIBUTING.md for development guidelines.

## License
[License Type]
"""
    
    def _generate_contributing_template(self) -> str:
        """Generate CONTRIBUTING template"""
        return """# Contributing

## Development Setup
1. Fork the repository
2. Clone your fork
3. Install dependencies
4. Create a feature branch

## Making Changes
1. Write tests for new features
2. Ensure all tests pass
3. Follow code style guidelines
4. Update documentation

## Submitting Pull Requests
1. Push to your fork
2. Create pull request
3. Describe your changes
4. Link relevant issues
"""
    
    def _generate_changelog_template(self) -> str:
        """Generate CHANGELOG template"""
        return """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security updates
"""
    
    def _generate_api_doc_template(self) -> str:
        """Generate API documentation template"""
        return """# API Documentation

## Base URL
```
https://api.example.com/v1
```

## Authentication
Describe authentication method

## Endpoints

### GET /endpoint
Description of endpoint

**Request:**
```json
{
  "param": "value"
}
```

**Response:**
```json
{
  "result": "value"
}
```

## Error Handling
Describe error responses
"""
    
    def _generate_architecture_template(self) -> str:
        """Generate architecture documentation template"""
        return """# Architecture

## Overview
High-level system architecture description

## Components
- Component 1: Description
- Component 2: Description

## Data Flow
Describe how data flows through the system

## Technology Stack
- Frontend: 
- Backend:
- Database:
- Infrastructure:

## Deployment
Describe deployment architecture

## Security
Security considerations and measures
"""


# Generate report function
def generate_gap_report(project_path: str = None) -> str:
    """
    Generate a comprehensive gap analysis report for a project
    Returns markdown-formatted report
    """
    analyzer = GapAnalyzer(project_path)
    report = analyzer.analyze_documentation_gaps()
    
    # Format report as markdown
    md_report = f"""# Gap Analysis Report

## Project Completeness Score: {report.completeness_score:.1%}

## Missing Commands ({len(report.missing_commands)})
"""
    
    if report.missing_commands:
        for cmd in report.missing_commands:
            md_report += f"- **{cmd.name}** ({cmd.priority}): {cmd.reason}\n"
            md_report += f"  - Suggested: `{cmd.suggested_command}`\n"
    else:
        md_report += "✅ No missing commands detected\n"
    
    md_report += f"\n## Missing Workflows ({len(report.missing_workflows)})\n"
    
    if report.missing_workflows:
        for wf in report.missing_workflows:
            md_report += f"- **{wf.name}** ({wf.priority}): {wf.reason}\n"
    else:
        md_report += "✅ No missing workflows detected\n"
    
    md_report += f"\n## Missing Documentation ({len(report.missing_documentation)})\n"
    
    if report.missing_documentation:
        for doc in report.missing_documentation:
            md_report += f"- **{doc.file}** ({doc.priority}): {doc.description}\n"
    else:
        md_report += "✅ Documentation is complete\n"
    
    md_report += f"\n## Suggested Agents ({len(report.suggested_agents)})\n"
    
    if report.suggested_agents:
        for agent in report.suggested_agents:
            md_report += f"- **{agent.name}** ({agent.priority}): {agent.reason}\n"
            md_report += f"  - Focus: {agent.focus_area}\n"
    else:
        md_report += "✅ Adequate agents configured\n"
    
    md_report += f"\n## Configuration Issues ({len(report.configuration_issues)})\n"
    
    if report.configuration_issues:
        for issue in report.configuration_issues:
            md_report += f"- ⚠️ {issue}\n"
    else:
        md_report += "✅ No configuration issues found\n"
    
    md_report += f"\n## Improvement Suggestions ({len(report.improvement_suggestions)})\n"
    
    if report.improvement_suggestions:
        for suggestion in report.improvement_suggestions:
            md_report += f"- 💡 {suggestion}\n"
    else:
        md_report += "✅ Project is well-optimized\n"
    
    return md_report


# Test function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = os.getcwd()
    
    print(f"Analyzing gaps in: {project_path}\n")
    
    report = generate_gap_report(project_path)
    print(report)