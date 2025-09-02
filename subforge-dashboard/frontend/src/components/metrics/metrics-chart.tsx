'use client'

import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface MetricsChartProps {
  title: string
  data: any[]
  type: 'line' | 'area'
  height?: number
}

export function MetricsChart({ title, data, type, height = 300 }: MetricsChartProps) {
  // Handle empty or undefined data
  if (!data || data.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {title}
        </h3>
        <div className="flex items-center justify-center h-[300px] text-gray-500 dark:text-gray-400">
          No data available
        </div>
      </div>
    )
  }

  const formatTooltip = (value: any, name: string) => {
    if (name === 'completed' || name === 'failed' || name === 'total') {
      return [`${value} tasks`, name.charAt(0).toUpperCase() + name.slice(1)]
    }
    if (name === 'tasksPerHour') {
      return [`${value} tasks/hr`, 'Tasks per Hour']
    }
    if (name === 'agentsActive') {
      return [`${value} agents`, 'Active Agents']
    }
    if (name === 'efficiency') {
      return [`${value}%`, 'Efficiency']
    }
    return [value, name]
  }

  const formatXAxisLabel = (tickItem: string) => {
    if (tickItem.includes('T')) {
      // Handle timestamp format
      return new Date(tickItem).toLocaleDateString()
    }
    return tickItem
  }

  const ChartComponent = type === 'area' ? AreaChart : LineChart

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {title}
      </h3>
      
      <ResponsiveContainer width="100%" height={height}>
        <ChartComponent data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis 
            dataKey="date" 
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
          />
          <Legend />

          {/* Task Completion Chart */}
          {data && data.length > 0 && data[0]?.completed !== undefined && (
            <>
              {type === 'area' ? (
                <>
                  <Area
                    type="monotone"
                    dataKey="completed"
                    stackId="1"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="failed"
                    stackId="1"
                    stroke="#ef4444"
                    fill="#ef4444"
                    fillOpacity={0.6}
                  />
                </>
              ) : (
                <>
                  <Line
                    type="monotone"
                    dataKey="completed"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={{ fill: '#10b981', strokeWidth: 2 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="failed"
                    stroke="#ef4444"
                    strokeWidth={2}
                    dot={{ fill: '#ef4444', strokeWidth: 2 }}
                  />
                </>
              )}
            </>
          )}

          {/* Productivity Chart */}
          {data && data.length > 0 && data[0]?.tasksPerHour !== undefined && (
            <>
              {type === 'area' ? (
                <>
                  <Area
                    type="monotone"
                    dataKey="tasksPerHour"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.4}
                  />
                  <Area
                    type="monotone"
                    dataKey="efficiency"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.3}
                  />
                </>
              ) : (
                <>
                  <Line
                    type="monotone"
                    dataKey="tasksPerHour"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6', strokeWidth: 2 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="efficiency"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    dot={{ fill: '#8b5cf6', strokeWidth: 2 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="agentsActive"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    dot={{ fill: '#f59e0b', strokeWidth: 2 }}
                  />
                </>
              )}
            </>
          )}
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  )
}