'use client'

import { useEffect, useState } from 'react'
import { MetricsCard } from '@/components/dashboard/metrics-card'
import { AgentStatus } from '@/components/dashboard/agent-status'
import { RecentTasks } from '@/components/dashboard/recent-tasks'
import { SystemHealth } from '@/components/dashboard/system-health'
import { useWebSocket } from '@/hooks/use-websocket'
import { LoadingSpinner } from '@/components/ui/loading-spinner'

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

  useEffect(() => {
    // Fetch initial dashboard data
    const fetchDashboardData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/overview')
        const data = await response.json()
        setDashboardData(data)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
        // Set mock data for development
        setDashboardData({
          agents: { total: 6, active: 4, idle: 1, error: 1 },
          tasks: { completed: 145, pending: 8, failed: 2, total: 155 },
          system: { uptime: 86400, cpu: 45, memory: 68, connections: 12 }
        })
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  // Update data with WebSocket updates
  useEffect(() => {
    if (data && data.type === 'dashboard_update') {
      setDashboardData(prev => ({ ...prev, ...data.payload }))
    }
  }, [data])

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
          title="Active Agents"
          value={dashboardData.agents.active}
          total={dashboardData.agents.total}
          trend="+2.5%"
          icon="users"
          color="blue"
        />
        <MetricsCard
          title="Completed Tasks"
          value={dashboardData.tasks.completed}
          total={dashboardData.tasks.total}
          trend="+12.3%"
          icon="check-circle"
          color="green"
        />
        <MetricsCard
          title="System Load"
          value={dashboardData.system.cpu}
          total={100}
          trend="-5.2%"
          icon="cpu"
          color="orange"
          suffix="%"
        />
        <MetricsCard
          title="Memory Usage"
          value={dashboardData.system.memory}
          total={100}
          trend="+1.8%"
          icon="hard-drive"
          color="purple"
          suffix="%"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Status */}
        <div className="lg:col-span-2">
          <AgentStatus />
        </div>

        {/* System Health */}
        <div>
          <SystemHealth data={dashboardData.system} />
        </div>
      </div>

      {/* Recent Tasks */}
      <RecentTasks />
    </div>
  )
}