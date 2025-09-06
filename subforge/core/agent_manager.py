#!/usr/bin/env python3
"""
Simple Agent Manager for SubForge
Handles dynamic agent creation and management in project's .claude/agents/ directory
No templates, no fake complexity - just simple file operations
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yaml


@dataclass
class Agent:
    """Simple agent representation"""
    name: str
    tools: List[str]
    model: str = "sonnet"
    prompt: str = ""
    
    def to_markdown(self) -> str:
        """Convert agent to markdown format for .claude/agents/"""
        return f"""---
name: {self.name}
tools: {', '.join(self.tools)}
model: {self.model}
---

{self.prompt}
"""


@dataclass
class ProjectAnalysis:
    """Real project analysis results"""
    project_path: str
    languages: List[str]
    frameworks: List[str]
    has_api: bool
    has_database: bool
    has_frontend: bool
    has_tests: bool
    complexity: str  # simple, moderate, complex
    suggested_agents: List[Dict[str, Any]]


class AgentManager:
    """
    Simple agent manager - no fake complexity, just real functionality
    """
    
    def __init__(self, project_path: str = None):
        """Initialize with optional project path"""
        self.project_path = project_path or os.getcwd()
        self.agents_dir = Path(self.project_path) / ".claude" / "agents"
        
    def analyze_project(self) -> ProjectAnalysis:
        """
        Analyze project to determine what agents are needed
        Returns real analysis, not fake scores
        """
        project_path = Path(self.project_path)
        
        # Real file analysis
        languages = set()
        frameworks = set()
        file_count = 0
        
        # Scan project files
        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]
            
            for file in files:
                file_count += 1
                ext = Path(file).suffix.lower()
                
                # Detect languages
                if ext in ['.py', '.pyw']:
                    languages.add('python')
                elif ext in ['.js', '.jsx', '.mjs']:
                    languages.add('javascript')
                elif ext in ['.ts', '.tsx']:
                    languages.add('typescript')
                elif ext in ['.java']:
                    languages.add('java')
                elif ext in ['.go']:
                    languages.add('go')
                elif ext in ['.rs']:
                    languages.add('rust')
                elif ext in ['.rb']:
                    languages.add('ruby')
                elif ext in ['.php']:
                    languages.add('php')
                elif ext in ['.cs']:
                    languages.add('csharp')
                elif ext in ['.cpp', '.cc', '.cxx', '.hpp']:
                    languages.add('cpp')
                elif ext in ['.html', '.htm']:
                    languages.add('html')
                elif ext in ['.css', '.scss', '.sass']:
                    languages.add('css')
                elif ext in ['.sql']:
                    languages.add('sql')
                elif ext in ['.yaml', '.yml']:
                    languages.add('yaml')
                elif ext in ['.json']:
                    languages.add('json')
                elif ext in ['.md', '.markdown']:
                    languages.add('markdown')
                
                # Detect frameworks from file names
                if 'package.json' == file:
                    # Read package.json to detect frameworks
                    try:
                        pkg_path = Path(root) / file
                        with open(pkg_path, 'r') as f:
                            pkg = json.load(f)
                            deps = pkg.get('dependencies', {})
                            dev_deps = pkg.get('devDependencies', {})
                            all_deps = {**deps, **dev_deps}
                            
                            if 'react' in all_deps:
                                frameworks.add('react')
                            if 'vue' in all_deps:
                                frameworks.add('vue')
                            if 'angular' in all_deps:
                                frameworks.add('angular')
                            if 'express' in all_deps:
                                frameworks.add('express')
                            if 'next' in all_deps:
                                frameworks.add('nextjs')
                            if 'fastify' in all_deps:
                                frameworks.add('fastify')
                    except:
                        pass
                
                elif 'requirements.txt' == file or 'pyproject.toml' == file:
                    # Read Python dependencies
                    try:
                        req_path = Path(root) / file
                        with open(req_path, 'r') as f:
                            content = f.read().lower()
                            if 'fastapi' in content:
                                frameworks.add('fastapi')
                            if 'flask' in content:
                                frameworks.add('flask')
                            if 'django' in content:
                                frameworks.add('django')
                            if 'pytest' in content:
                                frameworks.add('pytest')
                            if 'sqlalchemy' in content:
                                frameworks.add('sqlalchemy')
                    except:
                        pass
                
                elif 'go.mod' == file:
                    frameworks.add('go-modules')
                elif 'Cargo.toml' == file:
                    frameworks.add('cargo')
                elif 'pom.xml' == file:
                    frameworks.add('maven')
                elif 'build.gradle' == file:
                    frameworks.add('gradle')
        
        # Detect project characteristics
        has_api = any(fw in frameworks for fw in ['fastapi', 'flask', 'django', 'express', 'fastify'])
        has_database = 'sql' in languages or 'sqlalchemy' in frameworks or bool(list(Path(self.project_path).glob('**/migrations/**')))
        has_frontend = any(fw in frameworks for fw in ['react', 'vue', 'angular', 'nextjs']) or 'html' in languages
        has_tests = bool(list(Path(self.project_path).glob('**/test_*.py'))) or bool(list(Path(self.project_path).glob('**/*.test.js'))) or 'pytest' in frameworks
        
        # Determine complexity
        if file_count < 10:
            complexity = 'simple'
        elif file_count < 50:
            complexity = 'moderate'
        else:
            complexity = 'complex'
        
        # Suggest agents based on real project characteristics
        suggested_agents = []
        
        if has_api:
            suggested_agents.append({
                'name': 'api-specialist',
                'reason': 'Project has API framework',
                'tools': ['Read', 'Write', 'Edit', 'Bash', 'Grep'],
                'focus': 'API endpoints, request handling, middleware'
            })
        
        if has_database:
            suggested_agents.append({
                'name': 'database-specialist', 
                'reason': 'Project uses database',
                'tools': ['Read', 'Write', 'Edit', 'Bash'],
                'focus': 'Database schema, queries, migrations'
            })
        
        if has_frontend:
            suggested_agents.append({
                'name': 'frontend-specialist',
                'reason': 'Project has frontend framework',
                'tools': ['Read', 'Write', 'Edit', 'Bash', 'Grep'],
                'focus': 'UI components, state management, styling'
            })
        
        if has_tests:
            suggested_agents.append({
                'name': 'test-specialist',
                'reason': 'Project has test framework',
                'tools': ['Read', 'Write', 'Edit', 'Bash'],
                'focus': 'Test creation, coverage, test execution'
            })
        
        # Always suggest a general specialist for the main language
        if 'python' in languages:
            suggested_agents.append({
                'name': 'python-specialist',
                'reason': 'Python is primary language',
                'tools': ['Read', 'Write', 'Edit', 'Bash', 'Grep'],
                'focus': 'Python best practices, optimization, debugging'
            })
        elif 'javascript' in languages or 'typescript' in languages:
            suggested_agents.append({
                'name': 'javascript-specialist',
                'reason': 'JavaScript/TypeScript is primary language',
                'tools': ['Read', 'Write', 'Edit', 'Bash', 'Grep'],
                'focus': 'JavaScript/TypeScript best practices, async patterns'
            })
        
        return ProjectAnalysis(
            project_path=str(project_path),
            languages=list(languages),
            frameworks=list(frameworks),
            has_api=has_api,
            has_database=has_database,
            has_frontend=has_frontend,
            has_tests=has_tests,
            complexity=complexity,
            suggested_agents=suggested_agents
        )
    
    def create_agent(self, name: str, tools: List[str], prompt: str, model: str = "sonnet") -> bool:
        """
        Create an agent file in .claude/agents/
        Returns True if successful
        """
        # Ensure agents directory exists
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Create agent
        agent = Agent(name=name, tools=tools, model=model, prompt=prompt)
        
        # Write to file
        agent_file = self.agents_dir / f"{name}.md"
        try:
            with open(agent_file, 'w') as f:
                f.write(agent.to_markdown())
            return True
        except Exception as e:
            print(f"Error creating agent {name}: {e}")
            return False
    
    def read_agent(self, name: str) -> Optional[Agent]:
        """
        Read an agent definition from .claude/agents/
        Returns Agent object or None if not found
        """
        agent_file = self.agents_dir / f"{name}.md"
        
        if not agent_file.exists():
            return None
        
        try:
            with open(agent_file, 'r') as f:
                content = f.read()
            
            # Parse the markdown frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    prompt = parts[2].strip()
                    
                    tools = frontmatter.get('tools', '').split(', ') if isinstance(frontmatter.get('tools'), str) else frontmatter.get('tools', [])
                    
                    return Agent(
                        name=frontmatter.get('name', name),
                        tools=tools,
                        model=frontmatter.get('model', 'sonnet'),
                        prompt=prompt
                    )
        except Exception as e:
            print(f"Error reading agent {name}: {e}")
        
        return None
    
    def list_agents(self) -> List[str]:
        """
        List all available agents in the project
        Returns list of agent names
        """
        if not self.agents_dir.exists():
            return []
        
        agents = []
        for agent_file in self.agents_dir.glob("*.md"):
            agents.append(agent_file.stem)
        
        return sorted(agents)
    
    def delete_agent(self, name: str) -> bool:
        """
        Delete an agent file
        Returns True if successful
        """
        agent_file = self.agents_dir / f"{name}.md"
        
        if agent_file.exists():
            try:
                agent_file.unlink()
                return True
            except Exception as e:
                print(f"Error deleting agent {name}: {e}")
        
        return False


# Simple helper functions for direct use

def setup_project_agents(project_path: str = None) -> Dict[str, Any]:
    """
    Analyze project and create suggested agents
    This is what Claude Code would call to set up a new project
    """
    manager = AgentManager(project_path)
    analysis = manager.analyze_project()
    
    created_agents = []
    for suggestion in analysis.suggested_agents:
        # Create dynamic prompt based on project context
        prompt = f"""You are a {suggestion['name']} for this project.

