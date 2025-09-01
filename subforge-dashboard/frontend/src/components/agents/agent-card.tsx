import { Clock, Cpu, TrendingUp, Settings } from 'lucide-react'
import { getStatusColor } from '@/lib/utils'

interface Agent {
  id: string
  name: string
  type: string
  status: 'active' | 'idle' | 'busy' | 'error' | 'offline'
  model: string
  capabilities: string[]
  tasksCompleted: number
  currentTask?: string
  lastActive: string
  performance: {
    successRate: number
    avgResponseTime: number
    totalTasks: number
  }
}

interface AgentCardProps {
  agent: Agent
}

export function AgentCard({ agent }: AgentCardProps) {
  const getModelBadgeColor = (model: string) => {
    if (model.includes('Opus')) return 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400'
    if (model.includes('Sonnet')) return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
    if (model.includes('Haiku')) return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
    return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              agent.status === 'active' ? 'bg-green-500' :
              agent.status === 'busy' ? 'bg-blue-500' :
              agent.status === 'idle' ? 'bg-yellow-500' :
              agent.status === 'error' ? 'bg-red-500' :
              'bg-gray-500'
            }`} />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {agent.name}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {agent.type}
              </p>
            </div>
          </div>
          <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
            <Settings size={16} />
          </button>
        </div>
        
        <div className="mt-3 flex items-center justify-between">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            getStatusColor(agent.status)
          }`}>
            {agent.status}
          </span>
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            getModelBadgeColor(agent.model)
          }`}>
            {agent.model}
          </span>
        </div>
      </div>

      {/* Current Task */}
      {agent.currentTask && (
        <div className="px-6 py-3 bg-blue-50 dark:bg-blue-900/10 border-b border-gray-200 dark:border-gray-700">
          <p className="text-sm text-blue-800 dark:text-blue-400">
            <span className="font-medium">Current task:</span> {agent.currentTask}
          </p>
        </div>
      )}

      {/* Stats */}
      <div className="p-6">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Success Rate
              </span>
            </div>
            <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">
              {agent.performance.successRate}%
            </p>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Avg Response
              </span>
            </div>
            <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">
              {agent.performance.avgResponseTime}s
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
          <div className="flex items-center space-x-1">
            <Clock className="w-4 h-4" />
            <span>Last active: {agent.lastActive}</span>
          </div>
          <span>{agent.tasksCompleted} tasks</span>
        </div>
      </div>

      {/* Capabilities */}
      <div className="px-6 pb-6">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Capabilities
        </h4>
        <div className="flex flex-wrap gap-2">
          {agent.capabilities.slice(0, 4).map((capability, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
            >
              {capability}
            </span>
          ))}
          {agent.capabilities.length > 4 && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
              +{agent.capabilities.length - 4} more
            </span>
          )}
        </div>
      </div>
    </div>
  )
}