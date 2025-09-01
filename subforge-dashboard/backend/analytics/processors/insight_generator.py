"""
Insight Generation Module for SubForge Analytics
AI-powered insight generation and actionable recommendations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from ...app.models.agent import Agent
from ...app.models.task import Task
from ...app.models.workflow import Workflow
from ...app.models.system_metrics import SystemMetrics
from ..models.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class InsightType(Enum):
    PERFORMANCE = "performance"
    EFFICIENCY = "efficiency"
    RELIABILITY = "reliability"
    CAPACITY = "capacity"
    COST = "cost"
    SECURITY = "security"
    USER_EXPERIENCE = "user_experience"


class InsightPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ActionType(Enum):
    IMMEDIATE = "immediate"
    PLANNED = "planned"
    MONITORING = "monitoring"
    INVESTIGATION = "investigation"


@dataclass
class Insight:
    """AI-generated insight with actionable recommendations"""
    id: str
    title: str
    description: str
    insight_type: InsightType
    priority: InsightPriority
    
    # Evidence and context
    evidence: Dict[str, Any]
    affected_components: List[str]
    
    # Impact assessment
    impact_description: str
    estimated_impact_percentage: float
    confidence_score: float
    
    # Actionable recommendations
    recommended_actions: List[str]
    action_type: ActionType
    estimated_effort_hours: int
    
    # Business context
    business_value: str
    risk_level: str
    
    # Metadata
    generated_at: datetime
    data_sources: List[str]
    expires_at: Optional[datetime] = None


@dataclass
class InsightPattern:
    """Pattern used for insight generation"""
    pattern_name: str
    conditions: List[str]
    insight_template: str
    priority_logic: str
    evidence_requirements: List[str]


class InsightGenerator(BaseAnalyzer):
    """
    AI-powered insight generator for SubForge analytics
    Generates actionable insights from system data and patterns
    """
    
    def __init__(self):
        super().__init__()
        self.insight_patterns = self._initialize_insight_patterns()
        self.generated_insights = []
        self.insight_history = []
        
    def _initialize_insight_patterns(self) -> List[InsightPattern]:
        """Initialize predefined insight patterns"""
        patterns = [
            # Performance patterns
            InsightPattern(
                pattern_name="low_system_efficiency",
                conditions=["efficiency_score < 70", "trend_declining"],
                insight_template="System efficiency is below optimal levels at {efficiency_score}%",
                priority_logic="high if efficiency_score < 60 else medium",
                evidence_requirements=["efficiency_score", "trend_data", "agent_utilization"]
            ),
            
            InsightPattern(
                pattern_name="agent_overload",
                conditions=["agent_task_count > 15", "success_rate_declining"],
                insight_template="Agent {agent_name} is handling {task_count} tasks with declining success rate",
                priority_logic="critical if task_count > 20 else high",
                evidence_requirements=["agent_metrics", "task_distribution"]
            ),
            
            InsightPattern(
                pattern_name="task_backlog_growing",
                conditions=["pending_tasks > 50", "completion_rate < 80"],
                insight_template="Task backlog growing with {pending_count} pending tasks",
                priority_logic="high if pending_tasks > 100 else medium",
                evidence_requirements=["task_metrics", "completion_rates"]
            ),
            
            # Reliability patterns
            InsightPattern(
                pattern_name="failure_rate_spike",
                conditions=["failure_rate > 10", "failure_rate_increase > 5"],
                insight_template="Task failure rate has spiked to {failure_rate}%",
                priority_logic="critical",
                evidence_requirements=["failure_metrics", "error_patterns"]
            ),
            
            # Capacity patterns
            InsightPattern(
                pattern_name="resource_underutilization",
                conditions=["resource_utilization < 30", "idle_time > 60"],
                insight_template="{resource_type} resources are underutilized at {utilization}%",
                priority_logic="medium",
                evidence_requirements=["resource_metrics", "utilization_data"]
            ),
            
            # Cost optimization patterns
            InsightPattern(
                pattern_name="idle_agent_costs",
                conditions=["idle_agents > 2", "idle_duration > 4_hours"],
                insight_template="{idle_count} agents have been idle for over {duration} hours",
                priority_logic="medium if idle_count > 5 else low",
                evidence_requirements=["agent_activity", "cost_data"]
            )
        ]
        
        return patterns
    
    async def analyze(self, db: AsyncSession, **kwargs) -> Dict[str, Any]:
        """Main analysis method - generates comprehensive insights"""
        
        # Collect system intelligence data
        intelligence_data = await self._collect_system_intelligence(db)
        
        # Generate insights from patterns
        pattern_insights = await self._generate_pattern_insights(intelligence_data)
        
        # Generate AI-driven insights
        ai_insights = await self._generate_ai_insights(intelligence_data)
        
        # Combine and prioritize insights
        all_insights = pattern_insights + ai_insights
        prioritized_insights = self._prioritize_insights(all_insights)
        
        # Generate insight summary and recommendations
        summary = await self._generate_insight_summary(prioritized_insights, intelligence_data)
        
        # Store insights for historical tracking
        self._store_insights(prioritized_insights)
        
        return {
            "insights": [asdict(insight) for insight in prioritized_insights],
            "insight_summary": summary,
            "intelligence_data": intelligence_data,
            "generation_metadata": {
                "total_insights": len(prioritized_insights),
                "patterns_evaluated": len(self.insight_patterns),
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    
    async def _collect_system_intelligence(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Collect comprehensive system intelligence for insight generation
        """
        try:
            # Time ranges
            now = datetime.utcnow()
            last_hour = now - timedelta(hours=1)
            last_day = now - timedelta(days=1)
            last_week = now - timedelta(days=7)
            
            # Agent intelligence
            agents_query = select(Agent)
            agents_result = await db.execute(agents_query)
            agents = agents_result.scalars().all()
            
            agent_intelligence = await self._analyze_agent_intelligence(agents)
            
            # Task intelligence
            tasks_query = select(Task).where(Task.created_at >= last_week)
            tasks_result = await db.execute(tasks_query)
            tasks = tasks_result.scalars().all()
            
            task_intelligence = await self._analyze_task_intelligence(tasks)
            
            # System metrics intelligence
            metrics_query = select(SystemMetrics).where(
                SystemMetrics.recorded_at >= last_day
            ).order_by(SystemMetrics.recorded_at.desc())
            metrics_result = await db.execute(metrics_query)
            metrics = metrics_result.scalars().all()
            
            system_intelligence = await self._analyze_system_intelligence(metrics)
            
            # Workflow intelligence
            workflows_query = select(Workflow)
            workflows_result = await db.execute(workflows_query)
            workflows = workflows_result.scalars().all()
            
            workflow_intelligence = await self._analyze_workflow_intelligence(workflows)
            
            return {
                "agents": agent_intelligence,
                "tasks": task_intelligence,
                "system": system_intelligence,
                "workflows": workflow_intelligence,
                "collection_timestamp": now.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting system intelligence: {e}")
            return {}
    
    async def _analyze_agent_intelligence(self, agents: List[Agent]) -> Dict[str, Any]:
        """Analyze agent-related intelligence"""
        
        if not agents:
            return {"total_agents": 0}
        
        # Basic statistics
        total_agents = len(agents)
        active_agents = len([a for a in agents if a.status == "active"])
        idle_agents = len([a for a in agents if a.status == "idle"])
        offline_agents = len([a for a in agents if a.status == "offline"])
        
        # Performance analysis
        success_rates = [a.success_rate for a in agents if a.success_rate > 0]
        response_times = [a.avg_response_time for a in agents if a.avg_response_time > 0]
        uptime_percentages = [a.uptime_percentage for a in agents]
        
        avg_success_rate = np.mean(success_rates) if success_rates else 0
        avg_response_time = np.mean(response_times) if response_times else 0
        avg_uptime = np.mean(uptime_percentages) if uptime_percentages else 100
        
        # Identify problem agents
        problem_agents = []
        top_performers = []
        
        for agent in agents:
            if agent.success_rate < 70 or agent.uptime_percentage < 90:
                problem_agents.append({
                    "id": str(agent.id),
                    "name": agent.name,
                    "success_rate": agent.success_rate,
                    "uptime": agent.uptime_percentage,
                    "issues": []
                })
                
                if agent.success_rate < 70:
                    problem_agents[-1]["issues"].append("low_success_rate")
                if agent.uptime_percentage < 90:
                    problem_agents[-1]["issues"].append("low_uptime")
            
            elif agent.success_rate > 90 and agent.uptime_percentage > 95:
                top_performers.append({
                    "id": str(agent.id),
                    "name": agent.name,
                    "success_rate": agent.success_rate,
                    "uptime": agent.uptime_percentage
                })
        
        # Agent type analysis
        agent_types = Counter([a.agent_type for a in agents])
        
        # Workload distribution
        task_counts = [a.tasks_completed + a.tasks_failed for a in agents]
        workload_balance = np.std(task_counts) / np.mean(task_counts) if np.mean(task_counts) > 0 else 0
        
        return {
            "total_agents": total_agents,
            "status_distribution": {
                "active": active_agents,
                "idle": idle_agents,
                "offline": offline_agents
            },
            "performance_metrics": {
                "avg_success_rate": avg_success_rate,
                "avg_response_time": avg_response_time,
                "avg_uptime": avg_uptime
            },
            "problem_agents": problem_agents,
            "top_performers": top_performers,
            "agent_types": dict(agent_types),
            "workload_balance_score": workload_balance,
            "utilization_rate": (active_agents / total_agents * 100) if total_agents > 0 else 0
        }
    
    async def _analyze_task_intelligence(self, tasks: List[Task]) -> Dict[str, Any]:
        """Analyze task-related intelligence"""
        
        if not tasks:
            return {"total_tasks": 0}
        
        # Status distribution
        status_counts = Counter([t.status for t in tasks])
        total_tasks = len(tasks)
        
        # Time-based analysis
        now = datetime.utcnow()
        recent_tasks = [t for t in tasks if t.created_at and (now - t.created_at).total_seconds() < 3600]  # Last hour
        
        # Completion analysis
        completed_tasks = [t for t in tasks if t.status == "completed"]
        failed_tasks = [t for t in tasks if t.status == "failed"]
        
        completion_rate = (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0
        failure_rate = (len(failed_tasks) / total_tasks * 100) if total_tasks > 0 else 0
        
        # Duration analysis
        completion_times = [
            t.actual_duration_minutes for t in completed_tasks 
            if t.actual_duration_minutes is not None
        ]
        
        if completion_times:
            avg_completion_time = np.mean(completion_times)
            median_completion_time = np.median(completion_times)
            p95_completion_time = np.percentile(completion_times, 95)
        else:
            avg_completion_time = median_completion_time = p95_completion_time = 0
        
        # Priority analysis
        priority_counts = Counter([t.priority for t in tasks])
        high_priority_backlog = len([t for t in tasks if t.priority in ["high", "urgent"] and t.status == "pending"])
        
        # Agent workload distribution
        agent_task_counts = Counter([str(t.assigned_agent_id) for t in tasks if t.assigned_agent_id])
        
        # Identify bottlenecks
        bottlenecks = []
        if len(recent_tasks) < len([t for t in tasks if (now - t.created_at).total_seconds() < 7200]):  # Slowdown
            bottlenecks.append("throughput_decline")
        
        if failure_rate > 10:
            bottlenecks.append("high_failure_rate")
        
        if high_priority_backlog > 10:
            bottlenecks.append("priority_backlog")
        
        return {
            "total_tasks": total_tasks,
            "status_distribution": dict(status_counts),
            "completion_metrics": {
                "completion_rate": completion_rate,
                "failure_rate": failure_rate,
                "avg_completion_time": avg_completion_time,
                "median_completion_time": median_completion_time,
                "p95_completion_time": p95_completion_time
            },
            "priority_distribution": dict(priority_counts),
            "high_priority_backlog": high_priority_backlog,
            "recent_activity": {
                "tasks_last_hour": len(recent_tasks),
                "throughput_per_hour": len(recent_tasks)
            },
            "workload_distribution": dict(agent_task_counts),
            "identified_bottlenecks": bottlenecks
        }
    
    async def _analyze_system_intelligence(self, metrics: List[SystemMetrics]) -> Dict[str, Any]:
        """Analyze system-level intelligence"""
        
        if not metrics:
            return {"total_metrics": 0}
        
        # Get latest metrics
        latest = metrics[0] if metrics else None
        
        if not latest:
            return {"total_metrics": 0}
        
        # Resource utilization analysis
        current_cpu = latest.cpu_usage_percentage
        current_memory = latest.memory_usage_percentage
        current_load = latest.system_load_percentage
        
        # Trend analysis (simple)
        if len(metrics) >= 5:
            recent_metrics = metrics[:5]
            cpu_trend = self._calculate_simple_trend([m.cpu_usage_percentage for m in recent_metrics])
            memory_trend = self._calculate_simple_trend([m.memory_usage_percentage for m in recent_metrics])
            load_trend = self._calculate_simple_trend([m.system_load_percentage for m in recent_metrics])
        else:
            cpu_trend = memory_trend = load_trend = "stable"
        
        # Health assessment
        health_score = 100
        health_issues = []
        
        if current_cpu > 80:
            health_score -= 20
            health_issues.append("high_cpu_usage")
        
        if current_memory > 85:
            health_score -= 25
            health_issues.append("high_memory_usage")
        
        if current_load > 90:
            health_score -= 30
            health_issues.append("system_overload")
        
        if latest.error_rate_percentage > 5:
            health_score -= 15
            health_issues.append("high_error_rate")
        
        # Performance indicators
        uptime = latest.uptime_percentage
        error_rate = latest.error_rate_percentage
        response_time = latest.avg_response_time_ms
        
        return {
            "total_metrics": len(metrics),
            "current_state": {
                "cpu_usage": current_cpu,
                "memory_usage": current_memory,
                "system_load": current_load,
                "uptime": uptime,
                "error_rate": error_rate,
                "avg_response_time": response_time
            },
            "trends": {
                "cpu_trend": cpu_trend,
                "memory_trend": memory_trend,
                "load_trend": load_trend
            },
            "health_assessment": {
                "health_score": max(0, health_score),
                "health_issues": health_issues,
                "status": "healthy" if health_score > 80 else 
                         "warning" if health_score > 60 else "critical"
            },
            "capacity_status": {
                "cpu_headroom": 100 - current_cpu,
                "memory_headroom": 100 - current_memory,
                "load_headroom": 100 - current_load
            }
        }
    
    async def _analyze_workflow_intelligence(self, workflows: List[Workflow]) -> Dict[str, Any]:
        """Analyze workflow-related intelligence"""
        
        if not workflows:
            return {"total_workflows": 0}
        
        # Status distribution
        status_counts = Counter([w.status for w in workflows])
        total_workflows = len(workflows)
        
        # Success analysis
        completed_workflows = [w for w in workflows if w.status == "completed"]
        failed_workflows = [w for w in workflows if w.status == "failed"]
        
        success_rate = (len(completed_workflows) / total_workflows * 100) if total_workflows > 0 else 0
        
        return {
            "total_workflows": total_workflows,
            "status_distribution": dict(status_counts),
            "success_rate": success_rate,
            "active_workflows": status_counts.get("active", 0),
            "completed_workflows": len(completed_workflows),
            "failed_workflows": len(failed_workflows)
        }
    
    def _calculate_simple_trend(self, values: List[float]) -> str:
        """Calculate simple trend from values"""
        if len(values) < 2:
            return "stable"
        
        recent_avg = np.mean(values[:2])
        earlier_avg = np.mean(values[-2:])
        
        change_pct = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg != 0 else 0
        
        if change_pct > 10:
            return "increasing"
        elif change_pct < -10:
            return "decreasing"
        else:
            return "stable"
    
    async def _generate_pattern_insights(self, intelligence_data: Dict[str, Any]) -> List[Insight]:
        """Generate insights based on predefined patterns"""
        
        insights = []
        
        # System efficiency insights
        system_data = intelligence_data.get("system", {})
        health_score = system_data.get("health_assessment", {}).get("health_score", 100)
        
        if health_score < 70:
            insights.append(self._create_insight(
                title="System Health Below Optimal",
                description=f"System health score is {health_score}/100. Immediate attention required.",
                insight_type=InsightType.RELIABILITY,
                priority=InsightPriority.CRITICAL if health_score < 50 else InsightPriority.HIGH,
                evidence={"health_score": health_score, "health_issues": system_data.get("health_assessment", {}).get("health_issues", [])},
                affected_components=["system_health", "performance_monitor"],
                impact_description="System instability and potential service disruptions",
                estimated_impact_percentage=30.0,
                confidence_score=0.9,
                recommended_actions=[
                    "Investigate system health issues immediately",
                    "Check resource utilization and capacity",
                    "Review error logs and performance metrics",
                    "Implement immediate corrective measures"
                ],
                action_type=ActionType.IMMEDIATE,
                estimated_effort_hours=4
            ))
        
        # Agent performance insights
        agent_data = intelligence_data.get("agents", {})
        problem_agents = agent_data.get("problem_agents", [])
        
        if len(problem_agents) > 2:
            insights.append(self._create_insight(
                title="Multiple Agents Underperforming",
                description=f"{len(problem_agents)} agents are showing performance issues",
                insight_type=InsightType.PERFORMANCE,
                priority=InsightPriority.HIGH,
                evidence={"problem_agents": problem_agents, "total_agents": agent_data.get("total_agents", 0)},
                affected_components=["agent_manager", "performance_monitor"],
                impact_description="Reduced system capacity and reliability",
                estimated_impact_percentage=25.0,
                confidence_score=0.85,
                recommended_actions=[
                    "Review agent configurations and resources",
                    "Investigate root causes of performance issues",
                    "Consider agent reallocation or replacement",
                    "Implement performance monitoring enhancements"
                ],
                action_type=ActionType.PLANNED,
                estimated_effort_hours=8
            ))
        
        # Task backlog insights
        task_data = intelligence_data.get("tasks", {})
        high_priority_backlog = task_data.get("high_priority_backlog", 0)
        
        if high_priority_backlog > 10:
            insights.append(self._create_insight(
                title="High Priority Task Backlog",
                description=f"{high_priority_backlog} high-priority tasks are pending",
                insight_type=InsightType.CAPACITY,
                priority=InsightPriority.HIGH,
                evidence={"backlog_count": high_priority_backlog, "task_distribution": task_data.get("priority_distribution", {})},
                affected_components=["task_scheduler", "load_balancer"],
                impact_description="SLA violations and delayed critical work",
                estimated_impact_percentage=20.0,
                confidence_score=0.9,
                recommended_actions=[
                    "Increase agent capacity for high-priority tasks",
                    "Review task prioritization algorithms",
                    "Implement emergency task processing",
                    "Consider temporary resource scaling"
                ],
                action_type=ActionType.IMMEDIATE,
                estimated_effort_hours=6
            ))
        
        # Resource utilization insights
        utilization_rate = agent_data.get("utilization_rate", 100)
        
        if utilization_rate < 50:
            insights.append(self._create_insight(
                title="Low Agent Utilization",
                description=f"Agent utilization is only {utilization_rate:.1f}%",
                insight_type=InsightType.EFFICIENCY,
                priority=InsightPriority.MEDIUM,
                evidence={"utilization_rate": utilization_rate, "idle_agents": agent_data.get("status_distribution", {}).get("idle", 0)},
                affected_components=["resource_manager", "load_balancer"],
                impact_description="Inefficient resource usage and increased costs",
                estimated_impact_percentage=15.0,
                confidence_score=0.8,
                recommended_actions=[
                    "Analyze workload distribution patterns",
                    "Consider scaling down unused resources",
                    "Implement dynamic resource allocation",
                    "Review capacity planning strategies"
                ],
                action_type=ActionType.PLANNED,
                estimated_effort_hours=12
            ))
        
        return insights
    
    async def _generate_ai_insights(self, intelligence_data: Dict[str, Any]) -> List[Insight]:
        """Generate AI-driven insights from patterns and correlations"""
        
        insights = []
        
        # Correlation analysis between metrics
        system_data = intelligence_data.get("system", {})
        agent_data = intelligence_data.get("agents", {})
        task_data = intelligence_data.get("tasks", {})
        
        # CPU vs Performance correlation
        current_cpu = system_data.get("current_state", {}).get("cpu_usage", 0)
        avg_success_rate = agent_data.get("performance_metrics", {}).get("avg_success_rate", 100)
        
        if current_cpu > 70 and avg_success_rate < 80:
            insights.append(self._create_insight(
                title="Performance Degradation Due to High CPU",
                description=f"High CPU usage ({current_cpu}%) is correlating with low success rates ({avg_success_rate:.1f}%)",
                insight_type=InsightType.PERFORMANCE,
                priority=InsightPriority.HIGH,
                evidence={"cpu_usage": current_cpu, "success_rate": avg_success_rate},
                affected_components=["system_resources", "agent_performance"],
                impact_description="System performance bottleneck affecting agent success",
                estimated_impact_percentage=25.0,
                confidence_score=0.85,
                recommended_actions=[
                    "Optimize CPU-intensive operations",
                    "Implement resource monitoring and alerting",
                    "Consider scaling up computational resources",
                    "Review and optimize algorithms"
                ],
                action_type=ActionType.PLANNED,
                estimated_effort_hours=16
            ))
        
        # Workload balance analysis
        workload_balance = agent_data.get("workload_balance_score", 0)
        
        if workload_balance > 0.5:  # High workload imbalance
            insights.append(self._create_insight(
                title="Significant Workload Imbalance Detected",
                description="Uneven task distribution is creating performance bottlenecks",
                insight_type=InsightType.EFFICIENCY,
                priority=InsightPriority.MEDIUM,
                evidence={"workload_balance_score": workload_balance},
                affected_components=["load_balancer", "task_scheduler"],
                impact_description="Some agents overloaded while others underutilized",
                estimated_impact_percentage=18.0,
                confidence_score=0.75,
                recommended_actions=[
                    "Implement intelligent load balancing",
                    "Analyze task routing algorithms",
                    "Monitor agent capacity in real-time",
                    "Optimize task assignment strategies"
                ],
                action_type=ActionType.PLANNED,
                estimated_effort_hours=10
            ))
        
        # Failure rate trend analysis
        failure_rate = task_data.get("completion_metrics", {}).get("failure_rate", 0)
        bottlenecks = task_data.get("identified_bottlenecks", [])
        
        if failure_rate > 5 and "high_failure_rate" in bottlenecks:
            insights.append(self._create_insight(
                title="Increasing Task Failure Rate Pattern",
                description=f"Task failure rate of {failure_rate:.1f}% indicates systemic issues",
                insight_type=InsightType.RELIABILITY,
                priority=InsightPriority.HIGH,
                evidence={"failure_rate": failure_rate, "bottlenecks": bottlenecks},
                affected_components=["task_processor", "error_handler"],
                impact_description="System reliability degradation and potential cascading failures",
                estimated_impact_percentage=30.0,
                confidence_score=0.9,
                recommended_actions=[
                    "Investigate error patterns and root causes",
                    "Implement enhanced error handling",
                    "Add retry mechanisms and circuit breakers",
                    "Review system dependencies"
                ],
                action_type=ActionType.IMMEDIATE,
                estimated_effort_hours=8
            ))
        
        return insights
    
    def _create_insight(
        self,
        title: str,
        description: str,
        insight_type: InsightType,
        priority: InsightPriority,
        evidence: Dict[str, Any],
        affected_components: List[str],
        impact_description: str,
        estimated_impact_percentage: float,
        confidence_score: float,
        recommended_actions: List[str],
        action_type: ActionType,
        estimated_effort_hours: int
    ) -> Insight:
        """Create an insight object"""
        
        insight_id = f"insight_{int(datetime.utcnow().timestamp())}_{hash(title) % 10000}"
        
        # Determine business value and risk level
        business_value = self._assess_business_value(impact_description, estimated_impact_percentage)
        risk_level = self._assess_risk_level(priority, estimated_impact_percentage)
        
        return Insight(
            id=insight_id,
            title=title,
            description=description,
            insight_type=insight_type,
            priority=priority,
            evidence=evidence,
            affected_components=affected_components,
            impact_description=impact_description,
            estimated_impact_percentage=estimated_impact_percentage,
            confidence_score=confidence_score,
            recommended_actions=recommended_actions,
            action_type=action_type,
            estimated_effort_hours=estimated_effort_hours,
            business_value=business_value,
            risk_level=risk_level,
            generated_at=datetime.utcnow(),
            data_sources=["agents", "tasks", "system_metrics"]
        )
    
    def _assess_business_value(self, impact_description: str, impact_percentage: float) -> str:
        """Assess business value of addressing the insight"""
        if impact_percentage > 25:
            return "high"
        elif impact_percentage > 15:
            return "medium"
        else:
            return "low"
    
    def _assess_risk_level(self, priority: InsightPriority, impact_percentage: float) -> str:
        """Assess risk level if insight is not addressed"""
        if priority == InsightPriority.CRITICAL:
            return "critical"
        elif priority == InsightPriority.HIGH and impact_percentage > 20:
            return "high"
        elif priority == InsightPriority.MEDIUM:
            return "medium"
        else:
            return "low"
    
    def _prioritize_insights(self, insights: List[Insight]) -> List[Insight]:
        """Prioritize insights based on priority, impact, and confidence"""
        
        def priority_score(insight: Insight) -> float:
            priority_weights = {
                InsightPriority.CRITICAL: 100,
                InsightPriority.HIGH: 80,
                InsightPriority.MEDIUM: 60,
                InsightPriority.LOW: 40,
                InsightPriority.INFO: 20
            }
            
            base_score = priority_weights.get(insight.priority, 40)
            impact_score = insight.estimated_impact_percentage
            confidence_bonus = insight.confidence_score * 20
            
            return base_score + impact_score + confidence_bonus
        
        return sorted(insights, key=priority_score, reverse=True)
    
    async def _generate_insight_summary(
        self, 
        insights: List[Insight], 
        intelligence_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary of insights and recommendations"""
        
        # Priority distribution
        priority_counts = Counter([i.priority.value for i in insights])
        
        # Type distribution
        type_counts = Counter([i.insight_type.value for i in insights])
        
        # Action type distribution
        action_counts = Counter([i.action_type.value for i in insights])
        
        # Calculate total potential impact
        total_impact = sum(i.estimated_impact_percentage for i in insights[:5])  # Top 5
        total_effort = sum(i.estimated_effort_hours for i in insights[:5])
        
        # Key insights
        critical_insights = [i for i in insights if i.priority == InsightPriority.CRITICAL]
        high_impact_insights = [i for i in insights if i.estimated_impact_percentage > 20]
        
        # Generate action plan
        immediate_actions = [i for i in insights if i.action_type == ActionType.IMMEDIATE]
        planned_actions = [i for i in insights if i.action_type == ActionType.PLANNED]
        
        return {
            "total_insights": len(insights),
            "priority_distribution": dict(priority_counts),
            "type_distribution": dict(type_counts),
            "action_distribution": dict(action_counts),
            "impact_assessment": {
                "total_potential_impact": min(total_impact, 100),
                "implementation_effort_hours": total_effort,
                "roi_estimate": f"{total_impact / (total_effort / 40):.1f}% per week" if total_effort > 0 else "N/A"
            },
            "key_findings": {
                "critical_issues": len(critical_insights),
                "high_impact_opportunities": len(high_impact_insights),
                "immediate_actions_required": len(immediate_actions),
                "planned_improvements": len(planned_actions)
            },
            "executive_summary": self._generate_executive_summary(insights, intelligence_data),
            "next_steps": [
                f"Address {len(immediate_actions)} immediate action items",
                f"Plan implementation of {len(planned_actions)} improvement initiatives", 
                "Monitor system metrics for improvement validation",
                "Schedule follow-up analysis in 1 week"
            ]
        }
    
    def _generate_executive_summary(
        self, 
        insights: List[Insight], 
        intelligence_data: Dict[str, Any]
    ) -> List[str]:
        """Generate executive summary points"""
        
        summary = []
        
        # System health summary
        system_data = intelligence_data.get("system", {})
        health_score = system_data.get("health_assessment", {}).get("health_score", 100)
        
        if health_score < 70:
            summary.append(f"System health is below optimal at {health_score}/100 - immediate attention required")
        elif health_score < 90:
            summary.append(f"System health is good at {health_score}/100 with room for improvement")
        else:
            summary.append(f"System health is excellent at {health_score}/100")
        
        # Critical insights
        critical_count = len([i for i in insights if i.priority == InsightPriority.CRITICAL])
        if critical_count > 0:
            summary.append(f"{critical_count} critical issues identified requiring immediate action")
        
        # Opportunity insights
        efficiency_insights = len([i for i in insights if i.insight_type == InsightType.EFFICIENCY])
        if efficiency_insights > 0:
            summary.append(f"{efficiency_insights} efficiency improvement opportunities identified")
        
        # Performance insights
        performance_insights = len([i for i in insights if i.insight_type == InsightType.PERFORMANCE])
        if performance_insights > 0:
            summary.append(f"{performance_insights} performance optimization recommendations available")
        
        return summary
    
    def _store_insights(self, insights: List[Insight]):
        """Store insights for historical tracking"""
        self.generated_insights = insights
        self.insight_history.append({
            "timestamp": datetime.utcnow(),
            "insight_count": len(insights),
            "insights": [asdict(insight) for insight in insights]
        })
        
        # Keep only recent history (last 10 generations)
        if len(self.insight_history) > 10:
            self.insight_history = self.insight_history[-10:]
    
    def get_insight_by_id(self, insight_id: str) -> Optional[Insight]:
        """Get specific insight by ID"""
        for insight in self.generated_insights:
            if insight.id == insight_id:
                return insight
        return None
    
    def get_insights_by_type(self, insight_type: InsightType) -> List[Insight]:
        """Get insights by type"""
        return [i for i in self.generated_insights if i.insight_type == insight_type]
    
    def get_insights_by_priority(self, priority: InsightPriority) -> List[Insight]:
        """Get insights by priority"""
        return [i for i in self.generated_insights if i.priority == priority]