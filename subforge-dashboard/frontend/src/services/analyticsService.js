/**
 * Analytics Service for SubForge Dashboard Frontend
 * Provides client-side interface for analytics data and real-time updates
 */

import { API_BASE_URL } from '../config/constants';

class AnalyticsService {
  constructor() {
    this.baseURL = `${API_BASE_URL}/api/v2/analytics`;
    this.wsConnection = null;
    this.eventListeners = new Map();
  }

  // API Methods

  /**
   * Get analytics service status
   */
  async getStatus() {
    try {
      const response = await fetch(`${this.baseURL}/status`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting analytics status:', error);
      throw error;
    }
  }

  /**
   * Run comprehensive analytics analysis
   */
  async runComprehensiveAnalysis(options = {}) {
    try {
      const {
        timeRangeHours = 24,
        includePredictions = true,
        includeOptimization = true,
        agentId = null
      } = options;

      const response = await fetch(`${this.baseURL}/analyze/comprehensive`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          time_range_hours: timeRangeHours,
          include_predictions: includePredictions,
          include_optimization: includeOptimization,
          agent_id: agentId
        }),
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error running comprehensive analysis:', error);
      throw error;
    }
  }

  /**
   * Run performance analysis
   */
  async runPerformanceAnalysis(options = {}) {
    try {
      const {
        timeRangeHours = 24,
        agentId = null
      } = options;

      const response = await fetch(`${this.baseURL}/analyze/performance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          time_range_hours: timeRangeHours,
          agent_id: agentId
        }),
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error running performance analysis:', error);
      throw error;
    }
  }

  /**
   * Get real-time metrics
   */
  async getRealTimeMetrics() {
    try {
      const response = await fetch(`${this.baseURL}/metrics/realtime`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting real-time metrics:', error);
      throw error;
    }
  }

  /**
   * Get metric history
   */
  async getMetricHistory(metricName, minutes = 60) {
    try {
      const response = await fetch(`${this.baseURL}/metrics/history/${metricName}?minutes=${minutes}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting metric history:', error);
      throw error;
    }
  }

  /**
   * Generate report
   */
  async generateReport(options = {}) {
    try {
      const {
        reportType = 'performance',
        format = 'json',
        timeRangeHours = 24,
        includeCharts = true,
        includeRecommendations = true,
        customTitle = null
      } = options;

      const response = await fetch(`${this.baseURL}/reports/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          report_type: reportType,
          format,
          time_range_hours: timeRangeHours,
          include_charts: includeCharts,
          include_recommendations: includeRecommendations,
          custom_title: customTitle
        }),
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error generating report:', error);
      throw error;
    }
  }

  /**
   * Generate executive dashboard
   */
  async generateExecutiveDashboard(timeRangeDays = 7) {
    try {
      const response = await fetch(`${this.baseURL}/reports/executive-dashboard?time_range_days=${timeRangeDays}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error generating executive dashboard:', error);
      throw error;
    }
  }

  // WebSocket Methods

  /**
   * Connect to analytics WebSocket
   */
  connectWebSocket() {
    try {
      const wsURL = API_BASE_URL.replace('http', 'ws') + '/ws/v2';
      this.wsConnection = new WebSocket(wsURL);

      this.wsConnection.onopen = () => {
        console.log('Analytics WebSocket connected');
        // Join analytics room
        this.sendWebSocketMessage({
          type: 'join_room',
          room: 'analytics'
        });
      };

      this.wsConnection.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleWebSocketMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.wsConnection.onclose = () => {
        console.log('Analytics WebSocket disconnected');
        // Attempt to reconnect after 5 seconds
        setTimeout(() => this.connectWebSocket(), 5000);
      };

      this.wsConnection.onerror = (error) => {
        console.error('Analytics WebSocket error:', error);
      };

    } catch (error) {
      console.error('Error connecting to Analytics WebSocket:', error);
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnectWebSocket() {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }

  /**
   * Send WebSocket message
   */
  sendWebSocketMessage(message) {
    if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
      this.wsConnection.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected');
    }
  }

  /**
   * Handle incoming WebSocket message
   */
  handleWebSocketMessage(message) {
    const { type, data } = message;

    switch (type) {
      case 'analytics_update':
        this.emit('analyticsUpdate', data);
        break;
      case 'analytics_alert':
        this.emit('analyticsAlert', data);
        break;
      case 'analytics_report':
        this.emit('analyticsReport', data);
        break;
      case 'metrics_update':
        this.emit('metricsUpdate', data);
        break;
      default:
        console.log('Unknown analytics message type:', type);
    }
  }

  // Event Management

  /**
   * Add event listener
   */
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  /**
   * Remove event listener
   */
  off(event, callback) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  /**
   * Emit event to listeners
   */
  emit(event, data) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in event listener:', error);
        }
      });
    }
  }

  // Utility Methods

  /**
   * Format metric value for display
   */
  formatMetricValue(value, type = 'number') {
    if (typeof value !== 'number') return value;

    switch (type) {
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'duration':
        if (value < 60) return `${value.toFixed(1)}s`;
        if (value < 3600) return `${(value / 60).toFixed(1)}m`;
        return `${(value / 3600).toFixed(1)}h`;
      case 'bytes':
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = value;
        let unitIndex = 0;
        while (size >= 1024 && unitIndex < units.length - 1) {
          size /= 1024;
          unitIndex++;
        }
        return `${size.toFixed(1)} ${units[unitIndex]}`;
      default:
        return value.toLocaleString();
    }
  }

  /**
   * Get status color for metric
   */
  getStatusColor(value, thresholds = {}) {
    const { good = 80, warning = 60 } = thresholds;
    
    if (value >= good) return '#28a745'; // Green
    if (value >= warning) return '#ffc107'; // Yellow
    return '#dc3545'; // Red
  }

  /**
   * Calculate trend from data points
   */
  calculateTrend(dataPoints) {
    if (!dataPoints || dataPoints.length < 2) return 'stable';

    const recent = dataPoints.slice(-3);
    const earlier = dataPoints.slice(0, 3);

    if (recent.length < 2 || earlier.length < 2) return 'stable';

    const recentAvg = recent.reduce((sum, point) => sum + point.value, 0) / recent.length;
    const earlierAvg = earlier.reduce((sum, point) => sum + point.value, 0) / earlier.length;

    const changePct = ((recentAvg - earlierAvg) / earlierAvg) * 100;

    if (changePct > 5) return 'increasing';
    if (changePct < -5) return 'decreasing';
    return 'stable';
  }
}

// Create singleton instance
const analyticsService = new AnalyticsService();

export default analyticsService;

// Named exports for convenience
export {
  analyticsService,
  AnalyticsService
};