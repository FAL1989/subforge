#!/usr/bin/env python3
"""
Knowledge Extractor for SubForge
Extracts existing project knowledge from documentation, code, and configuration files
No assumptions, no templates - just extraction of what actually exists
"""

import os
import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import subprocess


@dataclass
class ProjectInfo:
    """Extracted project information"""
    name: str
    description: str
    languages: List[str]
    frameworks: List[str]
    databases: List[str]
    architecture: str
    conventions: str
    version: Optional[str] = None
    repository: Optional[str] = None
    
    
@dataclass
class Command:
    """Extracted command information"""
    name: str
    command: str
    description: str
    source: str  # Where it was found (package.json, Makefile, etc.)
    category: str  # dev, test, build, deploy, etc.
    

@dataclass
class Workflow:
    """Extracted workflow information"""
    name: str
    description: str
    steps: List[str]
    source: str  # Where it was found
    triggers: List[str] = field(default_factory=list)
    

@dataclass
class Module:
    """Identified module/subdirectory that needs its own context"""
    name: str
    path: Path
    description: str
    has_tests: bool
    has_docs: bool
    key_files: List[str]
    dependencies: List[str]
    test_command: Optional[str] = None
    conventions: Optional[str] = None
    

@dataclass
class Architecture:
    """Extracted architecture information"""
    pattern: str  # monolith, microservices, modular, etc.
    modules: List[Module]
    entry_points: List[str]
    api_endpoints: Optional[List[str]] = None
    database_schema: Optional[str] = None


@dataclass
class Conventions:
    """Extracted conventions"""
    linting: List[str]
    testing: str
    git: str


