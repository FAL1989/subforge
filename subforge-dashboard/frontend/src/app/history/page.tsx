'use client'

import { useEffect, useState } from 'react'
import { WorkflowTimeline } from '@/components/history/workflow-timeline'
import { HistoryFilters } from '@/components/history/history-filters'
import { HistoryStats } from '@/components/history/history-stats'
import { useWebSocket } from '@/hooks/use-websocket'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Download } from 'lucide-react'

export interface WorkflowEvent {
  id: string
  type: 'task_created' | 'task_completed' | 'task_failed' | 'agent_assigned' | 'workflow_started' | 'workflow_completed'
  title: string
  description: string
  agent?: string
  task?: string
  timestamp: string
  duration?: number
  status: 'success' | 'warning' | 'error' | 'info'
  metadata?: {
    taskId?: string
    agentId?: string
    workflowId?: string
    [key: string]: any
  }
}

export default function HistoryPage() {
  const [events, setEvents] = useState<WorkflowEvent[]>([])
  const [filteredEvents, setFilteredEvents] = useState<WorkflowEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    type: 'all',
    status: 'all',
    agent: 'all',
    dateRange: '7d',
    search: ''
  })
  const { data } = useWebSocket()

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/history?range=${filters.dateRange}`)
        const data = await response.json()
        setEvents(data.events || [])
      } catch (error) {
        console.error('Failed to fetch history:', error)
        // Mock data for development
        const mockEvents: WorkflowEvent[] = [
          {
            id: '1',
            type: 'workflow_started',
            title: 'Dashboard Development Workflow Started',
            description: 'Initiated comprehensive dashboard development project',
            timestamp: '2024-01-16T09:00:00Z',
            status: 'info',
            metadata: { workflowId: 'wf-001' }
          },
          {
            id: '2',
            type: 'agent_assigned',
            title: 'Frontend Developer Assigned',
            description: 'Frontend Developer assigned to dashboard UI development',
            agent: 'Frontend Developer',
            timestamp: '2024-01-16T09:05:00Z',
            status: 'info',
            metadata: { agentId: 'agent-001', taskId: 'task-001' }
          },
          {
            id: '3',
            type: 'task_created',
            title: 'Task Created: Design Dashboard Layout',
            description: 'Created task for designing responsive dashboard layout',
            agent: 'Frontend Developer',
            task: 'Design Dashboard Layout',
            timestamp: '2024-01-16T09:10:00Z',
            status: 'info',
            metadata: { taskId: 'task-001' }
          },
          {
            id: '4',
            type: 'task_completed',
            title: 'Task Completed: WebSocket Integration',
            description: 'Successfully implemented real-time WebSocket connections',
            agent: 'Backend Developer',
            task: 'WebSocket Integration',
            timestamp: '2024-01-16T11:30:00Z',
            duration: 8400, // 2.33 hours
            status: 'success',
            metadata: { taskId: 'task-002' }
          },
          {
            id: '5',
            type: 'task_failed',
            title: 'Task Failed: Database Migration',
            description: 'Database migration failed due to constraint conflicts',
            agent: 'Backend Developer',
            task: 'Database Migration',
            timestamp: '2024-01-16T13:45:00Z',
            duration: 3600, // 1 hour
            status: 'error',
            metadata: { taskId: 'task-003', error: 'Constraint violation' }
          },
          {
            id: '6',
            type: 'agent_assigned',
            title: 'Code Reviewer Assigned',
            description: 'Code Reviewer assigned for security audit',
            agent: 'Code Reviewer',
            timestamp: '2024-01-16T14:00:00Z',
            status: 'info',
            metadata: { agentId: 'agent-005', taskId: 'task-004' }
          },
          {
            id: '7',
            type: 'task_completed',
            title: 'Task Completed: Security Audit',
            description: 'Completed comprehensive security review with recommendations',
            agent: 'Code Reviewer',
            task: 'Security Audit',
            timestamp: '2024-01-16T16:30:00Z',
            duration: 9000, // 2.5 hours
            status: 'warning',
            metadata: { taskId: 'task-004', findings: 3 }
          },
          {
            id: '8',
            type: 'task_created',
            title: 'Task Created: Fix Security Issues',
            description: 'Created follow-up task to address security audit findings',
            agent: 'Backend Developer',
            task: 'Fix Security Issues',
            timestamp: '2024-01-16T16:35:00Z',
            status: 'info',
            metadata: { taskId: 'task-005', parentTaskId: 'task-004' }
          },
          {
            id: '9',
            type: 'task_completed',
            title: 'Task Completed: Docker Configuration',
            description: 'Successfully configured development and production containers',
            agent: 'DevOps Engineer',
            task: 'Docker Configuration',
            timestamp: '2024-01-16T17:15:00Z',
            duration: 7200, // 2 hours
            status: 'success',
            metadata: { taskId: 'task-006' }
          },
          {
            id: '10',
            type: 'workflow_completed',
            title: 'Workflow Milestone Reached',
            description: 'Completed Phase 1 of dashboard development workflow',
            timestamp: '2024-01-16T18:00:00Z',
            status: 'success',
            metadata: { workflowId: 'wf-001', phase: 1 }
          }
        ]
        setEvents(mockEvents.reverse()) // Most recent first
      } finally {
        setLoading(false)
      }
    }

    fetchHistory()
  }, [filters.dateRange])

  // Filter events based on filters
  useEffect(() => {
    let filtered = events

    if (filters.type !== 'all') {
      filtered = filtered.filter(event => event.type === filters.type)
    }

    if (filters.status !== 'all') {
      filtered = filtered.filter(event => event.status === filters.status)
    }

    if (filters.agent !== 'all') {
      filtered = filtered.filter(event => event.agent === filters.agent)
    }

    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      filtered = filtered.filter(event =>
        event.title.toLowerCase().includes(searchLower) ||
        event.description.toLowerCase().includes(searchLower) ||
        (event.agent && event.agent.toLowerCase().includes(searchLower))
      )
    }

    setFilteredEvents(filtered)
  }, [events, filters])

  // Update events with WebSocket data
  useEffect(() => {
    if (data && data.type === 'workflow_update') {
      const newEvent: WorkflowEvent = {
        id: data.payload.eventId || Date.now().toString(),
        type: data.payload.type,
        title: data.payload.title,
        description: data.payload.description,
        agent: data.payload.agent,
        task: data.payload.task,
        timestamp: new Date().toISOString(),
        status: data.payload.status,
        duration: data.payload.duration,
        metadata: data.payload.metadata
      }
      setEvents(prev => [newEvent, ...prev])
    }
  }, [data])

  const exportHistory = () => {
    const csvData = filteredEvents.map(event => ({
      Timestamp: new Date(event.timestamp).toLocaleString(),
      Type: event.type,
      Title: event.title,
      Description: event.description,
      Agent: event.agent || '',
      Task: event.task || '',
      Status: event.status,
      Duration: event.duration ? `${Math.round(event.duration / 60)} minutes` : ''
    }))
    
    const csv = [
      Object.keys(csvData[0] || {}).join(','),
      ...csvData.map(row => Object.values(row).map(val => `"${val}"`).join(','))
    ].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `workflow-history-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

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
            Workflow History
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Complete timeline of all workflow events and activities
          </p>
        </div>
        <button
          onClick={exportHistory}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
        >
          <Download size={16} />
          <span>Export History</span>
        </button>
      </div>

      {/* History Stats */}
      <HistoryStats events={events} />

      {/* Filters */}
      <HistoryFilters filters={filters} onFiltersChange={setFilters} />

      {/* Timeline */}
      <WorkflowTimeline events={filteredEvents} />

      {filteredEvents.length === 0 && !loading && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            No workflow events found matching your criteria.
          </p>
        </div>
      )}
    </div>
  )
}