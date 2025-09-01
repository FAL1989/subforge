"""
Trend Analysis Module for SubForge Analytics
Advanced time series analysis and pattern detection
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from ...app.models.agent import Agent
from ...app.models.task import Task
from ...app.models.system_metrics import SystemMetrics
from ..models.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


class SeasonalityType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NONE = "none"


@dataclass
class TrendResult:
    """Results of trend analysis"""
    metric_name: str
    direction: TrendDirection
    strength: float  # 0-1, how strong the trend is
    confidence: float  # 0-1, confidence in the trend
    slope: float  # Rate of change
    r_squared: float  # Goodness of fit
    
    # Statistical details
    p_value: float
    standard_error: float
    
    # Predictions
    predicted_next_value: Optional[float]
    prediction_interval: Optional[Tuple[float, float]]
    
    # Metadata
    data_points: int
    time_span_days: float
    analysis_timestamp: datetime


@dataclass
class SeasonalityResult:
    """Results of seasonality analysis"""
    metric_name: str
    has_seasonality: bool
    seasonality_type: SeasonalityType
    period_hours: Optional[float]
    strength: float  # 0-1
    
    # Pattern details
    peak_times: List[int]  # Hours of day for peaks
    low_times: List[int]   # Hours of day for lows
    weekly_pattern: Optional[List[float]]  # 7 values for days of week
    
    # Statistical measures
    autocorrelation_score: float
    fft_dominant_frequency: Optional[float]


@dataclass
class PatternDetection:
    """Detected patterns in time series"""
    pattern_type: str  # "anomaly", "cycle", "trend_change", "spike"
    start_time: datetime
    end_time: datetime
    magnitude: float
    confidence: float
    description: str
    
    # Pattern-specific data
    metadata: Dict[str, Any]


class TrendAnalyzer(BaseAnalyzer):
    """
    Advanced trend analysis for SubForge metrics
    Detects trends, seasonality, anomalies, and patterns in time series data
    """
    
    def __init__(self):
        super().__init__()
        self.scaler = StandardScaler()
        self.trend_cache = {}
        self.seasonality_cache = {}
        
    async def analyze(self, db: AsyncSession, **kwargs) -> Dict[str, Any]:
        """Main analysis method - comprehensive trend analysis"""
        
        # Get time series data
        time_series_data = await self._collect_time_series_data(db)
        
        # Analyze trends for each metric
        trend_results = await self._analyze_all_trends(time_series_data)
        
        # Detect seasonality
        seasonality_results = await self._analyze_seasonality(time_series_data)
        
        # Detect patterns and anomalies
        pattern_detections = await self._detect_patterns(time_series_data)
        
        # Generate forecasts
        forecasts = await self._generate_forecasts(time_series_data, trend_results)
        
        return {
            "trends": [asdict(result) for result in trend_results],
            "seasonality": [asdict(result) for result in seasonality_results],
            "patterns": [asdict(pattern) for pattern in pattern_detections],
            "forecasts": forecasts,
            "analysis_summary": await self._generate_trend_summary(
                trend_results, seasonality_results, pattern_detections
            )
        }
    
    async def _collect_time_series_data(self, db: AsyncSession) -> Dict[str, pd.DataFrame]:
        """
        Collect time series data for analysis
        Returns dictionary of metric_name -> DataFrame with timestamp and value columns
        """
        
        # Get data for last 30 days
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=30)
        
        time_series = {}
        
        # System metrics time series
        system_metrics_query = select(SystemMetrics).where(
            and_(
                SystemMetrics.recorded_at >= start_time,
                SystemMetrics.recorded_at <= end_time
            )
        ).order_by(SystemMetrics.recorded_at)
        
        result = await db.execute(system_metrics_query)
        system_metrics = result.scalars().all()
        
        if system_metrics:
            # Extract different metrics
            metrics_to_analyze = [
                ('system_load', 'system_load_percentage'),
                ('cpu_usage', 'cpu_usage_percentage'),
                ('memory_usage', 'memory_usage_percentage'),
                ('success_rate', 'overall_success_rate'),
                ('response_time', 'avg_response_time_ms'),
                ('active_agents', 'active_agents'),
                ('error_rate', 'error_rate_percentage')
            ]
            
            for metric_name, attribute in metrics_to_analyze:
                data = []
                for metric in system_metrics:
                    if hasattr(metric, attribute) and metric.recorded_at:
                        value = getattr(metric, attribute)
                        if value is not None:
                            data.append({
                                'timestamp': metric.recorded_at,
                                'value': float(value)
                            })
                
                if data:
                    df = pd.DataFrame(data)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.sort_values('timestamp').reset_index(drop=True)
                    time_series[metric_name] = df
        
        # Task completion rate time series
        tasks_query = select(Task).where(
            and_(
                Task.created_at >= start_time,
                Task.created_at <= end_time
            )
        ).order_by(Task.created_at)
        
        result = await db.execute(tasks_query)
        tasks = result.scalars().all()
        
        if tasks:
            # Group tasks by hour and calculate completion rate
            task_data = []
            current_hour = start_time.replace(minute=0, second=0, microsecond=0)
            
            while current_hour <= end_time:
                next_hour = current_hour + timedelta(hours=1)
                
                hour_tasks = [
                    t for t in tasks 
                    if current_hour <= t.created_at < next_hour
                ]
                
                if hour_tasks:
                    completed = len([t for t in hour_tasks if t.status == "completed"])
                    completion_rate = (completed / len(hour_tasks)) * 100
                    
                    task_data.append({
                        'timestamp': current_hour,
                        'value': completion_rate
                    })
                
                current_hour = next_hour
            
            if task_data:
                df = pd.DataFrame(task_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                time_series['task_completion_rate'] = df
        
        return time_series
    
    async def _analyze_all_trends(self, time_series_data: Dict[str, pd.DataFrame]) -> List[TrendResult]:
        """Analyze trends for all metrics"""
        
        trend_results = []
        
        for metric_name, df in time_series_data.items():
            if len(df) >= 10:  # Need minimum data points
                trend = await self._analyze_single_trend(metric_name, df)
                trend_results.append(trend)
        
        return trend_results
    
    async def _analyze_single_trend(self, metric_name: str, df: pd.DataFrame) -> TrendResult:
        """Analyze trend for a single metric"""
        
        try:
            # Prepare data
            df = df.copy()
            df['time_numeric'] = pd.to_numeric(df['timestamp']) / 10**9  # Convert to seconds
            
            # Remove outliers (optional)
            values = df['value'].values
            Q1 = np.percentile(values, 25)
            Q3 = np.percentile(values, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Keep outliers for now, but note them
            outlier_mask = (values < lower_bound) | (values > upper_bound)
            outlier_count = np.sum(outlier_mask)
            
            # Linear regression for trend
            x = df['time_numeric'].values.reshape(-1, 1)
            y = df['value'].values
            
            # Normalize time for better numerical stability
            x_normalized = (x - x.min()) / (x.max() - x.min() + 1e-10)
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_normalized.flatten(), y)
            
            # Determine trend direction
            if p_value < 0.05:  # Statistically significant
                if slope > 0.1:
                    direction = TrendDirection.INCREASING
                elif slope < -0.1:
                    direction = TrendDirection.DECREASING
                else:
                    direction = TrendDirection.STABLE
            else:
                # Check volatility
                cv = np.std(y) / np.mean(y) if np.mean(y) != 0 else 0
                if cv > 0.3:  # High coefficient of variation
                    direction = TrendDirection.VOLATILE
                else:
                    direction = TrendDirection.STABLE
            
            # Calculate trend strength
            strength = min(abs(r_value), 1.0)
            
            # Calculate confidence
            confidence = 1 - p_value if p_value < 1 else 0
            confidence = min(confidence * (len(df) / 50), 1.0)  # Adjust for sample size
            
            # Make prediction
            if len(df) > 5:
                # Predict next value
                x_next = x_normalized[-1] + (x_normalized[-1] - x_normalized[-2])
                predicted_value = slope * x_next + intercept
                
                # Simple prediction interval (±1 std dev)
                residuals = y - (slope * x_normalized.flatten() + intercept)
                residual_std = np.std(residuals)
                prediction_interval = (
                    predicted_value - 1.96 * residual_std,
                    predicted_value + 1.96 * residual_std
                )
            else:
                predicted_value = None
                prediction_interval = None
            
            # Calculate time span
            time_span = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / (24 * 3600)
            
            return TrendResult(
                metric_name=metric_name,
                direction=direction,
                strength=strength,
                confidence=confidence,
                slope=slope,
                r_squared=r_value**2,
                p_value=p_value,
                standard_error=std_err,
                predicted_next_value=predicted_value,
                prediction_interval=prediction_interval,
                data_points=len(df),
                time_span_days=time_span,
                analysis_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing trend for {metric_name}: {e}")
            return TrendResult(
                metric_name=metric_name,
                direction=TrendDirection.INSUFFICIENT_DATA,
                strength=0.0,
                confidence=0.0,
                slope=0.0,
                r_squared=0.0,
                p_value=1.0,
                standard_error=0.0,
                predicted_next_value=None,
                prediction_interval=None,
                data_points=len(df) if 'df' in locals() else 0,
                time_span_days=0.0,
                analysis_timestamp=datetime.utcnow()
            )
    
    async def _analyze_seasonality(self, time_series_data: Dict[str, pd.DataFrame]) -> List[SeasonalityResult]:
        """Analyze seasonality patterns in time series data"""
        
        seasonality_results = []
        
        for metric_name, df in time_series_data.items():
            if len(df) >= 48:  # Need at least 2 days of hourly data
                seasonality = await self._analyze_single_seasonality(metric_name, df)
                seasonality_results.append(seasonality)
        
        return seasonality_results
    
    async def _analyze_single_seasonality(self, metric_name: str, df: pd.DataFrame) -> SeasonalityResult:
        """Analyze seasonality for a single metric"""
        
        try:
            df = df.copy()
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            
            # Daily seasonality analysis
            hourly_means = df.groupby('hour')['value'].mean()
            hourly_std = df.groupby('hour')['value'].std()
            
            # Calculate coefficient of variation for daily pattern
            daily_cv = hourly_std.mean() / hourly_means.mean() if hourly_means.mean() != 0 else 0
            
            # Weekly seasonality analysis
            if len(df) >= 14 * 24:  # At least 2 weeks of hourly data
                weekly_means = df.groupby('day_of_week')['value'].mean()
                weekly_cv = weekly_means.std() / weekly_means.mean() if weekly_means.mean() != 0 else 0
            else:
                weekly_means = None
                weekly_cv = 0
            
            # Autocorrelation analysis
            autocorr_scores = []
            lags_to_test = [24, 168]  # 24h (daily), 168h (weekly)
            
            for lag in lags_to_test:
                if len(df) > lag * 2:
                    autocorr = df['value'].autocorr(lag=min(lag, len(df) - 1))
                    autocorr_scores.append(abs(autocorr) if not pd.isna(autocorr) else 0)
                else:
                    autocorr_scores.append(0)
            
            # Determine seasonality
            has_seasonality = False
            seasonality_type = SeasonalityType.NONE
            strength = 0.0
            
            if daily_cv > 0.1 and autocorr_scores[0] > 0.3:
                has_seasonality = True
                seasonality_type = SeasonalityType.DAILY
                strength = min(daily_cv * autocorr_scores[0], 1.0)
            elif weekly_cv > 0.1 and len(autocorr_scores) > 1 and autocorr_scores[1] > 0.3:
                has_seasonality = True
                seasonality_type = SeasonalityType.WEEKLY
                strength = min(weekly_cv * autocorr_scores[1], 1.0)
            
            # Find peak and low times
            if has_seasonality and seasonality_type == SeasonalityType.DAILY:
                # Find hours with highest and lowest values
                sorted_hours = hourly_means.sort_values(ascending=False)
                peak_times = sorted_hours.head(3).index.tolist()
                low_times = sorted_hours.tail(3).index.tolist()
            else:
                peak_times = []
                low_times = []
            
            # Weekly pattern
            weekly_pattern = weekly_means.tolist() if weekly_means is not None else None
            
            return SeasonalityResult(
                metric_name=metric_name,
                has_seasonality=has_seasonality,
                seasonality_type=seasonality_type,
                period_hours=24.0 if seasonality_type == SeasonalityType.DAILY else 
                           168.0 if seasonality_type == SeasonalityType.WEEKLY else None,
                strength=strength,
                peak_times=peak_times,
                low_times=low_times,
                weekly_pattern=weekly_pattern,
                autocorrelation_score=max(autocorr_scores) if autocorr_scores else 0,
                fft_dominant_frequency=None  # Could add FFT analysis later
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing seasonality for {metric_name}: {e}")
            return SeasonalityResult(
                metric_name=metric_name,
                has_seasonality=False,
                seasonality_type=SeasonalityType.NONE,
                period_hours=None,
                strength=0.0,
                peak_times=[],
                low_times=[],
                weekly_pattern=None,
                autocorrelation_score=0.0,
                fft_dominant_frequency=None
            )
    
    async def _detect_patterns(self, time_series_data: Dict[str, pd.DataFrame]) -> List[PatternDetection]:
        """Detect patterns and anomalies in time series data"""
        
        all_patterns = []
        
        for metric_name, df in time_series_data.items():
            if len(df) >= 20:  # Need sufficient data
                patterns = await self._detect_metric_patterns(metric_name, df)
                all_patterns.extend(patterns)
        
        return all_patterns
    
    async def _detect_metric_patterns(self, metric_name: str, df: pd.DataFrame) -> List[PatternDetection]:
        """Detect patterns for a single metric"""
        
        patterns = []
        
        try:
            values = df['value'].values
            timestamps = df['timestamp'].values
            
            # Anomaly detection using z-score
            z_scores = np.abs(stats.zscore(values))
            anomaly_threshold = 3.0
            anomaly_indices = np.where(z_scores > anomaly_threshold)[0]
            
            for idx in anomaly_indices:
                patterns.append(PatternDetection(
                    pattern_type="anomaly",
                    start_time=timestamps[idx],
                    end_time=timestamps[idx],
                    magnitude=float(z_scores[idx]),
                    confidence=min((z_scores[idx] - anomaly_threshold) / anomaly_threshold, 1.0),
                    description=f"Anomalous value detected: {values[idx]:.2f} (z-score: {z_scores[idx]:.2f})",
                    metadata={
                        "value": float(values[idx]),
                        "z_score": float(z_scores[idx]),
                        "metric_name": metric_name
                    }
                ))
            
            # Spike detection
            # Find peaks using scipy
            peaks, properties = find_peaks(values, height=np.mean(values) + 2*np.std(values), distance=5)
            
            for peak_idx in peaks:
                patterns.append(PatternDetection(
                    pattern_type="spike",
                    start_time=timestamps[max(0, peak_idx-1)],
                    end_time=timestamps[min(len(timestamps)-1, peak_idx+1)],
                    magnitude=float(values[peak_idx] - np.mean(values)),
                    confidence=0.8,
                    description=f"Spike detected at {timestamps[peak_idx]}",
                    metadata={
                        "peak_value": float(values[peak_idx]),
                        "baseline": float(np.mean(values)),
                        "metric_name": metric_name
                    }
                ))
            
            # Trend change detection
            # Look for significant changes in slope
            if len(values) >= 30:
                window_size = 10
                slopes = []
                
                for i in range(len(values) - window_size):
                    window_values = values[i:i+window_size]
                    x = np.arange(len(window_values))
                    slope, _, _, _, _ = stats.linregress(x, window_values)
                    slopes.append(slope)
                
                # Find significant slope changes
                slope_changes = np.diff(slopes)
                change_threshold = 2 * np.std(slope_changes)
                
                significant_changes = np.where(np.abs(slope_changes) > change_threshold)[0]
                
                for change_idx in significant_changes:
                    actual_idx = change_idx + window_size
                    if actual_idx < len(timestamps) - 1:
                        patterns.append(PatternDetection(
                            pattern_type="trend_change",
                            start_time=timestamps[actual_idx],
                            end_time=timestamps[min(actual_idx + window_size, len(timestamps)-1)],
                            magnitude=float(abs(slope_changes[change_idx])),
                            confidence=0.7,
                            description=f"Trend change detected around {timestamps[actual_idx]}",
                            metadata={
                                "slope_before": float(slopes[change_idx]),
                                "slope_after": float(slopes[change_idx + 1]),
                                "slope_change": float(slope_changes[change_idx]),
                                "metric_name": metric_name
                            }
                        ))
            
        except Exception as e:
            self.logger.error(f"Error detecting patterns for {metric_name}: {e}")
        
        return patterns
    
    async def _generate_forecasts(
        self, 
        time_series_data: Dict[str, pd.DataFrame], 
        trend_results: List[TrendResult]
    ) -> Dict[str, Any]:
        """Generate simple forecasts based on trend analysis"""
        
        forecasts = {}
        
        for trend in trend_results:
            if trend.predicted_next_value is not None:
                forecasts[trend.metric_name] = {
                    "next_value_prediction": trend.predicted_next_value,
                    "prediction_interval": trend.prediction_interval,
                    "confidence": trend.confidence,
                    "forecast_horizon": "1 time step",
                    "method": "linear_regression"
                }
        
        return forecasts
    
    async def _generate_trend_summary(
        self, 
        trend_results: List[TrendResult], 
        seasonality_results: List[SeasonalityResult],
        pattern_detections: List[PatternDetection]
    ) -> Dict[str, Any]:
        """Generate summary of trend analysis"""
        
        # Trend summary
        trend_directions = {}
        for trend in trend_results:
            trend_directions[trend.direction.value] = trend_directions.get(trend.direction.value, 0) + 1
        
        # Seasonality summary
        seasonal_metrics = [s for s in seasonality_results if s.has_seasonality]
        
        # Pattern summary
        pattern_types = {}
        for pattern in pattern_detections:
            pattern_types[pattern.pattern_type] = pattern_types.get(pattern.pattern_type, 0) + 1
        
        # Key findings
        key_findings = []
        
        # Strong trends
        strong_trends = [t for t in trend_results if t.strength > 0.7 and t.confidence > 0.8]
        if strong_trends:
            key_findings.append(f"Detected {len(strong_trends)} strong trends")
        
        # Seasonal patterns
        if seasonal_metrics:
            key_findings.append(f"Found {len(seasonal_metrics)} metrics with seasonal patterns")
        
        # Anomalies
        anomalies = [p for p in pattern_detections if p.pattern_type == "anomaly"]
        if len(anomalies) > 5:
            key_findings.append(f"High anomaly count detected: {len(anomalies)} anomalies")
        
        return {
            "total_metrics_analyzed": len(trend_results),
            "trend_distribution": trend_directions,
            "seasonal_patterns_found": len(seasonal_metrics),
            "total_patterns_detected": len(pattern_detections),
            "pattern_distribution": pattern_types,
            "key_findings": key_findings,
            "analysis_quality": {
                "avg_confidence": np.mean([t.confidence for t in trend_results]) if trend_results else 0,
                "avg_data_points": np.mean([t.data_points for t in trend_results]) if trend_results else 0,
                "total_time_span_days": sum([t.time_span_days for t in trend_results])
            },
            "recommendations": self._generate_trend_recommendations(trend_results, seasonality_results, pattern_detections)
        }
    
    def _generate_trend_recommendations(
        self, 
        trend_results: List[TrendResult], 
        seasonality_results: List[SeasonalityResult],
        pattern_detections: List[PatternDetection]
    ) -> List[str]:
        """Generate actionable recommendations based on trend analysis"""
        
        recommendations = []
        
        # Declining trends
        declining_trends = [t for t in trend_results if t.direction == TrendDirection.DECREASING and t.confidence > 0.6]
        if declining_trends:
            recommendations.append(f"Monitor declining trends in: {', '.join([t.metric_name for t in declining_trends])}")
        
        # Volatile metrics
        volatile_metrics = [t for t in trend_results if t.direction == TrendDirection.VOLATILE]
        if volatile_metrics:
            recommendations.append(f"Investigate high volatility in: {', '.join([t.metric_name for t in volatile_metrics])}")
        
        # Seasonal patterns
        daily_seasonal = [s for s in seasonality_results if s.seasonality_type == SeasonalityType.DAILY]
        if daily_seasonal:
            recommendations.append(f"Leverage daily patterns for optimization in: {', '.join([s.metric_name for s in daily_seasonal])}")
        
        # High anomaly count
        anomaly_count = len([p for p in pattern_detections if p.pattern_type == "anomaly"])
        if anomaly_count > 10:
            recommendations.append("High anomaly count suggests system instability - investigate root causes")
        
        # Trend changes
        trend_changes = [p for p in pattern_detections if p.pattern_type == "trend_change"]
        if trend_changes:
            recommendations.append(f"Recent trend changes detected - validate system changes or external factors")
        
        return recommendations