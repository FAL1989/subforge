'use client'

import { useEffect, useState } from 'react'
import { MetricsCard } from '@/components/dashboard/metrics-card'
import { AgentStatus } from '@/components/dashboard/agent-status'
import { RecentTasks } from '@/components/dashboard/recent-tasks'
import { SystemHealth } from '@/components/dashboard/system-health'
import { WorkflowMonitor } from '@/components/dashboard/workflow-monitor'
import { useWebSocket } from '@/hooks/use-websocket'
import { useSubForge } from '@/hooks/use-subforge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { WorkflowStatus } from '@/types/subforge'
import { Activity } from 'lucide-react'

interface DashboardData {
  agents: {
    total: number
    active: number
    idle: number
    error: number
  }
  tasks: {
    completed: number
    pending: number
    failed: number
    total: number
  }
  system: {
    uptime: number
    cpu: number
    memory: number
    connections: number
  }
}

export default function Dashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    agents: { total: 0, active: 0, idle: 0, error: 0 },
    tasks: { completed: 0, pending: 0, failed: 0, total: 0 },
    system: { uptime: 0, cpu: 0, memory: 0, connections: 0 }
  })
  const [loading, setLoading] = useState(true)
  const { isConnected, data } = useWebSocket()
  const { 
    workflows, 
    metrics, 
    status: subforgeStatus, 
    recentActivities, 
    loading: subforgeLoading 
  } = useSubForge()

  useEffect(() => {
    // Fetch initial dashboard data (legacy/system data)
    const fetchDashboardData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/overview')
        const data = await response.json()
        setDashboardData(data)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
        // Set mock data for development based on SubForge data if available
        if (metrics) {
          setDashboardData({
            agents: { 
              total: Object.keys(metrics.agent_utilization).length, 
              active: workflows.filter(w => w.status === WorkflowStatus.ACTIVE).reduce((sum, w) => sum + w.agent_count, 0),
              idle: 0, 
              error: workflows.filter(w => w.status === WorkflowStatus.FAILED).reduce((sum, w) => sum + w.agent_count, 0)
            },
            tasks: { 
              completed: workflows.reduce((sum, w) => sum + w.completed_phases, 0), 
              pending: workflows.filter(w => w.status === WorkflowStatus.ACTIVE).reduce((sum, w) => sum + (w.total_phases - w.completed_phases), 0), 
              failed: workflows.filter(w => w.status === WorkflowStatus.FAILED).reduce((sum, w) => sum + w.failed_phases, 0), 
              total: workflows.reduce((sum, w) => sum + w.total_phases, 0)
            },
            system: { uptime: 86400, cpu: 45, memory: 68, connections: isConnected ? 1 : 0 }
          })
        } else {
          setDashboardData({
            agents: { total: 6, active: 4, idle: 1, error: 1 },
            tasks: { completed: 145, pending: 8, failed: 2, total: 155 },
            system: { uptime: 86400, cpu: 45, memory: 68, connections: 12 }
          })
        }
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [metrics, workflows, isConnected])

  // Update data with WebSocket updates
  useEffect(() => {
    if (data && data.type === 'dashboard_update') {
      setDashboardData(prev => ({ ...prev, ...data.payload }))
    }
  }, [data])

  // Calculate SubForge-based metrics
  const activeWorkflows = workflows.filter(w => w.status === WorkflowStatus.ACTIVE).length
  const completedWorkflows = workflows.filter(w => w.status === WorkflowStatus.COMPLETED).length
  const totalAgents = workflows.reduce((sum, w) => sum + w.agent_count, 0)
  const completedTasks = workflows.reduce((sum, w) => sum + w.completed_phases, 0)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            SubForge AI Agent Orchestration Platform
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricsCard
          title="Active Workflows"
          value={activeWorkflows}
          total={workflows.length}
          trend={metrics ? `${Math.round(metrics.success_rate)}% success` : "N/A"}
          icon="activity"
          color="blue"
        />
        <MetricsCard
          title="Total Agents"
          value={totalAgents}
          total={metrics ? Object.keys(metrics.agent_utilization).length : dashboardData.agents.total}
          trend={subforgeStatus ? `${subforgeStatus.active_workflows} active` : "N/A"}
          icon="users"
          color="green"
        />
        <MetricsCard
          title="Completed Phases"
          value={completedTasks}
          total={workflows.reduce((sum, w) => sum + w.total_phases, 0)}
          trend={completedWorkflows > 0 ? `${completedWorkflows} workflows done` : "No completions"}
          icon="check-circle"
          color="purple"
        />
        <MetricsCard
          title="System Status"
          value={subforgeStatus?.service_status === 'active' ? 'Online' : 'Offline'}
          total={subforgeStatus?.monitoring_enabled ? 'Monitoring' : 'Idle'}
          trend={isConnected ? 'Connected' : 'Disconnected'}
          icon="hard-drive"
          color="orange"
          suffix=""
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Workflow Monitor */}
        <div>
          <WorkflowMonitor maxItems={5} />
        </div>

        {/* System Health */}
        <div>
          <SystemHealth data={dashboardData.system} />
        </div>
      </div>

      {/* Secondary Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Status */}
        <div className="lg:col-span-2">
          <AgentStatus />
        </div>

        {/* Recent SubForge Activities */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Activities
          </h3>
          {recentActivities.length > 0 ? (
            <div className="space-y-3">
              {recentActivities.slice(0, 5).map((activity, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {activity.agent_name}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                      {activity.description || activity.activity_type}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-3">
                <Activity className="w-6 h-6" />
              </div>
              <p className="text-sm">No recent activities</p>
              <p className="text-xs mt-1">Agent activities will appear here</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Tasks (Legacy) */}
      <RecentTasks />
    </div>
  )
}