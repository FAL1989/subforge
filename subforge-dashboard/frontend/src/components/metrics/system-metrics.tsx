'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface SystemMetricsProps {
  title: string
  data: {
    timestamp: string
    cpu: number
    memory: number
    activeConnections: number
  }[]
}

export function SystemMetrics({ title, data }: SystemMetricsProps) {
  // Handle empty or undefined data
  if (!data || data.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {title}
        </h3>
        <div className="flex items-center justify-center h-[240px] text-gray-500 dark:text-gray-400">
          No system metrics available
        </div>
      </div>
    )
  }

  const formatTooltip = (value: any, name: string) => {
    switch (name) {
      case 'cpu':
        return [`${value}%`, 'CPU Usage']
      case 'memory':
        return [`${value}%`, 'Memory Usage']
      case 'activeConnections':
        return [`${value} connections`, 'Active Connections']
      default:
        return [value, name]
    }
  }

  const formatXAxisLabel = (tickItem: string) => {
    return new Date(tickItem).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  const getHealthStatus = () => {
    if (!data || data.length === 0) {
      return { status: 'Unknown', color: 'text-gray-500' }
    }
    
    const latestData = data[data.length - 1]
    if (!latestData) return { status: 'Unknown', color: 'text-gray-500' }
    
    const { cpu, memory } = latestData
    if (cpu > 80 || memory > 80) {
      return { status: 'Critical', color: 'text-red-500' }
    }
    if (cpu > 60 || memory > 60) {
      return { status: 'Warning', color: 'text-yellow-500' }
    }
    return { status: 'Healthy', color: 'text-green-500' }
  }

  const health = getHealthStatus()
  const latestData = data && data.length > 0 ? data[data.length - 1] : null

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {title}
        </h3>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            health.status === 'Healthy' ? 'bg-green-500' :
            health.status === 'Warning' ? 'bg-yellow-500' :
            'bg-red-500'
          }`} />
          <span className={`text-sm font-medium ${health.color}`}>
            {health.status}
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={240}>
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis 
            dataKey="timestamp" 
            className="text-gray-600 dark:text-gray-400"
            tickFormatter={formatXAxisLabel}
          />
          <YAxis className="text-gray-600 dark:text-gray-400" />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--tw-color-gray-800)',
              border: '1px solid var(--tw-color-gray-700)',
              borderRadius: '8px',
              color: 'var(--tw-color-white)',
            }}
            formatter={formatTooltip}
            labelFormatter={(value) => `Time: ${formatXAxisLabel(value)}`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="cpu"
            stroke="#ef4444"
            strokeWidth={2}
            dot={{ fill: '#ef4444', strokeWidth: 2, r: 3 }}
            name="CPU"
          />
          <Line
            type="monotone"
            dataKey="memory"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 3 }}
            name="Memory"
          />
          <Line
            type="monotone"
            dataKey="activeConnections"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ fill: '#10b981', strokeWidth: 2, r: 3 }}
            name="Connections"
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Current Stats */}
      {latestData && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xl font-bold text-gray-900 dark:text-white">
                {latestData.cpu}%
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">CPU Usage</p>
              <div className="mt-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
                <div
                  className={`h-1 rounded-full transition-all duration-300 ${
                    latestData.cpu > 70 ? 'bg-red-500' :
                    latestData.cpu > 40 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(latestData.cpu, 100)}%` }}
                />
              </div>
            </div>
            <div>
              <p className="text-xl font-bold text-gray-900 dark:text-white">
                {latestData.memory}%
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Memory Usage</p>
              <div className="mt-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
                <div
                  className={`h-1 rounded-full transition-all duration-300 ${
                    latestData.memory > 70 ? 'bg-red-500' :
                    latestData.memory > 40 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(latestData.memory, 100)}%` }}
                />
              </div>
            </div>
            <div>
              <p className="text-xl font-bold text-gray-900 dark:text-white">
                {latestData.activeConnections}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Active Connections</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}