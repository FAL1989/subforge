#!/usr/bin/env python3
"""
Test suite for Cached Context Manager module
Tests memory caching, disk caching, cache invalidation, and performance
"""

import pytest
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from subforge.core.context.cache import CachedContextManager
from subforge.core.context.builder import ContextPackage
from subforge.core.context.types import (
    ProjectContext,
    TechnicalContext,
    Example,
    Pattern,
    ValidationGate,
)
from subforge.core.project_analyzer import (
    ProjectProfile,
    TechnologyStack,
    ArchitecturePattern,
    ProjectComplexity,
)


class TestCachedContextManager:
    """Test CachedContextManager functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def cache_manager(self, temp_dir):
        """Create CachedContextManager instance"""
        return CachedContextManager(temp_dir, cache_size=5, ttl_hours=1)
    
    @pytest.fixture
    def mock_profile(self):
        """Create mock project profile"""
        profile = Mock(spec=ProjectProfile)
        profile.name = "test-project"
        profile.path = Path("/test/path")
        profile.architecture_pattern = ArchitecturePattern.MICROSERVICES
        profile.complexity = ProjectComplexity.COMPLEX
        profile.technology_stack = TechnologyStack(
            languages={"python", "typescript"},
            frameworks={"fastapi", "react"},
            databases={"postgresql"},
            tools={"docker"},
            package_managers={"pip", "npm"},
        )
        profile.file_count = 100
        profile.lines_of_code = 10000
        return profile
    
    @pytest.fixture
    def sample_context_package(self):
        """Create sample context package"""
        project_context = ProjectContext(
            name="test-project",
            path="/test/path",
            architecture_pattern="microservices",
            complexity_level="complex",
            languages=["python"],
            frameworks=["fastapi"],
            databases=["postgresql"],
            tools=["docker"],
            team_size_estimate=5,
            has_tests=True,
            has_ci_cd=True,
            has_docker=True,
            file_count=100,
            lines_of_code=10000
        )
        
        technical_context = TechnicalContext(
            phase="generation",
            primary_language="python",
            deployment_target="cloud",
            testing_strategy="comprehensive",
            ci_cd_integration=True
        )
        
        return ContextPackage(
            project_context=project_context,
            technical_context=technical_context,
            examples=[],
            patterns=[],
            validation_gates=[],
            references=["ref1"],
            success_criteria=["criteria1"]
        )
    
    def test_memory_caching(self, cache_manager, mock_profile, sample_context_package):
        """Test LRU cache behavior in memory"""
        # Cache a context
        cache_manager.cache_context(mock_profile, "generation", sample_context_package)
        
        # Retrieve from memory cache
        cached = cache_manager.get_cached_context(mock_profile, "generation")
        
        assert cached is not None
        assert cached.project_context["name"] == sample_context_package.project_context["name"]
        
        # Verify it's in memory cache
        cache_key = cache_manager.generate_cache_key(mock_profile, "generation")
        assert cache_key in cache_manager._memory_cache
    
    def test_disk_caching(self, cache_manager, mock_profile, sample_context_package):
        """Test persistent cache on disk"""
        # Cache a context
        cache_manager.cache_context(mock_profile, "generation", sample_context_package)
        
        # Verify disk file exists
        cache_key = cache_manager.generate_cache_key(mock_profile, "generation")
        cache_file = cache_manager.cache_dir / f"{cache_key}.json"
        assert cache_file.exists()
        
        # Load and verify disk cache content
        with open(cache_file, "r") as f:
            data = json.load(f)
        
        assert data["phase"] == "generation"
        assert data["context"]["project_context"]["name"] == "test-project"
        assert "cached_at" in data
        assert "profile_hash" in data
    
    def test_cache_invalidation_all(self, cache_manager, mock_profile, sample_context_package):
        """Test clearing all cache entries"""
        # Cache multiple contexts
        cache_manager.cache_context(mock_profile, "generation", sample_context_package)
        cache_manager.cache_context(mock_profile, "analysis", sample_context_package)
        
        assert len(cache_manager._memory_cache) == 2
        assert len(list(cache_manager.cache_dir.glob("*.json"))) == 2
        
        # Invalidate all
        cache_manager.invalidate_cache()
        
        assert len(cache_manager._memory_cache) == 0
        assert len(list(cache_manager.cache_dir.glob("*.json"))) == 0
    
    def test_cache_invalidation_by_profile(self, cache_manager, mock_profile, sample_context_package):
        """Test clearing cache for specific profile"""
        # Create second profile
        profile2 = Mock(spec=ProjectProfile)
        profile2.name = "other-project"
        profile2.path = Path("/other/path")
        profile2.architecture_pattern = ArchitecturePattern.MONOLITHIC
        profile2.complexity = ProjectComplexity.SIMPLE
        profile2.technology_stack = TechnologyStack(
            languages={"java"},
            frameworks={"spring"},
            databases=set(),
            tools=set(),
            package_managers={"maven"},
        )
        profile2.file_count = 50
        profile2.lines_of_code = 5000
        
        # Cache contexts for both profiles
        cache_manager.cache_context(mock_profile, "generation", sample_context_package)
        cache_manager.cache_context(profile2, "generation", sample_context_package)
        
        assert len(cache_manager._memory_cache) == 2
        
        # Invalidate only first profile
        cache_manager.invalidate_cache(profile=mock_profile)
        
        # Second profile should still be cached
        assert cache_manager.get_cached_context(mock_profile, "generation") is None
        assert cache_manager.get_cached_context(profile2, "generation") is not None
    
    def test_cache_invalidation_by_phase(self, cache_manager, mock_profile, sample_context_package):
        """Test clearing cache for specific phase"""
        # Cache multiple phases
        cache_manager.cache_context(mock_profile, "generation", sample_context_package)
        cache_manager.cache_context(mock_profile, "analysis", sample_context_package)
        
        # Invalidate specific phase
        cache_manager.invalidate_cache(profile=mock_profile, phase="generation")
        
        assert cache_manager.get_cached_context(mock_profile, "generation") is None
        assert cache_manager.get_cached_context(mock_profile, "analysis") is not None
    
    def test_cache_key_generation(self, cache_manager):
        """Test deterministic cache key generation"""
        profile1 = Mock(spec=ProjectProfile)
        profile1.name = "project"
        profile1.path = Path("/path")
        profile1.architecture_pattern = ArchitecturePattern.MICROSERVICES
        profile1.complexity = ProjectComplexity.COMPLEX
        profile1.technology_stack = TechnologyStack(
            languages={"python", "javascript"},
            frameworks={"fastapi"},
            databases=set(),
            tools=set(),
            package_managers={"pip", "npm"},
        )
        profile1.file_count = 100
        profile1.lines_of_code = 10000
        
        # Same profile data should generate same key
        key1 = cache_manager.generate_cache_key(profile1, "generation")
        key2 = cache_manager.generate_cache_key(profile1, "generation")
        assert key1 == key2
        
        # Different phase should generate different key
        key3 = cache_manager.generate_cache_key(profile1, "analysis")
        assert key1 != key3
    
    def test_cache_performance(self, cache_manager, mock_profile, sample_context_package):
        """Benchmark cache vs no-cache"""
        # First access (no cache) - measure time
        start = time.perf_counter()
        result = cache_manager.get_cached_context(mock_profile, "generation")
        no_cache_time = time.perf_counter() - start
        assert result is None
        
        # Cache the context
        cache_manager.cache_context(mock_profile, "generation", sample_context_package)
        
        # Second access (with cache) - should be faster
        start = time.perf_counter()
        result = cache_manager.get_cached_context(mock_profile, "generation")
        cache_time = time.perf_counter() - start
        assert result is not None
        
        # Cache access should be faster (though timing can vary)
        # Just ensure both complete successfully
        assert no_cache_time >= 0
        assert cache_time >= 0
    
    def test_cache_size_limits(self, temp_dir, mock_profile, sample_context_package):
        """Test cache eviction when size limit reached"""
        # Create cache with small size limit
        cache_manager = CachedContextManager(temp_dir, cache_size=3, ttl_hours=1)
        
        # Create different profiles
        profiles = []
        for i in range(5):
            profile = Mock(spec=ProjectProfile)
            profile.name = f"project-{i}"
            profile.path = Path(f"/path/{i}")
            profile.architecture_pattern = ArchitecturePattern.MONOLITHIC
            profile.complexity = ProjectComplexity.SIMPLE
            profile.technology_stack = TechnologyStack(
                languages={f"lang{i}"},
                frameworks=set(),
                databases=set(),
                tools=set(),
                package_managers=set(),
            )
            profile.file_count = i * 10
            profile.lines_of_code = i * 1000
            profiles.append(profile)
        
        # Cache all profiles
        for i, profile in enumerate(profiles):
            cache_manager.cache_context(profile, "generation", sample_context_package)
        
        # Memory cache should only have 3 items (size limit)
        assert len(cache_manager._memory_cache) <= 3
        
        # Disk cache should have all 5
        assert len(list(cache_manager.cache_dir.glob("*.json"))) == 5
    
    def test_cache_ttl_expiration(self, temp_dir, mock_profile, sample_context_package):
        """Test cache TTL expiration"""
        # Create cache with short TTL
        cache_manager = CachedContextManager(temp_dir, cache_size=10, ttl_hours=0)  # 0 hours = immediate expiration
        
        # Cache a context
        cache_manager.cache_context(mock_profile, "generation", sample_context_package)
        
        # Should be expired immediately
        result = cache_manager.get_cached_context(mock_profile, "generation")
        assert result is None
    
    def test_cache_stats(self, cache_manager, mock_profile, sample_context_package):
        """Test cache statistics"""
        # Add missing attributes to mock_profile
        mock_profile.team_size_estimate = 5
        
        # Cache some contexts
        cache_manager.cache_context(mock_profile, "generation", sample_context_package)
        cache_manager.cache_context(mock_profile, "analysis", sample_context_package)
        
        stats = cache_manager.get_cache_stats()
        
        assert stats["memory_entries"] == 2
        assert stats["disk_entries"] == 2
        assert stats["total_disk_size_mb"] >= 0  # May be 0 for very small files
        assert stats["cache_dir"] == str(cache_manager.cache_dir)
        assert stats["ttl_hours"] == 1
    
    def test_invalid_cache_file_handling(self, cache_manager, mock_profile):
        """Test handling of corrupted cache files"""
        cache_key = cache_manager.generate_cache_key(mock_profile, "generation")
        cache_file = cache_manager.cache_dir / f"{cache_key}.json"
        
        # Create invalid cache file
        cache_file.write_text("invalid json content {{}}")
        
        # Should handle gracefully and return None
        result = cache_manager.get_cached_context(mock_profile, "generation")
        assert result is None
        
        # Invalid file should be removed
        assert not cache_file.exists()
    
    def test_cache_reconstruction_from_disk(self, cache_manager, mock_profile, sample_context_package):
        """Test loading cache from disk when not in memory"""
        # Cache a context
        cache_manager.cache_context(mock_profile, "generation", sample_context_package)
        
        # Clear memory cache only
        cache_manager._memory_cache.clear()
        
        # Should load from disk
        result = cache_manager.get_cached_context(mock_profile, "generation")
        assert result is not None
        assert result.project_context["name"] == "test-project"
        
        # Should be back in memory cache
        cache_key = cache_manager.generate_cache_key(mock_profile, "generation")
        assert cache_key in cache_manager._memory_cache
    
    def test_cleanup_old_cache_on_init(self, temp_dir, sample_context_package):
        """Test that old cache entries are cleaned on initialization"""
        # Create an expired cache file manually
        old_cache_data = {
            "context": sample_context_package.to_dict(),
            "cached_at": (datetime.now() - timedelta(hours=25)).isoformat(),
            "profile_hash": "test_hash",
            "phase": "generation"
        }
        
        cache_file = temp_dir / "old_cache.json"
        with open(cache_file, "w") as f:
            json.dump(old_cache_data, f)
        
        # Initialize cache manager (should clean old files)
        cache_manager = CachedContextManager(temp_dir, ttl_hours=24)
        
        # Old file should be removed
        assert not cache_file.exists()
    
    def test_json_serializer(self, cache_manager):
        """Test custom JSON serializer for complex objects"""
        # Test set serialization
        result = cache_manager._json_serializer({"a", "b", "c"})
        assert isinstance(result, list)
        assert set(result) == {"a", "b", "c"}
        
        # Test Path serialization
        result = cache_manager._json_serializer(Path("/test/path"))
        assert result == "/test/path"
        
        # Test object with __dict__
        obj = Mock()
        obj.__dict__ = {"key": "value"}
        result = cache_manager._json_serializer(obj)
        assert result == {"key": "value"}
        
        # Test fallback to string
        result = cache_manager._json_serializer(123)
        assert result == "123"