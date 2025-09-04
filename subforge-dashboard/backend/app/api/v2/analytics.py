"""
Analytics API endpoints for SubForge Dashboard
Provides comprehensive analytics and reporting endpoints
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ....analytics import (
    AnalyticsService,
    ReportConfig,
    ReportFormat,
    ReportGenerator,
    ReportType,
)
from ...database.session import get_db
from ...utils.logging_config import get_logger

router = APIRouter(tags=["analytics"])
logger = get_logger(__name__)

# Global analytics service instance
analytics_service = None
report_generator = None


async def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance"""
    global analytics_service
    if analytics_service is None:
        analytics_service = AnalyticsService()
        await analytics_service.initialize()
    return analytics_service


async def get_report_generator() -> ReportGenerator:
    """Get report generator instance"""
    global report_generator, analytics_service
    if report_generator is None:
        if analytics_service is None:
            analytics_service = await get_analytics_service()
        report_generator = ReportGenerator(analytics_service)
    return report_generator


# Pydantic models for request/response
class AnalysisRequest(BaseModel):
    time_range_hours: int = Field(
        default=24, ge=1, le=720, description="Time range in hours (1-720)"
    )
    include_predictions: bool = Field(
        default=True, description="Include predictive analytics"
    )
    include_optimization: bool = Field(
        default=True, description="Include optimization recommendations"
    )
    agent_id: Optional[str] = Field(
        default=None, description="Specific agent ID for focused analysis"
    )


class ReportGenerationRequest(BaseModel):
    report_type: str = Field(..., description="Type of report to generate")
    format: str = Field(
        default="json", description="Output format (json, csv, html, pdf)"
    )
    time_range_hours: int = Field(default=24, ge=1, le=720)
    include_charts: bool = Field(default=True)
    include_recommendations: bool = Field(default=True)
    custom_title: Optional[str] = Field(default=None)


class MetricDataPoint(BaseModel):
    metric_name: str = Field(..., description="Name of the metric")
    value: float = Field(..., description="Metric value")
    timestamp: Optional[datetime] = Field(
        default=None, description="Timestamp (defaults to now)"
    )


# Analytics endpoints


