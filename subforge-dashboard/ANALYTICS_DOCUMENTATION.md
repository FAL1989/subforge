# SubForge Analytics Module Documentation

## Overview

The SubForge Analytics Module provides comprehensive data science and machine learning capabilities for monitoring and analyzing the SubForge agent system. It includes real-time metrics collection, predictive analytics, performance optimization recommendations, and advanced reporting.

## Architecture

The analytics module follows a layered architecture:

```
analytics/
├── models/              # ML models and analyzers
├── processors/          # Data processing components
├── services/           # Service orchestration
├── generators/         # Report generation
└── utils/             # Utility functions
```

## Core Components

### 1. Analytics Models (`analytics/models/`)

#### PerformanceAnalyzer
- **Purpose**: Analyzes agent and system performance metrics
- **Features**:
  - Agent-level performance tracking (success rates, response times, efficiency scores)
  - System-wide performance analysis
  - Bottleneck identification
  - Performance trending

#### TaskDurationPredictor
- **Purpose**: Machine learning model for predicting task completion times
- **Features**:
  - Random Forest and Gradient Boosting ensemble
  - Feature engineering from task and agent characteristics
  - Confidence intervals for predictions
  - Model performance tracking

#### SystemLoadPredictor
- **Purpose**: Predicts future system load and capacity requirements
- **Features**:
  - Time series forecasting
  - Capacity planning recommendations
  - Load spike detection
  - Resource scaling suggestions

#### OptimizationEngine
- **Purpose**: AI-powered optimization recommendations
- **Features**:
  - System bottleneck analysis
  - Resource allocation optimization
  - Workflow efficiency improvements
  - Cost optimization suggestions

### 2. Data Processors (`analytics/processors/`)

#### DataAggregator
- **Purpose**: Real-time metrics aggregation and sliding window analysis
- **Features**:
  - Configurable time windows (1min, 5min, 15min, 1hour, 1day)
  - Statistical summaries (mean, median, std, percentiles)
  - Historical data aggregation
  - Memory-efficient sliding windows

#### TrendAnalyzer
- **Purpose**: Advanced time series analysis and pattern detection
- **Features**:
  - Linear regression trend analysis
  - Seasonality detection (daily, weekly, monthly patterns)
  - Anomaly detection using statistical methods
  - Peak/valley identification
  - Trend change detection

#### InsightGenerator
- **Purpose**: AI-powered insight generation from system data
- **Features**:
  - Pattern-based insight rules
  - Correlation analysis
  - Priority-based insight ranking
  - Actionable recommendations
  - Business impact assessment

### 3. Services (`analytics/services/`)

#### AnalyticsService
- **Purpose**: Central orchestration service for all analytics components
- **Features**:
  - Unified API for analytics operations
  - Background task management
  - Caching and optimization
  - Configuration management
  - Health monitoring

#### AnalyticsIntegrationService
- **Purpose**: Integration with existing SubForge backend services
- **Features**:
  - WebSocket real-time streaming
  - Redis caching integration
  - Background analysis scheduling
  - Event-driven metric collection

### 4. Report Generators (`analytics/generators/`)

#### ReportGenerator
- **Purpose**: Multi-format report generation with visualizations
- **Features**:
  - Multiple output formats (JSON, CSV, HTML, PDF)
  - Interactive charts and visualizations
  - Executive dashboard reports
  - Scheduled report generation
  - Custom report templates

## API Endpoints

### Analytics API (`/api/v2/analytics/`)

#### Core Analysis Endpoints
- `POST /analyze/comprehensive` - Run complete system analysis
- `POST /analyze/performance` - Focused performance analysis
- `POST /analyze/predictive` - Machine learning predictions
- `POST /analyze/trends` - Time series trend analysis

#### Real-Time Metrics
- `GET /metrics/realtime` - Current system metrics
- `POST /metrics/datapoint` - Add metric data point
- `GET /metrics/history/{metric_name}` - Historical metric data

#### Report Generation
- `POST /reports/generate` - Generate custom reports
- `GET /reports/executive-dashboard` - Executive dashboard
- `POST /reports/daily` - Daily analytics report
- `POST /reports/weekly` - Weekly analytics report
- `POST /reports/scheduled` - Generate all scheduled reports

#### Configuration & Management
- `GET /status` - Analytics service status
- `GET /config` - Current configuration
- `PUT /config` - Update configuration
- `POST /cache/clear` - Clear analytics cache

## Data Models

### Agent Performance Metrics
```python
@dataclass
class AgentPerformanceMetrics:
    agent_id: str
    agent_name: str
    agent_type: str
    
    # Task metrics
    tasks_completed: int
    tasks_failed: int
    success_rate: float
    
    # Time metrics
    avg_completion_time: float
    median_completion_time: float
    
    # Efficiency metrics
    productivity_score: float
    reliability_score: float
    efficiency_score: float
    
    # Trend analysis
    performance_trend: str
    trend_confidence: float
```

### Optimization Recommendations
```python
@dataclass
class OptimizationRecommendation:
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
    implementation_complexity: str
    estimated_effort_hours: int
    implementation_steps: List[str]
```

### Insights
```python
@dataclass
class Insight:
    id: str
    title: str
    description: str
    insight_type: InsightType
    priority: InsightPriority
    
    # Evidence and impact
    evidence: Dict[str, Any]
    estimated_impact_percentage: float
    confidence_score: float
    
    # Actionable recommendations
    recommended_actions: List[str]
    action_type: ActionType
    estimated_effort_hours: int
```

