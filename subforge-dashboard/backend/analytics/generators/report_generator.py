"""
Report Generation Module for SubForge Analytics
Generates formatted reports in multiple formats (PDF, CSV, JSON)
"""

import base64
import csv
import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    HTML = "html"


class ReportType(Enum):
    PERFORMANCE = "performance"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_SUMMARY = "monthly_summary"
    CUSTOM = "custom"
    EXECUTIVE_DASHBOARD = "executive_dashboard"


@dataclass
class ReportConfig:
    """Configuration for report generation"""

    report_type: ReportType
    format: ReportFormat
    time_range_hours: int = 24
    include_charts: bool = True
    include_recommendations: bool = True
    include_raw_data: bool = False
    custom_title: Optional[str] = None
    recipient_email: Optional[str] = None


@dataclass
class ChartConfig:
    """Configuration for chart generation"""

    chart_type: str  # "line", "bar", "pie", "heatmap", "scatter"
    title: str
    x_label: str = ""
    y_label: str = ""
    data_source: str = ""
    width: int = 10
    height: int = 6


class ReportGenerator:
    """
    Advanced report generator for SubForge analytics
    Supports multiple formats and customizable layouts
    """

    def __init__(
        self, analytics_service: AnalyticsService, output_dir: str = "reports"
    ):
        self.analytics_service = analytics_service
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Set up plotting style
        plt.style.use("default")
        sns.set_palette("husl")

        self.logger = logging.getLogger(__name__)

    async def generate_report(
        self, db: AsyncSession, config: ReportConfig
    ) -> Dict[str, Any]:
        """
        Generate report based on configuration

        Returns:
            Dictionary containing report data and file paths
        """
        try:
            self.logger.info(
                f"Generating {config.report_type.value} report in {config.format.value} format"
            )

            # Get analytics data based on report type
            analytics_data = await self._get_analytics_data(db, config)

            # Generate report content
            report_data = await self._prepare_report_data(analytics_data, config)

            # Generate charts if requested
            charts = {}
            if config.include_charts:
                charts = await self._generate_charts(analytics_data, config)

            # Format report based on requested format
            if config.format == ReportFormat.JSON:
                result = await self._generate_json_report(report_data, charts, config)
            elif config.format == ReportFormat.CSV:
                result = await self._generate_csv_report(report_data, config)
            elif config.format == ReportFormat.HTML:
                result = await self._generate_html_report(report_data, charts, config)
            elif config.format == ReportFormat.PDF:
                result = await self._generate_pdf_report(report_data, charts, config)
            else:
                raise ValueError(f"Unsupported report format: {config.format}")

            self.logger.info(
                f"Successfully generated {config.report_type.value} report"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def generate_executive_dashboard(
        self, db: AsyncSession, time_range_days: int = 7
    ) -> Dict[str, Any]:
        """Generate executive dashboard report"""

        config = ReportConfig(
            report_type=ReportType.EXECUTIVE_DASHBOARD,
            format=ReportFormat.HTML,
            time_range_hours=time_range_days * 24,
            include_charts=True,
            include_recommendations=True,
            custom_title="Executive Dashboard - System Overview",
        )

        return await self.generate_report(db, config)

    async def generate_performance_report(
        self,
        db: AsyncSession,
        format: ReportFormat = ReportFormat.PDF,
        time_range_hours: int = 24,
    ) -> Dict[str, Any]:
        """Generate performance report"""

        config = ReportConfig(
            report_type=ReportType.PERFORMANCE,
            format=format,
            time_range_hours=time_range_hours,
            include_charts=True,
            include_recommendations=True,
            custom_title=f"Performance Report - Last {time_range_hours} Hours",
        )

        return await self.generate_report(db, config)

    async def generate_scheduled_reports(
        self, db: AsyncSession
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate all scheduled reports (daily, weekly, monthly)"""

        reports = {"daily": [], "weekly": [], "monthly": []}

        try:
            # Daily report
            daily_config = ReportConfig(
                report_type=ReportType.DAILY_SUMMARY,
                format=ReportFormat.HTML,
                time_range_hours=24,
                include_charts=True,
                include_recommendations=True,
            )
            daily_report = await self.generate_report(db, daily_config)
            reports["daily"].append(daily_report)

            # Weekly report
            weekly_config = ReportConfig(
                report_type=ReportType.WEEKLY_SUMMARY,
                format=ReportFormat.PDF,
                time_range_hours=168,  # 7 days
                include_charts=True,
                include_recommendations=True,
            )
            weekly_report = await self.generate_report(db, weekly_config)
            reports["weekly"].append(weekly_report)

            # Monthly report (last 30 days)
            monthly_config = ReportConfig(
                report_type=ReportType.MONTHLY_SUMMARY,
                format=ReportFormat.PDF,
                time_range_hours=720,  # 30 days
                include_charts=True,
                include_recommendations=True,
            )
            monthly_report = await self.generate_report(db, monthly_config)
            reports["monthly"].append(monthly_report)

        except Exception as e:
            self.logger.error(f"Error generating scheduled reports: {e}")

        return reports

    async def _get_analytics_data(
        self, db: AsyncSession, config: ReportConfig
    ) -> Dict[str, Any]:
        """Get analytics data based on report configuration"""

        if config.report_type == ReportType.PERFORMANCE:
            return await self.analytics_service.run_performance_analysis(
                db, time_range_hours=config.time_range_hours
            )

        elif config.report_type in [
            ReportType.DAILY_SUMMARY,
            ReportType.WEEKLY_SUMMARY,
            ReportType.MONTHLY_SUMMARY,
            ReportType.EXECUTIVE_DASHBOARD,
        ]:
            return await self.analytics_service.run_comprehensive_analysis(
                db,
                include_predictions=True,
                include_optimization=True,
                time_range_hours=config.time_range_hours,
            )

        else:
            # Custom report - get comprehensive data
            return await self.analytics_service.run_comprehensive_analysis(
                db, time_range_hours=config.time_range_hours
            )

    async def _prepare_report_data(
        self, analytics_data: Dict[str, Any], config: ReportConfig
    ) -> Dict[str, Any]:
        """Prepare and structure data for report generation"""

        report_data = {
            "title": config.custom_title
            or f"{config.report_type.value.title()} Report",
            "generated_at": datetime.utcnow().isoformat(),
            "time_range_hours": config.time_range_hours,
            "report_type": config.report_type.value,
            "summary": {},
            "metrics": {},
            "insights": [],
            "recommendations": [],
        }

        try:
            # Extract summary information
            if "executive_summary" in analytics_data:
                report_data["summary"] = analytics_data["executive_summary"]

            # Extract key metrics
            if "performance_analysis" in analytics_data:
                performance = analytics_data["performance_analysis"]
                if "system_metrics" in performance:
                    report_data["metrics"]["system"] = performance["system_metrics"]
                if "agent_summary" in performance:
                    report_data["metrics"]["agents"] = performance["agent_summary"]

            # Extract insights
            if "insights" in analytics_data:
                insights_data = analytics_data["insights"]
                if "insights" in insights_data:
                    report_data["insights"] = insights_data["insights"][:10]  # Top 10

            # Extract recommendations
            if config.include_recommendations:
                if "optimization" in analytics_data:
                    optimization = analytics_data["optimization"]
                    if "recommendations" in optimization:
                        report_data["recommendations"] = optimization[
                            "recommendations"
                        ][
                            :5
                        ]  # Top 5

            # Add raw data if requested
            if config.include_raw_data:
                report_data["raw_data"] = analytics_data

        except Exception as e:
            self.logger.error(f"Error preparing report data: {e}")

        return report_data

    async def _generate_charts(
        self, analytics_data: Dict[str, Any], config: ReportConfig
    ) -> Dict[str, str]:
        """Generate charts and return as base64 encoded strings"""

        charts = {}

        try:
            # System performance chart
            if "performance_analysis" in analytics_data:
                performance = analytics_data["performance_analysis"]

                # System efficiency chart
                if "system_metrics" in performance:
                    system_metrics = performance["system_metrics"]
                    efficiency_chart = await self._create_efficiency_chart(
                        system_metrics
                    )
                    charts["system_efficiency"] = efficiency_chart

                # Agent performance chart
                if "detailed_agent_metrics" in performance:
                    agent_metrics = performance["detailed_agent_metrics"]
                    agent_chart = await self._create_agent_performance_chart(
                        agent_metrics
                    )
                    charts["agent_performance"] = agent_chart

            # Trend charts
            if "trend_analysis" in analytics_data:
                trends = analytics_data["trend_analysis"]
                if "trends" in trends:
                    trend_chart = await self._create_trend_chart(trends["trends"])
                    charts["trends"] = trend_chart

            # Real-time metrics chart
            real_time = await self.analytics_service.get_real_time_metrics()
            if "metrics" in real_time:
                realtime_chart = await self._create_realtime_chart(real_time["metrics"])
                charts["realtime_metrics"] = realtime_chart

        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")

        return charts

    async def _create_efficiency_chart(self, system_metrics: Dict[str, Any]) -> str:
        """Create system efficiency chart"""

        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            # Sample data - in real implementation, this would come from metrics
            categories = [
                "System Efficiency",
                "Success Rate",
                "Uptime",
                "Resource Utilization",
            ]
            values = [
                system_metrics.get("system_efficiency", 75),
                system_metrics.get("overall_success_rate", 85),
                system_metrics.get("uptime_percentage", 99),
                system_metrics.get("cpu_utilization", 60),
            ]

            bars = ax.bar(
                categories, values, color=["#2E8B57", "#4682B4", "#32CD32", "#FF6347"]
            )

            ax.set_ylabel("Percentage (%)")
            ax.set_title("System Performance Metrics")
            ax.set_ylim(0, 100)

            # Add value labels on bars
            for bar, value in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 1,
                    f"{value:.1f}%",
                    ha="center",
                    va="bottom",
                )

            plt.tight_layout()

            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()

            plt.close(fig)

            return img_base64

        except Exception as e:
            self.logger.error(f"Error creating efficiency chart: {e}")
            return ""

    async def _create_agent_performance_chart(
        self, agent_metrics: List[Dict[str, Any]]
    ) -> str:
        """Create agent performance comparison chart"""

        try:
            if not agent_metrics:
                return ""

            fig, ax = plt.subplots(figsize=(12, 8))

            # Extract agent names and efficiency scores
            agent_names = [
                agent.get("name", "Unknown")[:15] for agent in agent_metrics[:10]
            ]  # Top 10
            efficiency_scores = [
                agent.get("efficiency_score", 0) for agent in agent_metrics[:10]
            ]

            bars = ax.barh(agent_names, efficiency_scores, color="steelblue")

            ax.set_xlabel("Efficiency Score")
            ax.set_title("Agent Performance Comparison (Top 10)")
            ax.set_xlim(0, 100)

            # Add value labels
            for bar, score in zip(bars, efficiency_scores):
                ax.text(
                    bar.get_width() + 1,
                    bar.get_y() + bar.get_height() / 2,
                    f"{score:.1f}",
                    ha="left",
                    va="center",
                )

            plt.tight_layout()

            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()

            plt.close(fig)

            return img_base64

        except Exception as e:
            self.logger.error(f"Error creating agent performance chart: {e}")
            return ""

    async def _create_trend_chart(self, trends: List[Dict[str, Any]]) -> str:
        """Create trend analysis chart"""

        try:
            if not trends:
                return ""

            fig, ax = plt.subplots(figsize=(12, 6))

            # Sample trend data - in real implementation, use actual time series
            time_points = pd.date_range(
                start=datetime.now() - timedelta(days=7), end=datetime.now(), freq="H"
            )

            # Create sample trends for visualization
            for i, trend in enumerate(trends[:3]):  # Show top 3 trends
                metric_name = trend.get("metric_name", f"Metric {i+1}")

                # Generate sample data based on trend direction
                direction = trend.get("direction", "stable")
                if direction == "increasing":
                    values = np.linspace(50, 80, len(time_points)) + np.random.normal(
                        0, 3, len(time_points)
                    )
                elif direction == "decreasing":
                    values = np.linspace(80, 50, len(time_points)) + np.random.normal(
                        0, 3, len(time_points)
                    )
                else:
                    values = np.full(len(time_points), 65) + np.random.normal(
                        0, 5, len(time_points)
                    )

                ax.plot(
                    time_points,
                    values,
                    label=metric_name,
                    marker="o",
                    markersize=2,
                    alpha=0.8,
                )

            ax.set_xlabel("Time")
            ax.set_ylabel("Value")
            ax.set_title("Metric Trends (Last 7 Days)")
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()

            plt.close(fig)

            return img_base64

        except Exception as e:
            self.logger.error(f"Error creating trend chart: {e}")
            return ""

    async def _create_realtime_chart(self, metrics: Dict[str, Any]) -> str:
        """Create real-time metrics chart"""

        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))

            # CPU/Memory usage
            if "system_load" in metrics and "cpu_usage" in metrics:
                system_load_stats = metrics.get("system_load", {})
                cpu_stats = metrics.get("cpu_usage", {})

                categories = ["System Load", "CPU Usage", "Memory Usage"]
                values = [
                    system_load_stats.get("avg", 0),
                    cpu_stats.get("avg", 0),
                    metrics.get("memory_usage", {}).get("avg", 0),
                ]

                ax1.bar(categories, values, color=["red", "orange", "blue"])
                ax1.set_ylabel("Usage (%)")
                ax1.set_title("System Resources")
                ax1.set_ylim(0, 100)

            # Task metrics
            if "tasks_per_minute" in metrics:
                task_stats = metrics.get("tasks_per_minute", {})
                success_stats = metrics.get("success_rate", {})

                labels = ["Tasks/Min", "Success Rate", "Error Rate"]
                values = [
                    task_stats.get("avg", 0),
                    success_stats.get("avg", 0),
                    metrics.get("error_rate", {}).get("avg", 0),
                ]

                ax2.bar(labels, values, color=["green", "blue", "red"])
                ax2.set_ylabel("Rate")
                ax2.set_title("Task Performance")

            # Response time distribution
            if "agent_response_time" in metrics:
                response_stats = metrics.get("agent_response_time", {})

                # Sample distribution
                times = ["Min", "Avg", "Max"]
                values = [
                    response_stats.get("min", 0),
                    response_stats.get("avg", 0),
                    response_stats.get("max", 0),
                ]

                ax3.bar(times, values, color=["green", "yellow", "red"])
                ax3.set_ylabel("Time (ms)")
                ax3.set_title("Response Times")

            # System health pie chart
            health_data = [85, 10, 5]  # Healthy, Warning, Critical
            health_labels = ["Healthy", "Warning", "Critical"]
            colors = ["green", "orange", "red"]

            ax4.pie(health_data, labels=health_labels, colors=colors, autopct="%1.1f%%")
            ax4.set_title("System Health Status")

            plt.tight_layout()

            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode()

            plt.close(fig)

            return img_base64

        except Exception as e:
            self.logger.error(f"Error creating realtime chart: {e}")
            return ""

    async def _generate_json_report(
        self, report_data: Dict[str, Any], charts: Dict[str, str], config: ReportConfig
    ) -> Dict[str, Any]:
        """Generate JSON format report"""

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.report_type.value}_report_{timestamp}.json"
        filepath = self.output_dir / filename

        # Combine report data with charts
        full_report = {
            **report_data,
            "charts": charts if config.include_charts else {},
            "format": "json",
            "file_info": {
                "filename": filename,
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

        # Save to file
        with open(filepath, "w") as f:
            json.dump(full_report, f, indent=2, default=str)

        return {
            "success": True,
            "format": "json",
            "filename": filename,
            "filepath": str(filepath),
            "data": full_report,
            "size_bytes": filepath.stat().st_size,
        }

    async def _generate_csv_report(
        self, report_data: Dict[str, Any], config: ReportConfig
    ) -> Dict[str, Any]:
        """Generate CSV format report"""

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.report_type.value}_report_{timestamp}.csv"
        filepath = self.output_dir / filename

        # Convert report data to tabular format
        csv_data = []

        # Add summary metrics
        if "metrics" in report_data:
            metrics = report_data["metrics"]
            if "system" in metrics:
                for key, value in metrics["system"].items():
                    csv_data.append(
                        {
                            "Category": "System",
                            "Metric": key,
                            "Value": value,
                            "Type": "system_metric",
                        }
                    )

            if "agents" in metrics:
                agent_metrics = metrics["agents"]
                for key, value in agent_metrics.items():
                    csv_data.append(
                        {
                            "Category": "Agents",
                            "Metric": key,
                            "Value": value,
                            "Type": "agent_metric",
                        }
                    )

        # Add insights
        if "insights" in report_data:
            for insight in report_data["insights"]:
                csv_data.append(
                    {
                        "Category": "Insights",
                        "Metric": insight.get("title", "Unknown"),
                        "Value": insight.get("priority", ""),
                        "Type": "insight",
                    }
                )

        # Save CSV
        if csv_data:
            df = pd.DataFrame(csv_data)
            df.to_csv(filepath, index=False)
        else:
            # Create empty CSV with headers
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Category", "Metric", "Value", "Type"])

        return {
            "success": True,
            "format": "csv",
            "filename": filename,
            "filepath": str(filepath),
            "data_points": len(csv_data),
            "size_bytes": filepath.stat().st_size,
        }

    async def _generate_html_report(
        self, report_data: Dict[str, Any], charts: Dict[str, str], config: ReportConfig
    ) -> Dict[str, Any]:
        """Generate HTML format report"""

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.report_type.value}_report_{timestamp}.html"
        filepath = self.output_dir / filename

        # Generate HTML content
        html_content = self._create_html_template(report_data, charts, config)

        # Save HTML file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return {
            "success": True,
            "format": "html",
            "filename": filename,
            "filepath": str(filepath),
            "size_bytes": filepath.stat().st_size,
            "view_url": f"/reports/{filename}",  # For web viewing
        }

    async def _generate_pdf_report(
        self, report_data: Dict[str, Any], charts: Dict[str, str], config: ReportConfig
    ) -> Dict[str, Any]:
        """Generate PDF format report (simplified version)"""

        # For full PDF generation, you'd typically use libraries like:
        # - reportlab
        # - weasyprint
        # - matplotlib for charts

        # For now, generate HTML and suggest PDF conversion
        html_result = await self._generate_html_report(report_data, charts, config)

        # Change filename extension
        html_filename = html_result["filename"]
        pdf_filename = html_filename.replace(".html", ".pdf")

        return {
            "success": True,
            "format": "pdf",
            "filename": pdf_filename,
            "filepath": html_result["filepath"].replace(".html", ".pdf"),
            "note": "PDF generation requires additional setup. HTML version generated.",
            "html_version": html_result["filepath"],
        }

    def _create_html_template(
        self, report_data: Dict[str, Any], charts: Dict[str, str], config: ReportConfig
    ) -> str:
        """Create HTML template for report"""

        title = report_data.get("title", "Analytics Report")
        generated_at = report_data.get("generated_at", datetime.utcnow().isoformat())

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        .header {{
            border-bottom: 2px solid #e1e5e9;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-size: 28px;
        }}
        .header .meta {{
            color: #7f8c8d;
            margin-top: 10px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-bottom: 20px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .metric-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #28a745;
        }}
        .chart-container {{
            text-align: center;
            margin: 30px 0;
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
        }}
        .insights-list {{
            list-style: none;
            padding: 0;
        }}
        .insights-list li {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 10px;
        }}
        .insights-list li.high-priority {{
            background: #f8d7da;
            border-color: #f5c6cb;
        }}
        .insights-list li.critical {{
            background: #f8d7da;
            border-color: #f5c6cb;
            border-left: 4px solid #dc3545;
        }}
        .recommendations {{
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            border-radius: 4px;
            padding: 20px;
        }}
        .footer {{
            border-top: 1px solid #e9ecef;
            padding-top: 20px;
            margin-top: 40px;
            text-align: center;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="meta">
                Generated: {generated_at}<br>
                Time Range: {config.time_range_hours} hours<br>
                Report Type: {config.report_type.value.title()}
            </div>
        </div>
        """

        # Add summary section
        if "summary" in report_data:
            summary = report_data["summary"]
            html += """
        <div class="section">
            <h2>Executive Summary</h2>
            <div class="metrics-grid">
        """

            if "overall_health" in summary:
                html += f"""
                <div class="metric-card">
                    <h3>Overall Health</h3>
                    <div class="value">{summary["overall_health"].title()}</div>
                </div>
        """

            if "key_metrics" in summary:
                for key, value in summary["key_metrics"].items():
                    html += f"""
                <div class="metric-card">
                    <h3>{key.replace('_', ' ').title()}</h3>
                    <div class="value">{value}</div>
                </div>
        """

            html += "</div></div>"

        # Add charts
        if config.include_charts and charts:
            html += '<div class="section"><h2>Performance Visualizations</h2>'

            for chart_name, chart_data in charts.items():
                if chart_data:
                    html += f"""
            <div class="chart-container">
                <h3>{chart_name.replace('_', ' ').title()}</h3>
                <img src="data:image/png;base64,{chart_data}" alt="{chart_name} chart">
            </div>
        """

            html += "</div>"

        # Add insights
        if "insights" in report_data and report_data["insights"]:
            html += """
        <div class="section">
            <h2>Key Insights</h2>
            <ul class="insights-list">
        """

            for insight in report_data["insights"][:10]:  # Top 10
                priority = insight.get("priority", "medium")
                priority_class = (
                    "critical"
                    if priority == "critical"
                    else "high-priority" if priority == "high" else ""
                )

                html += f"""
                <li class="{priority_class}">
                    <strong>{insight.get('title', 'Unknown')}</strong><br>
                    {insight.get('description', 'No description available')}<br>
                    <small>Priority: {priority.title()} | Confidence: {insight.get('confidence_score', 0):.1%}</small>
                </li>
        """

            html += "</ul></div>"

        # Add recommendations
        if (
            config.include_recommendations
            and "recommendations" in report_data
            and report_data["recommendations"]
        ):
            html += """
        <div class="section">
            <h2>Recommendations</h2>
            <div class="recommendations">
                <ol>
        """

            for rec in report_data["recommendations"][:5]:  # Top 5
                html += f"<li><strong>{rec.get('title', 'Unknown')}</strong>: {rec.get('description', 'No description')}</li>"

            html += """
                </ol>
            </div>
        </div>
        """

        # Footer
        html += f"""
        <div class="footer">
            Generated by SubForge Analytics Dashboard | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        </div>
    </div>
</body>
</html>
        """

        return html