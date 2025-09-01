"""
Performance Analytics Module for SubForge Dashboard
Analyzes agent performance metrics, task completion rates, and system efficiency
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
from scipy import stats
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from ...app.models.agent import Agent
from ...app.models.task import Task
from ...app.models.system_metrics import SystemMetrics
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class AgentPerformanceMetrics:
    """Agent performance metrics data class"""
    agent_id: str
    agent_name: str
    agent_type: str
    
    # Task metrics
    tasks_completed: int
    tasks_failed: int
    tasks_in_progress: int
    success_rate: float
    
    # Time metrics
    avg_completion_time: float
    median_completion_time: float
    min_completion_time: float
    max_completion_time: float
    
    # Efficiency metrics
    productivity_score: float
    reliability_score: float
    efficiency_score: float
    
    # Activity metrics
    uptime_hours: float
    active_hours: float
    idle_time_percentage: float
    
    # Trend data
    performance_trend: str  # "improving", "declining", "stable"
    trend_confidence: float


@dataclass
class SystemPerformanceMetrics:
    """System-wide performance metrics"""
    
    # Overall metrics
    total_agents: int
    active_agents: int
    total_tasks: int
    completed_tasks: int
    
    # Performance indicators
    system_efficiency: float
    overall_success_rate: float
    avg_task_completion_time: float
    system_load: float
    
    # Resource utilization
    cpu_utilization: float
    memory_utilization: float
    network_utilization: float
    
    # Bottleneck analysis
    bottlenecks: List[Dict[str, Any]]
    optimization_opportunities: List[Dict[str, Any]]


class PerformanceAnalyzer(BaseAnalyzer):
    """
    Comprehensive performance analyzer for SubForge system
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
    async def analyze_agent_performance(
        self, 
        db: AsyncSession, 
        agent_id: Optional[str] = None,
        time_range_hours: int = 24
    ) -> List[AgentPerformanceMetrics]:
        """
        Analyze performance metrics for agents
        
        Args:
            db: Database session
            agent_id: Specific agent ID (optional, analyzes all if None)
            time_range_hours: Time range for analysis in hours
            
        Returns:
            List of agent performance metrics
        """
        try:
            start_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            
            # Build query
            agent_query = select(Agent)
            if agent_id:
                agent_query = agent_query.where(Agent.id == agent_id)
                
            result = await db.execute(agent_query)
            agents = result.scalars().all()
            
            performance_metrics = []
            
            for agent in agents:
                metrics = await self._analyze_single_agent(db, agent, start_time)
                performance_metrics.append(metrics)
            
            # Sort by efficiency score
            performance_metrics.sort(key=lambda x: x.efficiency_score, reverse=True)
            
            self.logger.info(f"Analyzed performance for {len(performance_metrics)} agents")
            return performance_metrics
            
        except Exception as e:
            self.logger.error(f"Error analyzing agent performance: {e}")
            raise
    
    async def _analyze_single_agent(
        self, 
        db: AsyncSession, 
        agent: Agent, 
        start_time: datetime
    ) -> AgentPerformanceMetrics:
        """Analyze performance metrics for a single agent"""
        
        # Get agent tasks in time range
        task_query = select(Task).where(
            and_(
                Task.assigned_agent_id == agent.id,
                Task.created_at >= start_time
            )
        )
        result = await db.execute(task_query)
        tasks = result.scalars().all()
        
        # Calculate basic metrics
        completed_tasks = [t for t in tasks if t.status == "completed"]
        failed_tasks = [t for t in tasks if t.status == "failed"]
        in_progress_tasks = [t for t in tasks if t.status == "in_progress"]
        
        total_attempted = len(completed_tasks) + len(failed_tasks)
        success_rate = (len(completed_tasks) / total_attempted * 100) if total_attempted > 0 else 0
        
        # Calculate time metrics
        completion_times = [
            t.actual_duration_minutes for t in completed_tasks 
            if t.actual_duration_minutes is not None
        ]
        
        if completion_times:
            avg_completion_time = np.mean(completion_times)
            median_completion_time = np.median(completion_times)
            min_completion_time = min(completion_times)
            max_completion_time = max(completion_times)
        else:
            avg_completion_time = median_completion_time = 0
            min_completion_time = max_completion_time = 0
        
        # Calculate efficiency scores
        productivity_score = self._calculate_productivity_score(agent, completed_tasks)
        reliability_score = self._calculate_reliability_score(success_rate, agent.uptime_percentage)
        efficiency_score = (productivity_score + reliability_score) / 2
        
        # Calculate activity metrics
        now = datetime.utcnow()
        total_hours = (now - start_time).total_seconds() / 3600
        active_hours = total_hours * (agent.uptime_percentage / 100)
        idle_time_percentage = 100 - agent.uptime_percentage
        
        # Analyze performance trend
        trend_data = await self._analyze_performance_trend(db, agent.id, start_time)
        
        return AgentPerformanceMetrics(
            agent_id=str(agent.id),
            agent_name=agent.name,
            agent_type=agent.agent_type,
            tasks_completed=len(completed_tasks),
            tasks_failed=len(failed_tasks),
            tasks_in_progress=len(in_progress_tasks),
            success_rate=success_rate,
            avg_completion_time=avg_completion_time,
            median_completion_time=median_completion_time,
            min_completion_time=min_completion_time,
            max_completion_time=max_completion_time,
            productivity_score=productivity_score,
            reliability_score=reliability_score,
            efficiency_score=efficiency_score,
            uptime_hours=active_hours,
            active_hours=active_hours,
            idle_time_percentage=idle_time_percentage,
            performance_trend=trend_data["trend"],
            trend_confidence=trend_data["confidence"]
        )
    
    def _calculate_productivity_score(self, agent: Agent, completed_tasks: List[Task]) -> float:
        """Calculate productivity score based on tasks completed and complexity"""
        if not completed_tasks:
            return 0.0
        
        # Base score from task completion
        base_score = min(len(completed_tasks) * 10, 80)  # Max 80 from volume
        
        # Quality bonus
        quality_scores = [t.quality_score for t in completed_tasks if t.quality_score is not None]
        if quality_scores:
            quality_bonus = np.mean(quality_scores) * 20  # Max 20 from quality
        else:
            quality_bonus = 0
        
        return min(base_score + quality_bonus, 100)
    
    def _calculate_reliability_score(self, success_rate: float, uptime_percentage: float) -> float:
        """Calculate reliability score based on success rate and uptime"""
        return (success_rate * 0.7) + (uptime_percentage * 0.3)
    
    async def _analyze_performance_trend(
        self, 
        db: AsyncSession, 
        agent_id: str, 
        start_time: datetime
    ) -> Dict[str, Any]:
        """Analyze performance trend for an agent"""
        
        try:
            # Get historical performance data
            intervals = 6  # Analyze in 6 intervals
            interval_hours = (datetime.utcnow() - start_time).total_seconds() / 3600 / intervals
            
            performance_points = []
            
            for i in range(intervals):
                interval_start = start_time + timedelta(hours=i * interval_hours)
                interval_end = start_time + timedelta(hours=(i + 1) * interval_hours)
                
                task_query = select(Task).where(
                    and_(
                        Task.assigned_agent_id == agent_id,
                        Task.created_at >= interval_start,
                        Task.created_at < interval_end,
                        Task.status == "completed"
                    )
                )
                
                result = await db.execute(task_query)
                tasks = result.scalars().all()
                
                # Simple performance metric: tasks completed per hour
                performance = len(tasks) / interval_hours if interval_hours > 0 else 0
                performance_points.append(performance)
            
            if len(performance_points) < 3:
                return {"trend": "insufficient_data", "confidence": 0.0}
            
            # Calculate trend using linear regression
            x = np.arange(len(performance_points))
            y = np.array(performance_points)
            
            if np.std(y) == 0:  # No variation
                return {"trend": "stable", "confidence": 1.0}
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            confidence = abs(r_value)  # R-squared as confidence measure
            
            if slope > 0.1 and confidence > 0.5:
                trend = "improving"
            elif slope < -0.1 and confidence > 0.5:
                trend = "declining"
            else:
                trend = "stable"
                
            return {"trend": trend, "confidence": confidence}
            
        except Exception as e:
            self.logger.warning(f"Error analyzing performance trend: {e}")
            return {"trend": "unknown", "confidence": 0.0}
    
    async def analyze_system_performance(
        self, 
        db: AsyncSession,
        time_range_hours: int = 24
    ) -> SystemPerformanceMetrics:
        """
        Analyze overall system performance
        
        Args:
            db: Database session
            time_range_hours: Time range for analysis in hours
            
        Returns:
            System performance metrics
        """
        try:
            start_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            
            # Get system data
            agents_result = await db.execute(select(Agent))
            agents = agents_result.scalars().all()
            
            tasks_result = await db.execute(
                select(Task).where(Task.created_at >= start_time)
            )
            tasks = tasks_result.scalars().all()
            
            # Calculate basic metrics
            total_agents = len(agents)
            active_agents = len([a for a in agents if a.status == "active"])
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == "completed"])
            
            # Calculate performance indicators
            overall_success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            completion_times = [
                t.actual_duration_minutes for t in tasks 
                if t.actual_duration_minutes is not None and t.status == "completed"
            ]
            avg_task_completion_time = np.mean(completion_times) if completion_times else 0
            
            # Calculate system efficiency
            system_efficiency = self._calculate_system_efficiency(agents, tasks)
            
            # Get latest system metrics for resource utilization
            latest_metrics_result = await db.execute(
                select(SystemMetrics).order_by(SystemMetrics.recorded_at.desc()).limit(1)
            )
            latest_metrics = latest_metrics_result.scalar_one_or_none()
            
            if latest_metrics:
                cpu_utilization = latest_metrics.cpu_usage_percentage
                memory_utilization = latest_metrics.memory_usage_percentage
                system_load = latest_metrics.system_load_percentage
                network_utilization = latest_metrics.api_requests_per_minute
            else:
                cpu_utilization = memory_utilization = system_load = network_utilization = 0
            
            # Identify bottlenecks and optimization opportunities
            bottlenecks = await self._identify_bottlenecks(db, agents, tasks)
            optimization_opportunities = await self._identify_optimization_opportunities(db, agents, tasks)
            
            return SystemPerformanceMetrics(
                total_agents=total_agents,
                active_agents=active_agents,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                system_efficiency=system_efficiency,
                overall_success_rate=overall_success_rate,
                avg_task_completion_time=avg_task_completion_time,
                system_load=system_load,
                cpu_utilization=cpu_utilization,
                memory_utilization=memory_utilization,
                network_utilization=network_utilization,
                bottlenecks=bottlenecks,
                optimization_opportunities=optimization_opportunities
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing system performance: {e}")
            raise
    
    def _calculate_system_efficiency(self, agents: List[Agent], tasks: List[Task]) -> float:
        """Calculate overall system efficiency score"""
        if not agents or not tasks:
            return 0.0
        
        # Agent utilization efficiency
        active_agents = len([a for a in agents if a.status == "active"])
        agent_utilization = (active_agents / len(agents)) * 100
        
        # Task completion efficiency
        completed_tasks = len([t for t in tasks if t.status == "completed"])
        completion_efficiency = (completed_tasks / len(tasks)) * 100
        
        # Average agent success rate
        agent_success_rates = [a.success_rate for a in agents if a.success_rate > 0]
        avg_success_rate = np.mean(agent_success_rates) if agent_success_rates else 0
        
        # Weighted efficiency score
        efficiency = (
            agent_utilization * 0.3 +
            completion_efficiency * 0.4 +
            avg_success_rate * 0.3
        )
        
        return min(efficiency, 100.0)
    
    async def _identify_bottlenecks(
        self, 
        db: AsyncSession, 
        agents: List[Agent], 
        tasks: List[Task]
    ) -> List[Dict[str, Any]]:
        """Identify system bottlenecks"""
        bottlenecks = []
        
        # Check for agent overload
        overloaded_agents = [
            a for a in agents 
            if a.status == "active" and len([t for t in tasks if t.assigned_agent_id == a.id]) > 10
        ]
        
        if overloaded_agents:
            bottlenecks.append({
                "type": "agent_overload",
                "description": f"{len(overloaded_agents)} agents are handling excessive workload",
                "severity": "high" if len(overloaded_agents) > 3 else "medium",
                "affected_agents": [str(a.id) for a in overloaded_agents],
                "recommendation": "Consider load balancing or adding more agents"
            })
        
        # Check for task backlog
        pending_tasks = [t for t in tasks if t.status == "pending"]
        if len(pending_tasks) > 50:
            bottlenecks.append({
                "type": "task_backlog",
                "description": f"{len(pending_tasks)} tasks are pending",
                "severity": "high" if len(pending_tasks) > 100 else "medium",
                "count": len(pending_tasks),
                "recommendation": "Scale up agent capacity or optimize task distribution"
            })
        
        # Check for failed tasks pattern
        failed_tasks = [t for t in tasks if t.status == "failed"]
        if len(failed_tasks) / len(tasks) > 0.1:  # More than 10% failure rate
            bottlenecks.append({
                "type": "high_failure_rate",
                "description": f"System has {len(failed_tasks) / len(tasks) * 100:.1f}% task failure rate",
                "severity": "high",
                "failure_rate": len(failed_tasks) / len(tasks) * 100,
                "recommendation": "Investigate task failures and improve error handling"
            })
        
        return bottlenecks
    
    async def _identify_optimization_opportunities(
        self, 
        db: AsyncSession, 
        agents: List[Agent], 
        tasks: List[Task]
    ) -> List[Dict[str, Any]]:
        """Identify optimization opportunities"""
        opportunities = []
        
        # Check for idle agents
        idle_agents = [a for a in agents if a.status == "idle"]
        if len(idle_agents) > 2:
            opportunities.append({
                "type": "idle_resources",
                "description": f"{len(idle_agents)} agents are idle",
                "potential_impact": "medium",
                "idle_count": len(idle_agents),
                "recommendation": "Redistribute tasks or temporarily scale down unused agents"
            })
        
        # Check for task complexity optimization
        long_running_tasks = [
            t for t in tasks 
            if t.actual_duration_minutes and t.actual_duration_minutes > 120
        ]
        if long_running_tasks:
            opportunities.append({
                "type": "task_optimization",
                "description": f"{len(long_running_tasks)} tasks take over 2 hours to complete",
                "potential_impact": "high",
                "long_task_count": len(long_running_tasks),
                "recommendation": "Break down long tasks or optimize task execution"
            })
        
        # Check for underutilized agent types
        agent_types = {}
        for agent in agents:
            agent_types[agent.agent_type] = agent_types.get(agent.agent_type, 0) + 1
        
        for agent_type, count in agent_types.items():
            type_tasks = [t for t in tasks if any(a.agent_type == agent_type and a.id == t.assigned_agent_id for a in agents)]
            if count > 1 and len(type_tasks) < count * 5:  # Less than 5 tasks per agent
                opportunities.append({
                    "type": "underutilized_agents",
                    "description": f"{agent_type} agents are underutilized",
                    "potential_impact": "low",
                    "agent_type": agent_type,
                    "agent_count": count,
                    "task_count": len(type_tasks),
                    "recommendation": "Consider consolidating or reassigning agent responsibilities"
                })
        
        return opportunities
    
    async def generate_performance_report(
        self, 
        db: AsyncSession,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Args:
            db: Database session
            time_range_hours: Time range for analysis
            
        Returns:
            Comprehensive performance report
        """
        try:
            # Get all performance data
            agent_metrics = await self.analyze_agent_performance(db, time_range_hours=time_range_hours)
            system_metrics = await self.analyze_system_performance(db, time_range_hours=time_range_hours)
            
            # Generate summary statistics
            if agent_metrics:
                top_performers = sorted(agent_metrics, key=lambda x: x.efficiency_score, reverse=True)[:5]
                bottom_performers = sorted(agent_metrics, key=lambda x: x.efficiency_score)[:3]
                avg_efficiency = np.mean([m.efficiency_score for m in agent_metrics])
                avg_success_rate = np.mean([m.success_rate for m in agent_metrics])
            else:
                top_performers = bottom_performers = []
                avg_efficiency = avg_success_rate = 0
            
            # Generate insights
            insights = self._generate_performance_insights(agent_metrics, system_metrics)
            
            report = {
                "report_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "time_range_hours": time_range_hours,
                    "report_type": "performance_analysis"
                },
                "system_overview": asdict(system_metrics),
                "agent_summary": {
                    "total_agents_analyzed": len(agent_metrics),
                    "average_efficiency_score": avg_efficiency,
                    "average_success_rate": avg_success_rate,
                    "top_performers": [asdict(agent) for agent in top_performers],
                    "needs_attention": [asdict(agent) for agent in bottom_performers]
                },
                "detailed_agent_metrics": [asdict(agent) for agent in agent_metrics],
                "insights_and_recommendations": insights,
                "next_analysis_scheduled": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            raise
    
    def _generate_performance_insights(
        self, 
        agent_metrics: List[AgentPerformanceMetrics], 
        system_metrics: SystemPerformanceMetrics
    ) -> Dict[str, Any]:
        """Generate insights from performance data"""
        
        insights = {
            "key_findings": [],
            "recommendations": [],
            "alerts": []
        }
        
        if not agent_metrics:
            insights["alerts"].append("No agent performance data available")
            return insights
        
        # Analyze efficiency distribution
        efficiency_scores = [m.efficiency_score for m in agent_metrics]
        avg_efficiency = np.mean(efficiency_scores)
        
        if avg_efficiency > 80:
            insights["key_findings"].append("System is operating at high efficiency")
        elif avg_efficiency < 50:
            insights["key_findings"].append("System efficiency is below optimal levels")
            insights["alerts"].append("Low system efficiency detected")
        
        # Check for performance trends
        improving_agents = [m for m in agent_metrics if m.performance_trend == "improving"]
        declining_agents = [m for m in agent_metrics if m.performance_trend == "declining"]
        
        if len(improving_agents) > len(declining_agents):
            insights["key_findings"].append(f"{len(improving_agents)} agents showing performance improvements")
        elif len(declining_agents) > len(improving_agents):
            insights["key_findings"].append(f"{len(declining_agents)} agents showing performance decline")
            insights["recommendations"].append("Review and support underperforming agents")
        
        # System capacity analysis
        if system_metrics.system_load > 80:
            insights["alerts"].append("High system load detected")
            insights["recommendations"].append("Consider scaling up system capacity")
        
        # Success rate analysis
        success_rates = [m.success_rate for m in agent_metrics]
        low_success_agents = [m for m in agent_metrics if m.success_rate < 70]
        
        if low_success_agents:
            insights["alerts"].append(f"{len(low_success_agents)} agents have success rates below 70%")
            insights["recommendations"].append("Investigate and improve low-performing agents")
        
        return insights