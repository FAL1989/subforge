'use client'

import { useEffect, useState } from 'react'
import { useWebSocket } from '@/hooks/use-websocket'
import { AgentCard } from '@/components/agents/agent-card'
import { AgentFilters } from '@/components/agents/agent-filters'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Plus } from 'lucide-react'

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
  createdAt: string
  performance: {
    successRate: number
    avgResponseTime: number
    totalTasks: number
  }
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [filteredAgents, setFilteredAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    status: 'all',
    type: 'all',
    search: ''
  })
  const { data } = useWebSocket()

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/agents/detailed')
        const data = await response.json()
        setAgents(data.agents || [])
      } catch (error) {
        console.error('Failed to fetch agents:', error)
        // Mock data for development
        const mockAgents: Agent[] = [
          {
            id: '1',
            name: 'Frontend Developer',
            type: 'Development',
            status: 'active',
            model: 'Claude Sonnet',
            capabilities: ['React', 'TypeScript', 'CSS', 'Testing'],
            tasksCompleted: 23,
            currentTask: 'Building dashboard components',
            lastActive: '2 minutes ago',
            createdAt: '2024-01-15',
            performance: {
              successRate: 96,
              avgResponseTime: 1.2,
              totalTasks: 24
            }
          },
          {
            id: '2',
            name: 'Backend Developer',
            type: 'Development',
            status: 'busy',
            model: 'Claude Sonnet',
            capabilities: ['Python', 'FastAPI', 'PostgreSQL', 'Redis'],
            tasksCompleted: 18,
            currentTask: 'API optimization',
            lastActive: '1 minute ago',
            createdAt: '2024-01-15',
            performance: {
              successRate: 94,
              avgResponseTime: 2.1,
              totalTasks: 19
            }
          },
          {
            id: '3',
            name: 'Data Scientist',
            type: 'Analytics',
            status: 'idle',
            model: 'Claude Opus',
            capabilities: ['Python', 'Pandas', 'ML', 'Statistics'],
            tasksCompleted: 12,
            lastActive: '15 minutes ago',
            createdAt: '2024-01-15',
            performance: {
              successRate: 98,
              avgResponseTime: 3.5,
              totalTasks: 12
            }
          },
          {
            id: '4',
            name: 'DevOps Engineer',
            type: 'Infrastructure',
            status: 'active',
            model: 'Claude Sonnet',
            capabilities: ['Docker', 'Kubernetes', 'AWS', 'Terraform'],
            tasksCompleted: 8,
            currentTask: 'Container deployment',
            lastActive: '5 minutes ago',
            createdAt: '2024-01-16',
            performance: {
              successRate: 92,
              avgResponseTime: 4.2,
              totalTasks: 9
            }
          },
          {
            id: '5',
            name: 'Code Reviewer',
            type: 'Quality',
            status: 'busy',
            model: 'Claude Opus',
            capabilities: ['Code Review', 'Security', 'Best Practices'],
            tasksCompleted: 31,
            currentTask: 'Security audit',
            lastActive: '3 minutes ago',
            createdAt: '2024-01-15',
            performance: {
              successRate: 99,
              avgResponseTime: 1.8,
              totalTasks: 31
            }
          },
          {
            id: '6',
            name: 'Test Engineer',
            type: 'Quality',
            status: 'error',
            model: 'Claude Haiku',
            capabilities: ['Testing', 'Automation', 'QA'],
            tasksCompleted: 7,
            lastActive: '1 hour ago',
            createdAt: '2024-01-16',
            performance: {
              successRate: 88,
              avgResponseTime: 2.5,
              totalTasks: 8
            }
          },
        ]
        setAgents(mockAgents)
      } finally {
        setLoading(false)
      }
    }

    fetchAgents()
  }, [])

  // Filter agents based on current filters
  useEffect(() => {
    let filtered = agents

    if (filters.status !== 'all') {
      filtered = filtered.filter(agent => agent.status === filters.status)
    }

    if (filters.type !== 'all') {
      filtered = filtered.filter(agent => agent.type === filters.type)
    }

    if (filters.search) {
      filtered = filtered.filter(agent =>
        agent.name.toLowerCase().includes(filters.search.toLowerCase()) ||
        agent.capabilities.some(cap => 
          cap.toLowerCase().includes(filters.search.toLowerCase())
        )
      )
    }

    setFilteredAgents(filtered)
  }, [agents, filters])

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
            Agents
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage and monitor your AI agents
          </p>
        </div>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors">
          <Plus size={16} />
          <span>Create Agent</span>
        </button>
      </div>

      {/* Filters */}
      <AgentFilters filters={filters} onFiltersChange={setFilters} />

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>

      {filteredAgents.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            No agents found matching your criteria.
          </p>
        </div>
      )}
    </div>
  )
}