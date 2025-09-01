"""
Analytics Processors Module
Data processing and analysis components for SubForge dashboard
"""

from .data_aggregator import DataAggregator, MetricWindow, AggregatedMetrics
from .trend_analyzer import TrendAnalyzer, TrendResult, SeasonalityResult, PatternDetection, TrendDirection, SeasonalityType
from .insight_generator import InsightGenerator, Insight, InsightType, InsightPriority, ActionType, InsightPattern

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
    "InsightPattern"
]