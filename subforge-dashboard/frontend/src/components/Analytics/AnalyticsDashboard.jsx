/**
 * Analytics Dashboard Component
 * Main dashboard for displaying SubForge analytics and insights
 */

import React, { useState, useEffect, useCallback } from 'react';
import analyticsService from '../../services/analyticsService';

const AnalyticsDashboard = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [realTimeMetrics, setRealTimeMetrics] = useState({});
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState(24);

  // Load initial analytics data
  const loadAnalyticsData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [comprehensiveData, realTimeData] = await Promise.all([
        analyticsService.runComprehensiveAnalysis({
          timeRangeHours: selectedTimeRange,
          includePredictions: true,
          includeOptimization: true
        }),
        analyticsService.getRealTimeMetrics()
      ]);

      setAnalyticsData(comprehensiveData.data);
      setRealTimeMetrics(realTimeData.data);

      // Extract insights
      if (comprehensiveData.data?.insights?.insights) {
        setInsights(comprehensiveData.data.insights.insights);
      }

    } catch (err) {
      setError(err.message);
      console.error('Error loading analytics data:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedTimeRange]);

  // Handle real-time updates from WebSocket
  useEffect(() => {
    const handleAnalyticsUpdate = (data) => {
      if (data.type === 'realtime_metrics') {
        setRealTimeMetrics(data.metrics || {});
      }
    };

    const handleAnalyticsAlert = (data) => {
      if (data.type === 'critical_insights') {
        setInsights(prevInsights => [...data.insights, ...prevInsights.slice(0, 10)]);
      }
    };

    // Connect to WebSocket and set up event listeners
    analyticsService.connectWebSocket();
    analyticsService.on('analyticsUpdate', handleAnalyticsUpdate);
    analyticsService.on('analyticsAlert', handleAnalyticsAlert);

    return () => {
      analyticsService.off('analyticsUpdate', handleAnalyticsUpdate);
      analyticsService.off('analyticsAlert', handleAnalyticsAlert);
      analyticsService.disconnectWebSocket();
    };
  }, []);

  // Load data on component mount and time range change
  useEffect(() => {
    loadAnalyticsData();
  }, [loadAnalyticsData]);

  // Render loading state
  if (loading && !analyticsData) {
    return (
      <div className="analytics-dashboard">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading analytics data...</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="analytics-dashboard">
        <div className="error-container">
          <h3>Error Loading Analytics</h3>
          <p>{error}</p>
          <button onClick={loadAnalyticsData} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <h1>SubForge Analytics Dashboard</h1>
        <div className="controls">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(Number(e.target.value))}
            className="time-range-select"
          >
            <option value={1}>Last 1 Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={168}>Last Week</option>
            <option value={720}>Last Month</option>
          </select>
          <button onClick={loadAnalyticsData} className="refresh-button">
            Refresh
          </button>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="executive-summary">
        <h2>Executive Summary</h2>
        <div className="summary-cards">
          <SummaryCard
            title="System Health"
            value={analyticsData?.executive_summary?.overall_health || 'Unknown'}
            type="status"
          />
          <SummaryCard
            title="System Efficiency"
            value={analyticsData?.executive_summary?.key_metrics?.system_efficiency || 0}
            type="percentage"
          />
          <SummaryCard
            title="Active Agents"
            value={analyticsData?.executive_summary?.key_metrics?.active_agents || 0}
            type="number"
          />
          <SummaryCard
            title="Success Rate"
            value={analyticsData?.executive_summary?.key_metrics?.success_rate || 0}
            type="percentage"
          />
        </div>
      </div>

      {/* Real-Time Metrics */}
      <div className="realtime-metrics">
        <h2>Real-Time Metrics</h2>
        <div className="metrics-grid">
          {Object.entries(realTimeMetrics.metrics || {}).map(([key, stats]) => (
            <MetricCard
              key={key}
              title={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              value={stats.avg}
              min={stats.min}
              max={stats.max}
              trend={analyticsService.calculateTrend(stats.history)}
            />
          ))}
        </div>
      </div>

      {/* Critical Insights */}
      <div className="insights-section">
        <h2>Key Insights & Alerts</h2>
        <div className="insights-list">
          {insights.slice(0, 10).map((insight, index) => (
            <InsightCard key={index} insight={insight} />
          ))}
        </div>
      </div>

      {/* Performance Analysis */}
      {analyticsData?.performance_analysis && (
        <div className="performance-section">
          <h2>Performance Analysis</h2>
          <div className="performance-grid">
            <div className="system-metrics">
              <h3>System Metrics</h3>
              <SystemMetricsChart data={analyticsData.performance_analysis.system_metrics} />
            </div>
            <div className="agent-performance">
              <h3>Agent Performance</h3>
              <AgentPerformanceChart data={analyticsData.performance_analysis.detailed_agent_metrics} />
            </div>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {analyticsData?.optimization?.recommendations && (
        <div className="recommendations-section">
          <h2>Optimization Recommendations</h2>
          <div className="recommendations-list">
            {analyticsData.optimization.recommendations.slice(0, 5).map((rec, index) => (
              <RecommendationCard key={index} recommendation={rec} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Summary Card Component
const SummaryCard = ({ title, value, type }) => {
  const formatValue = (val, type) => {
    switch (type) {
      case 'percentage':
        return analyticsService.formatMetricValue(val, 'percentage');
      case 'status':
        return val.charAt(0).toUpperCase() + val.slice(1);
      default:
        return analyticsService.formatMetricValue(val);
    }
  };

  const getStatusClass = (val, type) => {
    if (type === 'status') {
      return val === 'excellent' ? 'status-excellent' :
             val === 'good' ? 'status-good' :
             val === 'fair' ? 'status-warning' : 'status-critical';
    }
    if (type === 'percentage') {
      return val >= 80 ? 'status-excellent' :
             val >= 60 ? 'status-good' :
             val >= 40 ? 'status-warning' : 'status-critical';
    }
    return '';
  };

  return (
    <div className={`summary-card ${getStatusClass(value, type)}`}>
      <h3>{title}</h3>
      <div className="value">{formatValue(value, type)}</div>
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ title, value, min, max, trend }) => {
  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'increasing': return '↗️';
      case 'decreasing': return '↘️';
      default: return '→';
    }
  };

  const getTrendClass = (trend) => {
    switch (trend) {
      case 'increasing': return 'trend-up';
      case 'decreasing': return 'trend-down';
      default: return 'trend-stable';
    }
  };

  return (
    <div className="metric-card">
      <h4>{title}</h4>
      <div className="metric-value">
        {analyticsService.formatMetricValue(value)}
        <span className={`trend ${getTrendClass(trend)}`}>
          {getTrendIcon(trend)}
        </span>
      </div>
      <div className="metric-range">
        Range: {analyticsService.formatMetricValue(min)} - {analyticsService.formatMetricValue(max)}
      </div>
    </div>
  );
};

// Insight Card Component
const InsightCard = ({ insight }) => {
  const getPriorityClass = (priority) => {
    switch (priority) {
      case 'critical': return 'priority-critical';
      case 'high': return 'priority-high';
      case 'medium': return 'priority-medium';
      default: return 'priority-low';
    }
  };

  return (
    <div className={`insight-card ${getPriorityClass(insight.priority)}`}>
      <div className="insight-header">
        <h4>{insight.title}</h4>
        <span className="priority-badge">{insight.priority}</span>
      </div>
      <p>{insight.description}</p>
      <div className="insight-meta">
        <span>Confidence: {(insight.confidence_score * 100).toFixed(1)}%</span>
        <span>Impact: {insight.estimated_impact_percentage}%</span>
      </div>
    </div>
  );
};

// Recommendation Card Component
const RecommendationCard = ({ recommendation }) => {
  return (
    <div className="recommendation-card">
      <h4>{recommendation.title}</h4>
      <p>{recommendation.description}</p>
      <div className="recommendation-details">
        <span>Priority: {recommendation.priority}</span>
        <span>Effort: {recommendation.estimated_effort_hours}h</span>
        <span>Impact: {recommendation.estimated_impact_percentage}%</span>
      </div>
    </div>
  );
};

// Placeholder components for charts (would use actual charting library)
const SystemMetricsChart = ({ data }) => (
  <div className="chart-placeholder">
    <p>System Metrics Chart</p>
    <pre>{JSON.stringify(data, null, 2)}</pre>
  </div>
);

const AgentPerformanceChart = ({ data }) => (
  <div className="chart-placeholder">
    <p>Agent Performance Chart</p>
    <pre>{JSON.stringify(data?.slice(0, 3), null, 2)}</pre>
  </div>
);

export default AnalyticsDashboard;