"""
SubForge Analytics Module
Advanced data science and analytics capabilities for SubForge monitoring
"""

from .models.performance_analyzer import PerformanceAnalyzer
from .models.predictive_models import TaskDurationPredictor, SystemLoadPredictor
from .models.optimization_engine import OptimizationEngine
from .processors.data_aggregator import DataAggregator
from .processors.trend_analyzer import TrendAnalyzer
from .processors.insight_generator import InsightGenerator

__all__ = [
    "PerformanceAnalyzer",
    "TaskDurationPredictor", 
    "SystemLoadPredictor",
    "OptimizationEngine",
    "DataAggregator",
    "TrendAnalyzer",
    "InsightGenerator"
]

__version__ = "1.0.0"