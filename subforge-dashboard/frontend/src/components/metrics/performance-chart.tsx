'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface PerformanceChartProps {
  title: string
  data: {
    agentName: string
    successRate: number
    avgResponseTime: number
    tasksCompleted: number
  }[]
}

export function PerformanceChart({ title, data }: PerformanceChartProps) {
  const getBarColor = (successRate: number) => {
    if (successRate >= 95) return '#10b981' // green
    if (successRate >= 90) return '#f59e0b' // yellow
    return '#ef4444' // red
  }

  const formatTooltip = (value: any, name: string) => {
    switch (name) {
      case 'successRate':
        return [`${value}%`, 'Success Rate']
      case 'avgResponseTime':
        return [`${value}s`, 'Avg Response Time']
      case 'tasksCompleted':
        return [`${value} tasks`, 'Tasks Completed']
      default:
        return [value, name]
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {title}
        </h3>
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-gray-600 dark:text-gray-400">Excellent (≥95%)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span className="text-gray-600 dark:text-gray-400">Good (≥90%)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span className="text-gray-600 dark:text-gray-400">Needs Attention</span>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis 
            dataKey="agentName" 
            className="text-gray-600 dark:text-gray-400"
            angle={-45}
            textAnchor="end"
            height={80}
            interval={0}
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
          />
          <Bar dataKey="successRate" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.successRate)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Performance Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {Math.round(data.reduce((acc, item) => acc + item.successRate, 0) / data.length)}%
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Avg Success Rate</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {(data.reduce((acc, item) => acc + item.avgResponseTime, 0) / data.length).toFixed(1)}s
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Avg Response Time</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {data.reduce((acc, item) => acc + item.tasksCompleted, 0)}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Tasks</p>
          </div>
        </div>
      </div>
    </div>
  )
}