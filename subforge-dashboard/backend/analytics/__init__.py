"""
SubForge Analytics Module
Advanced data science and analytics capabilities for SubForge monitoring
"""

# Core analytics components
from .models.performance_analyzer import PerformanceAnalyzer, AgentPerformanceMetrics, SystemPerformanceMetrics
from .models.predictive_models import TaskDurationPredictor, SystemLoadPredictor, PredictionResult, ModelPerformance
from .models.optimization_engine import OptimizationEngine, OptimizationRecommendation, SystemAnalysis
from .models.base_analyzer import BaseAnalyzer, AnalysisConfig, AnalysisResult

# Data processors
from .processors.data_aggregator import DataAggregator, AggregatedMetrics, MetricWindow
from .processors.trend_analyzer import TrendAnalyzer, TrendResult, SeasonalityResult, PatternDetection
from .processors.insight_generator import InsightGenerator, Insight, InsightType, InsightPriority

# Services and generators
from .services.analytics_service import AnalyticsService
from .generators.report_generator import ReportGenerator, ReportConfig, ReportFormat, ReportType

__all__ = [
    # Core analyzers
    "PerformanceAnalyzer",
    "TaskDurationPredictor", 
    "SystemLoadPredictor",
    "OptimizationEngine",
    "BaseAnalyzer",
    
    # Data processors
    "DataAggregator",
    "TrendAnalyzer",
    "InsightGenerator",
    
    # Services
    "AnalyticsService",
    "ReportGenerator",
    
    # Data classes
    "AgentPerformanceMetrics",
    "SystemPerformanceMetrics",
    "PredictionResult",
    "ModelPerformance",
    "OptimizationRecommendation",
    "SystemAnalysis",
    "AnalysisConfig",
    "AnalysisResult",
    "AggregatedMetrics",
    "MetricWindow",
    "TrendResult",
    "SeasonalityResult",
    "PatternDetection",
    "Insight",
    "InsightType",
    "InsightPriority",
    "ReportConfig",
    "ReportFormat",
    "ReportType"
]

__version__ = "1.0.0"