class ProjectKnowledgeExtractor:
    """
    Extracts real knowledge from existing projects
    No fake data, no assumptions - just what's actually there
    """
    
    def __init__(self, project_path: str = None):
        """Initialize with project path"""
        self.project_path = Path(project_path or os.getcwd())
        self.ignored_dirs = {
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'dist', 'build', '.next', '.nuxt', 'coverage', '.pytest_cache'
        }
        
    def extract_project_info(self) -> ProjectInfo:
        """
        Extract general project information from various sources
        """
        name = self.project_path.name
        description = ""
        version = None
        repository = None
        
        # Extract from README
        readme_path = self._find_file(['README.md', 'README.rst', 'README.txt'])
        if readme_path:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Get first paragraph as description
                lines = content.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('#'):
                        description = line.strip()
                        break
        
        # Extract from package.json
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            with open(package_json, 'r') as f:
                pkg = json.load(f)
                name = pkg.get('name', name)
                description = pkg.get('description', description)
                version = pkg.get('version', version)
                if 'repository' in pkg:
                    repo = pkg['repository']
                    repository = repo['url'] if isinstance(repo, dict) else repo
        
        # Extract from pyproject.toml
        pyproject = self.project_path / 'pyproject.toml'
        if pyproject.exists():
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            
            with open(pyproject, 'rb') as f:
                data = tomllib.load(f)
                if 'project' in data:
                    proj = data['project']
                    name = proj.get('name', name)
                    description = proj.get('description', description)
                    version = proj.get('version', version)
        
        # Extract languages and frameworks
        languages = self._detect_languages()
        frameworks = self._detect_frameworks()
        databases = self._detect_databases()
        
        # Extract architecture pattern
        architecture = self._detect_architecture()
        
        # Extract conventions
        conventions = self._extract_conventions()
        
        return ProjectInfo(
            name=name,
            description=description,
            languages=list(languages),
            frameworks=list(frameworks),
            databases=list(databases),
            architecture=architecture,
            conventions=conventions,
            version=version,
            repository=repository
        )
    
    def extract_commands(self) -> Dict[str, Command]:
        """
        Extract commands from package.json, Makefile, scripts/, etc.
        """
        commands = {}
        
        # Extract from package.json scripts
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            with open(package_json, 'r') as f:
                pkg = json.load(f)
                scripts = pkg.get('scripts', {})
                for name, cmd in scripts.items():
                    category = self._categorize_command(name, cmd)
                    commands[name] = Command(
                        name=name,
                        command=f"npm run {name}",
                        description=self._generate_command_description(name, cmd),
                        source="package.json",
                        category=category
                    )
        
        # Extract from Makefile
        makefile_paths = ['Makefile', 'makefile', 'GNUmakefile']
        for makefile_name in makefile_paths:
            makefile = self.project_path / makefile_name
            if makefile.exists():
                with open(makefile, 'r') as f:
                    content = f.read()
                    # Find all targets
                    targets = re.findall(r'^([a-zA-Z0-9_-]+):', content, re.MULTILINE)
                    for target in targets:
                        if not target.startswith('.'):  # Skip hidden targets
                            # Try to find comment above target
                            desc_match = re.search(rf'#\s*(.+)\n{target}:', content)
                            description = desc_match.group(1) if desc_match else f"Run {target} target"
                            
                            category = self._categorize_command(target, target)
                            commands[target] = Command(
                                name=target,
                                command=f"make {target}",
                                description=description,
                                source="Makefile",
                                category=category
                            )
        
        # Extract from scripts/ directory
        scripts_dir = self.project_path / 'scripts'
        if scripts_dir.exists() and scripts_dir.is_dir():
            for script in scripts_dir.glob('*.sh'):
                name = script.stem
                # Try to extract description from first comment
                with open(script, 'r') as f:
                    lines = f.readlines()
                    description = f"Run {name} script"
                    for line in lines[:10]:  # Check first 10 lines
                        if line.startswith('#') and not line.startswith('#!'):
                            description = line[1:].strip()
                            break
                
                category = self._categorize_command(name, str(script))
                commands[name] = Command(
                    name=name,
                    command=f"./scripts/{script.name}",
                    description=description,
                    source="scripts/",
                    category=category
                )
        
        # Extract from composer.json (PHP)
        composer_json = self.project_path / 'composer.json'
        if composer_json.exists():
            with open(composer_json, 'r') as f:
                composer = json.load(f)
                scripts = composer.get('scripts', {})
                for name, cmd in scripts.items():
                    if isinstance(cmd, list):
                        cmd = ' && '.join(cmd)
                    category = self._categorize_command(name, cmd)
                    commands[name] = Command(
                        name=name,
                        command=f"composer {name}",
                        description=self._generate_command_description(name, cmd),
                        source="composer.json",
                        category=category
                    )
        
        return commands
    
    def extract_workflows(self) -> Dict[str, Workflow]:
        """
        Extract workflows from CI/CD configs, CONTRIBUTING.md, etc.
        """
        workflows = {}
        
        # Extract from GitHub Actions
        github_workflows = self.project_path / '.github' / 'workflows'
        if github_workflows.exists():
            for workflow_file in list(github_workflows.glob('*.yml')) + list(github_workflows.glob('*.yaml')):
                with open(workflow_file, 'r') as f:
                    workflow_data = yaml.safe_load(f)
                    name = workflow_data.get('name', workflow_file.stem)
                    
                    # Extract triggers
                    triggers = []
                    if 'on' in workflow_data:
                        on_data = workflow_data['on']
                        if isinstance(on_data, str):
                            triggers = [on_data]
                        elif isinstance(on_data, list):
                            triggers = on_data
                        elif isinstance(on_data, dict):
                            triggers = list(on_data.keys())
                    
                    # Extract steps from jobs
                    steps = []
                    if 'jobs' in workflow_data:
                        for job_name, job_data in workflow_data['jobs'].items():
                            if 'steps' in job_data:
                                for step in job_data['steps']:
                                    if 'name' in step:
                                        steps.append(step['name'])
                                    elif 'run' in step:
                                        steps.append(step['run'][:50])  # First 50 chars
                    
                    workflows[name] = Workflow(
                        name=name,
                        description=f"GitHub Actions workflow: {name}",
                        steps=steps,
                        source=f".github/workflows/{workflow_file.name}",
                        triggers=triggers
                    )
        
        # Extract from CONTRIBUTING.md
        contributing = self._find_file(['CONTRIBUTING.md', 'CONTRIBUTING.rst'])
        if contributing:
            with open(contributing, 'r') as f:
                content = f.read()
                
                # Look for common workflow patterns
                if 'pull request' in content.lower() or 'pr process' in content.lower():
                    # Extract PR workflow
                    pr_steps = self._extract_numbered_steps(content, 'pull request')
                    if pr_steps:
                        workflows['pull-request'] = Workflow(
                            name='pull-request',
                            description='Pull request submission process',
                            steps=pr_steps,
                            source='CONTRIBUTING.md'
                        )
                
                if 'release' in content.lower():
                    # Extract release workflow
                    release_steps = self._extract_numbered_steps(content, 'release')
                    if release_steps:
                        workflows['release'] = Workflow(
                            name='release',
                            description='Release process',
                            steps=release_steps,
                            source='CONTRIBUTING.md'
                        )
        
        # Extract from Jenkinsfile
        jenkinsfile = self.project_path / 'Jenkinsfile'
        if jenkinsfile.exists():
            with open(jenkinsfile, 'r') as f:
                content = f.read()
                # Basic stage extraction
                stages = re.findall(r"stage\(['\"]([^'\"]+)['\"]", content)
                if stages:
                    workflows['jenkins-pipeline'] = Workflow(
                        name='jenkins-pipeline',
                        description='Jenkins CI/CD pipeline',
                        steps=stages,
                        source='Jenkinsfile'
                    )
        
        return workflows
    
    def extract_architecture(self) -> Architecture:
        """
        Extract architecture information from project structure
        """
        modules = self.identify_modules()
        pattern = self._detect_architecture()
        entry_points = self._find_entry_points()
        api_endpoints = self._extract_api_endpoints()
        
        return Architecture(
            pattern=pattern,
            modules=modules,
            entry_points=entry_points,
            api_endpoints=api_endpoints
        )
    
    def identify_modules(self) -> List[Module]:
        """
        Identify important subdirectories that need their own context
        """
        modules = []
        
        # Common module patterns
        module_indicators = [
            'src', 'lib', 'app', 'apps', 'packages', 'services',
            'modules', 'components', 'features', 'domains'
        ]
        
        for indicator in module_indicators:
            indicator_path = self.project_path / indicator
            if indicator_path.exists() and indicator_path.is_dir():
                # Check subdirectories
                for subdir in indicator_path.iterdir():
                    if subdir.is_dir() and subdir.name not in self.ignored_dirs:
                        module = self._analyze_module(subdir)
                        if module:
                            modules.append(module)
        
        # Also check root-level directories that look like modules
        for path in self.project_path.iterdir():
            if path.is_dir() and path.name not in self.ignored_dirs:
                # Check if it's a significant module
                if self._is_significant_module(path):
                    module = self._analyze_module(path)
                    if module:
                        modules.append(module)
        
        return modules
    
    def detect_conventions(self) -> Conventions:
        """
        Extract coding conventions from linting configs, editorconfig, etc.
        """
        conventions = []
        
        # Check for ESLint
        eslint_files = ['.eslintrc.json', '.eslintrc.js', '.eslintrc.yml']
        for eslint_file in eslint_files:
            if (self.project_path / eslint_file).exists():
                conventions.append("ESLint configuration found")
                break
        
        # Check for Prettier
        prettier_files = ['.prettierrc', '.prettierrc.json', '.prettierrc.js']
        for prettier_file in prettier_files:
            if (self.project_path / prettier_file).exists():
                conventions.append("Prettier formatting configured")
                break
        
        # Check for Python linting
        if (self.project_path / '.flake8').exists():
            conventions.append("Flake8 linting configured")
        if (self.project_path / 'pyproject.toml').exists():
            with open(self.project_path / 'pyproject.toml', 'r') as f:
                content = f.read()
                if '[tool.black]' in content:
                    conventions.append("Black formatting configured")
                if '[tool.ruff]' in content:
                    conventions.append("Ruff linting configured")
        
        # Check for EditorConfig
        if (self.project_path / '.editorconfig').exists():
            conventions.append("EditorConfig for consistent coding styles")
        
        # Check for pre-commit hooks
        if (self.project_path / '.pre-commit-config.yaml').exists():
            conventions.append("Pre-commit hooks configured")
        
        return Conventions(
            linting=conventions,
            testing=self._extract_testing_conventions(),
            git=self._extract_git_conventions()
        )
    
    # Helper methods
    
    def _detect_languages(self) -> Set[str]:
        """Detect programming languages used in the project"""
        languages = set()
        
        # File extension mapping
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.cs': 'C#',
            '.cpp': 'C++',
            '.c': 'C',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.r': 'R',
            '.m': 'MATLAB',
            '.jl': 'Julia',
            '.lua': 'Lua',
            '.dart': 'Dart',
            '.ex': 'Elixir',
            '.clj': 'Clojure',
            '.hs': 'Haskell',
            '.ml': 'OCaml',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.bash': 'Bash',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'Sass',
            '.less': 'Less',
            '.vue': 'Vue',
            '.svelte': 'Svelte'
        }
        
        # Scan project files
        for root, dirs, files in os.walk(self.project_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in extension_map:
                    languages.add(extension_map[ext])
        
        return languages
    
    def _detect_frameworks(self) -> Set[str]:
        """Detect frameworks and libraries used in the project"""
        frameworks = set()
        
        # Check package.json for JS frameworks
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            with open(package_json, 'r') as f:
                pkg = json.load(f)
                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                
                # Check for common frameworks
                framework_checks = {
                    'react': 'React',
                    'vue': 'Vue',
                    '@angular/core': 'Angular',
                    'svelte': 'Svelte',
                    'next': 'Next.js',
                    'nuxt': 'Nuxt',
                    'gatsby': 'Gatsby',
                    'express': 'Express',
                    'fastify': 'Fastify',
                    'koa': 'Koa',
                    'nestjs': 'NestJS',
                    'electron': 'Electron',
                    'react-native': 'React Native',
                    'expo': 'Expo',
                    'jest': 'Jest',
                    'mocha': 'Mocha',
                    'cypress': 'Cypress',
                    'playwright': 'Playwright',
                    'puppeteer': 'Puppeteer',
                    'webpack': 'Webpack',
                    'vite': 'Vite',
                    'rollup': 'Rollup',
                    'parcel': 'Parcel',
                    'tailwindcss': 'Tailwind CSS',
                    'styled-components': 'Styled Components',
                    '@mui/material': 'Material-UI',
                    'antd': 'Ant Design',
                    'bootstrap': 'Bootstrap'
                }
                
                for key, framework in framework_checks.items():
                    if key in deps:
                        frameworks.add(framework)
        
        # Check for Python frameworks
        requirements_files = ['requirements.txt', 'Pipfile', 'pyproject.toml']
        for req_file in requirements_files:
            req_path = self.project_path / req_file
            if req_path.exists():
                with open(req_path, 'r') as f:
                    content = f.read().lower()
                    
                    framework_checks = {
                        'django': 'Django',
                        'flask': 'Flask',
                        'fastapi': 'FastAPI',
                        'pyramid': 'Pyramid',
                        'tornado': 'Tornado',
                        'aiohttp': 'aiohttp',
                        'sanic': 'Sanic',
                        'pytest': 'pytest',
                        'unittest': 'unittest',
                        'numpy': 'NumPy',
                        'pandas': 'pandas',
                        'tensorflow': 'TensorFlow',
                        'torch': 'PyTorch',
                        'scikit-learn': 'scikit-learn',
                        'sqlalchemy': 'SQLAlchemy',
                        'celery': 'Celery',
                        'scrapy': 'Scrapy',
                        'beautifulsoup': 'BeautifulSoup',
                        'requests': 'Requests'
                    }
                    
                    for key, framework in framework_checks.items():
                        if key in content:
                            frameworks.add(framework)
        
        # Check for other framework indicators
        if (self.project_path / 'pom.xml').exists():
            frameworks.add('Maven')
            # Could parse pom.xml for Spring, etc.
        
        if (self.project_path / 'build.gradle').exists() or (self.project_path / 'build.gradle.kts').exists():
            frameworks.add('Gradle')
        
        if (self.project_path / 'Cargo.toml').exists():
            frameworks.add('Cargo')
            # Could parse for specific Rust frameworks
        
        if (self.project_path / 'go.mod').exists():
            frameworks.add('Go Modules')
            # Could parse for specific Go frameworks
        
        if (self.project_path / 'Gemfile').exists():
            with open(self.project_path / 'Gemfile', 'r') as f:
                content = f.read()
                if 'rails' in content:
                    frameworks.add('Ruby on Rails')
                if 'sinatra' in content:
                    frameworks.add('Sinatra')
        
        return frameworks
    
    def _detect_databases(self) -> Set[str]:
        """Detect databases used in the project"""
        databases = set()
        
        # Check for database configuration files
        db_indicators = {
            'docker-compose': ['postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch'],
            '.env': ['DATABASE_URL', 'MONGO_URI', 'REDIS_URL'],
            'config/database': ['postgresql', 'mysql', 'sqlite', 'mongodb']
        }
        
        # Check docker-compose files
        compose_files = ['docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml']
        for compose_file in compose_files:
            compose_path = self.project_path / compose_file
            if compose_path.exists():
                with open(compose_path, 'r') as f:
                    content = f.read().lower()
                    if 'postgres' in content:
                        databases.add('PostgreSQL')
                    if 'mysql' in content or 'mariadb' in content:
                        databases.add('MySQL/MariaDB')
                    if 'mongo' in content:
                        databases.add('MongoDB')
                    if 'redis' in content:
                        databases.add('Redis')
                    if 'elasticsearch' in content:
                        databases.add('Elasticsearch')
                    if 'cassandra' in content:
                        databases.add('Cassandra')
                    if 'neo4j' in content:
                        databases.add('Neo4j')
        
        # Check for ORM/database libraries
        if self._check_dependency_exists(['sqlalchemy', 'django', 'prisma', 'typeorm', 'sequelize']):
            # These suggest SQL databases
            if not databases:  # Only add if we haven't detected specific ones
                databases.add('SQL Database')
        
        if self._check_dependency_exists(['mongoose', 'mongodb', 'pymongo']):
            databases.add('MongoDB')
        
        if self._check_dependency_exists(['redis', 'ioredis', 'redis-py']):
            databases.add('Redis')
        
        return databases
    
    def _detect_architecture(self) -> str:
        """Detect architecture pattern"""
        # Check for microservices indicators
        if (self.project_path / 'docker-compose.yml').exists():
            with open(self.project_path / 'docker-compose.yml', 'r') as f:
                content = f.read()
                # Multiple services suggest microservices
                service_count = content.count('services:')
                if service_count > 0:
                    services = re.findall(r'^\s{2,4}(\w+):', content, re.MULTILINE)
                    if len(services) > 2:  # More than 2 services
                        return 'Microservices'
        
        # Check for monorepo indicators
        if (self.project_path / 'lerna.json').exists():
            return 'Monorepo (Lerna)'
        if (self.project_path / 'nx.json').exists():
            return 'Monorepo (Nx)'
        if (self.project_path / 'pnpm-workspace.yaml').exists():
            return 'Monorepo (pnpm)'
        if (self.project_path / 'rush.json').exists():
            return 'Monorepo (Rush)'
        
        # Check for serverless
        if (self.project_path / 'serverless.yml').exists() or (self.project_path / 'serverless.yaml').exists():
            return 'Serverless'
        
        # Check for packages directory (monorepo pattern)
        packages_dir = self.project_path / 'packages'
        if packages_dir.exists() and packages_dir.is_dir():
            subdirs = [d for d in packages_dir.iterdir() if d.is_dir()]
            if len(subdirs) > 1:
                return 'Monorepo'
        
        # Check for apps directory (monorepo pattern)
        apps_dir = self.project_path / 'apps'
        if apps_dir.exists() and apps_dir.is_dir():
            subdirs = [d for d in apps_dir.iterdir() if d.is_dir()]
            if len(subdirs) > 1:
                return 'Monorepo'
        
        # Check for modular architecture
        src_dir = self.project_path / 'src'
        if src_dir.exists():
            modules = ['modules', 'features', 'domains', 'components']
            for module_type in modules:
                module_dir = src_dir / module_type
                if module_dir.exists() and module_dir.is_dir():
                    return f'Modular ({module_type})'
        
        # Default to monolith
        return 'Monolithic'
    
    def _extract_conventions(self) -> str:
        """Extract coding conventions from various sources"""
        conventions = []
        
        # Check for linting/formatting configs
        if (self.project_path / '.eslintrc.json').exists() or (self.project_path / '.eslintrc.js').exists():
            conventions.append("ESLint for JavaScript linting")
        
        if (self.project_path / '.prettierrc').exists() or (self.project_path / '.prettierrc.json').exists():
            conventions.append("Prettier for code formatting")
        
        if (self.project_path / '.editorconfig').exists():
            conventions.append("EditorConfig for consistent coding styles")
        
        if (self.project_path / 'tslint.json').exists():
            conventions.append("TSLint for TypeScript linting")
        
        if (self.project_path / '.flake8').exists() or (self.project_path / 'setup.cfg').exists():
            conventions.append("Flake8 for Python linting")
        
        if (self.project_path / '.rubocop.yml').exists():
            conventions.append("RuboCop for Ruby linting")
        
        # Check for pre-commit hooks
        if (self.project_path / '.pre-commit-config.yaml').exists():
            conventions.append("Pre-commit hooks for code quality")
        
        if (self.project_path / '.husky').exists():
            conventions.append("Husky for Git hooks")
        
        # Check for testing conventions
        if (self.project_path / 'jest.config.js').exists() or (self.project_path / 'jest.config.json').exists():
            conventions.append("Jest for JavaScript testing")
        
        if (self.project_path / 'pytest.ini').exists() or (self.project_path / 'setup.cfg').exists():
            conventions.append("Pytest for Python testing")
        
        # Check for Git workflow
        if (self.project_path / '.github' / 'workflows').exists():
            conventions.append("GitHub Actions for CI/CD")
        
        if (self.project_path / '.gitlab-ci.yml').exists():
            conventions.append("GitLab CI/CD")
        
        if (self.project_path / 'Jenkinsfile').exists():
            conventions.append("Jenkins for CI/CD")
        
        if (self.project_path / '.circleci').exists():
            conventions.append("CircleCI for CI/CD")
        
        return '\n'.join(f"- {conv}" for conv in conventions) if conventions else "No specific conventions detected"
    
    def _find_file(self, filenames: List[str]) -> Optional[Path]:
        """Find first existing file from list"""
        for filename in filenames:
            path = self.project_path / filename
            if path.exists():
                return path
        return None
    
    def _categorize_command(self, name: str, command: str) -> str:
        """Categorize a command based on its name and content"""
        name_lower = name.lower()
        command_lower = command.lower() if command else ''
        
        if any(keyword in name_lower for keyword in ['test', 'spec', 'check']):
            return 'test'
        elif any(keyword in name_lower for keyword in ['build', 'compile', 'bundle']):
            return 'build'
        elif any(keyword in name_lower for keyword in ['deploy', 'publish', 'release']):
            return 'deploy'
        elif any(keyword in name_lower for keyword in ['dev', 'start', 'serve', 'watch']):
            return 'dev'
        elif any(keyword in name_lower for keyword in ['lint', 'format', 'prettier', 'eslint']):
            return 'lint'
        elif any(keyword in name_lower for keyword in ['clean', 'clear', 'reset']):
            return 'clean'
        elif any(keyword in name_lower for keyword in ['install', 'setup', 'init']):
            return 'setup'
        elif any(keyword in name_lower for keyword in ['migrate', 'migration', 'db']):
            return 'database'
        else:
            return 'other'
    
    def _generate_command_description(self, name: str, command: str) -> str:
        """Generate a description for a command"""
        category = self._categorize_command(name, command)
        
        descriptions = {
            'test': f"Run {name} tests",
            'build': f"Build the project ({name})",
            'deploy': f"Deploy using {name}",
            'dev': f"Start development server ({name})",
            'lint': f"Run {name} linting/formatting",
            'clean': f"Clean/reset {name}",
            'setup': f"Setup/install {name}",
            'database': f"Database operation: {name}",
            'other': f"Run {name}"
        }
        
        return descriptions.get(category, f"Run {name}")
    
    def _analyze_module(self, path: Path) -> Optional[Module]:
        """Analyze a directory to see if it's a significant module"""
        if not self._is_significant_module(path):
            return None
        
        name = path.name
        has_tests = self._has_tests(path)
        has_docs = self._has_docs(path)
        key_files = self._find_key_files(path)
        dependencies = self._extract_module_dependencies(path)
        
        # Generate description based on contents
        description = self._generate_module_description(path)
        
        # Find test command specific to this module
        test_command = self._find_module_test_command(path)
        
        return Module(
            name=name,
            path=path,
            description=description,
            has_tests=has_tests,
            has_docs=has_docs,
            key_files=key_files,
            dependencies=dependencies,
            test_command=test_command
        )
    
    def _is_significant_module(self, path: Path) -> bool:
        """Check if a directory is significant enough to be a module"""
        # Must have at least some code files
        code_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs']
        code_files = []
        
        for ext in code_extensions:
            code_files.extend(path.rglob(f'*{ext}'))
            if len(code_files) > 2:  # At least 3 code files
                return True
        
        return False
    
    def _has_tests(self, path: Path) -> bool:
        """Check if module has tests"""
        test_patterns = ['test_*.py', '*_test.py', '*.test.js', '*.spec.js', 
                        '*.test.ts', '*.spec.ts', '__tests__', 'tests']
        
        for pattern in test_patterns:
            if list(path.rglob(pattern)):
                return True
        
        return False
    
    def _has_docs(self, path: Path) -> bool:
        """Check if module has documentation"""
        doc_files = ['README.md', 'README.rst', 'README.txt', 'docs']
        
        for doc_file in doc_files:
            if (path / doc_file).exists():
                return True
        
        return False
    
    def _find_key_files(self, path: Path) -> List[str]:
        """Find key files in a module"""
        key_files = []
        
        # Common important files
        important_names = ['index', 'main', 'app', '__init__', 'routes', 
                          'models', 'views', 'controllers', 'services',
                          'handlers', 'middleware', 'config', 'schema']
        
        for name in important_names:
            for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go']:
                file_path = path / f"{name}{ext}"
                if file_path.exists():
                    key_files.append(file_path.relative_to(path).as_posix())
        
        return key_files[:5]  # Return top 5 key files
    
    def _extract_module_dependencies(self, path: Path) -> List[str]:
        """Extract dependencies specific to a module"""
        dependencies = []
        
        # Check for module-specific package.json
        module_package = path / 'package.json'
        if module_package.exists():
            with open(module_package, 'r') as f:
                pkg = json.load(f)
                deps = pkg.get('dependencies', {})
                dependencies.extend(deps.keys())
        
        # Check for module-specific requirements.txt
        module_requirements = path / 'requirements.txt'
        if module_requirements.exists():
            with open(module_requirements, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name (before any version specifier)
                        pkg_name = re.split(r'[<>=!]', line)[0].strip()
                        dependencies.append(pkg_name)
        
        return dependencies[:10]  # Return top 10 dependencies
    
    def _generate_module_description(self, path: Path) -> str:
        """Generate description for a module based on its contents"""
        name = path.name
        
        # Try to read from module's README
        readme_path = path / 'README.md'
        if readme_path.exists():
            with open(readme_path, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.strip() and not line.startswith('#'):
                        return line.strip()
        
        # Generate based on name and contents
        if 'auth' in name.lower():
            return "Authentication and authorization module"
        elif 'api' in name.lower():
            return "API endpoints and routes"
        elif 'database' in name.lower() or 'db' in name.lower():
            return "Database models and operations"
        elif 'test' in name.lower():
            return "Test suites and testing utilities"
        elif 'util' in name.lower() or 'helper' in name.lower():
            return "Utility functions and helpers"
        elif 'component' in name.lower():
            return "UI components"
        elif 'service' in name.lower():
            return "Business logic and services"
        elif 'model' in name.lower():
            return "Data models and schemas"
        else:
            return f"{name} module"
    
    def _find_module_test_command(self, path: Path) -> Optional[str]:
        """Find test command specific to a module"""
        module_name = path.name
        
        # Check if there's a specific test script in package.json
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            with open(package_json, 'r') as f:
                pkg = json.load(f)
                scripts = pkg.get('scripts', {})
                
                # Look for module-specific test scripts
                for script_name, script_cmd in scripts.items():
                    if module_name in script_name and 'test' in script_name:
                        return f"npm run {script_name}"
        
        # Check for Makefile targets
        makefile = self.project_path / 'Makefile'
        if makefile.exists():
            with open(makefile, 'r') as f:
                content = f.read()
                # Look for module-specific targets
                if f'test-{module_name}' in content:
                    return f"make test-{module_name}"
        
        return None
    
    def _extract_numbered_steps(self, content: str, section_keyword: str) -> List[str]:
        """Extract numbered steps from a documentation section"""
        steps = []
        
        # Find the section
        section_start = content.lower().find(section_keyword.lower())
        if section_start == -1:
            return steps
        
        # Extract numbered lists (1. 2. 3. etc)
        pattern = r'^\s*\d+\.\s+(.+)$'
        lines = content[section_start:].split('\n')
        
        for line in lines[:20]:  # Check next 20 lines
            match = re.match(pattern, line)
            if match:
                steps.append(match.group(1).strip())
        
        return steps
    
    def _find_entry_points(self) -> List[str]:
        """Find application entry points"""
        entry_points = []
        
        # Common entry point files
        common_entries = [
            'main.py', 'app.py', 'index.js', 'index.ts', 'main.js', 'main.ts',
            'server.js', 'server.ts', 'start.js', 'start.ts', 'index.html',
            'main.go', 'main.rs', 'Main.java', 'Program.cs'
        ]
        
        for entry in common_entries:
            entry_path = self.project_path / entry
            if entry_path.exists():
                entry_points.append(entry)
        
        # Check src directory
        src_dir = self.project_path / 'src'
        if src_dir.exists():
            for entry in common_entries:
                entry_path = src_dir / entry
                if entry_path.exists():
                    entry_points.append(f"src/{entry}")
        
        # Check package.json main field
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            with open(package_json, 'r') as f:
                pkg = json.load(f)
                if 'main' in pkg:
                    entry_points.append(pkg['main'])
        
        return entry_points
    
    def _extract_api_endpoints(self) -> Optional[List[str]]:
        """Extract API endpoints from route definitions"""
        endpoints = []
        
        # This would need more sophisticated parsing based on framework
        # For now, return None to indicate it needs framework-specific extraction
        return None if not endpoints else endpoints
    
    def _check_dependency_exists(self, dependencies: List[str]) -> bool:
        """Check if any of the dependencies exist in the project"""
        # Check package.json
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            with open(package_json, 'r') as f:
                pkg = json.load(f)
                all_deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                for dep in dependencies:
                    if dep in all_deps:
                        return True
        
        # Check Python requirements
        requirements_files = ['requirements.txt', 'Pipfile', 'pyproject.toml']
        for req_file in requirements_files:
            req_path = self.project_path / req_file
            if req_path.exists():
                with open(req_path, 'r') as f:
                    content = f.read().lower()
                    for dep in dependencies:
                        if dep.lower() in content:
                            return True
        
        return False
    
    def _extract_testing_conventions(self) -> str:
        """Extract testing conventions"""
        conventions = []
        
        if (self.project_path / 'jest.config.js').exists():
            conventions.append("Jest for JavaScript testing")
        if (self.project_path / 'pytest.ini').exists():
            conventions.append("Pytest for Python testing")
        if (self.project_path / '.mocharc.json').exists():
            conventions.append("Mocha for JavaScript testing")
        if (self.project_path / 'karma.conf.js').exists():
            conventions.append("Karma for testing")
        
        return ', '.join(conventions) if conventions else "Standard testing practices"
    
    def _extract_git_conventions(self) -> str:
        """Extract Git conventions"""
        conventions = []
        
        # Check for branch protection rules (would need API access)
        gitignore = self.project_path / '.gitignore'
        if gitignore.exists():
            conventions.append(".gitignore configured")
        
        # Check for commit message conventions
        if (self.project_path / '.gitmessage').exists():
            conventions.append("Git message template configured")
        
        if (self.project_path / '.commitlintrc.json').exists():
            conventions.append("Commitlint for commit message linting")
        
        return ', '.join(conventions) if conventions else "Standard Git workflow"


# Simple test function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = os.getcwd()
    
    print(f"Extracting knowledge from: {project_path}\n")
    
    extractor = ProjectKnowledgeExtractor(project_path)
    
    # Extract project info
    info = extractor.extract_project_info()
    print(f"Project: {info.name}")
    print(f"Description: {info.description}")
    print(f"Languages: {', '.join(info.languages)}")
    print(f"Frameworks: {', '.join(info.frameworks)}")
    print(f"Architecture: {info.architecture}")
    
    # Extract commands
    print("\nExtracted Commands:")
    commands = extractor.extract_commands()
    for name, cmd in list(commands.items())[:5]:  # Show first 5
        print(f"  {name}: {cmd.command} ({cmd.category})")
    
    # Extract modules
    print("\nIdentified Modules:")
    modules = extractor.identify_modules()
    for module in modules[:5]:  # Show first 5
        print(f"  {module.name}: {module.description}")