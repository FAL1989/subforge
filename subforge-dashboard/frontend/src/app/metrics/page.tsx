'use client'

import { useEffect, useState } from 'react'
import { MetricsChart } from '@/components/metrics/metrics-chart'
import { PerformanceChart } from '@/components/metrics/performance-chart'
import { AgentMetrics } from '@/components/metrics/agent-metrics'
import { SystemMetrics } from '@/components/metrics/system-metrics'
import { useWebSocket } from '@/hooks/use-websocket'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Calendar, Download } from 'lucide-react'

interface MetricsData {
  taskCompletion: {
    date: string
    completed: number
    failed: number
    total: number
  }[]
  agentPerformance: {
    agentName: string
    successRate: number
    avgResponseTime: number
    tasksCompleted: number
  }[]
  systemHealth: {
    timestamp: string
    cpu: number
    memory: number
    activeConnections: number
  }[]
  productivity: {
    date: string
    tasksPerHour: number
    agentsActive: number
    efficiency: number
  }[]
}

export default function MetricsPage() {
  const [metricsData, setMetricsData] = useState<MetricsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('7d')
  const { data } = useWebSocket()

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/metrics?range=${timeRange}`)
        const data = await response.json()
        setMetricsData(data)
      } catch (error) {
        console.error('Failed to fetch metrics:', error)
        // Mock data for development
        const mockData: MetricsData = {
          taskCompletion: [
            { date: '2024-01-10', completed: 12, failed: 1, total: 13 },
            { date: '2024-01-11', completed: 15, failed: 2, total: 17 },
            { date: '2024-01-12', completed: 18, failed: 1, total: 19 },
            { date: '2024-01-13', completed: 22, failed: 3, total: 25 },
            { date: '2024-01-14', completed: 20, failed: 2, total: 22 },
            { date: '2024-01-15', completed: 25, failed: 1, total: 26 },
            { date: '2024-01-16', completed: 28, failed: 2, total: 30 },
          ],
          agentPerformance: [
            { agentName: 'Frontend Developer', successRate: 96, avgResponseTime: 1.2, tasksCompleted: 23 },
            { agentName: 'Backend Developer', successRate: 94, avgResponseTime: 2.1, tasksCompleted: 18 },
            { agentName: 'Code Reviewer', successRate: 99, avgResponseTime: 1.8, tasksCompleted: 31 },
            { agentName: 'Data Scientist', successRate: 98, avgResponseTime: 3.5, tasksCompleted: 12 },
            { agentName: 'DevOps Engineer', successRate: 92, avgResponseTime: 4.2, tasksCompleted: 8 },
            { agentName: 'Test Engineer', successRate: 88, avgResponseTime: 2.5, tasksCompleted: 7 },
          ],
          systemHealth: [
            { timestamp: '2024-01-16T06:00:00Z', cpu: 35, memory: 45, activeConnections: 8 },
            { timestamp: '2024-01-16T09:00:00Z', cpu: 55, memory: 62, activeConnections: 12 },
            { timestamp: '2024-01-16T12:00:00Z', cpu: 72, memory: 68, activeConnections: 15 },
            { timestamp: '2024-01-16T15:00:00Z', cpu: 45, memory: 58, activeConnections: 10 },
            { timestamp: '2024-01-16T18:00:00Z', cpu: 38, memory: 52, activeConnections: 9 },
          ],
          productivity: [
            { date: '2024-01-10', tasksPerHour: 1.8, agentsActive: 4, efficiency: 78 },
            { date: '2024-01-11', tasksPerHour: 2.1, agentsActive: 5, efficiency: 82 },
            { date: '2024-01-12', tasksPerHour: 2.3, agentsActive: 5, efficiency: 85 },
            { date: '2024-01-13', tasksPerHour: 2.8, agentsActive: 6, efficiency: 88 },
            { date: '2024-01-14', tasksPerHour: 2.5, agentsActive: 5, efficiency: 83 },
            { date: '2024-01-15', tasksPerHour: 3.1, agentsActive: 6, efficiency: 91 },
            { date: '2024-01-16', tasksPerHour: 3.5, agentsActive: 6, efficiency: 94 },
          ],
        }
        setMetricsData(mockData)
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [timeRange])

  // Update metrics with WebSocket data
  useEffect(() => {
    if (data && data.type === 'metrics_update' && metricsData) {
      const newDataPoint = data.payload
      setMetricsData(prev => {
        if (!prev) return prev
        
        // Update the latest data point or add new one
        const updated = { ...prev }
        
        if (newDataPoint.systemHealth) {
          updated.systemHealth = [...prev.systemHealth.slice(-23), newDataPoint.systemHealth]
        }
        
        return updated
      })
    }
  }, [data, metricsData])

  const timeRangeOptions = [
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!metricsData) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-600 dark:text-gray-400">
          Failed to load metrics data
        </h2>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Metrics & Analytics
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Performance insights and system analytics
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            >
              {timeRangeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors">
            <Download size={16} />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Task Completion Chart */}
      <MetricsChart
        title="Task Completion Trends"
        data={metricsData.taskCompletion}
        type="area"
      />

      {/* Performance and System Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PerformanceChart
          title="Agent Performance"
          data={metricsData.agentPerformance}
        />
        <SystemMetrics
          title="System Health"
          data={metricsData.systemHealth}
        />
      </div>

      {/* Agent Metrics */}
      <AgentMetrics data={metricsData.agentPerformance} />

      {/* Productivity Trends */}
      <MetricsChart
        title="Productivity Trends"
        data={metricsData.productivity}
        type="line"
      />
    </div>
  )
}