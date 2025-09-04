"""
SubForge Analytics Module
Advanced data science and analytics capabilities for SubForge monitoring
"""

from .generators.report_generator import (
    ReportConfig,
    ReportFormat,
    ReportGenerator,
    ReportType,
)
from .models.base_analyzer import AnalysisConfig, AnalysisResult, BaseAnalyzer
from .models.optimization_engine import (
    OptimizationEngine,
    OptimizationRecommendation,
    SystemAnalysis,
)

# Core analytics components
from .models.performance_analyzer import (
    AgentPerformanceMetrics,
    PerformanceAnalyzer,
    SystemPerformanceMetrics,
)
from .models.predictive_models import (
    ModelPerformance,
    PredictionResult,
    SystemLoadPredictor,
    TaskDurationPredictor,
)

# Data processors
from .processors.data_aggregator import AggregatedMetrics, DataAggregator, MetricWindow
from .processors.insight_generator import (
    Insight,
    InsightGenerator,
    InsightPriority,
    InsightType,
)
from .processors.trend_analyzer import (
    PatternDetection,
    SeasonalityResult,
    TrendAnalyzer,
    TrendResult,
)

# Services and generators
from .services.analytics_service import AnalyticsService

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
    "ReportType",
]

__version__ = "1.0.0"