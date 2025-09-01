"""
Redis service for caching, pub/sub, and session management
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager

import aioredis
from aioredis.client import PubSub

from ..core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for caching and pub/sub operations"""
    
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.pubsub_client: Optional[PubSub] = None
        self.subscribers: Dict[str, List[callable]] = {}
        self._pubsub_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=20
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis service initialized")
            
            # Initialize pub/sub
            self.pubsub_client = self.redis_client.pubsub()
            self._pubsub_task = asyncio.create_task(self._listen_for_messages())
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connections"""
        try:
            if self._pubsub_task:
                self._pubsub_task.cancel()
                try:
                    await self._pubsub_task
                except asyncio.CancelledError:
                    pass
            
            if self.pubsub_client:
                await self.pubsub_client.close()
            
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("✅ Redis service closed")
            
        except Exception as e:
            logger.error(f"❌ Error closing Redis: {e}")
    
    async def set(
        self,
        key: str,
        value: Union[str, int, float, dict, list],
        expire: Optional[int] = None
    ) -> bool:
        """Set a value in Redis with optional expiration"""
        try:
            if not self.redis_client:
                return False
            
            # Serialize complex types to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            
            result = await self.redis_client.set(
                key, 
                value, 
                ex=expire or settings.REDIS_EXPIRE
            )
            return result is True
            
        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {e}")
            return False
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value from Redis"""
        try:
            if not self.redis_client:
                return default
            
            value = await self.redis_client.get(key)
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {e}")
            return default
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        try:
            if not self.redis_client:
                return False
            
            result = await self.redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting Redis key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        try:
            if not self.redis_client:
                return False
            
            result = await self.redis_client.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Error checking Redis key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value in Redis"""
        try:
            if not self.redis_client:
                return None
            
            result = await self.redis_client.incrby(key, amount)
            return result
            
        except Exception as e:
            logger.error(f"Error incrementing Redis key {key}: {e}")
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key"""
        try:
            if not self.redis_client:
                return False
            
            result = await self.redis_client.expire(key, seconds)
            return result
            
        except Exception as e:
            logger.error(f"Error setting expiration for Redis key {key}: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern"""
        try:
            if not self.redis_client:
                return []
            
            keys = await self.redis_client.keys(pattern)
            return keys
            
        except Exception as e:
            logger.error(f"Error getting Redis keys with pattern {pattern}: {e}")
            return []
    
    async def flushdb(self) -> bool:
        """Clear all keys in the current database"""
        try:
            if not self.redis_client:
                return False
            
            await self.redis_client.flushdb()
            return True
            
        except Exception as e:
            logger.error(f"Error flushing Redis database: {e}")
            return False
    
    # Hash operations
    async def hset(self, name: str, key: str, value: Union[str, int, float, dict]) -> bool:
        """Set field in a hash"""
        try:
            if not self.redis_client:
                return False
            
            if isinstance(value, dict):
                value = json.dumps(value, default=str)
            
            result = await self.redis_client.hset(name, key, value)
            return result >= 0
            
        except Exception as e:
            logger.error(f"Error setting hash field {name}:{key}: {e}")
            return False
    
    async def hget(self, name: str, key: str) -> Any:
        """Get field from a hash"""
        try:
            if not self.redis_client:
                return None
            
            value = await self.redis_client.hget(name, key)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Error getting hash field {name}:{key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all fields from a hash"""
        try:
            if not self.redis_client:
                return {}
            
            hash_data = await self.redis_client.hgetall(name)
            
            # Try to deserialize JSON values
            result = {}
            for key, value in hash_data.items():
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting hash {name}: {e}")
            return {}
    
    async def hdel(self, name: str, *keys: str) -> bool:
        """Delete fields from a hash"""
        try:
            if not self.redis_client:
                return False
            
            result = await self.redis_client.hdel(name, *keys)
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting hash fields {name}: {e}")
            return False
    
    # List operations
    async def lpush(self, name: str, *values: Union[str, dict]) -> Optional[int]:
        """Push values to the left of a list"""
        try:
            if not self.redis_client:
                return None
            
            serialized_values = []
            for value in values:
                if isinstance(value, dict):
                    serialized_values.append(json.dumps(value, default=str))
                else:
                    serialized_values.append(str(value))
            
            result = await self.redis_client.lpush(name, *serialized_values)
            return result
            
        except Exception as e:
            logger.error(f"Error pushing to list {name}: {e}")
            return None
    
    async def rpop(self, name: str) -> Any:
        """Pop value from the right of a list"""
        try:
            if not self.redis_client:
                return None
            
            value = await self.redis_client.rpop(name)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Error popping from list {name}: {e}")
            return None
    
    async def lrange(self, name: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get a range of elements from a list"""
        try:
            if not self.redis_client:
                return []
            
            values = await self.redis_client.lrange(name, start, end)
            
            result = []
            for value in values:
                try:
                    result.append(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.append(value)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting list range {name}: {e}")
            return []
    
    async def ltrim(self, name: str, start: int, end: int) -> bool:
        """Trim a list to the specified range"""
        try:
            if not self.redis_client:
                return False
            
            result = await self.redis_client.ltrim(name, start, end)
            return result
            
        except Exception as e:
            logger.error(f"Error trimming list {name}: {e}")
            return False
    
    # Set operations
    async def sadd(self, name: str, *values: str) -> Optional[int]:
        """Add members to a set"""
        try:
            if not self.redis_client:
                return None
            
            result = await self.redis_client.sadd(name, *values)
            return result
            
        except Exception as e:
            logger.error(f"Error adding to set {name}: {e}")
            return None
    
    async def srem(self, name: str, *values: str) -> Optional[int]:
        """Remove members from a set"""
        try:
            if not self.redis_client:
                return None
            
            result = await self.redis_client.srem(name, *values)
            return result
            
        except Exception as e:
            logger.error(f"Error removing from set {name}: {e}")
            return None
    
    async def smembers(self, name: str) -> List[str]:
        """Get all members of a set"""
        try:
            if not self.redis_client:
                return []
            
            members = await self.redis_client.smembers(name)
            return list(members)
            
        except Exception as e:
            logger.error(f"Error getting set members {name}: {e}")
            return []
    
    async def sismember(self, name: str, value: str) -> bool:
        """Check if a value is a member of a set"""
        try:
            if not self.redis_client:
                return False
            
            result = await self.redis_client.sismember(name, value)
            return result
            
        except Exception as e:
            logger.error(f"Error checking set membership {name}: {e}")
            return False
    
    # Pub/Sub operations
    async def publish(self, channel: str, message: Union[str, dict]) -> Optional[int]:
        """Publish a message to a channel"""
        try:
            if not self.redis_client:
                return None
            
            if isinstance(message, dict):
                message = json.dumps(message, default=str)
            
            result = await self.redis_client.publish(channel, message)
            return result
            
        except Exception as e:
            logger.error(f"Error publishing to channel {channel}: {e}")
            return None
    
    async def subscribe(self, channel: str, callback: callable):
        """Subscribe to a channel with a callback"""
        try:
            if channel not in self.subscribers:
                self.subscribers[channel] = []
            
            self.subscribers[channel].append(callback)
            
            if self.pubsub_client:
                await self.pubsub_client.subscribe(channel)
            
        except Exception as e:
            logger.error(f"Error subscribing to channel {channel}: {e}")
    
    async def unsubscribe(self, channel: str, callback: Optional[callable] = None):
        """Unsubscribe from a channel"""
        try:
            if channel in self.subscribers:
                if callback:
                    self.subscribers[channel] = [
                        cb for cb in self.subscribers[channel] if cb != callback
                    ]
                else:
                    self.subscribers[channel] = []
                
                if not self.subscribers[channel]:
                    del self.subscribers[channel]
                    if self.pubsub_client:
                        await self.pubsub_client.unsubscribe(channel)
            
        except Exception as e:
            logger.error(f"Error unsubscribing from channel {channel}: {e}")
    
    async def _listen_for_messages(self):
        """Listen for pub/sub messages"""
        if not self.pubsub_client:
            return
        
        try:
            async for message in self.pubsub_client.listen():
                if message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    
                    # Try to deserialize JSON
                    try:
                        data = json.loads(data)
                    except (json.JSONDecodeError, TypeError):
                        pass
                    
                    # Call subscribers
                    if channel in self.subscribers:
                        for callback in self.subscribers[channel]:
                            try:
                                await callback(channel, data)
                            except Exception as e:
                                logger.error(f"Error in subscriber callback: {e}")
        
        except asyncio.CancelledError:
            logger.info("Pub/sub listener cancelled")
        except Exception as e:
            logger.error(f"Error in pub/sub listener: {e}")
    
    # Cache decorators and utilities
    @asynccontextmanager
    async def cache_lock(self, key: str, timeout: int = 60):
        """Distributed lock using Redis"""
        lock_key = f"lock:{key}"
        lock_acquired = False
        
        try:
            # Try to acquire lock
            result = await self.redis_client.set(lock_key, "locked", nx=True, ex=timeout)
            lock_acquired = result is True
            
            if not lock_acquired:
                raise Exception(f"Could not acquire lock for {key}")
            
            yield
            
        finally:
            if lock_acquired:
                await self.redis_client.delete(lock_key)
    
    async def cache_key(self, *parts: str) -> str:
        """Generate a cache key from parts"""
        return ":".join(str(part) for part in parts)
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern"""
        try:
            if not self.redis_client:
                return 0
            
            keys = await self.keys(pattern)
            if keys:
                result = await self.redis_client.delete(*keys)
                return result
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
            return 0


# Global Redis service instance
redis_service = RedisService()