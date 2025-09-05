#!/usr/bin/env python3
"""
Example Repository - Manages code examples and patterns
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .types import Example
from ..project_analyzer import ProjectProfile

logger = logging.getLogger(__name__)


class ExampleRepository:
    """Repository for managing and finding relevant code examples"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.examples_dir = storage_path / "examples"
        self._examples_cache: Dict[str, List[Example]] = {}
        
        # Ensure directory exists
        self.examples_dir.mkdir(parents=True, exist_ok=True)

    async def find_by_language(
        self, language: str, phase: str
    ) -> List[Example]:
        """Find examples specific to a programming language"""
        cache_key = f"{language}:{phase}"
        
        if cache_key in self._examples_cache:
            return self._examples_cache[cache_key]
        
        examples = self._get_language_examples(language.lower(), phase)
        self._examples_cache[cache_key] = examples
        return examples

    async def find_by_framework(
        self, framework: str, phase: str
    ) -> List[Example]:
        """Find examples specific to a framework"""
        cache_key = f"framework:{framework}:{phase}"
        
        if cache_key in self._examples_cache:
            return self._examples_cache[cache_key]
        
        examples = self._get_framework_examples(framework.lower(), phase)
        self._examples_cache[cache_key] = examples
        return examples

    async def find_by_architecture(
        self, architecture: str, phase: str
    ) -> List[Example]:
        """Find examples specific to an architecture pattern"""
        cache_key = f"arch:{architecture}:{phase}"
        
        if cache_key in self._examples_cache:
            return self._examples_cache[cache_key]
        
        examples = self._get_architecture_examples(architecture, phase)
        self._examples_cache[cache_key] = examples
        return examples

    async def find_relevant(
        self, profile: ProjectProfile, phase: str, limit: int = 5
    ) -> List[Example]:
        """Find the most relevant examples for a project profile"""
        all_examples: List[Example] = []
        
        # Gather examples from different sources
        for lang in profile.technology_stack.languages:
            lang_examples = await self.find_by_language(lang, phase)
            all_examples.extend(lang_examples)
        
        for framework in profile.technology_stack.frameworks:
            fw_examples = await self.find_by_framework(framework, phase)
            all_examples.extend(fw_examples)
        
        arch_examples = await self.find_by_architecture(
            profile.architecture_pattern.value, phase
        )
        all_examples.extend(arch_examples)
        
        # Remove duplicates and limit
        seen_titles = set()
        unique_examples = []
        for example in all_examples:
            title = example.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_examples.append(example)
        
        return unique_examples[:limit]

    def _get_language_examples(self, language: str, phase: str) -> List[Example]:
        """Get language-specific examples"""
        examples: List[Example] = []

        if language == "python" and phase == "generation":
            examples.append(
                Example(
                    title="Python CLAUDE.md Configuration",
                    purpose="Standard Python project configuration",
                    language="markdown",
                    code="""# Python Project Configuration

## Build Commands
```bash
python -m pip install -r requirements.txt
python -m pytest tests/
python -m mypy src/
```

## Code Style
- Use Black for formatting
- Follow PEP 8 standards
- Type hints required for public APIs
""",
                    notes="Adapt build commands based on project structure",
                )
            )
            
            examples.append(
                Example(
                    title="Python Agent Template",
                    purpose="Python-focused agent configuration",
                    language="yaml",
                    code="""---
name: python-developer
description: Python development specialist
model: sonnet
tools: [read, write, edit, bash, grep]
---

# Python Developer

You are an expert Python developer specializing in:
- Clean, idiomatic Python code
- Type hints and static typing with mypy
- Comprehensive testing with pytest
- Performance optimization
""",
                    notes="Customize for specific Python frameworks",
                )
            )

        elif language == "javascript" and phase == "generation":
            examples.append(
                Example(
                    title="JavaScript/Node.js Configuration",
                    purpose="Modern JavaScript project setup",
                    language="markdown",
                    code="""# JavaScript Project Configuration

## Build Commands
```bash
npm install
npm run lint
npm run test
npm run build
```

## Code Style
- Use ESLint + Prettier
- Follow Airbnb style guide
- TypeScript preferred for large projects
""",
                    notes="Adjust package manager (npm/yarn/pnpm) based on project",
                )
            )

        elif language == "typescript" and phase == "generation":
            examples.append(
                Example(
                    title="TypeScript Configuration",
                    purpose="TypeScript project configuration",
                    language="markdown",
                    code="""# TypeScript Project Configuration

## Build Commands
```bash
npm install
npm run type-check
npm run lint
npm run test
npm run build
```

## TypeScript Standards
- Strict mode enabled
- No implicit any
- Explicit return types for public APIs
- Interface over type where possible
""",
                    notes="Ensure tsconfig.json is properly configured",
                )
            )

        return examples

    def _get_framework_examples(self, framework: str, phase: str) -> List[Example]:
        """Get framework-specific examples"""
        examples: List[Example] = []

        if framework in ["fastapi", "django"] and phase == "generation":
            examples.append(
                Example(
                    title="FastAPI Agent Configuration",
                    purpose="API-focused agent specialization",
                    language="yaml",
                    code="""---
name: api-developer
description: FastAPI specialist for REST API development
model: sonnet
tools: [read, write, edit, bash, grep]
---

# API Developer - FastAPI Specialist

You are an expert FastAPI developer specializing in:
- RESTful API design and implementation
- Pydantic model validation
- Async/await patterns
- Database integration with SQLAlchemy
- API documentation with OpenAPI
""",
                    notes="Customize based on specific API requirements",
                    framework=framework,
                )
            )

        elif framework == "react" and phase == "generation":
            examples.append(
                Example(
                    title="React Agent Configuration",
                    purpose="React frontend development",
                    language="yaml",
                    code="""---
name: react-developer
description: React specialist for modern UI development
model: sonnet
tools: [read, write, edit, bash, grep]
---

# React Developer

You are an expert React developer specializing in:
- Functional components with hooks
- State management (Redux/Context API)
- Performance optimization
- Testing with React Testing Library
- Responsive design
""",
                    notes="Include state management preferences",
                    framework="react",
                )
            )

        elif framework == "nextjs" and phase == "generation":
            examples.append(
                Example(
                    title="Next.js Full-Stack Configuration",
                    purpose="Next.js application development",
                    language="yaml",
                    code="""---
name: nextjs-developer
description: Next.js full-stack specialist
model: sonnet
tools: [read, write, edit, bash, grep]
---

# Next.js Developer

You are an expert Next.js developer specializing in:
- Server-side rendering (SSR) and static generation (SSG)
- API routes and middleware
- Image optimization and performance
- Incremental Static Regeneration (ISR)
- App Router and layouts
""",
                    notes="Consider App Router vs Pages Router",
                    framework="nextjs",
                )
            )

        return examples

    def _get_architecture_examples(self, architecture: str, phase: str) -> List[Example]:
        """Get architecture pattern examples"""
        examples: List[Example] = []

        if phase == "generation":
            if architecture == "microservices":
                examples.append(
                    Example(
                        title="Microservices Architecture Workflow",
                        purpose="Workflow patterns for microservices",
                        language="markdown",
                        code="""# Microservices Development Workflow

## Service Development Process
1. **Service Design**
   - Define service boundaries
   - Design API contracts
   - Plan data models

2. **Implementation**
   - Implement service logic
   - Add monitoring and health checks
   - Create comprehensive tests

3. **Integration**
   - Test service interactions
   - Validate API contracts
   - Performance testing

## Agent Coordination
- `api-developer`: Service API design
- `backend-developer`: Service implementation
- `devops-engineer`: Container orchestration
- `test-engineer`: Integration testing
""",
                        notes="Customize for specific microservices framework",
                    )
                )
            elif architecture == "monolithic":
                examples.append(
                    Example(
                        title="Monolithic Architecture Workflow",
                        purpose="Workflow for monolithic applications",
                        language="markdown",
                        code="""# Monolithic Development Workflow

## Development Process
1. **Module Development**
   - Implement features in modules
   - Maintain clear module boundaries
   - Share common utilities

2. **Integration**
   - Ensure module compatibility
   - Maintain single database schema
   - Coordinate deployments

## Agent Roles
- `backend-developer`: Core application logic
- `frontend-developer`: UI components
- `database-specialist`: Schema management
- `test-engineer`: End-to-end testing
""",
                        notes="Focus on modular design within monolith",
                    )
                )
            elif architecture == "serverless":
                examples.append(
                    Example(
                        title="Serverless Architecture Workflow",
                        purpose="Workflow for serverless applications",
                        language="markdown",
                        code="""# Serverless Development Workflow

## Function Development Process
1. **Function Design**
   - Single responsibility principle
   - Event-driven architecture
   - Stateless design

2. **Implementation**
   - Lambda/Function implementation
   - API Gateway configuration
   - Event source mapping

3. **Deployment**
   - Infrastructure as Code (IaC)
   - Environment configuration
   - Monitoring and logging

## Specialized Agents
- `serverless-developer`: Function implementation
- `cloud-architect`: AWS/Azure/GCP services
- `devops-engineer`: IaC and deployment
""",
                        notes="Platform-specific (AWS/Azure/GCP)",
                    )
                )
            else:
                # Default/standard architecture
                examples.append(
                    Example(
                        title=f"{architecture.title()} Architecture Workflow",
                        purpose=f"Standard workflow for {architecture}",
                        language="markdown",
                        code="""# Standard Development Workflow

## Feature Development Process
1. **Requirements Analysis**
   - Understand feature requirements
   - Plan implementation approach
   - Identify dependencies

2. **Implementation**
   - Write code following project patterns
   - Add comprehensive tests
   - Update documentation

3. **Quality Assurance**
   - Code review process
   - Integration testing
   - Performance validation
""",
                        notes="Adapt to specific project needs",
                    )
                )

        return examples

    def clear_cache(self):
        """Clear the examples cache"""
        self._examples_cache.clear()
        logger.info("Example repository cache cleared")