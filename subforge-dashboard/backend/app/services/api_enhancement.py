"""
API enhancement service with rate limiting, caching, and advanced features
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from .redis_service import redis_service

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Security scheme for API authentication
security = HTTPBearer(auto_error=False)


class CacheConfig(BaseModel):
    """Configuration for API caching"""

    ttl: int = 300  # Time to live in seconds
    prefix: str = "api_cache"
    include_headers: List[str] = []
    exclude_params: List[str] = ["timestamp", "cache_bust"]
    vary_by_user: bool = False


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting"""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10


class APIMetrics(BaseModel):
    """API metrics data model"""

    endpoint: str
    method: str
    status_code: int
    response_time: float
    timestamp: datetime
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_size: int = 0
    response_size: int = 0


class APIEnhancementService:
    """Service for API enhancements like caching, rate limiting, and metrics"""

    def __init__(self):
        self.metrics_buffer: List[APIMetrics] = []
        self.buffer_size = 100
        self._metrics_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the API enhancement service"""
        try:
            # Start metrics collection task
            self._metrics_task = asyncio.create_task(self._process_metrics_buffer())
            logger.info("✅ API Enhancement Service initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize API Enhancement Service: {e}")
            raise

    async def shutdown(self):
        """Shutdown the service"""
        try:
            if self._metrics_task:
                self._metrics_task.cancel()
                try:
                    await self._metrics_task
                except asyncio.CancelledError:
                    pass

            # Flush remaining metrics
            if self.metrics_buffer:
                await self._flush_metrics()

            logger.info("✅ API Enhancement Service shut down")

        except Exception as e:
            logger.error(f"❌ Error shutting down API Enhancement Service: {e}")

    def cache_response(
        self,
        ttl: int = 300,
        prefix: str = "api_cache",
        vary_by_user: bool = False,
        include_headers: List[str] = None,
        exclude_params: List[str] = None,
    ):
        """Decorator for caching API responses"""

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract request object
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

                if not request:
                    # No request object found, execute without caching
                    return await func(*args, **kwargs)

                # Generate cache key
                cache_key = await self._generate_cache_key(
                    request,
                    func.__name__,
                    prefix,
                    vary_by_user,
                    include_headers or [],
                    exclude_params or ["timestamp", "cache_bust"],
                )

                # Try to get from cache
                cached_response = await redis_service.get(cache_key)
                if cached_response is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_response

                # Execute function
                result = await func(*args, **kwargs)

                # Cache the result
                await redis_service.set(cache_key, result, expire=ttl)
                logger.debug(f"Cached response for key: {cache_key}")

                return result

            return wrapper

        return decorator

    def rate_limit(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        per_user: bool = False,
    ):
        """Decorator for rate limiting API endpoints"""

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract request object
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

                if not request:
                    return await func(*args, **kwargs)

                # Determine rate limit key
                if per_user:
                    user_id = await self._get_user_id_from_request(request)
                    limit_key = f"rate_limit:user:{user_id}"
                else:
                    client_ip = get_remote_address(request)
                    limit_key = f"rate_limit:ip:{client_ip}"

                # Check rate limits
                await self._check_rate_limits(
                    limit_key, requests_per_minute, requests_per_hour
                )

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    async def record_api_metrics(
        self, request: Request, response: Response, response_time: float, endpoint: str
    ):
        """Record API metrics for monitoring"""
        try:
            user_id = await self._get_user_id_from_request(request)

            metrics = APIMetrics(
                endpoint=endpoint,
                method=request.method,
                status_code=response.status_code,
                response_time=response_time,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                ip_address=get_remote_address(request),
                user_agent=request.headers.get("user-agent", "unknown"),
                request_size=int(request.headers.get("content-length", 0)),
                response_size=len(response.body) if hasattr(response, "body") else 0,
            )

            # Add to buffer
            self.metrics_buffer.append(metrics)

            # Flush buffer if full
            if len(self.metrics_buffer) >= self.buffer_size:
                await self._flush_metrics()

        except Exception as e:
            logger.error(f"Error recording API metrics: {e}")

    async def get_api_statistics(
        self, time_range: str = "24h", endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get API usage statistics"""
        try:
            # Calculate time range
            now = datetime.utcnow()
            if time_range == "1h":
                start_time = now - timedelta(hours=1)
            elif time_range == "24h":
                start_time = now - timedelta(hours=24)
            elif time_range == "7d":
                start_time = now - timedelta(days=7)
            else:
                start_time = now - timedelta(hours=24)

            # Get metrics from Redis
            metrics_key = f"api_metrics:{time_range}"
            cached_stats = await redis_service.get(metrics_key)

            if cached_stats:
                return cached_stats

            # Calculate fresh statistics
            all_metrics = await self._get_metrics_from_storage(start_time, endpoint)

            stats = {
                "time_range": time_range,
                "start_time": start_time.isoformat(),
                "end_time": now.isoformat(),
                "total_requests": len(all_metrics),
                "unique_users": len(set(m.user_id for m in all_metrics if m.user_id)),
                "unique_ips": len(
                    set(m.ip_address for m in all_metrics if m.ip_address)
                ),
                "average_response_time": 0.0,
                "error_rate": 0.0,
                "status_codes": {},
                "endpoints": {},
                "methods": {},
                "hourly_distribution": {},
                "top_user_agents": {},
            }

            if all_metrics:
                # Calculate averages
                total_response_time = sum(m.response_time for m in all_metrics)
                stats["average_response_time"] = total_response_time / len(all_metrics)

                error_count = len([m for m in all_metrics if m.status_code >= 400])
                stats["error_rate"] = (error_count / len(all_metrics)) * 100

                # Count by status codes
                for metric in all_metrics:
                    code = str(metric.status_code)
                    stats["status_codes"][code] = stats["status_codes"].get(code, 0) + 1

                    # Count by endpoints
                    stats["endpoints"][metric.endpoint] = (
                        stats["endpoints"].get(metric.endpoint, 0) + 1
                    )

                    # Count by methods
                    stats["methods"][metric.method] = (
                        stats["methods"].get(metric.method, 0) + 1
                    )

                    # Count by hour
                    hour = metric.timestamp.strftime("%H:00")
                    stats["hourly_distribution"][hour] = (
                        stats["hourly_distribution"].get(hour, 0) + 1
                    )

                    # Count user agents
                    if metric.user_agent:
                        ua = metric.user_agent[:50]  # Truncate long user agents
                        stats["top_user_agents"][ua] = (
                            stats["top_user_agents"].get(ua, 0) + 1
                        )

            # Cache statistics for 5 minutes
            await redis_service.set(metrics_key, stats, expire=300)

            return stats

        except Exception as e:
            logger.error(f"Error getting API statistics: {e}")
            return {}

    async def invalidate_cache(
        self, pattern: Optional[str] = None, prefix: str = "api_cache"
    ) -> int:
        """Invalidate cached responses"""
        try:
            if pattern:
                cache_pattern = f"{prefix}:{pattern}"
            else:
                cache_pattern = f"{prefix}:*"

            invalidated_count = await redis_service.invalidate_pattern(cache_pattern)
            logger.info(
                f"Invalidated {invalidated_count} cache entries with pattern: {cache_pattern}"
            )

            return invalidated_count

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return 0

    async def get_rate_limit_status(
        self, request: Request, per_user: bool = False
    ) -> Dict[str, Any]:
        """Get current rate limit status"""
        try:
            if per_user:
                user_id = await self._get_user_id_from_request(request)
                limit_key = f"rate_limit:user:{user_id}"
                identifier = user_id
            else:
                client_ip = get_remote_address(request)
                limit_key = f"rate_limit:ip:{client_ip}"
                identifier = client_ip

            # Get current usage
            minute_key = (
                f"{limit_key}:minute:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
            )
            hour_key = f"{limit_key}:hour:{datetime.utcnow().strftime('%Y%m%d%H')}"

            minute_count = await redis_service.get(minute_key) or 0
            hour_count = await redis_service.get(hour_key) or 0

            return {
                "identifier": identifier,
                "type": "user" if per_user else "ip",
                "current_minute_requests": minute_count,
                "current_hour_requests": hour_count,
                "limits": {"per_minute": 60, "per_hour": 1000},  # Default values
            }

        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {}

    async def _generate_cache_key(
        self,
        request: Request,
        function_name: str,
        prefix: str,
        vary_by_user: bool,
        include_headers: List[str],
        exclude_params: List[str],
    ) -> str:
        """Generate a cache key for the request"""
        key_parts = [prefix, function_name]

        # Add path
        key_parts.append(request.url.path)

        # Add query parameters (excluding specified ones)
        if request.query_params:
            filtered_params = {
                k: v for k, v in request.query_params.items() if k not in exclude_params
            }
            if filtered_params:
                params_str = "&".join(
                    f"{k}={v}" for k, v in sorted(filtered_params.items())
                )
                key_parts.append(params_str)

        # Add user ID if vary_by_user is True
        if vary_by_user:
            user_id = await self._get_user_id_from_request(request)
            if user_id:
                key_parts.append(f"user:{user_id}")

        # Add specified headers
        for header_name in include_headers:
            header_value = request.headers.get(header_name)
            if header_value:
                key_parts.append(f"header:{header_name}:{header_value}")

        # Create hash of the key parts
        key_string = ":".join(key_parts)
        cache_key = hashlib.md5(key_string.encode()).hexdigest()

        return f"{prefix}:{cache_key}"

    async def _get_user_id_from_request(self, request: Request) -> Optional[str]:
        """Extract user ID from request (mock implementation)"""
        # This would typically extract from JWT token or session
        # For now, return a mock user ID based on IP
        client_ip = get_remote_address(request)
        return f"user_{hashlib.md5(client_ip.encode()).hexdigest()[:8]}"

    async def _check_rate_limits(
        self, limit_key: str, requests_per_minute: int, requests_per_hour: int
    ):
        """Check if rate limits are exceeded"""
        now = datetime.utcnow()

        # Check minute limit
        minute_key = f"{limit_key}:minute:{now.strftime('%Y%m%d%H%M')}"
        minute_count = await redis_service.get(minute_key) or 0

        if int(minute_count) >= requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {requests_per_minute} requests per minute",
                headers={"Retry-After": "60"},
            )

        # Check hour limit
        hour_key = f"{limit_key}:hour:{now.strftime('%Y%m%d%H')}"
        hour_count = await redis_service.get(hour_key) or 0

        if int(hour_count) >= requests_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {requests_per_hour} requests per hour",
                headers={"Retry-After": "3600"},
            )

        # Increment counters
        await redis_service.increment(minute_key)
        await redis_service.expire(minute_key, 60)

        await redis_service.increment(hour_key)
        await redis_service.expire(hour_key, 3600)

    async def _process_metrics_buffer(self):
        """Process metrics buffer periodically"""
        while True:
            try:
                await asyncio.sleep(30)  # Process every 30 seconds

                if self.metrics_buffer:
                    await self._flush_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing metrics buffer: {e}")

    async def _flush_metrics(self):
        """Flush metrics buffer to storage"""
        if not self.metrics_buffer:
            return

        try:
            # Store metrics in Redis
            metrics_data = [metric.dict() for metric in self.metrics_buffer]

            for metric_data in metrics_data:
                # Store individual metric
                metric_key = (
                    f"api_metric:{datetime.utcnow().isoformat()}:{id(metric_data)}"
                )
                await redis_service.set(
                    metric_key, metric_data, expire=604800
                )  # 7 days

                # Add to time-series list
                await redis_service.lpush("api_metrics_series", metric_data)
                await redis_service.ltrim(
                    "api_metrics_series", 0, 10000
                )  # Keep last 10k metrics

            logger.info(f"Flushed {len(self.metrics_buffer)} metrics to storage")
            self.metrics_buffer.clear()

        except Exception as e:
            logger.error(f"Error flushing metrics: {e}")

    async def _get_metrics_from_storage(
        self, start_time: datetime, endpoint: Optional[str] = None
    ) -> List[APIMetrics]:
        """Get metrics from storage"""
        try:
            # Get from time-series list
            metrics_data = await redis_service.lrange("api_metrics_series", 0, -1)

            metrics = []
            for data in metrics_data:
                try:
                    metric = APIMetrics(**data)

                    # Filter by time
                    if metric.timestamp < start_time:
                        continue

                    # Filter by endpoint if specified
                    if endpoint and metric.endpoint != endpoint:
                        continue

                    metrics.append(metric)

                except Exception as e:
                    logger.warning(f"Error parsing metric data: {e}")

            return metrics

        except Exception as e:
            logger.error(f"Error getting metrics from storage: {e}")
            return []


# Global API enhancement service
api_enhancement_service = APIEnhancementService()


# Utility functions and dependencies
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Dependency to get current user (mock implementation)"""
    if not credentials:
        return None

    # Mock user validation - in production, validate JWT token
    return {
        "id": "mock_user_id",
        "username": "mock_user",
        "permissions": ["read", "write"],
    }


def require_auth(func: Callable):
    """Decorator to require authentication"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        user = None
        for arg in args:
            if isinstance(arg, dict) and "id" in arg:
                user = arg
                break

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await func(*args, **kwargs)

    return wrapper


def require_permission(permission: str):
    """Decorator to require specific permission"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = None
            for arg in args:
                if isinstance(arg, dict) and "permissions" in arg:
                    user = arg
                    break

            if not user or permission not in user.get("permissions", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator