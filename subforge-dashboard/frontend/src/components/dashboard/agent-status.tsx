'use client'

import { useEffect, useState } from 'react'
import { useWebSocket } from '@/hooks/use-websocket'
import { getStatusColor } from '@/lib/utils'
import { LoadingSpinner } from '@/components/ui/loading-spinner'

interface Agent {
  id: string
  name: string
  type: string
  status: 'active' | 'idle' | 'busy' | 'error'
  lastActive: string
  tasksCompleted: number
  currentTask?: string
}

export function AgentStatus() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const { data } = useWebSocket()

  useEffect(() => {
    // Fetch initial agent data
    const fetchAgents = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/agents')
        const data = await response.json()
        setAgents(data.agents || [])
      } catch (error) {
        console.error('Failed to fetch agents:', error)
        // Set mock data for development
        setAgents([
          {
            id: '1',
            name: 'Frontend Developer',
            type: 'Development',
            status: 'active',
            lastActive: '2 minutes ago',
            tasksCompleted: 23,
            currentTask: 'Building React components'
          },
          {
            id: '2',
            name: 'Backend Developer',
            type: 'Development',
            status: 'busy',
            lastActive: '1 minute ago',
            tasksCompleted: 18,
            currentTask: 'API endpoint optimization'
          },
          {
            id: '3',
            name: 'Data Scientist',
            type: 'Analytics',
            status: 'idle',
            lastActive: '15 minutes ago',
            tasksCompleted: 12,
          },
          {
            id: '4',
            name: 'DevOps Engineer',
            type: 'Infrastructure',
            status: 'active',
            lastActive: '5 minutes ago',
            tasksCompleted: 8,
            currentTask: 'Docker container updates'
          },
          {
            id: '5',
            name: 'Code Reviewer',
            type: 'Quality',
            status: 'busy',
            lastActive: '3 minutes ago',
            tasksCompleted: 31,
            currentTask: 'Security audit review'
          },
          {
            id: '6',
            name: 'Test Engineer',
            type: 'Quality',
            status: 'error',
            lastActive: '1 hour ago',
            tasksCompleted: 7,
          },
        ])
      } finally {
        setLoading(false)
      }
    }

    fetchAgents()
  }, [])

  // Update agents with WebSocket data
  useEffect(() => {
    if (data && data.type === 'agent_status_update') {
      setAgents(prev => 
        prev.map(agent => 
          agent.id === data.payload.agentId 
            ? { ...agent, ...data.payload }
            : agent
        )
      )
    }
  }, [data])

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-center h-32">
          <LoadingSpinner />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Agent Status
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Real-time monitoring of all active agents
        </p>
      </div>
      
      <div className="p-6">
        <div className="grid gap-4">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${
                    agent.status === 'active' ? 'bg-green-500' :
                    agent.status === 'busy' ? 'bg-blue-500' :
                    agent.status === 'idle' ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`} />
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {agent.name}
                    </h4>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {agent.type} • {agent.lastActive}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {agent.tasksCompleted} tasks
                  </p>
                  {agent.currentTask && (
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {agent.currentTask}
                    </p>
                  )}
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  getStatusColor(agent.status)
                }`}>
                  {agent.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}