'use client'

import { useEffect, useState } from 'react'
import { TaskBoard } from '@/components/tasks/task-board'
import { TaskFilters } from '@/components/tasks/task-filters'
import { TaskStats } from '@/components/tasks/task-stats'
import { useWebSocket } from '@/hooks/use-websocket'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { Plus } from 'lucide-react'

export interface Task {
  id: string
  title: string
  description: string
  status: 'todo' | 'in_progress' | 'review' | 'done'
  priority: 'low' | 'medium' | 'high'
  agent?: string
  assignee?: string
  tags: string[]
  createdAt: string
  updatedAt: string
  dueDate?: string
  estimatedTime?: number
  actualTime?: number
  dependencies?: string[]
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    status: 'all',
    priority: 'all',
    agent: 'all',
    search: ''
  })
  const { data } = useWebSocket()

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/tasks')
        const data = await response.json()
        setTasks(data.tasks || [])
      } catch (error) {
        console.error('Failed to fetch tasks:', error)
        // Mock data for development
        const mockTasks: Task[] = [
          {
            id: '1',
            title: 'Implement WebSocket connections',
            description: 'Set up real-time communication between frontend and backend',
            status: 'done',
            priority: 'high',
            agent: 'Backend Developer',
            assignee: 'Backend Developer',
            tags: ['backend', 'websockets', 'real-time'],
            createdAt: '2024-01-15T10:00:00Z',
            updatedAt: '2024-01-15T14:30:00Z',
            estimatedTime: 480,
            actualTime: 520
          },
          {
            id: '2',
            title: 'Design dashboard layout',
            description: 'Create responsive layout for the main dashboard',
            status: 'done',
            priority: 'high',
            agent: 'Frontend Developer',
            assignee: 'Frontend Developer',
            tags: ['frontend', 'ui', 'design'],
            createdAt: '2024-01-15T09:00:00Z',
            updatedAt: '2024-01-15T16:00:00Z',
            estimatedTime: 360,
            actualTime: 420
          },
          {
            id: '3',
            title: 'Set up Docker containers',
            description: 'Configure development and production containers',
            status: 'review',
            priority: 'medium',
            agent: 'DevOps Engineer',
            assignee: 'DevOps Engineer',
            tags: ['devops', 'docker', 'infrastructure'],
            createdAt: '2024-01-15T11:00:00Z',
            updatedAt: '2024-01-15T17:30:00Z',
            estimatedTime: 240,
            dependencies: ['1']
          },
          {
            id: '4',
            title: 'Implement task drag and drop',
            description: 'Add drag and drop functionality to task board',
            status: 'in_progress',
            priority: 'medium',
            agent: 'Frontend Developer',
            assignee: 'Frontend Developer',
            tags: ['frontend', 'ui', 'interaction'],
            createdAt: '2024-01-16T09:00:00Z',
            updatedAt: '2024-01-16T11:00:00Z',
            estimatedTime: 180
          },
          {
            id: '5',
            title: 'Write API documentation',
            description: 'Document all REST API endpoints',
            status: 'todo',
            priority: 'low',
            agent: 'Backend Developer',
            tags: ['documentation', 'api'],
            createdAt: '2024-01-16T10:00:00Z',
            updatedAt: '2024-01-16T10:00:00Z',
            estimatedTime: 120
          },
          {
            id: '6',
            title: 'Add error handling',
            description: 'Implement comprehensive error handling across the application',
            status: 'todo',
            priority: 'medium',
            tags: ['frontend', 'backend', 'error-handling'],
            createdAt: '2024-01-16T12:00:00Z',
            updatedAt: '2024-01-16T12:00:00Z',
            estimatedTime: 300
          },
          {
            id: '7',
            title: 'Performance optimization',
            description: 'Optimize application performance and loading times',
            status: 'in_progress',
            priority: 'high',
            agent: 'Backend Developer',
            assignee: 'Backend Developer',
            tags: ['performance', 'optimization'],
            createdAt: '2024-01-16T08:00:00Z',
            updatedAt: '2024-01-16T13:00:00Z',
            estimatedTime: 240
          },
          {
            id: '8',
            title: 'Security audit',
            description: 'Perform comprehensive security review of the application',
            status: 'review',
            priority: 'high',
            agent: 'Code Reviewer',
            assignee: 'Code Reviewer',
            tags: ['security', 'audit', 'review'],
            createdAt: '2024-01-15T15:00:00Z',
            updatedAt: '2024-01-16T09:30:00Z',
            estimatedTime: 480
          }
        ]
        setTasks(mockTasks)
      } finally {
        setLoading(false)
      }
    }

    fetchTasks()
  }, [])

  // Update tasks with WebSocket data
  useEffect(() => {
    if (data && data.type === 'task_update') {
      setTasks(prev => {
        if (data.payload.action === 'create') {
          return [...prev, data.payload.task]
        } else if (data.payload.action === 'update') {
          return prev.map(task =>
            task.id === data.payload.task.id
              ? { ...task, ...data.payload.task }
              : task
          )
        } else if (data.payload.action === 'delete') {
          return prev.filter(task => task.id !== data.payload.taskId)
        }
        return prev
      })
    }
  }, [data])

  const handleTaskUpdate = (updatedTask: Task) => {
    setTasks(prev =>
      prev.map(task => task.id === updatedTask.id ? updatedTask : task)
    )
  }

  const handleTaskMove = (taskId: string, newStatus: Task['status']) => {
    const updatedTask = tasks.find(task => task.id === taskId)
    if (updatedTask) {
      const updated = {
        ...updatedTask,
        status: newStatus,
        updatedAt: new Date().toISOString()
      }
      handleTaskUpdate(updated)
    }
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
            Tasks
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage and track development tasks
          </p>
        </div>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors">
          <Plus size={16} />
          <span>New Task</span>
        </button>
      </div>

      {/* Task Stats */}
      <TaskStats tasks={tasks} />

      {/* Filters */}
      <TaskFilters filters={filters} onFiltersChange={setFilters} />

      {/* Task Board */}
      <TaskBoard 
        tasks={tasks} 
        filters={filters}
        onTaskUpdate={handleTaskUpdate}
        onTaskMove={handleTaskMove}
      />
    </div>
  )
}