Project context:
- Languages: {', '.join(analysis.languages)}
- Frameworks: {', '.join(analysis.frameworks)}
- Complexity: {analysis.complexity}

Your focus areas:
{suggestion['focus']}

Guidelines:
1. Follow existing project patterns and conventions
2. Ensure code quality and maintainability
3. Consider the project's current structure
4. Write clear, well-documented code
5. Test your changes when possible
"""
        
        success = manager.create_agent(
            name=suggestion['name'],
            tools=suggestion['tools'],
            prompt=prompt
        )
        
        if success:
            created_agents.append(suggestion['name'])
    
    return {
        'analysis': analysis,
        'created_agents': created_agents,
        'agents_dir': str(manager.agents_dir)
    }


def get_agent_prompt(project_path: str, agent_name: str) -> Optional[str]:
    """
    Get the full prompt for an agent
    This is what Claude Code would call when user types @agent-name
    """
    manager = AgentManager(project_path)
    agent = manager.read_agent(agent_name)
    
    if agent:
        return agent.prompt
    return None


if __name__ == "__main__":
    # Test the system
    import sys
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = os.getcwd()
    
    print(f"Analyzing project: {project_path}")
    result = setup_project_agents(project_path)
    
    print(f"\nProject Analysis:")
    print(f"  Languages: {', '.join(result['analysis'].languages)}")
    print(f"  Frameworks: {', '.join(result['analysis'].frameworks)}")
    print(f"  Complexity: {result['analysis'].complexity}")
    
    print(f"\nCreated Agents:")
    for agent in result['created_agents']:
        print(f"  - {agent}")
    
    print(f"\nAgents directory: {result['agents_dir']}")