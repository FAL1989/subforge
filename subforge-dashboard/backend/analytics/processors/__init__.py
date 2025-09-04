"""
Analytics Processors Module
Data processing and analysis components for SubForge dashboard
"""

from .data_aggregator import AggregatedMetrics, DataAggregator, MetricWindow
from .insight_generator import (
    ActionType,
    Insight,
    InsightGenerator,
    InsightPattern,
    InsightPriority,
    InsightType,
)
from .trend_analyzer import (
    PatternDetection,
    SeasonalityResult,
    SeasonalityType,
    TrendAnalyzer,
    TrendDirection,
    TrendResult,
)

__all__ = [
    # Data aggregation
    "DataAggregator",
    "MetricWindow",
    "AggregatedMetrics",
    # Trend analysis
    "TrendAnalyzer",
    "TrendResult",
    "SeasonalityResult",
    "PatternDetection",
    "TrendDirection",
    "SeasonalityType",
    # Insight generation
    "InsightGenerator",
    "Insight",
    "InsightType",
    "InsightPriority",
    "ActionType",
    "InsightPattern",
]