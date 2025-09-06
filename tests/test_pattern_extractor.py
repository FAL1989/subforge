#!/usr/bin/env python3
"""
Test suite for Pattern Extractor module
Tests pattern extraction, architecture patterns, and framework patterns
"""

import pytest
from unittest.mock import Mock

from subforge.core.context.patterns import PatternExtractor, ContextLevel
from subforge.core.context.types import Pattern
from subforge.core.project_analyzer import (
    ProjectProfile,
    TechnologyStack,
    ArchitecturePattern,
    ProjectComplexity,
)


class TestPatternExtractor:
    """Test PatternExtractor functionality"""
    
    @pytest.fixture
    def extractor(self):
        """Create PatternExtractor instance"""
        return PatternExtractor()
    
    @pytest.fixture
    def mock_profile(self):
        """Create mock project profile"""
        profile = Mock(spec=ProjectProfile)
        profile.name = "test-project"
        profile.technology_stack = TechnologyStack(
            languages={"python", "typescript"},
            frameworks={"fastapi", "react"},
            databases={"postgresql"},
            tools={"docker"},
            package_managers={"pip", "npm"},
        )
        profile.architecture_pattern = ArchitecturePattern.MICROSERVICES
        profile.complexity = ProjectComplexity.COMPLEX
        profile.team_size_estimate = 5
        profile.has_tests = True
        profile.has_ci_cd = True
        profile.has_docker = True
        return profile
    
    def test_extract_from_profile_minimal(self, extractor, mock_profile):
        """Test pattern extraction from project profile with minimal context"""
        patterns = extractor.extract_from_profile(
            mock_profile, "generation", ContextLevel.MINIMAL
        )
        
        assert isinstance(patterns, list)
        assert all(isinstance(p, dict) for p in patterns)
        assert len(patterns) > 0
        
        # Should have base patterns
        assert any(p["name"] == "Agent Specialization Pattern" for p in patterns)
        assert any(p["name"] == "Team Coordination Pattern" for p in patterns)
    
    def test_extract_from_profile_standard(self, extractor, mock_profile):
        """Test pattern extraction with standard context level"""
        patterns = extractor.extract_from_profile(
            mock_profile, "generation", ContextLevel.STANDARD
        )
        
        assert len(patterns) > 0
        # Should have base patterns but not advanced
        pattern_names = [p["name"] for p in patterns]
        assert "Agent Specialization Pattern" in pattern_names
        assert "Team Coordination Pattern" in pattern_names
    
    def test_extract_from_profile_deep(self, extractor, mock_profile):
        """Test pattern extraction with deep context level"""
        patterns = extractor.extract_from_profile(
            mock_profile, "generation", ContextLevel.DEEP
        )
        
        # Should have base + advanced patterns
        pattern_names = [p["name"] for p in patterns]
        assert "Agent Specialization Pattern" in pattern_names
        assert "Test-Driven Development Pattern" in pattern_names
        assert "Continuous Integration Pattern" in pattern_names
    
    def test_extract_from_profile_expert(self, extractor, mock_profile):
        """Test pattern extraction with expert context level"""
        patterns = extractor.extract_from_profile(
            mock_profile, "generation", ContextLevel.EXPERT
        )
        
        # Should have all pattern types
        pattern_names = [p["name"] for p in patterns]
        assert "Agent Specialization Pattern" in pattern_names
        assert "Test-Driven Development Pattern" in pattern_names
        assert "Enterprise Coordination Pattern" in pattern_names
        assert "Domain-Driven Design Pattern" in pattern_names
        assert "Service Mesh Pattern" in pattern_names  # Microservices-specific
    
    def test_architecture_patterns_microservices(self, extractor):
        """Test microservices architecture patterns"""
        patterns = extractor.extract_from_architecture("microservices", "generation")
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern["name"] == "Microservices Communication Pattern"
        assert "Resilience" in pattern["benefits"]
        assert "REST APIs" in str(pattern["examples"])
    
    def test_architecture_patterns_serverless(self, extractor):
        """Test serverless architecture patterns"""
        patterns = extractor.extract_from_architecture("serverless", "generation")
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern["name"] == "Serverless Event Pattern"
        assert "Cost efficiency" in pattern["benefits"]
        assert "Lambda" in str(pattern["examples"])
    
    def test_architecture_patterns_monolithic(self, extractor):
        """Test monolithic architecture patterns"""
        patterns = extractor.extract_from_architecture("monolithic", "generation")
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern["name"] == "Modular Monolith Pattern"
        assert "Simplicity" in pattern["benefits"]
        assert "Layered architecture" in str(pattern["examples"])
    
    def test_architecture_patterns_event_driven(self, extractor):
        """Test event-driven architecture patterns"""
        patterns = extractor.extract_from_architecture("event-driven", "generation")
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern["name"] == "Event Sourcing Pattern"
        assert "Audit trail" in pattern["benefits"]
        assert "Event store" in str(pattern["examples"])
    
    def test_framework_patterns_react(self, extractor):
        """Test React framework patterns"""
        patterns = extractor.extract_from_frameworks(["react"], "generation")
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert "React Component Pattern" in pattern["name"]
        assert "Reusability" in pattern["benefits"]
        assert "Atomic design" in str(pattern["examples"])
    
    def test_framework_patterns_fastapi(self, extractor):
        """Test FastAPI framework patterns"""
        patterns = extractor.extract_from_frameworks(["fastapi"], "generation")
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert "Fastapi API Pattern" in pattern["name"]
        assert "Consistency" in pattern["benefits"]
        assert "RESTful endpoints" in str(pattern["examples"])
    
    def test_framework_patterns_nextjs(self, extractor):
        """Test Next.js framework patterns"""
        patterns = extractor.extract_from_frameworks(["nextjs"], "generation")
        
        assert len(patterns) == 1
        pattern = patterns[0]
        assert "Nextjs Fullstack Pattern" in pattern["name"]
        assert "SEO optimization" in pattern["benefits"]
        assert "Server components" in str(pattern["examples"])
    
    def test_pattern_relevance(self, extractor):
        """Test pattern scoring/relevance"""
        # Create profiles with different characteristics
        simple_profile = Mock(spec=ProjectProfile)
        simple_profile.complexity = ProjectComplexity.SIMPLE
        simple_profile.team_size_estimate = 1
        simple_profile.has_tests = False
        simple_profile.has_ci_cd = False
        
        complex_profile = Mock(spec=ProjectProfile)
        complex_profile.complexity = ProjectComplexity.COMPLEX
        complex_profile.team_size_estimate = 10
        complex_profile.has_tests = True
        complex_profile.has_ci_cd = True
        
        # Simple profile should get fewer patterns
        simple_patterns = extractor.extract_from_profile(
            simple_profile, "generation", ContextLevel.STANDARD
        )
        
        # Complex profile should get more patterns
        complex_patterns = extractor.extract_from_profile(
            complex_profile, "generation", ContextLevel.STANDARD
        )
        
        # Complex should have more patterns due to team size and features
        assert len(complex_patterns) >= len(simple_patterns)
    
    def test_pattern_combination(self, extractor, mock_profile):
        """Test combining multiple patterns from different sources"""
        # Extract from multiple sources
        arch_patterns = extractor.extract_from_architecture("microservices", "generation")
        framework_patterns = extractor.extract_from_frameworks(
            ["react", "fastapi"], "generation"
        )
        profile_patterns = extractor.extract_from_profile(
            mock_profile, "generation", ContextLevel.STANDARD
        )
        
        # All should be valid patterns
        all_patterns = arch_patterns + framework_patterns + profile_patterns
        assert all(isinstance(p, dict) for p in all_patterns)
        assert all("name" in p for p in all_patterns)
        assert all("purpose" in p for p in all_patterns)
        assert all("implementation" in p for p in all_patterns)
        assert all("benefits" in p for p in all_patterns)
        assert all("examples" in p for p in all_patterns)
    
    def test_pattern_registry_initialization(self, extractor):
        """Test pattern registry is properly initialized"""
        registry = extractor._pattern_registry
        
        assert "separation_of_concerns" in registry
        assert "dependency_injection" in registry
        assert "repository_pattern" in registry
        
        # Check registry patterns have proper structure
        for key, pattern in registry.items():
            assert isinstance(pattern, dict)
            assert "name" in pattern
            assert "purpose" in pattern
            assert "implementation" in pattern
            assert "benefits" in pattern
            assert "examples" in pattern
    
    def test_team_coordination_pattern_threshold(self, extractor):
        """Test team coordination pattern only appears for larger teams"""
        # Small team
        small_team_profile = Mock(spec=ProjectProfile)
        small_team_profile.team_size_estimate = 2
        small_team_profile.has_tests = False
        small_team_profile.has_ci_cd = False
        
        patterns = extractor.extract_from_profile(
            small_team_profile, "generation", ContextLevel.STANDARD
        )
        pattern_names = [p["name"] for p in patterns]
        assert "Team Coordination Pattern" not in pattern_names
        
        # Large team
        large_team_profile = Mock(spec=ProjectProfile)
        large_team_profile.team_size_estimate = 5
        large_team_profile.has_tests = False
        large_team_profile.has_ci_cd = False
        
        patterns = extractor.extract_from_profile(
            large_team_profile, "generation", ContextLevel.STANDARD
        )
        pattern_names = [p["name"] for p in patterns]
        assert "Team Coordination Pattern" in pattern_names
    
    def test_no_test_patterns_without_tests(self, extractor):
        """Test that TDD pattern doesn't appear without tests"""
        profile = Mock(spec=ProjectProfile)
        profile.has_tests = False
        profile.has_ci_cd = False
        profile.complexity = ProjectComplexity.SIMPLE
        profile.team_size_estimate = 1
        
        patterns = extractor.extract_from_profile(
            profile, "generation", ContextLevel.DEEP
        )
        
        pattern_names = [p["name"] for p in patterns]
        assert "Test-Driven Development Pattern" not in pattern_names
    
    def test_multiple_framework_patterns(self, extractor):
        """Test extracting patterns for multiple frameworks"""
        frameworks = ["react", "vue", "angular", "django", "fastapi", "nextjs"]
        patterns = extractor.extract_from_frameworks(frameworks, "generation")
        
        # Should have one pattern per framework type
        assert len(patterns) >= 3  # At least SPA, API, and fullstack patterns
        
        # Check variety of patterns
        pattern_names = [p["name"] for p in patterns]
        assert any("Component Pattern" in name for name in pattern_names)
        assert any("API Pattern" in name for name in pattern_names)
        assert any("Fullstack Pattern" in name for name in pattern_names)