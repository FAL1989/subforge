"""
Data Aggregation Module for SubForge Analytics
Processes and aggregates real-time metrics from agent activities
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from ...app.models.agent import Agent
from ...app.models.task import Task
from ...app.models.workflow import Workflow  
from ...app.models.system_metrics import SystemMetrics
from ..models.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class MetricWindow:
    """Time window for metric aggregation"""
    window_size_minutes: int
    data_points: deque
    timestamps: deque
    max_points: int = 1000
    
    def add_point(self, value: float, timestamp: datetime = None):
        """Add a data point to the window"""
        timestamp = timestamp or datetime.utcnow()
        
        # Remove old points outside window
        cutoff_time = timestamp - timedelta(minutes=self.window_size_minutes)
        while self.timestamps and self.timestamps[0] < cutoff_time:
            self.timestamps.popleft()
            self.data_points.popleft()
        
        # Add new point
        self.data_points.append(value)
        self.timestamps.append(timestamp)
        
        # Limit total points for memory management
        while len(self.data_points) > self.max_points:
            self.data_points.popleft()
            self.timestamps.popleft()
    
    def get_stats(self) -> Dict[str, float]:
        """Get statistics for current window"""
        if not self.data_points:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "std": 0}
        
        values = list(self.data_points)
        return {
            "count": len(values),
            "avg": np.mean(values),
            "min": np.min(values),
            "max": np.max(values),
            "std": np.std(values),
            "sum": np.sum(values)
        }


@dataclass
class AggregatedMetrics:
    """Container for aggregated metrics"""
    timestamp: datetime
    time_period: str  # "1min", "5min", "1hour", "1day"
    
    # System metrics
    system_load: float
    cpu_usage: float
    memory_usage: float
    active_agents: int
    
    # Task metrics  
    tasks_completed: int
    tasks_failed: int
    tasks_pending: int
    avg_completion_time: float
    
    # Agent metrics
    agent_success_rate: float
    agent_response_time: float
    agent_uptime: float
    
    # Workflow metrics
    workflows_active: int
    workflows_completed: int
    workflow_success_rate: float
    
    # Performance indicators
    throughput_tasks_per_hour: float
    error_rate_percentage: float
    availability_percentage: float


class DataAggregator(BaseAnalyzer):
    """
    Real-time data aggregation engine for SubForge metrics
    Processes streaming data and generates time-based aggregations
    """
    
    def __init__(self):
        super().__init__()
        
        # Metric windows for different time periods
        self.metric_windows = {
            "1min": {},
            "5min": {},
            "15min": {},
            "1hour": {},
            "1day": {}
        }
        
        # Initialize windows for key metrics
        self._initialize_metric_windows()
        
        # Real-time metric buffers
        self.real_time_buffers = defaultdict(deque)
        self.buffer_max_size = 10000
        
        # Aggregation state
        self.last_aggregation = {}
        self.aggregation_lock = asyncio.Lock()
        
        # Statistics cache
        self.stats_cache = {}
        self.cache_ttl = timedelta(minutes=1)
        
    def _initialize_metric_windows(self):
        """Initialize metric windows for different time periods"""
        window_configs = {
            "1min": 1,
            "5min": 5,
            "15min": 15,
            "1hour": 60,
            "1day": 1440
        }
        
        metric_names = [
            "system_load", "cpu_usage", "memory_usage", "task_completion_time",
            "agent_response_time", "tasks_per_minute", "error_rate", "success_rate"
        ]
        
        for period, window_size in window_configs.items():
            self.metric_windows[period] = {}
            for metric_name in metric_names:
                self.metric_windows[period][metric_name] = MetricWindow(
                    window_size_minutes=window_size,
                    data_points=deque(),
                    timestamps=deque()
                )
    
    async def analyze(self, db: AsyncSession, **kwargs) -> Dict[str, Any]:
        """Main analysis method - performs comprehensive data aggregation"""
        
        # Real-time aggregation
        real_time_metrics = await self.aggregate_real_time_metrics(db)
        
        # Historical aggregation
        historical_metrics = await self.aggregate_historical_metrics(db)
        
        # Statistical summaries
        statistical_summaries = await self.generate_statistical_summaries(db)
        
        return {
            "real_time": real_time_metrics,
            "historical": historical_metrics,
            "statistics": statistical_summaries,
            "aggregation_metadata": {
                "last_update": datetime.utcnow().isoformat(),
                "total_windows": sum(len(windows) for windows in self.metric_windows.values()),
                "buffer_sizes": {key: len(buffer) for key, buffer in self.real_time_buffers.items()}
            }
        }
    
    async def aggregate_real_time_metrics(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Aggregate real-time metrics from current system state
        """
        try:
            current_time = datetime.utcnow()
            
            # Get current system state
            agents = await self._get_current_agents(db)
            tasks = await self._get_recent_tasks(db, hours=1)
            system_metrics = await self._get_latest_system_metrics(db)
            
            # Calculate real-time aggregations for different periods
            aggregations = {}
            
            for period in ["1min", "5min", "15min", "1hour"]:
                aggregations[period] = await self._aggregate_for_period(
                    agents, tasks, system_metrics, period, current_time
                )
            
            # Update metric windows
            await self._update_metric_windows(aggregations, current_time)
            
            return aggregations
            
        except Exception as e:
            self.logger.error(f"Error in real-time aggregation: {e}")
            return {}
    
    async def _aggregate_for_period(
        self, 
        agents: List[Agent], 
        tasks: List[Task], 
        system_metrics: SystemMetrics,
        period: str,
        current_time: datetime
    ) -> AggregatedMetrics:
        """Aggregate metrics for a specific time period"""
        
        # Calculate period boundaries
        period_minutes = {"1min": 1, "5min": 5, "15min": 15, "1hour": 60}[period]
        period_start = current_time - timedelta(minutes=period_minutes)
        
        # Filter data for period
        period_tasks = [t for t in tasks if t.created_at and t.created_at >= period_start]
        
        # System metrics
        system_load = system_metrics.system_load_percentage if system_metrics else 0
        cpu_usage = system_metrics.cpu_usage_percentage if system_metrics else 0
        memory_usage = system_metrics.memory_usage_percentage if system_metrics else 0
        active_agents = len([a for a in agents if a.status == "active"])
        
        # Task metrics
        completed_tasks = [t for t in period_tasks if t.status == "completed"]
        failed_tasks = [t for t in period_tasks if t.status == "failed"]
        pending_tasks = [t for t in period_tasks if t.status == "pending"]
        
        # Calculate completion times
        completion_times = [
            t.actual_duration_minutes for t in completed_tasks 
            if t.actual_duration_minutes is not None
        ]
        avg_completion_time = np.mean(completion_times) if completion_times else 0
        
        # Agent metrics
        agent_success_rates = [a.success_rate for a in agents if a.success_rate > 0]
        agent_response_times = [a.avg_response_time for a in agents if a.avg_response_time > 0]
        agent_uptimes = [a.uptime_percentage for a in agents]
        
        avg_agent_success_rate = np.mean(agent_success_rates) if agent_success_rates else 0
        avg_agent_response_time = np.mean(agent_response_times) if agent_response_times else 0
        avg_agent_uptime = np.mean(agent_uptimes) if agent_uptimes else 100
        
        # Performance indicators
        tasks_per_hour = len(completed_tasks) * (60 / period_minutes)
        total_attempted = len(completed_tasks) + len(failed_tasks)
        error_rate = (len(failed_tasks) / total_attempted * 100) if total_attempted > 0 else 0
        availability = avg_agent_uptime
        
        return AggregatedMetrics(
            timestamp=current_time,
            time_period=period,
            system_load=system_load,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            active_agents=active_agents,
            tasks_completed=len(completed_tasks),
            tasks_failed=len(failed_tasks),
            tasks_pending=len(pending_tasks),
            avg_completion_time=avg_completion_time,
            agent_success_rate=avg_agent_success_rate,
            agent_response_time=avg_agent_response_time,
            agent_uptime=avg_agent_uptime,
            workflows_active=0,  # Would need workflow data
            workflows_completed=0,
            workflow_success_rate=0,
            throughput_tasks_per_hour=tasks_per_hour,
            error_rate_percentage=error_rate,
            availability_percentage=availability
        )
    
    async def _update_metric_windows(self, aggregations: Dict[str, Any], timestamp: datetime):
        """Update sliding metric windows with new data"""
        
        for period, metrics in aggregations.items():
            if period in self.metric_windows:
                windows = self.metric_windows[period]
                
                # Update each metric window
                if "system_load" in windows:
                    windows["system_load"].add_point(metrics.system_load, timestamp)
                if "cpu_usage" in windows:
                    windows["cpu_usage"].add_point(metrics.cpu_usage, timestamp)
                if "memory_usage" in windows:
                    windows["memory_usage"].add_point(metrics.memory_usage, timestamp)
                if "task_completion_time" in windows:
                    windows["task_completion_time"].add_point(metrics.avg_completion_time, timestamp)
                if "agent_response_time" in windows:
                    windows["agent_response_time"].add_point(metrics.agent_response_time, timestamp)
                if "tasks_per_minute" in windows:
                    windows["tasks_per_minute"].add_point(metrics.throughput_tasks_per_hour / 60, timestamp)
                if "error_rate" in windows:
                    windows["error_rate"].add_point(metrics.error_rate_percentage, timestamp)
                if "success_rate" in windows:
                    windows["success_rate"].add_point(metrics.agent_success_rate, timestamp)
    
    async def aggregate_historical_metrics(
        self, 
        db: AsyncSession, 
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Aggregate historical metrics for trend analysis
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)
            
            # Get historical data
            historical_metrics = await self._get_historical_system_metrics(db, start_time, end_time)
            historical_tasks = await self._get_historical_tasks(db, start_time, end_time)
            
            # Generate daily, weekly aggregations
            daily_aggregates = await self._aggregate_by_day(historical_metrics, historical_tasks)
            weekly_aggregates = await self._aggregate_by_week(historical_metrics, historical_tasks)
            
            return {
                "daily": daily_aggregates,
                "weekly": weekly_aggregates,
                "period": f"{days_back} days",
                "total_data_points": len(historical_metrics)
            }
            
        except Exception as e:
            self.logger.error(f"Error in historical aggregation: {e}")
            return {}
    
    async def _aggregate_by_day(
        self, 
        metrics: List[SystemMetrics], 
        tasks: List[Task]
    ) -> List[Dict[str, Any]]:
        """Aggregate metrics by day"""
        
        # Group by day
        daily_groups = defaultdict(lambda: {"metrics": [], "tasks": []})
        
        for metric in metrics:
            if metric.recorded_at:
                day_key = metric.recorded_at.date()
                daily_groups[day_key]["metrics"].append(metric)
        
        for task in tasks:
            if task.created_at:
                day_key = task.created_at.date()
                daily_groups[day_key]["tasks"].append(task)
        
        # Calculate daily aggregates
        daily_aggregates = []
        for day, data in sorted(daily_groups.items()):
            day_metrics = data["metrics"]
            day_tasks = data["tasks"]
            
            # Calculate averages for the day
            if day_metrics:
                avg_cpu = np.mean([m.cpu_usage_percentage for m in day_metrics])
                avg_memory = np.mean([m.memory_usage_percentage for m in day_metrics])
                avg_load = np.mean([m.system_load_percentage for m in day_metrics])
                avg_success_rate = np.mean([m.overall_success_rate for m in day_metrics])
            else:
                avg_cpu = avg_memory = avg_load = avg_success_rate = 0
            
            # Task statistics
            completed_tasks = len([t for t in day_tasks if t.status == "completed"])
            failed_tasks = len([t for t in day_tasks if t.status == "failed"])
            total_tasks = len(day_tasks)
            
            daily_aggregates.append({
                "date": day.isoformat(),
                "system_metrics": {
                    "avg_cpu_usage": avg_cpu,
                    "avg_memory_usage": avg_memory,
                    "avg_system_load": avg_load,
                    "avg_success_rate": avg_success_rate
                },
                "task_metrics": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks,
                    "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                }
            })
        
        return daily_aggregates
    
    async def _aggregate_by_week(
        self, 
        metrics: List[SystemMetrics], 
        tasks: List[Task]
    ) -> List[Dict[str, Any]]:
        """Aggregate metrics by week"""
        
        # Group by week
        weekly_groups = defaultdict(lambda: {"metrics": [], "tasks": []})
        
        for metric in metrics:
            if metric.recorded_at:
                # Get ISO week
                year, week, _ = metric.recorded_at.isocalendar()
                week_key = f"{year}-W{week:02d}"
                weekly_groups[week_key]["metrics"].append(metric)
        
        for task in tasks:
            if task.created_at:
                year, week, _ = task.created_at.isocalendar()
                week_key = f"{year}-W{week:02d}"
                weekly_groups[week_key]["tasks"].append(task)
        
        # Calculate weekly aggregates
        weekly_aggregates = []
        for week, data in sorted(weekly_groups.items()):
            week_metrics = data["metrics"]
            week_tasks = data["tasks"]
            
            # Calculate averages for the week
            if week_metrics:
                avg_cpu = np.mean([m.cpu_usage_percentage for m in week_metrics])
                avg_memory = np.mean([m.memory_usage_percentage for m in week_metrics])
                avg_load = np.mean([m.system_load_percentage for m in week_metrics])
                avg_success_rate = np.mean([m.overall_success_rate for m in week_metrics])
                uptime = np.mean([m.uptime_percentage for m in week_metrics])
            else:
                avg_cpu = avg_memory = avg_load = avg_success_rate = uptime = 0
            
            # Task statistics
            completed_tasks = len([t for t in week_tasks if t.status == "completed"])
            failed_tasks = len([t for t in week_tasks if t.status == "failed"])
            total_tasks = len(week_tasks)
            
            weekly_aggregates.append({
                "week": week,
                "system_metrics": {
                    "avg_cpu_usage": avg_cpu,
                    "avg_memory_usage": avg_memory,
                    "avg_system_load": avg_load,
                    "avg_success_rate": avg_success_rate,
                    "avg_uptime": uptime
                },
                "task_metrics": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks,
                    "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                }
            })
        
        return weekly_aggregates
    
    async def generate_statistical_summaries(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Generate statistical summaries from metric windows
        """
        try:
            summaries = {}
            
            for period, windows in self.metric_windows.items():
                period_stats = {}
                
                for metric_name, window in windows.items():
                    stats = window.get_stats()
                    if stats["count"] > 0:
                        period_stats[metric_name] = stats
                
                if period_stats:
                    summaries[period] = period_stats
            
            # Add trend analysis
            trends = await self._analyze_metric_trends()
            summaries["trends"] = trends
            
            return summaries
            
        except Exception as e:
            self.logger.error(f"Error generating statistical summaries: {e}")
            return {}
    
    async def _analyze_metric_trends(self) -> Dict[str, Any]:
        """Analyze trends in metric windows"""
        trends = {}
        
        for period, windows in self.metric_windows.items():
            if period == "1hour":  # Analyze hourly trends
                period_trends = {}
                
                for metric_name, window in windows.items():
                    if len(window.data_points) >= 10:  # Need sufficient data
                        values = list(window.data_points)
                        
                        # Simple trend analysis
                        recent_values = values[-5:]  # Last 5 points
                        earlier_values = values[:5]   # First 5 points
                        
                        if len(recent_values) >= 3 and len(earlier_values) >= 3:
                            recent_avg = np.mean(recent_values)
                            earlier_avg = np.mean(earlier_values)
                            
                            change_pct = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg != 0 else 0
                            
                            if abs(change_pct) > 10:  # Significant change
                                trend = "increasing" if change_pct > 0 else "decreasing"
                            else:
                                trend = "stable"
                            
                            period_trends[metric_name] = {
                                "trend": trend,
                                "change_percentage": change_pct,
                                "confidence": min(len(values) / 20, 1.0)  # More data = higher confidence
                            }
                
                if period_trends:
                    trends[period] = period_trends
        
        return trends
    
    async def add_real_time_metric(
        self, 
        metric_name: str, 
        value: float, 
        timestamp: datetime = None
    ):
        """
        Add a real-time metric data point
        For external services to feed real-time data
        """
        timestamp = timestamp or datetime.utcnow()
        
        # Add to buffer
        buffer = self.real_time_buffers[metric_name]
        buffer.append((timestamp, value))
        
        # Limit buffer size
        while len(buffer) > self.buffer_max_size:
            buffer.popleft()
        
        # Update relevant metric windows
        for period, windows in self.metric_windows.items():
            if metric_name in windows:
                windows[metric_name].add_point(value, timestamp)
    
    def get_current_metric_stats(self, metric_name: str, period: str = "5min") -> Dict[str, Any]:
        """Get current statistics for a specific metric"""
        if period in self.metric_windows and metric_name in self.metric_windows[period]:
            return self.metric_windows[period][metric_name].get_stats()
        return {}
    
    def get_metric_history(self, metric_name: str, minutes: int = 60) -> List[Tuple[datetime, float]]:
        """Get historical data points for a metric"""
        if metric_name not in self.real_time_buffers:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            (timestamp, value) for timestamp, value in self.real_time_buffers[metric_name]
            if timestamp >= cutoff_time
        ]
    
    async def cleanup_old_data(self, retention_hours: int = 24):
        """Clean up old data to manage memory usage"""
        cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
        
        # Clean buffers
        for metric_name, buffer in self.real_time_buffers.items():
            # Remove old points
            while buffer and buffer[0][0] < cutoff_time:
                buffer.popleft()
        
        self.logger.info(f"Cleaned up data older than {retention_hours} hours")
    
    # Helper methods for data retrieval
    async def _get_current_agents(self, db: AsyncSession) -> List[Agent]:
        """Get current agents"""
        result = await db.execute(select(Agent))
        return result.scalars().all()
    
    async def _get_recent_tasks(self, db: AsyncSession, hours: int = 1) -> List[Task]:
        """Get recent tasks"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        result = await db.execute(
            select(Task).where(Task.created_at >= start_time)
        )
        return result.scalars().all()
    
    async def _get_latest_system_metrics(self, db: AsyncSession) -> Optional[SystemMetrics]:
        """Get latest system metrics"""
        result = await db.execute(
            select(SystemMetrics).order_by(desc(SystemMetrics.recorded_at)).limit(1)
        )
        return result.scalar_one_or_none()
    
    async def _get_historical_system_metrics(
        self, 
        db: AsyncSession, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[SystemMetrics]:
        """Get historical system metrics"""
        result = await db.execute(
            select(SystemMetrics).where(
                and_(
                    SystemMetrics.recorded_at >= start_time,
                    SystemMetrics.recorded_at <= end_time
                )
            ).order_by(SystemMetrics.recorded_at)
        )
        return result.scalars().all()
    
    async def _get_historical_tasks(
        self, 
        db: AsyncSession, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Task]:
        """Get historical tasks"""
        result = await db.execute(
            select(Task).where(
                and_(
                    Task.created_at >= start_time,
                    Task.created_at <= end_time
                )
            ).order_by(Task.created_at)
        )
        return result.scalars().all()