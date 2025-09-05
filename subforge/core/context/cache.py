#!/usr/bin/env python3
"""
Cached Context Manager - Manages caching of context packages for performance
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache
from datetime import datetime, timedelta

from .builder import ContextPackage
from .types import ContextPackageDict
from ..project_analyzer import ProjectProfile

logger = logging.getLogger(__name__)


class CachedContextManager:
    """Manages caching of context packages for improved performance"""

    def __init__(self, cache_dir: Path, cache_size: int = 128, ttl_hours: int = 24):
        """
        Initialize the cache manager
        
        Args:
            cache_dir: Directory for persistent cache storage
            cache_size: Maximum number of items in memory cache
            ttl_hours: Time to live for cache entries in hours
        """
        self.cache_dir = cache_dir
        self.cache_size = cache_size
        self.ttl_hours = ttl_hours
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for fast access
        self._memory_cache: Dict[str, tuple[ContextPackage, datetime]] = {}
        
        # Clean up old cache entries on initialization
        self._cleanup_old_cache()

    def get_cached_context(
        self, profile: ProjectProfile, phase: str
    ) -> Optional[ContextPackage]:
        """
        Get cached context if available and valid
        
        Args:
            profile: Project profile
            phase: Factory phase name
            
        Returns:
            Cached context package or None if not found/expired
        """
        cache_key = self.generate_cache_key(profile, phase)
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            context, timestamp = self._memory_cache[cache_key]
            if self._is_cache_valid(timestamp):
                logger.info(f"Context retrieved from memory cache: {cache_key}")
                return context
            else:
                # Remove expired entry
                del self._memory_cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                
                # Check if cache is still valid
                timestamp = datetime.fromisoformat(data["cached_at"])
                if self._is_cache_valid(timestamp):
                    # Reconstruct context package
                    context = self._reconstruct_context(data["context"])
                    
                    # Add to memory cache
                    self._add_to_memory_cache(cache_key, context)
                    
                    logger.info(f"Context retrieved from disk cache: {cache_key}")
                    return context
                else:
                    # Remove expired file
                    cache_file.unlink()
                    
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Invalid cache file {cache_file}: {e}")
                cache_file.unlink()
        
        return None

    def cache_context(
        self, profile: ProjectProfile, phase: str, context: ContextPackage
    ) -> None:
        """
        Cache a context package
        
        Args:
            profile: Project profile
            phase: Factory phase name
            context: Context package to cache
        """
        cache_key = self.generate_cache_key(profile, phase)
        
        # Add to memory cache
        self._add_to_memory_cache(cache_key, context)
        
        # Save to disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            cache_data = {
                "context": context.to_dict(),
                "cached_at": datetime.now().isoformat(),
                "profile_hash": self._hash_profile(profile),
                "phase": phase,
            }
            
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2, default=self._json_serializer)
            
            logger.info(f"Context cached: {cache_key}")
            
        except Exception as e:
            logger.error(f"Failed to cache context: {e}")

    def invalidate_cache(
        self, profile: Optional[ProjectProfile] = None, phase: Optional[str] = None
    ) -> None:
        """
        Invalidate cache entries
        
        Args:
            profile: Project profile (if None, invalidate all)
            phase: Phase name (if None, invalidate all phases for profile)
        """
        if profile is None:
            # Clear all caches
            self._memory_cache.clear()
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("All cache entries invalidated")
            
        elif phase is None:
            # Clear all phases for this profile
            profile_hash = self._hash_profile(profile)
            keys_to_remove = [
                k for k in self._memory_cache.keys()
                if k.startswith(profile_hash)
            ]
            for key in keys_to_remove:
                del self._memory_cache[key]
            
            for cache_file in self.cache_dir.glob(f"{profile_hash}_*.json"):
                cache_file.unlink()
            logger.info(f"Cache invalidated for profile: {profile.name}")
            
        else:
            # Clear specific cache entry
            cache_key = self.generate_cache_key(profile, phase)
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
            
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                cache_file.unlink()
            logger.info(f"Cache invalidated: {cache_key}")

    def generate_cache_key(self, profile: ProjectProfile, phase: str) -> str:
        """
        Generate a deterministic cache key
        
        Args:
            profile: Project profile
            phase: Factory phase name
            
        Returns:
            Cache key string
        """
        profile_hash = self._hash_profile(profile)
        return f"{profile_hash}_{phase}"

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_entries = len(self._memory_cache)
        disk_entries = len(list(self.cache_dir.glob("*.json")))
        
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))
        
        return {
            "memory_entries": memory_entries,
            "disk_entries": disk_entries,
            "total_disk_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
            "ttl_hours": self.ttl_hours,
        }

    def _hash_profile(self, profile: ProjectProfile) -> str:
        """Generate a hash of the project profile for caching"""
        # Create a deterministic string representation
        profile_str = (
            f"{profile.name}:"
            f"{profile.path}:"
            f"{profile.architecture_pattern.value}:"
            f"{profile.complexity.value}:"
            f"{sorted(profile.technology_stack.languages)}:"
            f"{sorted(profile.technology_stack.frameworks)}:"
            f"{profile.file_count}:"
            f"{profile.lines_of_code}"
        )
        return hashlib.md5(profile_str.encode()).hexdigest()[:16]

    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if a cache entry is still valid based on TTL"""
        age = datetime.now() - timestamp
        return age < timedelta(hours=self.ttl_hours)

    def _add_to_memory_cache(self, key: str, context: ContextPackage) -> None:
        """Add context to memory cache with size management"""
        # Remove oldest entries if cache is full
        if len(self._memory_cache) >= self.cache_size:
            # Find and remove oldest entry
            oldest_key = min(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k][1]
            )
            del self._memory_cache[oldest_key]
        
        self._memory_cache[key] = (context, datetime.now())

    def _reconstruct_context(self, data: ContextPackageDict) -> ContextPackage:
        """Reconstruct a ContextPackage from cached data"""
        from .builder import ContextPackage
        
        return ContextPackage(
            project_context=data["project_context"],
            technical_context=data["technical_context"],
            examples=data["examples"],
            patterns=data["patterns"],
            validation_gates=data["validation_gates"],
            references=data["references"],
            success_criteria=data["success_criteria"],
        )

    def _cleanup_old_cache(self) -> None:
        """Clean up expired cache files from disk"""
        cleaned = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                
                timestamp = datetime.fromisoformat(data["cached_at"])
                if not self._is_cache_valid(timestamp):
                    cache_file.unlink()
                    cleaned += 1
                    
            except (json.JSONDecodeError, KeyError, ValueError):
                # Remove invalid cache files
                cache_file.unlink()
                cleaned += 1
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired cache entries")

    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects"""
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, Path):
            return str(obj)
        return str(obj)