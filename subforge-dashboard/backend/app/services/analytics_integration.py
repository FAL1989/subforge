"""
Analytics Integration Service
Integrates analytics with the existing SubForge backend services
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ...analytics import AnalyticsService, ReportGenerator
from ..database.session import get_db
from ..websocket.enhanced_manager import (
    MessageType,
    WebSocketMessage,
    enhanced_websocket_manager,
)
from .redis_service import redis_service

logger = logging.getLogger(__name__)


class AnalyticsIntegrationService:
    """
    Service to integrate analytics with existing SubForge backend components
    """

    def __init__(self):
        self.analytics_service = None
        self.report_generator = None
        self.background_tasks = []
        self.is_running = False

        # Configuration
        self.config = {
            "realtime_update_interval": 30,  # seconds
            "analysis_interval": 300,  # 5 minutes
            "report_interval": 3600,  # 1 hour
            "websocket_room": "analytics",
            "redis_key_prefix": "analytics:",
            "enable_realtime_streaming": True,
            "enable_background_analysis": True,
        }

    async def initialize(self):
        """Initialize the analytics integration service"""
        try:
            logger.info("Initializing Analytics Integration Service...")

            # Initialize analytics service
            self.analytics_service = AnalyticsService()
            await self.analytics_service.initialize()

            # Initialize report generator
            self.report_generator = ReportGenerator(self.analytics_service)

            # Start background tasks
            if self.config["enable_background_analysis"]:
                await self._start_background_tasks()

            self.is_running = True
            logger.info("✅ Analytics Integration Service initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Analytics Integration Service: {e}")
            raise

    async def shutdown(self):
        """Shutdown the analytics integration service"""
        try:
            logger.info("Shutting down Analytics Integration Service...")

            self.is_running = False

            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Shutdown analytics service
            if self.analytics_service:
                await self.analytics_service.shutdown()

            logger.info("✅ Analytics Integration Service shutdown complete")

        except Exception as e:
            logger.error(f"❌ Error during Analytics Integration Service shutdown: {e}")

    async def process_agent_activity(self, agent_data: Dict[str, Any]):
        """Process agent activity for analytics"""
        try:
            # Extract metrics from agent activity
            agent_data.get("id")
            status = agent_data.get("status")
            response_time = agent_data.get("avg_response_time", 0)
            success_rate = agent_data.get("success_rate", 0)

            # Add metrics to analytics service
            if self.analytics_service:
                await self.analytics_service.add_metric_data_point(
                    "agent_response_time", response_time
                )
                await self.analytics_service.add_metric_data_point(
                    "agent_success_rate", success_rate
                )

                # Update agent status metrics
                if status == "active":
                    await self.analytics_service.add_metric_data_point(
                        "active_agents", 1
                    )

        except Exception as e:
            logger.error(f"Error processing agent activity: {e}")

    async def process_task_completion(self, task_data: Dict[str, Any]):
        """Process task completion for analytics"""
        try:
            # Extract metrics from task completion
            task_status = task_data.get("status")
            duration = task_data.get("actual_duration_minutes", 0)
            priority = task_data.get("priority", "medium")

            if self.analytics_service:
                # Add task completion metrics
                await self.analytics_service.add_metric_data_point(
                    "task_completion_time", duration
                )

                # Success/failure tracking
                if task_status == "completed":
                    await self.analytics_service.add_metric_data_point(
                        "tasks_completed", 1
                    )
                elif task_status == "failed":
                    await self.analytics_service.add_metric_data_point(
                        "tasks_failed", 1
                    )

                # Priority-based metrics
                await self.analytics_service.add_metric_data_point(
                    f"tasks_{priority}_priority", 1
                )

        except Exception as e:
            logger.error(f"Error processing task completion: {e}")

    async def process_system_metrics(self, metrics_data: Dict[str, Any]):
        """Process system metrics for analytics"""
        try:
            if not self.analytics_service:
                return

            # Extract and add system metrics
            metrics_map = {
                "cpu_usage_percentage": "cpu_usage",
                "memory_usage_percentage": "memory_usage",
                "system_load_percentage": "system_load",
                "error_rate_percentage": "error_rate",
                "uptime_percentage": "uptime",
            }

            for source_key, target_key in metrics_map.items():
                if source_key in metrics_data:
                    await self.analytics_service.add_metric_data_point(
                        target_key, metrics_data[source_key]
                    )

        except Exception as e:
            logger.error(f"Error processing system metrics: {e}")

    async def stream_realtime_analytics(self):
        """Stream real-time analytics to WebSocket clients"""
        try:
            if not self.config["enable_realtime_streaming"]:
                return

            # Get real-time metrics
            metrics = await self.analytics_service.get_real_time_metrics()

            # Prepare WebSocket message
            message = WebSocketMessage(
                type=MessageType.ANALYTICS_UPDATE,
                data={
                    "type": "realtime_metrics",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": metrics.get("metrics", {}),
                    "data_freshness": "real-time",
                },
            )

            # Send to analytics room
            await enhanced_websocket_manager.broadcast_to_room(
                self.config["websocket_room"], message
            )

            # Cache in Redis for API access
            await self._cache_realtime_data(metrics)

        except Exception as e:
            logger.error(f"Error streaming real-time analytics: {e}")

    async def generate_and_broadcast_insights(self, db: AsyncSession):
        """Generate insights and broadcast to WebSocket clients"""
        try:
            # Run insight analysis
            insights_data = await self.analytics_service.insight_generator.analyze(db)

            # Extract critical insights
            insights = insights_data.get("insights", [])
            critical_insights = [
                insight
                for insight in insights
                if insight.get("priority") in ["critical", "high"]
            ]

            if critical_insights:
                # Broadcast critical insights
                message = WebSocketMessage(
                    type=MessageType.ANALYTICS_ALERT,
                    data={
                        "type": "critical_insights",
                        "timestamp": datetime.utcnow().isoformat(),
                        "insights": critical_insights[:5],  # Top 5 critical
                        "total_insights": len(insights),
                    },
                )

                await enhanced_websocket_manager.broadcast_to_room(
                    self.config["websocket_room"], message
                )

            # Cache insights for API access
            await self._cache_insights_data(insights_data)

        except Exception as e:
            logger.error(f"Error generating and broadcasting insights: {e}")

    async def run_periodic_analysis(self, db: AsyncSession):
        """Run periodic comprehensive analysis"""
        try:
            logger.info("Running periodic analytics analysis")

            # Run comprehensive analysis
            analysis_result = await self.analytics_service.run_comprehensive_analysis(
                db,
                include_predictions=True,
                include_optimization=True,
                time_range_hours=24,
            )

            # Extract key findings for broadcasting
            summary = analysis_result.get("executive_summary", {})

            message = WebSocketMessage(
                type=MessageType.ANALYTICS_UPDATE,
                data={
                    "type": "periodic_analysis",
                    "timestamp": datetime.utcnow().isoformat(),
                    "summary": summary,
                    "analysis_available": True,
                },
            )

            await enhanced_websocket_manager.broadcast_to_room(
                self.config["websocket_room"], message
            )

            # Cache analysis result
            await self._cache_analysis_data(analysis_result)

            logger.info("Completed periodic analytics analysis")

        except Exception as e:
            logger.error(f"Error in periodic analysis: {e}")

    async def generate_scheduled_reports(self, db: AsyncSession):
        """Generate scheduled reports"""
        try:
            logger.info("Generating scheduled analytics reports")

            # Generate reports
            reports = await self.report_generator.generate_scheduled_reports(db)

            # Broadcast report availability
            message = WebSocketMessage(
                type=MessageType.ANALYTICS_UPDATE,
                data={
                    "type": "reports_generated",
                    "timestamp": datetime.utcnow().isoformat(),
                    "reports": {
                        "daily": len(reports.get("daily", [])),
                        "weekly": len(reports.get("weekly", [])),
                        "monthly": len(reports.get("monthly", [])),
                    },
                },
            )

            await enhanced_websocket_manager.broadcast_to_room(
                self.config["websocket_room"], message
            )

            logger.info("Completed scheduled report generation")

        except Exception as e:
            logger.error(f"Error generating scheduled reports: {e}")

    async def _start_background_tasks(self):
        """Start background analytics tasks"""

        # Real-time streaming task
        if self.config["enable_realtime_streaming"]:
            realtime_task = asyncio.create_task(self._realtime_streaming_loop())
            self.background_tasks.append(realtime_task)

        # Periodic analysis task
        analysis_task = asyncio.create_task(self._periodic_analysis_loop())
        self.background_tasks.append(analysis_task)

        # Report generation task
        report_task = asyncio.create_task(self._report_generation_loop())
        self.background_tasks.append(report_task)

        logger.info(f"Started {len(self.background_tasks)} analytics background tasks")

    async def _realtime_streaming_loop(self):
        """Background loop for real-time analytics streaming"""
        while self.is_running:
            try:
                await self.stream_realtime_analytics()
                await asyncio.sleep(self.config["realtime_update_interval"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in realtime streaming loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    async def _periodic_analysis_loop(self):
        """Background loop for periodic analysis"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config["analysis_interval"])

                # Get database session
                async with get_db().__anext__() as db:
                    await self.run_periodic_analysis(db)
                    await self.generate_and_broadcast_insights(db)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic analysis loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _report_generation_loop(self):
        """Background loop for report generation"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config["report_interval"])

                # Get database session
                async with get_db().__anext__() as db:
                    await self.generate_scheduled_reports(db)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in report generation loop: {e}")
                await asyncio.sleep(300)  # Wait before retrying

    async def _cache_realtime_data(self, data: Dict[str, Any]):
        """Cache real-time data in Redis"""
        try:
            cache_key = f"{self.config['redis_key_prefix']}realtime"
            await redis_service.set(cache_key, data, expire=60)  # 1 minute TTL
        except Exception as e:
            logger.error(f"Error caching realtime data: {e}")

    async def _cache_insights_data(self, data: Dict[str, Any]):
        """Cache insights data in Redis"""
        try:
            cache_key = f"{self.config['redis_key_prefix']}insights"
            await redis_service.set(cache_key, data, expire=600)  # 10 minutes TTL
        except Exception as e:
            logger.error(f"Error caching insights data: {e}")

    async def _cache_analysis_data(self, data: Dict[str, Any]):
        """Cache analysis data in Redis"""
        try:
            cache_key = f"{self.config['redis_key_prefix']}analysis"
            await redis_service.set(cache_key, data, expire=1800)  # 30 minutes TTL
        except Exception as e:
            logger.error(f"Error caching analysis data: {e}")

    async def get_cached_data(self, data_type: str) -> Optional[Dict[str, Any]]:
        """Get cached analytics data"""
        try:
            cache_key = f"{self.config['redis_key_prefix']}{data_type}"
            return await redis_service.get(cache_key)
        except Exception as e:
            logger.error(f"Error getting cached data: {e}")
            return None

    def update_configuration(self, config_updates: Dict[str, Any]):
        """Update integration service configuration"""
        for key, value in config_updates.items():
            if key in self.config:
                self.config[key] = value
                logger.info(f"Updated analytics integration config: {key} = {value}")

    def get_status(self) -> Dict[str, Any]:
        """Get integration service status"""
        return {
            "is_running": self.is_running,
            "background_tasks": len(self.background_tasks),
            "configuration": self.config,
            "analytics_service_status": (
                self.analytics_service.get_service_status()
                if self.analytics_service
                else None
            ),
        }


# Global instance
analytics_integration_service = AnalyticsIntegrationService()