## Frontend Integration

### Analytics Service (`analyticsService.js`)
```javascript
// Initialize service
import analyticsService from './services/analyticsService';

// Connect to real-time updates
analyticsService.connectWebSocket();

// Run analysis
const analysisResult = await analyticsService.runComprehensiveAnalysis({
  timeRangeHours: 24,
  includePredictions: true,
  includeOptimization: true
});

// Listen for real-time updates
analyticsService.on('analyticsUpdate', (data) => {
  // Handle real-time metric updates
});

analyticsService.on('analyticsAlert', (data) => {
  // Handle critical insights and alerts
});
```

### React Components
- `AnalyticsDashboard.jsx` - Main dashboard component
- Real-time metric visualization
- Interactive charts and graphs
- Insight cards with priority indicators
- Responsive design for all screen sizes

## Machine Learning Models

### Task Duration Prediction
- **Algorithm**: Ensemble of Random Forest, Gradient Boosting, and Linear Regression
- **Features**: 
  - Agent success rate and response time
  - Task complexity and priority
  - Historical patterns and workload
  - Time-of-day and day-of-week patterns
- **Performance**: R² score tracking, MSE, and confidence intervals

### System Load Prediction
- **Algorithm**: Gradient Boosting Regressor
- **Features**:
  - Current system metrics (CPU, memory, load)
  - Active agent counts and task volumes
  - Time-based patterns and trends
- **Forecast Horizon**: Up to 72 hours ahead with decreasing confidence

### Anomaly Detection
- **Methods**: Z-score analysis, peak detection, trend change identification
- **Applications**: Performance degradation, unusual patterns, system alerts
- **Thresholds**: Configurable sensitivity levels

## Real-Time Features

### WebSocket Streaming
- Real-time metric updates every 30 seconds
- Critical insight alerts
- Analysis completion notifications
- Automatic reconnection handling

### Background Processing
- Continuous metric aggregation
- Scheduled analysis runs (every 5 minutes)
- Report generation (hourly/daily/weekly)
- Cache management and cleanup

## Configuration

### Analytics Service Configuration
```python
config = {
    "cache_ttl_minutes": 30,
    "auto_analysis_interval_minutes": 60,
    "enable_background_analysis": True,
    "enable_predictive_models": True,
    "storage_enabled": True
}
```

### Integration Service Configuration
```python
config = {
    "realtime_update_interval": 30,  # seconds
    "analysis_interval": 300,        # 5 minutes
    "report_interval": 3600,         # 1 hour
    "websocket_room": "analytics",
    "enable_realtime_streaming": True
}
```

## Performance Considerations

### Caching Strategy
- Multi-level caching (memory, Redis)
- Configurable TTL values
- Cache invalidation on data changes
- Background cache warming

### Scalability Features
- Async/await throughout
- Database query optimization
- Efficient data structures
- Memory management for large datasets
- Horizontal scaling support

### Resource Management
- Configurable analysis intervals
- Background task limiting
- Memory cleanup routines
- Database connection pooling

## Installation & Setup

### Required Dependencies
```bash
# Core data science libraries
pip install pandas numpy scikit-learn scipy matplotlib seaborn plotly

# Additional requirements already in requirements.txt
```

### Database Setup
The analytics module uses existing SubForge database models:
- `Agent` - Agent information and performance metrics
- `Task` - Task details and completion data
- `SystemMetrics` - System performance snapshots
- `Workflow` - Workflow execution data

### Service Initialization
Analytics services are automatically initialized with the main FastAPI application:
```python
# In main.py lifespan
await analytics_integration_service.initialize()
```

## Monitoring & Debugging

### Health Checks
- `GET /api/v2/analytics/health` - Service health status
- Component status monitoring
- Cache size and performance metrics
- Background task status

### Logging
- Structured logging throughout
- Error tracking and alerting
- Performance metrics logging
- Debug endpoints for development

## Future Enhancements

### Planned Features
1. **Advanced ML Models**
   - Deep learning models for complex patterns
   - Reinforcement learning for optimization
   - Natural language processing for log analysis

2. **Enhanced Visualizations**
   - Interactive dashboards with drill-down capabilities
   - 3D visualizations for complex data relationships
   - Custom chart builders

3. **Integration Improvements**
   - External data source connectors
   - Third-party analytics platform integration
   - Advanced alerting and notification systems

4. **Performance Optimizations**
   - Distributed computing support
   - GPU acceleration for ML models
   - Advanced caching strategies

## Troubleshooting

### Common Issues
1. **High Memory Usage**: Adjust cache TTL and cleanup intervals
2. **Slow Analysis**: Reduce time range or disable heavy computations
3. **WebSocket Connection Issues**: Check network configuration and reconnection logic
4. **Missing Predictions**: Ensure sufficient historical data for model training

### Debug Commands
```python
# Clear analytics cache
await analytics_service.performance_analyzer.clear_cache()

# Check service status
status = analytics_service.get_service_status()

# Manual analysis run
result = await analytics_service.run_comprehensive_analysis(db)
```

This comprehensive analytics module provides SubForge with enterprise-grade monitoring, machine learning capabilities, and actionable insights to optimize agent performance and system efficiency.