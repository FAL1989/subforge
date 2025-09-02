import { TrendingUp, Clock, CheckCircle, AlertCircle } from 'lucide-react'

interface AgentMetricsProps {
  data: {
    agentName: string
    successRate: number
    avgResponseTime: number
    tasksCompleted: number
  }[]
}

export function AgentMetrics({ data }: AgentMetricsProps) {
  // Handle empty or undefined data
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Agent Performance Details
          </h3>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Ranked by success rate
          </div>
        </div>
        <div className="flex items-center justify-center h-[240px] text-gray-500 dark:text-gray-400">
          No agent metrics available
        </div>
      </div>
    )
  }

  const sortedData = [...data].sort((a, b) => b.successRate - a.successRate)

  const getPerformanceLevel = (successRate: number) => {
    if (successRate >= 95) return { level: 'Excellent', color: 'text-green-600', bgColor: 'bg-green-50 dark:bg-green-900/20' }
    if (successRate >= 90) return { level: 'Good', color: 'text-yellow-600', bgColor: 'bg-yellow-50 dark:bg-yellow-900/20' }
    return { level: 'Needs Attention', color: 'text-red-600', bgColor: 'bg-red-50 dark:bg-red-900/20' }
  }

  const getResponseTimeLevel = (responseTime: number) => {
    if (responseTime <= 2) return { level: 'Fast', color: 'text-green-600' }
    if (responseTime <= 4) return { level: 'Moderate', color: 'text-yellow-600' }
    return { level: 'Slow', color: 'text-red-600' }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Agent Performance Details
        </h3>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Ranked by success rate
        </div>
      </div>

      <div className="space-y-4">
        {sortedData.map((agent, index) => {
          const performance = getPerformanceLevel(agent.successRate)
          const responseLevel = getResponseTimeLevel(agent.avgResponseTime)

          return (
            <div
              key={agent.agentName}
              className={`p-4 rounded-lg border border-gray-200 dark:border-gray-600 ${performance.bgColor}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      #{index + 1}
                    </span>
                    <h4 className="font-semibold text-gray-900 dark:text-white">
                      {agent.agentName}
                    </h4>
                  </div>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    performance.level === 'Excellent' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                      : performance.level === 'Good'
                      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                  }`}>
                    {performance.level}
                  </span>
                </div>
                <div className="text-right">
                  <div className="flex items-center space-x-1">
                    <TrendingUp className="w-4 h-4 text-green-500" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {agent.successRate}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Success Rate */}
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Success Rate
                    </p>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-green-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${agent.successRate}%` }}
                        />
                      </div>
                      <span className="text-sm font-bold text-gray-900 dark:text-white">
                        {agent.successRate}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Response Time */}
                <div className="flex items-center space-x-3">
                  <Clock className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Avg Response Time
                    </p>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-bold text-gray-900 dark:text-white">
                        {agent.avgResponseTime}s
                      </span>
                      <span className={`text-xs ${responseLevel.color}`}>
                        ({responseLevel.level})
                      </span>
                    </div>
                  </div>
                </div>

                {/* Tasks Completed */}
                <div className="flex items-center space-x-3">
                  <AlertCircle className="w-5 h-5 text-purple-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Tasks Completed
                    </p>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-bold text-gray-900 dark:text-white">
                        {agent.tasksCompleted}
                      </span>
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        tasks
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {data && Array.isArray(data) ? data.filter(agent => agent.successRate >= 95).length : 0}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Excellent Performers</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {data && Array.isArray(data) && data.length > 0 
                ? Math.round(data.reduce((acc, agent) => acc + agent.successRate, 0) / data.length)
                : 0}%
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Average Success Rate</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {data && Array.isArray(data) && data.length > 0 
                ? (data.reduce((acc, agent) => acc + agent.avgResponseTime, 0) / data.length).toFixed(1)
                : 0.0}s
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Average Response Time</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {data && Array.isArray(data) ? data.reduce((acc, agent) => acc + agent.tasksCompleted, 0) : 0}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Tasks Completed</p>
          </div>
        </div>
      </div>
    </div>
  )
}