@router.get("/status")
async def get_analytics_status(
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Get analytics service status and health"""
    try:
        status = analytics.get_service_status()
        return {
            "success": True,
            "data": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting analytics status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/comprehensive")
async def run_comprehensive_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Run comprehensive analytics analysis"""
    try:
        logger.info(
            f"Starting comprehensive analysis for {request.time_range_hours} hours"
        )

        result = await analytics.run_comprehensive_analysis(
            db,
            include_predictions=request.include_predictions,
            include_optimization=request.include_optimization,
            time_range_hours=request.time_range_hours,
        )

        return {
            "success": True,
            "data": result,
            "request_params": request.dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/performance")
async def run_performance_analysis(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Run focused performance analysis"""
    try:
        result = await analytics.run_performance_analysis(
            db, agent_id=request.agent_id, time_range_hours=request.time_range_hours
        )

        return {
            "success": True,
            "data": result,
            "request_params": request.dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in performance analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/predictive")
async def run_predictive_analysis(
    prediction_type: str = Query(
        default="both",
        description="Prediction type: task_duration, system_load, or both",
    ),
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Run predictive analysis"""
    try:
        if prediction_type not in ["task_duration", "system_load", "both"]:
            raise HTTPException(status_code=400, detail="Invalid prediction type")

        result = await analytics.run_predictive_analysis(db, prediction_type)

        return {
            "success": True,
            "data": result,
            "prediction_type": prediction_type,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in predictive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/trends")
async def run_trend_analysis(
    metrics: Optional[List[str]] = Query(
        default=None, description="Specific metrics to analyze"
    ),
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Run trend analysis"""
    try:
        result = await analytics.run_trend_analysis(db, metrics=metrics)

        return {
            "success": True,
            "data": result,
            "metrics_analyzed": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in trend analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/realtime")
async def get_realtime_metrics(
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Get current real-time metrics"""
    try:
        result = await analytics.get_real_time_metrics()

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/datapoint")
async def add_metric_datapoint(
    datapoint: MetricDataPoint,
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Add a real-time metric data point"""
    try:
        await analytics.add_metric_data_point(
            datapoint.metric_name, datapoint.value, datapoint.timestamp
        )

        return {
            "success": True,
            "message": "Data point added successfully",
            "datapoint": datapoint.dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error adding metric datapoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/history/{metric_name}")
async def get_metric_history(
    metric_name: str,
    minutes: int = Query(
        default=60, ge=1, le=1440, description="Time range in minutes"
    ),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Get historical data for a specific metric"""
    try:
        history = await analytics.get_metric_history(metric_name, minutes)

        return {
            "success": True,
            "data": {
                "metric_name": metric_name,
                "history": history,
                "time_range_minutes": minutes,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting metric history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Report generation endpoints


@router.post("/reports/generate")
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    report_gen: ReportGenerator = Depends(get_report_generator),
) -> Dict[str, Any]:
    """Generate analytics report"""
    try:
        # Validate report type and format
        try:
            report_type = ReportType(request.report_type)
            report_format = ReportFormat(request.format)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid report type or format: {e}"
            )

        config = ReportConfig(
            report_type=report_type,
            format=report_format,
            time_range_hours=request.time_range_hours,
            include_charts=request.include_charts,
            include_recommendations=request.include_recommendations,
            custom_title=request.custom_title,
        )

        result = await report_gen.generate_report(db, config)

        return {
            "success": True,
            "data": result,
            "config": request.dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/executive-dashboard")
async def generate_executive_dashboard(
    time_range_days: int = Query(
        default=7, ge=1, le=30, description="Time range in days"
    ),
    db: AsyncSession = Depends(get_db),
    report_gen: ReportGenerator = Depends(get_report_generator),
) -> Dict[str, Any]:
    """Generate executive dashboard report"""
    try:
        result = await report_gen.generate_executive_dashboard(db, time_range_days)

        return {
            "success": True,
            "data": result,
            "time_range_days": time_range_days,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error generating executive dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/daily")
async def generate_daily_report(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Generate daily analytics report"""
    try:
        result = await analytics.generate_daily_report(db)

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/weekly")
async def generate_weekly_report(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Generate weekly analytics report"""
    try:
        result = await analytics.generate_weekly_report(db)

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error generating weekly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/scheduled")
async def generate_scheduled_reports(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    report_gen: ReportGenerator = Depends(get_report_generator),
) -> Dict[str, Any]:
    """Generate all scheduled reports (daily, weekly, monthly)"""
    try:
        # Run in background for performance
        background_tasks.add_task(
            _generate_scheduled_reports_background, db, report_gen
        )

        return {
            "success": True,
            "message": "Scheduled report generation started in background",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error initiating scheduled reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Configuration endpoints


@router.put("/config")
async def update_analytics_config(
    config_updates: Dict[str, Any],
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Update analytics service configuration"""
    try:
        analytics.update_configuration(config_updates)

        return {
            "success": True,
            "message": "Configuration updated successfully",
            "updated_config": config_updates,
            "current_config": analytics.get_service_status()["configuration"],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error updating analytics config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_analytics_config(
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Get current analytics service configuration"""
    try:
        status = analytics.get_service_status()

        return {
            "success": True,
            "data": {
                "configuration": status["configuration"],
                "components": status["components"],
                "last_analysis_runs": status["last_analysis_runs"],
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting analytics config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health and debugging endpoints


@router.get("/health")
async def analytics_health_check(
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Health check for analytics service"""
    try:
        status = analytics.get_service_status()

        # Determine overall health
        health_status = "healthy"
        if status["cache_size"] > 1000:
            health_status = "warning"

        return {
            "status": health_status,
            "components_status": status["components"],
            "cache_size": status["cache_size"],
            "background_tasks": status["background_tasks"],
            "last_analysis": status["last_analysis_runs"],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in analytics health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_analytics_cache(
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Clear analytics cache"""
    try:
        # Clear cache for each component
        analytics.performance_analyzer.clear_cache()
        analytics.data_aggregator.analysis_cache.clear()
        analytics.trend_analyzer.clear_cache()
        analytics.insight_generator.generated_insights.clear()

        return {
            "success": True,
            "message": "Analytics cache cleared successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error clearing analytics cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task functions


async def _generate_scheduled_reports_background(
    db: AsyncSession, report_gen: ReportGenerator
):
    """Background task for generating scheduled reports"""
    try:
        logger.info("Starting scheduled report generation in background")
        reports = await report_gen.generate_scheduled_reports(db)
        logger.info(
            f"Completed scheduled report generation: {len(reports)} report types"
        )
    except Exception as e:
        logger.error(f"Error in scheduled report generation: {e}")


# Startup event
@router.on_event("startup")
async def startup_analytics():
    """Initialize analytics service on startup"""
    try:
        global analytics_service
        analytics_service = AnalyticsService()
        await analytics_service.initialize()
        logger.info("✅ Analytics API initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Analytics API: {e}")


# Shutdown event
@router.on_event("shutdown")
async def shutdown_analytics():
    """Cleanup analytics service on shutdown"""
    try:
        global analytics_service
        if analytics_service:
            await analytics_service.shutdown()
        logger.info("✅ Analytics API shutdown complete")
    except Exception as e:
        logger.error(f"❌ Error during Analytics API shutdown: {e}")