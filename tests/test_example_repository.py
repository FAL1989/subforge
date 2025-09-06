#!/usr/bin/env python3
"""
Test suite for Example Repository module
Tests example management, caching, and relevance ranking
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from subforge.core.context.repository import ExampleRepository
from subforge.core.context.types import Example
from subforge.core.project_analyzer import (
    ProjectProfile,
    TechnologyStack,
    ArchitecturePattern,
    ProjectComplexity,
)


class TestExampleRepository:
    """Test ExampleRepository functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def repository(self, temp_dir):
        """Create ExampleRepository instance"""
        return ExampleRepository(temp_dir)
    
    @pytest.fixture
    def mock_profile(self):
        """Create mock project profile"""
        profile = Mock(spec=ProjectProfile)
        profile.technology_stack = TechnologyStack(
            languages={"python", "javascript", "typescript"},
            frameworks={"fastapi", "react", "nextjs"},
            databases={"postgresql"},
            tools={"docker"},
            package_managers={"pip", "npm"},
        )
        profile.architecture_pattern = ArchitecturePattern.MICROSERVICES
        profile.complexity = ProjectComplexity.COMPLEX
        return profile
    
    @pytest.mark.asyncio
    async def test_find_by_language_python(self, repository):
        """Test finding Python examples"""
        examples = await repository.find_by_language("python", "generation")
        
        assert len(examples) > 0
        assert all(isinstance(ex, dict) for ex in examples)
        assert any("Python" in ex.get("title", "") for ex in examples)
    
    @pytest.mark.asyncio
    async def test_find_by_language_javascript(self, repository):
        """Test finding JavaScript examples"""
        examples = await repository.find_by_language("javascript", "generation")
        
        assert len(examples) > 0
        assert any("JavaScript" in ex.get("title", "") for ex in examples)
    
    @pytest.mark.asyncio
    async def test_find_by_language_typescript(self, repository):
        """Test finding TypeScript examples"""
        examples = await repository.find_by_language("typescript", "generation")
        
        assert len(examples) > 0
        assert any("TypeScript" in ex.get("title", "") for ex in examples)
    
    @pytest.mark.asyncio
    async def test_find_by_framework_fastapi(self, repository):
        """Test finding FastAPI examples"""
        examples = await repository.find_by_framework("fastapi", "generation")
        
        assert len(examples) > 0
        assert any("FastAPI" in ex.get("title", "") or "API" in ex.get("title", "") for ex in examples)
    
    @pytest.mark.asyncio
    async def test_find_by_framework_react(self, repository):
        """Test finding React examples"""
        examples = await repository.find_by_framework("react", "generation")
        
        assert len(examples) > 0
        assert any("React" in ex.get("title", "") for ex in examples)
    
    @pytest.mark.asyncio
    async def test_find_by_framework_nextjs(self, repository):
        """Test finding Next.js examples"""
        examples = await repository.find_by_framework("nextjs", "generation")
        
        assert len(examples) > 0
        assert any("Next.js" in ex.get("title", "") for ex in examples)
    
    @pytest.mark.asyncio
    async def test_find_by_architecture_microservices(self, repository):
        """Test finding microservices architecture examples"""
        examples = await repository.find_by_architecture("microservices", "generation")
        
        assert len(examples) > 0
        assert any("Microservices" in ex.get("title", "") for ex in examples)
    
    @pytest.mark.asyncio
    async def test_find_by_architecture_monolithic(self, repository):
        """Test finding monolithic architecture examples"""
        examples = await repository.find_by_architecture("monolithic", "generation")
        
        assert len(examples) > 0
        assert any("Monolithic" in ex.get("title", "") for ex in examples)
    
    @pytest.mark.asyncio
    async def test_find_by_architecture_serverless(self, repository):
        """Test finding serverless architecture examples"""
        examples = await repository.find_by_architecture("serverless", "generation")
        
        assert len(examples) > 0
        assert any("Serverless" in ex.get("title", "") for ex in examples)
    
    @pytest.mark.asyncio
    async def test_repository_caching(self, repository):
        """Test caching mechanism"""
        # First call - should fetch and cache
        examples1 = await repository.find_by_language("python", "generation")
        
        # Second call - should use cache
        examples2 = await repository.find_by_language("python", "generation")
        
        assert examples1 == examples2
        assert repository._examples_cache.get("python:generation") == examples1
    
    @pytest.mark.asyncio
    async def test_example_ranking(self, repository, mock_profile):
        """Test relevance ranking in find_relevant"""
        examples = await repository.find_relevant(mock_profile, "generation", limit=5)
        
        assert len(examples) <= 5
        assert all(isinstance(ex, dict) for ex in examples)
        
        # Check for duplicate removal
        titles = [ex.get("title", "") for ex in examples]
        assert len(titles) == len(set(titles))  # No duplicates
    
    @pytest.mark.asyncio
    async def test_empty_results(self, repository):
        """Test when no examples found"""
        # Using a non-existent language/phase combination
        examples = await repository.find_by_language("cobol", "unknown_phase")
        
        assert examples == []
    
    @pytest.mark.asyncio
    async def test_find_relevant_with_limit(self, repository, mock_profile):
        """Test find_relevant respects limit parameter"""
        examples_3 = await repository.find_relevant(mock_profile, "generation", limit=3)
        examples_10 = await repository.find_relevant(mock_profile, "generation", limit=10)
        
        assert len(examples_3) <= 3
        assert len(examples_10) <= 10
    
    def test_clear_cache(self, repository):
        """Test cache clearing"""
        # Add some items to cache
        repository._examples_cache["test:key1"] = []
        repository._examples_cache["test:key2"] = []
        
        assert len(repository._examples_cache) == 2
        
        repository.clear_cache()
        
        assert len(repository._examples_cache) == 0
    
    def test_examples_dir_creation(self, temp_dir):
        """Test that examples directory is created"""
        repository = ExampleRepository(temp_dir)
        
        assert (temp_dir / "examples").exists()
        assert (temp_dir / "examples").is_dir()
    
    @pytest.mark.asyncio
    async def test_language_examples_structure(self, repository):
        """Test that language examples have proper structure"""
        examples = await repository.find_by_language("python", "generation")
        
        for example in examples:
            assert "title" in example
            assert "purpose" in example
            assert "language" in example
            assert "code" in example
            assert "notes" in example
    
    @pytest.mark.asyncio
    async def test_framework_examples_structure(self, repository):
        """Test that framework examples have proper structure"""
        examples = await repository.find_by_framework("fastapi", "generation")
        
        for example in examples:
            assert "title" in example
            assert "purpose" in example
            assert "language" in example
            assert "code" in example
            assert "notes" in example
    
    @pytest.mark.asyncio
    async def test_architecture_examples_structure(self, repository):
        """Test that architecture examples have proper structure"""
        examples = await repository.find_by_architecture("microservices", "generation")
        
        for example in examples:
            assert "title" in example
            assert "purpose" in example
            assert "language" in example
            assert "code" in example
            assert "notes" in example
    
    @pytest.mark.asyncio
    async def test_case_insensitive_lookup(self, repository):
        """Test that lookups are case-insensitive"""
        examples_lower = await repository.find_by_language("python", "generation")
        examples_upper = await repository.find_by_language("PYTHON", "generation")
        examples_mixed = await repository.find_by_language("Python", "generation")
        
        # All should return the same examples
        assert examples_lower == examples_upper == examples_mixed
    
    @pytest.mark.asyncio
    async def test_find_relevant_empty_profile(self, repository):
        """Test find_relevant with minimal profile"""
        profile = Mock(spec=ProjectProfile)
        profile.technology_stack = TechnologyStack(
            languages=set(),
            frameworks=set(),
            databases=set(),
            tools=set(),
            package_managers=set(),
        )
        profile.architecture_pattern = ArchitecturePattern.MONOLITHIC
        profile.complexity = ProjectComplexity.SIMPLE
        
        examples = await repository.find_relevant(profile, "generation")
        
        # Should still return some default examples
        assert isinstance(examples, list)