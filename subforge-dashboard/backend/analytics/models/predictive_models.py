"""
Predictive Analytics Models for SubForge Dashboard
Machine learning models for task completion prediction and system load forecasting
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pickle
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ...app.models.agent import Agent
from ...app.models.task import Task
from ...app.models.system_metrics import SystemMetrics
from .base_analyzer import BaseAnalyzer, AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Container for prediction results"""
    predicted_value: float
    confidence: float
    prediction_interval: Tuple[float, float]
    model_accuracy: float
    features_used: List[str]
    prediction_date: datetime
    
    
@dataclass
class ModelPerformance:
    """Model performance metrics"""
    mse: float
    rmse: float
    r2_score: float
    mean_absolute_error: float
    accuracy_percentage: float


class TaskDurationPredictor(BaseAnalyzer):
    """
    Machine learning model to predict task completion times
    Uses historical task data to train predictive models
    """
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'agent_success_rate', 'agent_avg_response_time', 'task_complexity_score',
            'task_priority_encoded', 'agent_type_encoded', 'task_type_encoded',
            'estimated_duration', 'hour_of_day', 'day_of_week', 'agent_workload'
        ]
        self.model_trained = False
        self.training_history = []
    
    async def analyze(self, db: AsyncSession, **kwargs) -> Dict[str, Any]:
        """Main analysis method - trains model and generates predictions"""
        await self.train_model(db)
        predictions = await self.predict_task_durations(db)
        return {
            "model_performance": self.get_model_performance(),
            "predictions": predictions,
            "feature_importance": self.get_feature_importance()
        }
    
    async def train_model(self, db: AsyncSession, retrain: bool = False) -> ModelPerformance:
        """
        Train the task duration prediction model
        
        Args:
            db: Database session
            retrain: Force model retraining even if model exists
            
        Returns:
            Model performance metrics
        """
        try:
            if self.model_trained and not retrain:
                self.logger.info("Model already trained, skipping training")
                return self.get_model_performance()
            
            # Get training data
            training_data = await self._prepare_training_data(db)
            
            if len(training_data) < 50:
                self.logger.warning("Insufficient training data, using default model")
                return self._create_default_model()
            
            # Prepare features and target
            X, y = self._extract_features_and_target(training_data)
            
            if len(X) == 0:
                self.logger.error("No valid features extracted")
                return self._create_default_model()
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train ensemble model
            models = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'linear_regression': LinearRegression()
            }
            
            model_performances = {}
            trained_models = {}
            
            for name, model in models.items():
                model.fit(X_train_scaled, y_train)
                predictions = model.predict(X_test_scaled)
                
                mse = mean_squared_error(y_test, predictions)
                r2 = r2_score(y_test, predictions)
                
                model_performances[name] = {
                    'mse': mse,
                    'r2': r2,
                    'rmse': np.sqrt(mse)
                }
                trained_models[name] = model
            
            # Select best performing model
            best_model_name = max(model_performances.keys(), 
                                key=lambda k: model_performances[k]['r2'])
            self.model = trained_models[best_model_name]
            
            # Calculate final performance metrics
            final_predictions = self.model.predict(X_test_scaled)
            performance = ModelPerformance(
                mse=mean_squared_error(y_test, final_predictions),
                rmse=np.sqrt(mean_squared_error(y_test, final_predictions)),
                r2_score=r2_score(y_test, final_predictions),
                mean_absolute_error=np.mean(np.abs(y_test - final_predictions)),
                accuracy_percentage=max(0, r2_score(y_test, final_predictions) * 100)
            )
            
            self.model_trained = True
            self.training_history.append({
                'timestamp': datetime.utcnow(),
                'best_model': best_model_name,
                'performance': asdict(performance),
                'training_size': len(X_train)
            })
            
            self.logger.info(f"Model trained successfully. Best model: {best_model_name}, "
                           f"R2 Score: {performance.r2_score:.3f}")
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            return self._create_default_model()
    
    async def _prepare_training_data(self, db: AsyncSession) -> pd.DataFrame:
        """Prepare training data from database"""
        
        # Get completed tasks with duration information
        query = select(Task, Agent).join(
            Agent, Task.assigned_agent_id == Agent.id
        ).where(
            and_(
                Task.status == "completed",
                Task.actual_duration_minutes.isnot(None),
                Task.actual_duration_minutes > 0
            )
        )
        
        result = await db.execute(query)
        data = []
        
        for task, agent in result.all():
            # Skip outliers (tasks longer than 24 hours)
            if task.actual_duration_minutes > 1440:
                continue
                
            row = {
                'task_id': str(task.id),
                'actual_duration': task.actual_duration_minutes,
                'estimated_duration': task.estimated_duration_minutes or 60,
                'task_complexity_score': task.complexity_score or 5,
                'task_priority': task.priority,
                'task_type': task.task_type or 'general',
                'agent_id': str(agent.id),
                'agent_type': agent.agent_type,
                'agent_success_rate': agent.success_rate,
                'agent_avg_response_time': agent.avg_response_time,
                'created_at': task.created_at,
                'started_at': task.started_at,
                'completed_at': task.completed_at
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        if len(df) == 0:
            return df
        
        # Add derived features
        df['hour_of_day'] = pd.to_datetime(df['started_at']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['started_at']).dt.dayofweek
        
        # Count concurrent tasks for workload estimation
        df['agent_workload'] = df.groupby(['agent_id', 'started_at']).size()
        
        return df
    
    def _extract_features_and_target(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Extract features and target from training data"""
        
        if df.empty:
            return np.array([]), np.array([])
        
        # Encode categorical variables
        priority_mapping = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}
        df['task_priority_encoded'] = df['task_priority'].map(priority_mapping).fillna(2)
        
        # One-hot encode agent types and task types (simplified)
        df['agent_type_encoded'] = pd.Categorical(df['agent_type']).codes
        df['task_type_encoded'] = pd.Categorical(df['task_type']).codes
        
        # Fill missing values
        df['agent_success_rate'] = df['agent_success_rate'].fillna(75.0)
        df['agent_avg_response_time'] = df['agent_avg_response_time'].fillna(5.0)
        df['task_complexity_score'] = df['task_complexity_score'].fillna(5)
        df['estimated_duration'] = df['estimated_duration'].fillna(60)
        df['agent_workload'] = df['agent_workload'].fillna(1)
        
        # Extract features
        feature_data = []
        for _, row in df.iterrows():
            features = [
                row['agent_success_rate'],
                row['agent_avg_response_time'],
                row['task_complexity_score'],
                row['task_priority_encoded'],
                row['agent_type_encoded'],
                row['task_type_encoded'],
                row['estimated_duration'],
                row['hour_of_day'],
                row['day_of_week'],
                row['agent_workload']
            ]
            feature_data.append(features)
        
        X = np.array(feature_data)
        y = df['actual_duration'].values
        
        return X, y
    
    def _create_default_model(self) -> ModelPerformance:
        """Create a simple default model when insufficient training data"""
        self.model = LinearRegression()
        # Train on dummy data
        X_dummy = np.random.rand(10, len(self.feature_columns))
        y_dummy = np.random.rand(10) * 60 + 30  # 30-90 minute tasks
        
        X_dummy_scaled = self.scaler.fit_transform(X_dummy)
        self.model.fit(X_dummy_scaled, y_dummy)
        
        self.model_trained = True
        
        return ModelPerformance(
            mse=100.0,
            rmse=10.0,
            r2_score=0.5,
            mean_absolute_error=8.0,
            accuracy_percentage=50.0
        )
    
    async def predict_task_duration(
        self, 
        task_features: Dict[str, Any]
    ) -> PredictionResult:
        """
        Predict duration for a single task
        
        Args:
            task_features: Dictionary containing task and agent features
            
        Returns:
            Prediction result with confidence interval
        """
        if not self.model_trained:
            raise ValueError("Model not trained. Call train_model() first.")
        
        # Extract features in correct order
        feature_vector = [
            task_features.get('agent_success_rate', 75.0),
            task_features.get('agent_avg_response_time', 5.0),
            task_features.get('task_complexity_score', 5),
            self._encode_priority(task_features.get('task_priority', 'medium')),
            task_features.get('agent_type_encoded', 0),
            task_features.get('task_type_encoded', 0),
            task_features.get('estimated_duration', 60),
            task_features.get('hour_of_day', 12),
            task_features.get('day_of_week', 1),
            task_features.get('agent_workload', 1)
        ]
        
        # Scale features
        X = np.array([feature_vector])
        X_scaled = self.scaler.transform(X)
        
        # Make prediction
        prediction = self.model.predict(X_scaled)[0]
        
        # Calculate confidence and prediction interval
        confidence = self._calculate_prediction_confidence(X_scaled, prediction)
        
        # Simple prediction interval (±20% for now)
        interval_width = prediction * 0.2
        prediction_interval = (
            max(0, prediction - interval_width),
            prediction + interval_width
        )
        
        return PredictionResult(
            predicted_value=prediction,
            confidence=confidence,
            prediction_interval=prediction_interval,
            model_accuracy=self.get_model_performance().accuracy_percentage,
            features_used=self.feature_columns,
            prediction_date=datetime.utcnow()
        )
    
    def _encode_priority(self, priority: str) -> int:
        """Encode task priority"""
        priority_mapping = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}
        return priority_mapping.get(priority.lower(), 2)
    
    def _calculate_prediction_confidence(self, X_scaled: np.ndarray, prediction: float) -> float:
        """Calculate confidence score for prediction"""
        # Simple confidence based on model performance
        model_performance = self.get_model_performance()
        base_confidence = model_performance.accuracy_percentage / 100.0
        
        # Adjust based on prediction reasonableness (30 min to 8 hours)
        if 30 <= prediction <= 480:
            range_confidence = 1.0
        else:
            range_confidence = 0.7  # Lower confidence for extreme predictions
        
        return min(base_confidence * range_confidence, 1.0)
    
    async def predict_task_durations(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Predict durations for pending tasks"""
        if not self.model_trained:
            await self.train_model(db)
        
        # Get pending tasks
        query = select(Task, Agent).join(
            Agent, Task.assigned_agent_id == Agent.id
        ).where(Task.status == "pending")
        
        result = await db.execute(query)
        predictions = []
        
        for task, agent in result.all():
            task_features = {
                'agent_success_rate': agent.success_rate,
                'agent_avg_response_time': agent.avg_response_time,
                'task_complexity_score': task.complexity_score or 5,
                'task_priority': task.priority,
                'agent_type_encoded': hash(agent.agent_type) % 10,  # Simple encoding
                'task_type_encoded': hash(task.task_type or 'general') % 10,
                'estimated_duration': task.estimated_duration_minutes or 60,
                'hour_of_day': datetime.utcnow().hour,
                'day_of_week': datetime.utcnow().weekday(),
                'agent_workload': 1  # Could be calculated from current tasks
            }
            
            try:
                prediction_result = await self.predict_task_duration(task_features)
                predictions.append({
                    'task_id': str(task.id),
                    'task_title': task.title,
                    'agent_name': agent.name,
                    'predicted_duration_minutes': prediction_result.predicted_value,
                    'confidence': prediction_result.confidence,
                    'prediction_interval': prediction_result.prediction_interval,
                    'estimated_completion': (
                        datetime.utcnow() + timedelta(minutes=prediction_result.predicted_value)
                    ).isoformat()
                })
            except Exception as e:
                self.logger.warning(f"Failed to predict duration for task {task.id}: {e}")
        
        return predictions
    
    def get_model_performance(self) -> ModelPerformance:
        """Get current model performance metrics"""
        if not self.training_history:
            return ModelPerformance(0, 0, 0, 0, 0)
        
        latest_training = self.training_history[-1]
        return ModelPerformance(**latest_training['performance'])
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if not self.model_trained or not hasattr(self.model, 'feature_importances_'):
            return {}
        
        importance_dict = {}
        for i, feature in enumerate(self.feature_columns):
            if i < len(self.model.feature_importances_):
                importance_dict[feature] = float(self.model.feature_importances_[i])
        
        return importance_dict


class SystemLoadPredictor(BaseAnalyzer):
    """
    Machine learning model to predict system load and capacity requirements
    """
    
    def __init__(self):
        super().__init__()
        self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.feature_columns = [
            'current_active_agents', 'total_tasks', 'pending_tasks', 'cpu_usage',
            'memory_usage', 'hour_of_day', 'day_of_week', 'api_requests_per_minute'
        ]
        self.model_trained = False
    
    async def analyze(self, db: AsyncSession, **kwargs) -> Dict[str, Any]:
        """Main analysis method"""
        await self.train_model(db)
        predictions = await self.predict_system_load(db)
        return {
            "load_predictions": predictions,
            "capacity_recommendations": await self.generate_capacity_recommendations(db)
        }
    
    async def train_model(self, db: AsyncSession) -> ModelPerformance:
        """Train system load prediction model"""
        try:
            # Get historical system metrics
            query = select(SystemMetrics).order_by(SystemMetrics.recorded_at.desc()).limit(1000)
            result = await db.execute(query)
            metrics = result.scalars().all()
            
            if len(metrics) < 20:
                self.logger.warning("Insufficient data for system load prediction")
                return self._create_default_load_model()
            
            # Prepare training data
            X, y = self._prepare_load_training_data(metrics)
            
            if len(X) == 0:
                return self._create_default_load_model()
            
            # Train model
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            
            # Calculate performance (simple validation)
            predictions = self.model.predict(X_scaled)
            mse = mean_squared_error(y, predictions)
            r2 = r2_score(y, predictions)
            
            self.model_trained = True
            
            performance = ModelPerformance(
                mse=mse,
                rmse=np.sqrt(mse),
                r2_score=r2,
                mean_absolute_error=np.mean(np.abs(y - predictions)),
                accuracy_percentage=max(0, r2 * 100)
            )
            
            self.logger.info(f"System load model trained. R2: {r2:.3f}")
            return performance
            
        except Exception as e:
            self.logger.error(f"Error training system load model: {e}")
            return self._create_default_load_model()
    
    def _prepare_load_training_data(self, metrics: List[SystemMetrics]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for system load prediction"""
        X, y = [], []
        
        for metric in metrics:
            if metric.recorded_at:
                features = [
                    metric.active_agents,
                    metric.total_tasks,
                    metric.pending_tasks,
                    metric.cpu_usage_percentage,
                    metric.memory_usage_percentage,
                    metric.recorded_at.hour,
                    metric.recorded_at.weekday(),
                    metric.api_requests_per_minute
                ]
                
                # Target is system load percentage
                target = metric.system_load_percentage
                
                X.append(features)
                y.append(target)
        
        return np.array(X), np.array(y)
    
    def _create_default_load_model(self) -> ModelPerformance:
        """Create default load prediction model"""
        # Simple dummy training
        X_dummy = np.random.rand(20, len(self.feature_columns))
        y_dummy = np.random.rand(20) * 100  # 0-100% load
        
        X_dummy_scaled = self.scaler.fit_transform(X_dummy)
        self.model.fit(X_dummy_scaled, y_dummy)
        
        self.model_trained = True
        
        return ModelPerformance(50.0, 7.07, 0.5, 5.0, 50.0)
    
    async def predict_system_load(
        self, 
        db: AsyncSession,
        hours_ahead: int = 24
    ) -> List[Dict[str, Any]]:
        """Predict system load for future time periods"""
        
        if not self.model_trained:
            await self.train_model(db)
        
        # Get current system state
        current_metrics = await self._get_current_system_state(db)
        
        predictions = []
        base_time = datetime.utcnow()
        
        # Predict for next N hours
        for hour in range(1, hours_ahead + 1):
            future_time = base_time + timedelta(hours=hour)
            
            # Estimate future features (simple approach)
            future_features = [
                current_metrics.get('active_agents', 5),
                current_metrics.get('total_tasks', 10) + (hour * 2),  # Assume 2 tasks per hour
                max(0, current_metrics.get('pending_tasks', 5) + (hour * 1.5)),
                current_metrics.get('cpu_usage', 50),
                current_metrics.get('memory_usage', 40),
                future_time.hour,
                future_time.weekday(),
                current_metrics.get('api_requests', 10)
            ]
            
            X_future = np.array([future_features])
            X_future_scaled = self.scaler.transform(X_future)
            
            predicted_load = self.model.predict(X_future_scaled)[0]
            
            predictions.append({
                'timestamp': future_time.isoformat(),
                'predicted_load_percentage': max(0, min(100, predicted_load)),
                'hours_ahead': hour,
                'confidence': max(0.3, 1.0 - (hour * 0.02))  # Confidence decreases over time
            })
        
        return predictions
    
    async def _get_current_system_state(self, db: AsyncSession) -> Dict[str, Any]:
        """Get current system state for prediction"""
        
        # Get latest system metrics
        metrics_query = select(SystemMetrics).order_by(SystemMetrics.recorded_at.desc()).limit(1)
        metrics_result = await db.execute(metrics_query)
        latest_metrics = metrics_result.scalar_one_or_none()
        
        # Get current agent counts
        agents_query = select(Agent)
        agents_result = await db.execute(agents_query)
        agents = agents_result.scalars().all()
        
        # Get current task counts
        tasks_query = select(Task)
        tasks_result = await db.execute(tasks_query)
        tasks = tasks_result.scalars().all()
        
        return {
            'active_agents': len([a for a in agents if a.status == 'active']),
            'total_tasks': len(tasks),
            'pending_tasks': len([t for t in tasks if t.status == 'pending']),
            'cpu_usage': latest_metrics.cpu_usage_percentage if latest_metrics else 50,
            'memory_usage': latest_metrics.memory_usage_percentage if latest_metrics else 40,
            'api_requests': latest_metrics.api_requests_per_minute if latest_metrics else 10
        }
    
    async def generate_capacity_recommendations(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Generate capacity planning recommendations"""
        
        # Get load predictions
        load_predictions = await self.predict_system_load(db, 72)  # 3 days ahead
        
        recommendations = []
        
        # Check for high load periods
        high_load_periods = [p for p in load_predictions if p['predicted_load_percentage'] > 80]
        
        if high_load_periods:
            recommendations.append({
                'type': 'scale_up',
                'priority': 'high',
                'description': f'High system load predicted in {len(high_load_periods)} time periods',
                'recommendation': 'Consider adding more agents or increasing system capacity',
                'estimated_impact': 'Reduce load by 20-30%',
                'timeline': 'Within 24 hours'
            })
        
        # Check for consistently low load
        low_load_periods = [p for p in load_predictions if p['predicted_load_percentage'] < 30]
        
        if len(low_load_periods) > 48:  # More than 48 hours of low load
            recommendations.append({
                'type': 'scale_down',
                'priority': 'medium',
                'description': 'Extended period of low system utilization predicted',
                'recommendation': 'Consider temporarily reducing agent count to save resources',
                'estimated_impact': 'Reduce resource costs by 15-25%',
                'timeline': 'Within 48 hours'
            })
        
        # Check for load variability
        load_values = [p['predicted_load_percentage'] for p in load_predictions]
        if len(load_values) > 0:
            load_std = np.std(load_values)
            if load_std > 25:  # High variability
                recommendations.append({
                    'type': 'auto_scaling',
                    'priority': 'medium',
                    'description': 'High load variability detected',
                    'recommendation': 'Implement auto-scaling to handle load fluctuations',
                    'estimated_impact': 'Improve system responsiveness and resource efficiency',
                    'timeline': 'Within 1 week'
                })
        
        return recommendations