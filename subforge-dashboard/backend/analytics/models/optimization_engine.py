"""
Optimization Engine for SubForge Dashboard
Provides AI-powered optimization recommendations for system performance
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...app.models.agent import Agent
from ...app.models.system_metrics import SystemMetrics
from ...app.models.task import Task
from ...app.models.workflow import Workflow
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class OptimizationPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OptimizationCategory(Enum):
    PERFORMANCE = "performance"
    RESOURCE_ALLOCATION = "resource_allocation"
    WORKFLOW_EFFICIENCY = "workflow_efficiency"
    COST_OPTIMIZATION = "cost_optimization"
    RELIABILITY = "reliability"


@dataclass
class OptimizationRecommendation:
    """Individual optimization recommendation"""

    id: str
    title: str
    description: str
    category: OptimizationCategory
    priority: OptimizationPriority

    # Impact assessment
    expected_improvement: str
    estimated_impact_percentage: float
    confidence_score: float

    # Implementation details
    implementation_complexity: str  # "low", "medium", "high"
    estimated_effort_hours: int
    implementation_steps: List[str]

    # Supporting data
    evidence: Dict[str, Any]
    affected_components: List[str]

    # Tracking
    created_at: datetime
    status: str = "pending"  # pending, implemented, rejected


@dataclass
class SystemAnalysis:
    """Comprehensive system analysis results"""

    efficiency_score: float
    bottlenecks: List[Dict[str, Any]]
    underutilized_resources: List[Dict[str, Any]]
    performance_trends: Dict[str, Any]
    resource_allocation: Dict[str, Any]


class OptimizationEngine(BaseAnalyzer):
    """
    AI-powered optimization engine for SubForge system
    Analyzes system performance and generates actionable recommendations
    """

    def __init__(self):
        super().__init__()
        self.recommendations_cache = []
        self.analysis_history = []

    async def analyze(self, db: AsyncSession, **kwargs) -> Dict[str, Any]:
        """Main analysis method - generates comprehensive optimization recommendations"""

        # Perform system analysis
        system_analysis = await self.analyze_system_performance(db)

        # Generate optimization recommendations
        recommendations = await self.generate_recommendations(db, system_analysis)

        # Prioritize recommendations
        prioritized_recommendations = self._prioritize_recommendations(recommendations)

        # Generate implementation roadmap
        roadmap = self._generate_implementation_roadmap(prioritized_recommendations)

        result = {
            "system_analysis": asdict(system_analysis),
            "recommendations": [asdict(rec) for rec in prioritized_recommendations],
            "implementation_roadmap": roadmap,
            "summary": self._generate_summary(system_analysis, recommendations),
        }

        self.analysis_history.append({"timestamp": datetime.utcnow(), "result": result})

        return result

    async def analyze_system_performance(self, db: AsyncSession) -> SystemAnalysis:
        """
        Perform comprehensive system performance analysis
        """
        try:
            # Get system data
            agents = await self._get_agents_with_metrics(db)
            tasks = await self._get_tasks_with_metrics(db)
            workflows = await self._get_workflows_with_metrics(db)
            system_metrics = await self._get_recent_system_metrics(db)

            # Calculate efficiency score
            efficiency_score = await self._calculate_system_efficiency(
                agents, tasks, workflows
            )

            # Identify bottlenecks
            bottlenecks = await self._identify_system_bottlenecks(
                db, agents, tasks, workflows
            )

            # Find underutilized resources
            underutilized_resources = await self._identify_underutilized_resources(
                agents, tasks
            )

            # Analyze performance trends
            performance_trends = await self._analyze_performance_trends(
                db, system_metrics
            )

            # Analyze resource allocation
            resource_allocation = self._analyze_resource_allocation(agents, tasks)

            return SystemAnalysis(
                efficiency_score=efficiency_score,
                bottlenecks=bottlenecks,
                underutilized_resources=underutilized_resources,
                performance_trends=performance_trends,
                resource_allocation=resource_allocation,
            )

        except Exception as e:
            self.logger.error(f"Error in system analysis: {e}")
            # Return default analysis
            return SystemAnalysis(
                efficiency_score=50.0,
                bottlenecks=[],
                underutilized_resources=[],
                performance_trends={},
                resource_allocation={},
            )

    async def generate_recommendations(
        self, db: AsyncSession, analysis: SystemAnalysis
    ) -> List[OptimizationRecommendation]:
        """
        Generate optimization recommendations based on system analysis
        """
        recommendations = []

        # Performance optimization recommendations
        recommendations.extend(
            await self._generate_performance_recommendations(analysis)
        )

        # Resource allocation recommendations
        recommendations.extend(await self._generate_resource_recommendations(analysis))

        # Workflow optimization recommendations
        recommendations.extend(
            await self._generate_workflow_recommendations(db, analysis)
        )

        # Cost optimization recommendations
        recommendations.extend(await self._generate_cost_recommendations(analysis))

        # Reliability improvements
        recommendations.extend(
            await self._generate_reliability_recommendations(db, analysis)
        )

        return recommendations

    async def _generate_performance_recommendations(
        self, analysis: SystemAnalysis
    ) -> List[OptimizationRecommendation]:
        """Generate performance-focused recommendations"""
        recommendations = []

        # Low efficiency score
        if analysis.efficiency_score < 70:
            recommendations.append(
                OptimizationRecommendation(
                    id=f"perf_efficiency_{int(datetime.utcnow().timestamp())}",
                    title="Improve Overall System Efficiency",
                    description=f"System efficiency is at {analysis.efficiency_score:.1f}%. "
                    f"Implementing targeted optimizations could improve performance.",
                    category=OptimizationCategory.PERFORMANCE,
                    priority=OptimizationPriority.HIGH,
                    expected_improvement="15-25% efficiency increase",
                    estimated_impact_percentage=20.0,
                    confidence_score=0.85,
                    implementation_complexity="medium",
                    estimated_effort_hours=16,
                    implementation_steps=[
                        "Analyze performance bottlenecks in detail",
                        "Optimize agent task allocation algorithms",
                        "Implement performance monitoring enhancements",
                        "Fine-tune system parameters",
                    ],
                    evidence={
                        "current_efficiency": analysis.efficiency_score,
                        "target_efficiency": 85.0,
                        "bottleneck_count": len(analysis.bottlenecks),
                    },
                    affected_components=[
                        "task_scheduler",
                        "agent_manager",
                        "performance_monitor",
                    ],
                    created_at=datetime.utcnow(),
                )
            )

        # Address specific bottlenecks
        for bottleneck in analysis.bottlenecks:
            if bottleneck.get("severity") == "high":
                recommendations.append(
                    OptimizationRecommendation(
                        id=f"perf_bottleneck_{bottleneck.get('type', 'unknown')}",
                        title=f"Resolve {bottleneck.get('type', 'Unknown')} Bottleneck",
                        description=f"Critical bottleneck detected: {bottleneck.get('description', '')}",
                        category=OptimizationCategory.PERFORMANCE,
                        priority=OptimizationPriority.CRITICAL,
                        expected_improvement="Eliminate performance bottleneck",
                        estimated_impact_percentage=30.0,
                        confidence_score=0.90,
                        implementation_complexity="high",
                        estimated_effort_hours=24,
                        implementation_steps=self._get_bottleneck_resolution_steps(
                            bottleneck
                        ),
                        evidence=bottleneck,
                        affected_components=bottleneck.get("affected_components", []),
                        created_at=datetime.utcnow(),
                    )
                )

        return recommendations

    async def _generate_resource_recommendations(
        self, analysis: SystemAnalysis
    ) -> List[OptimizationRecommendation]:
        """Generate resource allocation recommendations"""
        recommendations = []

        # Underutilized resources
        for resource in analysis.underutilized_resources:
            if resource.get("utilization_percentage", 100) < 30:
                recommendations.append(
                    OptimizationRecommendation(
                        id=f"resource_underutil_{resource.get('type', 'unknown')}",
                        title=f"Optimize {resource.get('name', 'Resource')} Utilization",
                        description=f"Resource is only {resource.get('utilization_percentage', 0):.1f}% utilized. "
                        f"Consider reallocation or scaling down.",
                        category=OptimizationCategory.RESOURCE_ALLOCATION,
                        priority=OptimizationPriority.MEDIUM,
                        expected_improvement="Better resource efficiency",
                        estimated_impact_percentage=15.0,
                        confidence_score=0.75,
                        implementation_complexity="low",
                        estimated_effort_hours=4,
                        implementation_steps=[
                            "Analyze resource usage patterns",
                            "Implement resource reallocation strategy",
                            "Monitor utilization improvements",
                        ],
                        evidence=resource,
                        affected_components=[resource.get("name", "unknown")],
                        created_at=datetime.utcnow(),
                    )
                )

        # Resource allocation imbalance
        resource_alloc = analysis.resource_allocation
        if resource_alloc.get("imbalance_score", 0) > 0.3:
            recommendations.append(
                OptimizationRecommendation(
                    id="resource_rebalance",
                    title="Rebalance Resource Allocation",
                    description="Detected significant resource allocation imbalance across agents.",
                    category=OptimizationCategory.RESOURCE_ALLOCATION,
                    priority=OptimizationPriority.HIGH,
                    expected_improvement="More balanced workload distribution",
                    estimated_impact_percentage=18.0,
                    confidence_score=0.80,
                    implementation_complexity="medium",
                    estimated_effort_hours=12,
                    implementation_steps=[
                        "Analyze current workload distribution",
                        "Implement intelligent load balancing",
                        "Redistribute tasks across agents",
                        "Monitor balance improvements",
                    ],
                    evidence=resource_alloc,
                    affected_components=["load_balancer", "task_scheduler"],
                    created_at=datetime.utcnow(),
                )
            )

        return recommendations

    async def _generate_workflow_recommendations(
        self, db: AsyncSession, analysis: SystemAnalysis
    ) -> List[OptimizationRecommendation]:
        """Generate workflow optimization recommendations"""
        recommendations = []

        # Analyze workflow patterns
        workflows = await self._get_workflows_with_metrics(db)

        # Long-running workflows
        long_workflows = [
            w for w in workflows if getattr(w, "avg_duration_hours", 0) > 8
        ]

        if long_workflows:
            recommendations.append(
                OptimizationRecommendation(
                    id="workflow_duration_optimize",
                    title="Optimize Long-Running Workflows",
                    description=f"Found {len(long_workflows)} workflows with extended execution times.",
                    category=OptimizationCategory.WORKFLOW_EFFICIENCY,
                    priority=OptimizationPriority.HIGH,
                    expected_improvement="Reduce workflow execution time by 25-40%",
                    estimated_impact_percentage=30.0,
                    confidence_score=0.75,
                    implementation_complexity="high",
                    estimated_effort_hours=32,
                    implementation_steps=[
                        "Profile workflow execution patterns",
                        "Identify parallelization opportunities",
                        "Optimize task dependencies",
                        "Implement workflow caching strategies",
                    ],
                    evidence={"long_workflow_count": len(long_workflows)},
                    affected_components=["workflow_engine", "task_scheduler"],
                    created_at=datetime.utcnow(),
                )
            )

        # Workflow failure patterns
        failed_workflows = [w for w in workflows if getattr(w, "failure_rate", 0) > 0.1]

        if failed_workflows:
            recommendations.append(
                OptimizationRecommendation(
                    id="workflow_reliability_improve",
                    title="Improve Workflow Reliability",
                    description=f"Several workflows showing high failure rates. Implementing error handling improvements.",
                    category=OptimizationCategory.RELIABILITY,
                    priority=OptimizationPriority.HIGH,
                    expected_improvement="Reduce workflow failures by 50-70%",
                    estimated_impact_percentage=25.0,
                    confidence_score=0.85,
                    implementation_complexity="medium",
                    estimated_effort_hours=20,
                    implementation_steps=[
                        "Analyze failure patterns and root causes",
                        "Implement robust error handling",
                        "Add retry mechanisms and fallbacks",
                        "Improve monitoring and alerting",
                    ],
                    evidence={"failed_workflow_count": len(failed_workflows)},
                    affected_components=["workflow_engine", "error_handler"],
                    created_at=datetime.utcnow(),
                )
            )

        return recommendations

    async def _generate_cost_recommendations(
        self, analysis: SystemAnalysis
    ) -> List[OptimizationRecommendation]:
        """Generate cost optimization recommendations"""
        recommendations = []

        # Idle resource costs
        idle_resources = [
            r
            for r in analysis.underutilized_resources
            if r.get("utilization_percentage", 100) < 20
        ]

        if idle_resources:
            total_idle_cost = len(idle_resources) * 100  # Simplified cost calculation
            recommendations.append(
                OptimizationRecommendation(
                    id="cost_idle_resources",
                    title="Reduce Idle Resource Costs",
                    description=f"Estimated ${total_idle_cost}/month in idle resource costs detected.",
                    category=OptimizationCategory.COST_OPTIMIZATION,
                    priority=OptimizationPriority.MEDIUM,
                    expected_improvement=f"Save ${total_idle_cost * 0.7:.0f}/month",
                    estimated_impact_percentage=15.0,
                    confidence_score=0.70,
                    implementation_complexity="low",
                    estimated_effort_hours=6,
                    implementation_steps=[
                        "Audit idle resources",
                        "Implement auto-scaling policies",
                        "Schedule resource hibernation",
                        "Monitor cost savings",
                    ],
                    evidence={
                        "idle_resource_count": len(idle_resources),
                        "estimated_monthly_cost": total_idle_cost,
                    },
                    affected_components=["resource_manager", "auto_scaler"],
                    created_at=datetime.utcnow(),
                )
            )

        # Optimization opportunities
        if analysis.efficiency_score < 80:
            potential_savings = (
                80 - analysis.efficiency_score
            ) * 10  # $10 per efficiency point
            recommendations.append(
                OptimizationRecommendation(
                    id="cost_efficiency_improve",
                    title="Cost Reduction Through Efficiency",
                    description="Improving system efficiency can lead to significant cost savings.",
                    category=OptimizationCategory.COST_OPTIMIZATION,
                    priority=OptimizationPriority.MEDIUM,
                    expected_improvement=f"Save ${potential_savings:.0f}/month through efficiency gains",
                    estimated_impact_percentage=12.0,
                    confidence_score=0.65,
                    implementation_complexity="medium",
                    estimated_effort_hours=16,
                    implementation_steps=[
                        "Implement efficiency monitoring",
                        "Optimize resource allocation algorithms",
                        "Reduce processing overhead",
                        "Track cost impact",
                    ],
                    evidence={
                        "current_efficiency": analysis.efficiency_score,
                        "potential_savings": potential_savings,
                    },
                    affected_components=["efficiency_monitor", "resource_optimizer"],
                    created_at=datetime.utcnow(),
                )
            )

        return recommendations

    async def _generate_reliability_recommendations(
        self, db: AsyncSession, analysis: SystemAnalysis
    ) -> List[OptimizationRecommendation]:
        """Generate reliability improvement recommendations"""
        recommendations = []

        # Analyze system health trends
        if analysis.performance_trends.get("reliability_trend") == "declining":
            recommendations.append(
                OptimizationRecommendation(
                    id="reliability_trend_improve",
                    title="Address Declining Reliability Trend",
                    description="System reliability metrics show declining trend. Proactive measures needed.",
                    category=OptimizationCategory.RELIABILITY,
                    priority=OptimizationPriority.HIGH,
                    expected_improvement="Improve system reliability by 20-30%",
                    estimated_impact_percentage=25.0,
                    confidence_score=0.80,
                    implementation_complexity="medium",
                    estimated_effort_hours=18,
                    implementation_steps=[
                        "Implement comprehensive health checks",
                        "Add redundancy for critical components",
                        "Improve error recovery mechanisms",
                        "Enhance monitoring and alerting",
                    ],
                    evidence=analysis.performance_trends,
                    affected_components=["health_monitor", "error_recovery"],
                    created_at=datetime.utcnow(),
                )
            )

        return recommendations

    def _prioritize_recommendations(
        self, recommendations: List[OptimizationRecommendation]
    ) -> List[OptimizationRecommendation]:
        """
        Prioritize recommendations based on impact, urgency, and implementation complexity
        """

        def priority_score(rec: OptimizationRecommendation) -> float:
            # Priority weight
            priority_weights = {
                OptimizationPriority.CRITICAL: 100,
                OptimizationPriority.HIGH: 80,
                OptimizationPriority.MEDIUM: 60,
                OptimizationPriority.LOW: 40,
            }

            # Complexity penalty
            complexity_penalties = {"low": 0, "medium": -10, "high": -20}

            base_score = priority_weights.get(rec.priority, 40)
            impact_score = rec.estimated_impact_percentage
            confidence_bonus = rec.confidence_score * 20
            complexity_penalty = complexity_penalties.get(
                rec.implementation_complexity, -10
            )

            return base_score + impact_score + confidence_bonus + complexity_penalty

        return sorted(recommendations, key=priority_score, reverse=True)

    def _generate_implementation_roadmap(
        self, recommendations: List[OptimizationRecommendation]
    ) -> Dict[str, Any]:
        """
        Generate implementation roadmap for recommendations
        """
        roadmap = {
            "phases": [],
            "timeline": {},
            "resource_requirements": {},
            "dependencies": [],
        }

        # Group recommendations into phases
        critical_recs = [
            r for r in recommendations if r.priority == OptimizationPriority.CRITICAL
        ]
        high_recs = [
            r for r in recommendations if r.priority == OptimizationPriority.HIGH
        ]
        medium_recs = [
            r for r in recommendations if r.priority == OptimizationPriority.MEDIUM
        ]
        low_recs = [
            r for r in recommendations if r.priority == OptimizationPriority.LOW
        ]

        # Phase 1: Critical (immediate)
        if critical_recs:
            roadmap["phases"].append(
                {
                    "phase": 1,
                    "name": "Critical Fixes",
                    "duration_weeks": 1,
                    "recommendations": [r.id for r in critical_recs],
                    "description": "Address critical system issues immediately",
                }
            )

        # Phase 2: High priority (1-2 weeks)
        if high_recs:
            roadmap["phases"].append(
                {
                    "phase": 2,
                    "name": "High Impact Improvements",
                    "duration_weeks": 3,
                    "recommendations": [r.id for r in high_recs],
                    "description": "Implement high-impact optimizations",
                }
            )

        # Phase 3: Medium priority (3-4 weeks)
        if medium_recs:
            roadmap["phases"].append(
                {
                    "phase": 3,
                    "name": "System Optimization",
                    "duration_weeks": 4,
                    "recommendations": [r.id for r in medium_recs],
                    "description": "Comprehensive system improvements",
                }
            )

        # Phase 4: Low priority (ongoing)
        if low_recs:
            roadmap["phases"].append(
                {
                    "phase": 4,
                    "name": "Continuous Improvement",
                    "duration_weeks": 8,
                    "recommendations": [r.id for r in low_recs],
                    "description": "Long-term optimization initiatives",
                }
            )

        # Calculate resource requirements
        total_effort = sum(r.estimated_effort_hours for r in recommendations)
        roadmap["resource_requirements"] = {
            "total_effort_hours": total_effort,
            "estimated_team_weeks": total_effort / 40,  # Assuming 40 hours per week
            "recommended_team_size": max(
                1, min(4, total_effort // 80)
            ),  # 2 weeks per person max
        }

        return roadmap

    def _generate_summary(
        self,
        analysis: SystemAnalysis,
        recommendations: List[OptimizationRecommendation],
    ) -> Dict[str, Any]:
        """
        Generate executive summary of optimization analysis
        """
        # Calculate potential impact
        total_impact = sum(
            r.estimated_impact_percentage for r in recommendations[:5]
        )  # Top 5
        total_effort = sum(r.estimated_effort_hours for r in recommendations[:5])

        # Categorize recommendations
        by_category = {}
        for rec in recommendations:
            category = rec.category.value
            by_category[category] = by_category.get(category, 0) + 1

        # Priority breakdown
        by_priority = {}
        for rec in recommendations:
            priority = rec.priority.value
            by_priority[priority] = by_priority.get(priority, 0) + 1

        return {
            "system_health": {
                "efficiency_score": analysis.efficiency_score,
                "status": (
                    "good"
                    if analysis.efficiency_score > 80
                    else (
                        "needs_attention"
                        if analysis.efficiency_score > 60
                        else "critical"
                    )
                ),
            },
            "optimization_potential": {
                "total_recommendations": len(recommendations),
                "estimated_impact_percentage": min(total_impact, 100),
                "implementation_effort_hours": total_effort,
                "roi_estimate": f"{total_impact / (total_effort / 40):.1f}% per week",
            },
            "key_areas": {
                "bottlenecks_identified": len(analysis.bottlenecks),
                "underutilized_resources": len(analysis.underutilized_resources),
                "primary_focus_area": (
                    max(by_category.keys(), key=lambda k: by_category[k])
                    if by_category
                    else "none"
                ),
            },
            "recommendations_breakdown": {
                "by_priority": by_priority,
                "by_category": by_category,
            },
            "next_steps": [
                "Review critical recommendations immediately",
                "Plan implementation phases",
                "Allocate resources for optimization work",
                "Monitor progress and measure impact",
            ],
        }

    def _get_bottleneck_resolution_steps(self, bottleneck: Dict[str, Any]) -> List[str]:
        """Get specific resolution steps for a bottleneck type"""
        bottleneck_type = bottleneck.get("type", "unknown")

        resolution_steps = {
            "agent_overload": [
                "Analyze agent workload distribution",
                "Implement load balancing algorithms",
                "Add additional agents if needed",
                "Optimize task scheduling",
            ],
            "task_backlog": [
                "Increase agent capacity",
                "Optimize task prioritization",
                "Implement parallel processing",
                "Review task complexity",
            ],
            "high_failure_rate": [
                "Analyze failure patterns",
                "Improve error handling",
                "Add retry mechanisms",
                "Enhance system monitoring",
            ],
            "resource_contention": [
                "Identify competing processes",
                "Implement resource queuing",
                "Optimize resource allocation",
                "Add resource monitoring",
            ],
        }

        return resolution_steps.get(
            bottleneck_type,
            [
                "Analyze the specific bottleneck",
                "Develop targeted solution",
                "Implement and test fix",
                "Monitor for improvement",
            ],
        )

    # Helper methods for data retrieval
    async def _get_agents_with_metrics(self, db: AsyncSession) -> List[Agent]:
        """Get agents with calculated metrics"""
        result = await db.execute(select(Agent))
        return result.scalars().all()

    async def _get_tasks_with_metrics(self, db: AsyncSession) -> List[Task]:
        """Get tasks with metrics from last 24 hours"""
        start_time = datetime.utcnow() - timedelta(hours=24)
        result = await db.execute(select(Task).where(Task.created_at >= start_time))
        return result.scalars().all()

    async def _get_workflows_with_metrics(self, db: AsyncSession) -> List[Workflow]:
        """Get workflows with metrics"""
        result = await db.execute(select(Workflow))
        return result.scalars().all()

    async def _get_recent_system_metrics(self, db: AsyncSession) -> List[SystemMetrics]:
        """Get recent system metrics"""
        result = await db.execute(
            select(SystemMetrics).order_by(SystemMetrics.recorded_at.desc()).limit(100)
        )
        return result.scalars().all()

    async def _calculate_system_efficiency(
        self, agents: List[Agent], tasks: List[Task], workflows: List[Workflow]
    ) -> float:
        """Calculate overall system efficiency score"""
        if not agents or not tasks:
            return 50.0  # Default neutral score

        # Agent utilization
        active_agents = len([a for a in agents if a.status == "active"])
        agent_utilization = (active_agents / len(agents)) * 100 if agents else 0

        # Task completion rate
        completed_tasks = len([t for t in tasks if t.status == "completed"])
        completion_rate = (completed_tasks / len(tasks)) * 100 if tasks else 0

        # Agent success rates
        success_rates = [a.success_rate for a in agents if a.success_rate > 0]
        avg_success_rate = (
            sum(success_rates) / len(success_rates) if success_rates else 75
        )

        # Weighted efficiency score
        efficiency = (
            agent_utilization * 0.3 + completion_rate * 0.4 + avg_success_rate * 0.3
        )

        return min(efficiency, 100.0)

    async def _identify_system_bottlenecks(
        self,
        db: AsyncSession,
        agents: List[Agent],
        tasks: List[Task],
        workflows: List[Workflow],
    ) -> List[Dict[str, Any]]:
        """Identify system bottlenecks"""
        bottlenecks = []

        # Agent overload
        overloaded_agents = []
        for agent in agents:
            agent_tasks = [t for t in tasks if t.assigned_agent_id == agent.id]
            if len(agent_tasks) > 10:  # More than 10 tasks per agent
                overloaded_agents.append(agent)

        if overloaded_agents:
            bottlenecks.append(
                {
                    "type": "agent_overload",
                    "severity": "high" if len(overloaded_agents) > 3 else "medium",
                    "description": f"{len(overloaded_agents)} agents are overloaded",
                    "affected_components": [str(a.id) for a in overloaded_agents],
                    "impact": "Reduced performance and increased failure risk",
                }
            )

        # Task backlog
        pending_tasks = [t for t in tasks if t.status == "pending"]
        if len(pending_tasks) > 50:
            bottlenecks.append(
                {
                    "type": "task_backlog",
                    "severity": "high" if len(pending_tasks) > 100 else "medium",
                    "description": f"{len(pending_tasks)} tasks in backlog",
                    "affected_components": ["task_scheduler"],
                    "impact": "Delayed task completion and SLA violations",
                }
            )

        return bottlenecks

    async def _identify_underutilized_resources(
        self, agents: List[Agent], tasks: List[Task]
    ) -> List[Dict[str, Any]]:
        """Identify underutilized resources"""
        underutilized = []

        for agent in agents:
            agent_tasks = [t for t in tasks if t.assigned_agent_id == agent.id]
            utilization = min(len(agent_tasks) * 10, 100)  # Simple utilization calc

            if utilization < 30:  # Less than 30% utilized
                underutilized.append(
                    {
                        "type": "agent",
                        "name": agent.name,
                        "id": str(agent.id),
                        "utilization_percentage": utilization,
                        "recommendation": "Consider reassigning tasks or scaling down",
                    }
                )

        return underutilized

    async def _analyze_performance_trends(
        self, db: AsyncSession, metrics: List[SystemMetrics]
    ) -> Dict[str, Any]:
        """Analyze performance trends from historical data"""
        if len(metrics) < 5:
            return {"trend": "insufficient_data"}

        # Sort by timestamp
        sorted_metrics = sorted(metrics, key=lambda m: m.recorded_at)

        # Analyze efficiency trend
        efficiency_values = [
            m.overall_success_rate for m in sorted_metrics[-10:]
        ]  # Last 10 points

        if len(efficiency_values) >= 3:
            # Simple trend analysis
            recent_avg = sum(efficiency_values[-3:]) / 3
            earlier_avg = sum(efficiency_values[:3]) / 3

            if recent_avg > earlier_avg + 5:
                trend = "improving"
            elif recent_avg < earlier_avg - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "efficiency_trend": trend,
            "reliability_trend": trend,  # Simplified - same as efficiency
            "recent_average": recent_avg if "recent_avg" in locals() else 0,
            "data_points": len(efficiency_values),
        }

    def _analyze_resource_allocation(
        self, agents: List[Agent], tasks: List[Task]
    ) -> Dict[str, Any]:
        """Analyze current resource allocation patterns"""

        # Calculate task distribution
        agent_task_counts = {}
        for task in tasks:
            agent_id = (
                str(task.assigned_agent_id) if task.assigned_agent_id else "unassigned"
            )
            agent_task_counts[agent_id] = agent_task_counts.get(agent_id, 0) + 1

        # Calculate imbalance
        if agent_task_counts:
            task_counts = list(agent_task_counts.values())
            avg_tasks = sum(task_counts) / len(task_counts)
            variance = sum((count - avg_tasks) ** 2 for count in task_counts) / len(
                task_counts
            )
            imbalance_score = min(
                variance / (avg_tasks + 1), 1.0
            )  # Normalized imbalance
        else:
            imbalance_score = 0

        return {
            "total_agents": len(agents),
            "total_tasks": len(tasks),
            "average_tasks_per_agent": len(tasks) / len(agents) if agents else 0,
            "imbalance_score": imbalance_score,
            "distribution": agent_task_counts,
        }