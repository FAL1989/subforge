"""
Analytics Service for SubForge Dashboard
Orchestrates all analytics components and provides unified interface
"""

import asyncio
import json
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.optimization_engine import OptimizationEngine
from ..models.performance_analyzer import PerformanceAnalyzer
from ..models.predictive_models import SystemLoadPredictor, TaskDurationPredictor
from ..processors.data_aggregator import DataAggregator
from ..processors.insight_generator import InsightGenerator
from ..processors.trend_analyzer import TrendAnalyzer

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Central analytics service that orchestrates all analytics components
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = (
            Path(storage_path) if storage_path else Path("analytics_data")
        )
        self.storage_path.mkdir(exist_ok=True)

        # Initialize analytics components
        self.performance_analyzer = PerformanceAnalyzer()
        self.task_duration_predictor = TaskDurationPredictor()
        self.system_load_predictor = SystemLoadPredictor()
        self.optimization_engine = OptimizationEngine()
        self.data_aggregator = DataAggregator()
        self.trend_analyzer = TrendAnalyzer()
        self.insight_generator = InsightGenerator()

        # Service state
        self.last_analysis_run = {}
        self.analysis_cache = {}
        self.background_tasks = []

        # Configuration
        self.config = {
            "cache_ttl_minutes": 30,
            "auto_analysis_interval_minutes": 60,
            "enable_background_analysis": True,
            "enable_predictive_models": True,
            "storage_enabled": True,
        }

        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize the analytics service"""
        try:
            self.logger.info("Initializing Analytics Service...")

            # Load any cached data
            await self._load_cached_data()

            # Start background tasks if enabled
            if self.config["enable_background_analysis"]:
                await self._start_background_tasks()

            self.logger.info("✅ Analytics Service initialized successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Analytics Service: {e}")
            raise

    async def shutdown(self):
        """Shutdown the analytics service"""
        try:
            self.logger.info("Shutting down Analytics Service...")

            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Save current state
            await self._save_cached_data()

            self.logger.info("✅ Analytics Service shutdown complete")

        except Exception as e:
            self.logger.error(f"❌ Error during Analytics Service shutdown: {e}")

    async def run_comprehensive_analysis(
        self,
        db: AsyncSession,
        include_predictions: bool = True,
        include_optimization: bool = True,
        time_range_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Run comprehensive analytics analysis

        Args:
            db: Database session
            include_predictions: Include predictive analytics
            include_optimization: Include optimization recommendations
            time_range_hours: Time range for analysis

        Returns:
            Complete analytics report
        """
        try:
            self.logger.info(
                f"Starting comprehensive analysis (time_range: {time_range_hours}h)"
            )
            start_time = datetime.utcnow()

            # Check cache first
            cache_key = f"comprehensive_{time_range_hours}_{include_predictions}_{include_optimization}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                self.logger.info("Returning cached comprehensive analysis")
                return cached_result

            # Run all analytics in parallel for efficiency
            analysis_tasks = []

            # Core analytics
            analysis_tasks.append(
                self._run_with_error_handling(
                    "performance_analysis",
                    self.performance_analyzer.analyze(
                        db, time_range_hours=time_range_hours
                    ),
                )
            )

            analysis_tasks.append(
                self._run_with_error_handling(
                    "data_aggregation",
                    self.data_aggregator.analyze(db, time_range_hours=time_range_hours),
                )
            )

            analysis_tasks.append(
                self._run_with_error_handling(
                    "trend_analysis",
                    self.trend_analyzer.analyze(db, time_range_hours=time_range_hours),
                )
            )

            analysis_tasks.append(
                self._run_with_error_handling(
                    "insight_generation",
                    self.insight_generator.analyze(
                        db, time_range_hours=time_range_hours
                    ),
                )
            )

            # Predictive analytics (if enabled)
            if include_predictions and self.config["enable_predictive_models"]:
                analysis_tasks.append(
                    self._run_with_error_handling(
                        "task_duration_prediction",
                        self.task_duration_predictor.analyze(
                            db, time_range_hours=time_range_hours
                        ),
                    )
                )

                analysis_tasks.append(
                    self._run_with_error_handling(
                        "system_load_prediction",
                        self.system_load_predictor.analyze(
                            db, time_range_hours=time_range_hours
                        ),
                    )
                )

            # Optimization analysis (if enabled)
            if include_optimization:
                analysis_tasks.append(
                    self._run_with_error_handling(
                        "optimization_analysis",
                        self.optimization_engine.analyze(
                            db, time_range_hours=time_range_hours
                        ),
                    )
                )

            # Wait for all analyses to complete
            results = await asyncio.gather(*analysis_tasks)

            # Compile comprehensive report
            comprehensive_report = {
                "analysis_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "time_range_hours": time_range_hours,
                    "analysis_duration_seconds": (
                        datetime.utcnow() - start_time
                    ).total_seconds(),
                    "components_analyzed": len(analysis_tasks),
                },
                "performance_analysis": results[0].get("result", {}),
                "data_aggregation": results[1].get("result", {}),
                "trend_analysis": results[2].get("result", {}),
                "insights": results[3].get("result", {}),
                "predictions": {},
                "optimization": {},
                "executive_summary": {},
            }

            # Add predictive results
            if include_predictions and len(results) > 4:
                comprehensive_report["predictions"] = {
                    "task_duration": results[4].get("result", {}),
                    "system_load": (
                        results[5].get("result", {}) if len(results) > 5 else {}
                    ),
                }

            # Add optimization results
            if include_optimization:
                optimization_index = 6 if include_predictions else 4
                if len(results) > optimization_index:
                    comprehensive_report["optimization"] = results[
                        optimization_index
                    ].get("result", {})

            # Generate executive summary
            comprehensive_report["executive_summary"] = (
                await self._generate_executive_summary(comprehensive_report)
            )

            # Cache the result
            self._set_cache(cache_key, comprehensive_report)

            # Update last analysis timestamp
            self.last_analysis_run["comprehensive"] = datetime.utcnow()

            self.logger.info(
                f"✅ Comprehensive analysis completed in {(datetime.utcnow() - start_time).total_seconds():.2f}s"
            )
            return comprehensive_report

        except Exception as e:
            self.logger.error(f"❌ Error in comprehensive analysis: {e}")
            return {
                "error": str(e),
                "analysis_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "status": "failed",
                },
            }

    async def run_performance_analysis(
        self,
        db: AsyncSession,
        agent_id: Optional[str] = None,
        time_range_hours: int = 24,
    ) -> Dict[str, Any]:
        """Run focused performance analysis"""

        cache_key = f"performance_{agent_id}_{time_range_hours}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        try:
            result = await self.performance_analyzer.analyze(
                db, agent_id=agent_id, time_range_hours=time_range_hours
            )

            self._set_cache(cache_key, result)
            self.last_analysis_run["performance"] = datetime.utcnow()

            return result

        except Exception as e:
            self.logger.error(f"Error in performance analysis: {e}")
            return {"error": str(e)}

    async def run_predictive_analysis(
        self,
        db: AsyncSession,
        prediction_type: str = "both",  # "task_duration", "system_load", "both"
    ) -> Dict[str, Any]:
        """Run predictive analysis"""

        if not self.config["enable_predictive_models"]:
            return {"error": "Predictive models are disabled"}

        cache_key = f"predictive_{prediction_type}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        try:
            results = {}

            if prediction_type in ["task_duration", "both"]:
                results["task_duration"] = await self.task_duration_predictor.analyze(
                    db
                )

            if prediction_type in ["system_load", "both"]:
                results["system_load"] = await self.system_load_predictor.analyze(db)

            self._set_cache(cache_key, results)
            self.last_analysis_run["predictive"] = datetime.utcnow()

            return results

        except Exception as e:
            self.logger.error(f"Error in predictive analysis: {e}")
            return {"error": str(e)}

    async def run_trend_analysis(
        self, db: AsyncSession, metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run trend analysis for specific metrics"""

        cache_key = f"trends_{','.join(metrics) if metrics else 'all'}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        try:
            result = await self.trend_analyzer.analyze(db, metrics=metrics)

            self._set_cache(cache_key, result)
            self.last_analysis_run["trends"] = datetime.utcnow()

            return result

        except Exception as e:
            self.logger.error(f"Error in trend analysis: {e}")
            return {"error": str(e)}

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics from data aggregator"""
        try:
            # Get current metric stats
            real_time_data = {}

            metrics_to_fetch = [
                "system_load",
                "cpu_usage",
                "memory_usage",
                "task_completion_time",
                "agent_response_time",
                "tasks_per_minute",
                "error_rate",
                "success_rate",
            ]

            for metric in metrics_to_fetch:
                stats = self.data_aggregator.get_current_metric_stats(
                    metric, period="5min"
                )
                if stats:
                    real_time_data[metric] = stats

            return {
                "metrics": real_time_data,
                "timestamp": datetime.utcnow().isoformat(),
                "data_freshness": "real-time",
            }

        except Exception as e:
            self.logger.error(f"Error getting real-time metrics: {e}")
            return {"error": str(e)}

    async def add_metric_data_point(
        self, metric_name: str, value: float, timestamp: Optional[datetime] = None
    ):
        """Add a real-time metric data point"""
        try:
            await self.data_aggregator.add_real_time_metric(
                metric_name, value, timestamp
            )
        except Exception as e:
            self.logger.error(f"Error adding metric data point: {e}")

    async def get_metric_history(
        self, metric_name: str, minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Get historical data for a specific metric"""
        try:
            history = self.data_aggregator.get_metric_history(metric_name, minutes)
            return [
                {"timestamp": timestamp.isoformat(), "value": value}
                for timestamp, value in history
            ]
        except Exception as e:
            self.logger.error(f"Error getting metric history: {e}")
            return []

    async def generate_daily_report(self, db: AsyncSession) -> Dict[str, Any]:
        """Generate daily analytics report"""
        try:
            # Run comprehensive analysis for last 24 hours
            analysis = await self.run_comprehensive_analysis(
                db,
                include_predictions=True,
                include_optimization=True,
                time_range_hours=24,
            )

            # Format as daily report
            report = {
                "report_type": "daily",
                "report_date": datetime.utcnow().date().isoformat(),
                "generated_at": datetime.utcnow().isoformat(),
                "analysis_data": analysis,
                "key_highlights": self._extract_key_highlights(analysis),
                "action_items": self._extract_action_items(analysis),
            }

            # Save report if storage enabled
            if self.config["storage_enabled"]:
                await self._save_report(report, "daily")

            return report

        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")
            return {"error": str(e)}

    async def generate_weekly_report(self, db: AsyncSession) -> Dict[str, Any]:
        """Generate weekly analytics report"""
        try:
            # Run comprehensive analysis for last 7 days
            analysis = await self.run_comprehensive_analysis(
                db,
                include_predictions=True,
                include_optimization=True,
                time_range_hours=168,  # 7 days
            )

            # Format as weekly report
            report = {
                "report_type": "weekly",
                "report_week": datetime.utcnow().isocalendar()[:2],  # year, week
                "generated_at": datetime.utcnow().isoformat(),
                "analysis_data": analysis,
                "weekly_trends": self._extract_weekly_trends(analysis),
                "improvement_opportunities": self._extract_improvement_opportunities(
                    analysis
                ),
            }

            # Save report if storage enabled
            if self.config["storage_enabled"]:
                await self._save_report(report, "weekly")

            return report

        except Exception as e:
            self.logger.error(f"Error generating weekly report: {e}")
            return {"error": str(e)}

    def get_service_status(self) -> Dict[str, Any]:
        """Get analytics service status"""
        return {
            "status": "running",
            "components": {
                "performance_analyzer": "active",
                "predictive_models": (
                    "active" if self.config["enable_predictive_models"] else "disabled"
                ),
                "optimization_engine": "active",
                "data_aggregator": "active",
                "trend_analyzer": "active",
                "insight_generator": "active",
            },
            "last_analysis_runs": {
                key: (
                    timestamp.isoformat()
                    if isinstance(timestamp, datetime)
                    else timestamp
                )
                for key, timestamp in self.last_analysis_run.items()
            },
            "cache_size": len(self.analysis_cache),
            "background_tasks": len(self.background_tasks),
            "configuration": self.config,
        }

    def update_configuration(self, config_updates: Dict[str, Any]):
        """Update service configuration"""
        for key, value in config_updates.items():
            if key in self.config:
                self.config[key] = value
                self.logger.info(f"Updated config: {key} = {value}")

    # Private helper methods

    async def _run_with_error_handling(
        self, component_name: str, coroutine
    ) -> Dict[str, Any]:
        """Run analysis component with error handling"""
        try:
            result = await coroutine
            return {"component": component_name, "status": "success", "result": result}
        except Exception as e:
            self.logger.error(f"Error in {component_name}: {e}")
            return {
                "component": component_name,
                "status": "error",
                "error": str(e),
                "result": {},
            }

    async def _generate_executive_summary(
        self, analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive summary from analysis data"""

        summary = {
            "overall_health": "unknown",
            "key_metrics": {},
            "critical_issues": 0,
            "improvement_opportunities": 0,
            "recommendations": [],
        }

        try:
            # Extract key metrics
            performance = analysis_data.get("performance_analysis", {})
            insights = analysis_data.get("insights", {})

            # System health assessment
            if performance and "system_metrics" in performance:
                system_metrics = performance["system_metrics"]
                efficiency = system_metrics.get("system_efficiency", 50)

                if efficiency > 80:
                    summary["overall_health"] = "excellent"
                elif efficiency > 60:
                    summary["overall_health"] = "good"
                elif efficiency > 40:
                    summary["overall_health"] = "fair"
                else:
                    summary["overall_health"] = "poor"

                summary["key_metrics"] = {
                    "system_efficiency": efficiency,
                    "success_rate": system_metrics.get("overall_success_rate", 0),
                    "active_agents": system_metrics.get("active_agents", 0),
                }

            # Critical issues count
            insight_data = insights.get("insights", [])
            if insight_data:
                summary["critical_issues"] = len(
                    [
                        i
                        for i in insight_data
                        if i.get("priority") in ["critical", "high"]
                    ]
                )
                summary["improvement_opportunities"] = len(insight_data)

                # Top recommendations
                summary["recommendations"] = [
                    i.get("title", "Unknown") for i in insight_data[:3]
                ]

        except Exception as e:
            self.logger.error(f"Error generating executive summary: {e}")

        return summary

    def _extract_key_highlights(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Extract key highlights from analysis data"""
        highlights = []

        try:
            # Performance highlights
            performance = analysis_data.get("performance_analysis", {})
            if performance:
                system_metrics = performance.get("system_metrics", {})
                efficiency = system_metrics.get("system_efficiency", 0)
                highlights.append(f"System efficiency: {efficiency:.1f}%")

            # Insight highlights
            insights = analysis_data.get("insights", {})
            if insights:
                insight_data = insights.get("insights", [])
                if insight_data:
                    critical_count = len(
                        [i for i in insight_data if i.get("priority") == "critical"]
                    )
                    if critical_count > 0:
                        highlights.append(
                            f"{critical_count} critical issues identified"
                        )

            # Trend highlights
            trends = analysis_data.get("trend_analysis", {})
            if trends:
                trend_data = trends.get("trends", [])
                improving_trends = len(
                    [t for t in trend_data if t.get("direction") == "increasing"]
                )
                if improving_trends > 0:
                    highlights.append(
                        f"{improving_trends} metrics showing positive trends"
                    )

        except Exception as e:
            self.logger.error(f"Error extracting highlights: {e}")

        return highlights or ["Analysis completed successfully"]

    def _extract_action_items(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Extract action items from analysis data"""
        actions = []

        try:
            # From insights
            insights = analysis_data.get("insights", {})
            if insights:
                insight_data = insights.get("insights", [])
                for insight in insight_data[:5]:  # Top 5
                    recommended_actions = insight.get("recommended_actions", [])
                    if recommended_actions:
                        actions.append(recommended_actions[0])  # First action

            # From optimization
            optimization = analysis_data.get("optimization", {})
            if optimization:
                recommendations = optimization.get("recommendations", [])
                for rec in recommendations[:3]:  # Top 3
                    actions.append(rec.get("title", "Review system optimization"))

        except Exception as e:
            self.logger.error(f"Error extracting action items: {e}")

        return actions or ["Continue monitoring system performance"]

    def _extract_weekly_trends(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract weekly trends from analysis data"""
        return analysis_data.get("trend_analysis", {})

    def _extract_improvement_opportunities(
        self, analysis_data: Dict[str, Any]
    ) -> List[str]:
        """Extract improvement opportunities from analysis data"""
        opportunities = []

        try:
            optimization = analysis_data.get("optimization", {})
            if optimization:
                recommendations = optimization.get("recommendations", [])
                opportunities = [rec.get("title", "") for rec in recommendations[:5]]
        except Exception as e:
            self.logger.error(f"Error extracting opportunities: {e}")

        return opportunities

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get result from cache if still valid"""
        if cache_key in self.analysis_cache:
            cached_data, timestamp = self.analysis_cache[cache_key]
            if datetime.utcnow() - timestamp < timedelta(
                minutes=self.config["cache_ttl_minutes"]
            ):
                return cached_data
            else:
                del self.analysis_cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, data: Dict[str, Any]):
        """Set data in cache"""
        self.analysis_cache[cache_key] = (data, datetime.utcnow())

    async def _start_background_tasks(self):
        """Start background analytics tasks"""
        # Auto-analysis task
        auto_analysis_task = asyncio.create_task(self._auto_analysis_loop())
        self.background_tasks.append(auto_analysis_task)

        # Cache cleanup task
        cache_cleanup_task = asyncio.create_task(self._cache_cleanup_loop())
        self.background_tasks.append(cache_cleanup_task)

    async def _auto_analysis_loop(self):
        """Background task for automatic analysis"""
        while True:
            try:
                await asyncio.sleep(self.config["auto_analysis_interval_minutes"] * 60)
                # Auto-analysis would require database session from caller
                self.logger.info(
                    "Auto-analysis interval reached (database session needed)"
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in auto-analysis loop: {e}")

    async def _cache_cleanup_loop(self):
        """Background task for cache cleanup"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                # Clean expired cache entries
                current_time = datetime.utcnow()
                ttl = timedelta(minutes=self.config["cache_ttl_minutes"])

                expired_keys = [
                    key
                    for key, (_, timestamp) in self.analysis_cache.items()
                    if current_time - timestamp > ttl
                ]

                for key in expired_keys:
                    del self.analysis_cache[key]

                if expired_keys:
                    self.logger.info(
                        f"Cleaned {len(expired_keys)} expired cache entries"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cache cleanup loop: {e}")

    async def _load_cached_data(self):
        """Load cached data from storage"""
        try:
            cache_file = self.storage_path / "analytics_cache.pkl"
            if cache_file.exists():
                with open(cache_file, "rb") as f:
                    self.analysis_cache = pickle.load(f)
                self.logger.info("Loaded cached analytics data")
        except Exception as e:
            self.logger.warning(f"Could not load cached data: {e}")

    async def _save_cached_data(self):
        """Save cached data to storage"""
        try:
            if self.config["storage_enabled"]:
                cache_file = self.storage_path / "analytics_cache.pkl"
                with open(cache_file, "wb") as f:
                    pickle.dump(self.analysis_cache, f)
                self.logger.info("Saved analytics cache to storage")
        except Exception as e:
            self.logger.warning(f"Could not save cached data: {e}")

    async def _save_report(self, report: Dict[str, Any], report_type: str):
        """Save report to storage"""
        try:
            if self.config["storage_enabled"]:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"{report_type}_report_{timestamp}.json"
                report_file = self.storage_path / filename

                with open(report_file, "w") as f:
                    json.dump(report, f, indent=2, default=str)

                self.logger.info(f"Saved {report_type} report: {filename}")
        except Exception as e:
            self.logger.warning(f"Could not save {report_type} report: {e}")