"""
Base Analytics Class for SubForge Dashboard
Provides common functionality for all analytics components
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import asyncio
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AnalysisConfig:
    """Configuration for analysis operations"""
    time_range_hours: int = 24
    confidence_threshold: float = 0.7
    sample_size_threshold: int = 10
    enable_caching: bool = True
    cache_ttl_minutes: int = 30


class BaseAnalyzer(ABC):
    """
    Base class for all analytics components
    Provides common functionality and interface
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        self.config = config or AnalysisConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._cache = {}
        self._cache_timestamps = {}
    
    def _get_cache_key(self, method_name: str, **kwargs) -> str:
        """Generate cache key for method and parameters"""
        params_str = "_".join([f"{k}={v}" for k, v in sorted(kwargs.items())])
        return f"{method_name}_{params_str}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid"""
        if not self.config.enable_caching:
            return False
        
        if cache_key not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[cache_key]
        ttl = timedelta(minutes=self.config.cache_ttl_minutes)
        
        return datetime.utcnow() - cache_time < ttl
    
    def _set_cache(self, cache_key: str, result: Any) -> None:
        """Store result in cache"""
        if self.config.enable_caching:
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.utcnow()
    
    def _get_cache(self, cache_key: str) -> Optional[Any]:
        """Get result from cache"""
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None
    
    def clear_cache(self) -> None:
        """Clear all cached results"""
        self._cache.clear()
        self._cache_timestamps.clear()
        self.logger.info("Analytics cache cleared")
    
    def _validate_sample_size(self, data_count: int, operation: str = "analysis") -> bool:
        """Validate that we have sufficient data for reliable analysis"""
        if data_count < self.config.sample_size_threshold:
            self.logger.warning(
                f"Insufficient data for {operation}: {data_count} items "
                f"(minimum: {self.config.sample_size_threshold})"
            )
            return False
        return True
    
    def _calculate_confidence_score(self, 
                                  data_points: int, 
                                  variance: float, 
                                  time_span_hours: float) -> float:
        """
        Calculate confidence score for analysis results
        Based on data volume, variance, and time span
        """
        # Base confidence from sample size
        size_confidence = min(data_points / 100.0, 1.0)  # Up to 100 points gives full confidence
        
        # Variance penalty (lower variance = higher confidence)
        variance_confidence = max(0.0, 1.0 - (variance / 100.0))  # Normalize variance impact
        
        # Time span bonus (longer periods = more reliable)
        time_confidence = min(time_span_hours / 168.0, 1.0)  # 1 week = full time confidence
        
        # Combined confidence score
        confidence = (size_confidence * 0.4) + (variance_confidence * 0.3) + (time_confidence * 0.3)
        
        return min(confidence, 1.0)
    
    def _format_percentage(self, value: float, decimal_places: int = 1) -> str:
        """Format percentage value consistently"""
        return f"{value:.{decimal_places}f}%"
    
    def _format_duration(self, minutes: float) -> str:
        """Format duration in human-readable format"""
        if minutes < 60:
            return f"{minutes:.1f} min"
        elif minutes < 1440:  # Less than 24 hours
            hours = minutes / 60
            return f"{hours:.1f} hours"
        else:
            days = minutes / 1440
            return f"{days:.1f} days"
    
    def _get_time_range(self, hours: Optional[int] = None) -> tuple[datetime, datetime]:
        """Get start and end time for analysis"""
        hours = hours or self.config.time_range_hours
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        return start_time, end_time
    
    def _categorize_trend(self, slope: float, confidence: float) -> str:
        """Categorize trend based on slope and confidence"""
        if confidence < self.config.confidence_threshold:
            return "insufficient_data"
        
        if abs(slope) < 0.01:  # Very small change
            return "stable"
        elif slope > 0.05:  # Significant positive trend
            return "improving"
        elif slope < -0.05:  # Significant negative trend
            return "declining"
        else:
            return "stable"
    
    def _detect_anomalies(self, values: List[float], threshold_std: float = 2.0) -> List[Dict[str, Any]]:
        """
        Detect anomalies in time series data using standard deviation method
        """
        import numpy as np
        
        if len(values) < 3:
            return []
        
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if std_val == 0:  # No variation
            return []
        
        anomalies = []
        for i, value in enumerate(values):
            z_score = abs((value - mean_val) / std_val)
            if z_score > threshold_std:
                anomalies.append({
                    "index": i,
                    "value": value,
                    "z_score": z_score,
                    "deviation": abs(value - mean_val),
                    "type": "high" if value > mean_val else "low"
                })
        
        return anomalies
    
    def _calculate_moving_average(self, values: List[float], window_size: int = 5) -> List[float]:
        """Calculate moving average for smoothing time series data"""
        if len(values) < window_size:
            return values
        
        moving_averages = []
        for i in range(len(values)):
            if i < window_size - 1:
                # For early values, use available data
                window_values = values[:i+1]
            else:
                window_values = values[i-window_size+1:i+1]
            
            moving_averages.append(sum(window_values) / len(window_values))
        
        return moving_averages
    
    def _generate_insights(self, 
                          metric_name: str, 
                          current_value: float, 
                          historical_values: List[float],
                          thresholds: Dict[str, float] = None) -> List[str]:
        """
        Generate insights based on current value vs historical performance
        """
        insights = []
        
        if not historical_values:
            insights.append(f"No historical data available for {metric_name}")
            return insights
        
        import numpy as np
        
        avg_historical = np.mean(historical_values)
        std_historical = np.std(historical_values)
        
        # Compare current vs average
        if current_value > avg_historical + std_historical:
            insights.append(f"{metric_name} is significantly above historical average")
        elif current_value < avg_historical - std_historical:
            insights.append(f"{metric_name} is significantly below historical average")
        
        # Check against thresholds if provided
        if thresholds:
            for threshold_name, threshold_value in thresholds.items():
                if threshold_name == "critical_high" and current_value > threshold_value:
                    insights.append(f"{metric_name} exceeds critical threshold ({threshold_value})")
                elif threshold_name == "critical_low" and current_value < threshold_value:
                    insights.append(f"{metric_name} below critical threshold ({threshold_value})")
                elif threshold_name == "warning_high" and current_value > threshold_value:
                    insights.append(f"{metric_name} approaching high threshold ({threshold_value})")
                elif threshold_name == "warning_low" and current_value < threshold_value:
                    insights.append(f"{metric_name} approaching low threshold ({threshold_value})")
        
        return insights
    
    @abstractmethod
    async def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Main analysis method - must be implemented by subclasses
        """
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return {
            "time_range_hours": self.config.time_range_hours,
            "confidence_threshold": self.config.confidence_threshold,
            "sample_size_threshold": self.config.sample_size_threshold,
            "enable_caching": self.config.enable_caching,
            "cache_ttl_minutes": self.config.cache_ttl_minutes
        }
    
    def update_config(self, **kwargs) -> None:
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"Updated config: {key} = {value}")
            else:
                self.logger.warning(f"Unknown config parameter: {key}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the analyzer
        """
        try:
            return {
                "status": "healthy",
                "cache_size": len(self._cache),
                "cache_entries": list(self._cache.keys()),
                "config": self.get_config(),
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }


class AnalysisResult:
    """
    Container for analysis results with metadata
    """
    
    def __init__(self, 
                 data: Any, 
                 confidence: float = 1.0,
                 metadata: Optional[Dict[str, Any]] = None):
        self.data = data
        self.confidence = confidence
        self.metadata = metadata or {}
        self.generated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "data": self.data,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "generated_at": self.generated_at.isoformat()
        }
    
    def is_reliable(self, threshold: float = 0.7) -> bool:
        """Check if result meets reliability threshold"""
        return self.confidence >= threshold