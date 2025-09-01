'use client'

import { useEffect, useState } from 'react'
import { useWebSocket } from '@/hooks/use-websocket'
import { getStatusColor } from '@/lib/utils'
import { Clock, User, Tag } from 'lucide-react'

interface Task {
  id: string
  title: string
  agent: string
  status: 'completed' | 'pending' | 'failed' | 'in_progress'
  priority: 'low' | 'medium' | 'high'
  timestamp: string
  duration?: number
}

export function RecentTasks() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const { data } = useWebSocket()

  useEffect(() => {
    // Fetch recent tasks
    const fetchTasks = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/tasks/recent')
        const data = await response.json()
        setTasks(data.tasks || [])
      } catch (error) {
        console.error('Failed to fetch tasks:', error)
        // Set mock data for development
        setTasks([
          {
            id: '1',
            title: 'Implement user authentication system',
            agent: 'Backend Developer',
            status: 'completed',
            priority: 'high',
            timestamp: '2 minutes ago',
            duration: 1800
          },
          {
            id: '2',
            title: 'Design responsive navigation component',
            agent: 'Frontend Developer',
            status: 'in_progress',
            priority: 'medium',
            timestamp: '5 minutes ago'
          },
          {
            id: '3',
            title: 'Optimize database queries',
            agent: 'Backend Developer',
            status: 'completed',
            priority: 'medium',
            timestamp: '12 minutes ago',
            duration: 3600
          },
          {
            id: '4',
            title: 'Set up CI/CD pipeline',
            agent: 'DevOps Engineer',
            status: 'failed',
            priority: 'high',
            timestamp: '15 minutes ago'
          },
          {
            id: '5',
            title: 'Write unit tests for API endpoints',
            agent: 'Test Engineer',
            status: 'pending',
            priority: 'low',
            timestamp: '18 minutes ago'
          },
        ])
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
        const updated = prev.map(task =>
          task.id === data.payload.taskId
            ? { ...task, ...data.payload }
            : task
        )
        
        // If it's a new task, add it to the beginning
        if (!prev.find(task => task.id === data.payload.taskId) && data.payload.taskId) {
          updated.unshift(data.payload)
        }
        
        return updated.slice(0, 10) // Keep only latest 10 tasks
      })
    }
  }, [data])

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/20'
      case 'medium':
        return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/20'
      case 'low':
        return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/20'
      default:
        return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-700'
    }
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return ''
    const minutes = Math.floor(seconds / 60)
    return `${minutes}m`
  }

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center space-x-4">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/6"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/12"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Recent Tasks
          </h3>
          <button className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
            View all
          </button>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Latest task activities from all agents
        </p>
      </div>

      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {tasks.map((task) => (
          <div key={task.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-3 mb-2">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {task.title}
                  </h4>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    getStatusColor(task.status)
                  }`}>
                    {task.status.replace('_', ' ')}
                  </span>
                </div>
                
                <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                  <div className="flex items-center space-x-1">
                    <User className="w-3 h-3" />
                    <span>{task.agent}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>{task.timestamp}</span>
                  </div>
                  {task.duration && (
                    <div className="flex items-center space-x-1">
                      <span>Duration: {formatDuration(task.duration)}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center space-x-2 ml-4">
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  getPriorityColor(task.priority)
                }`}>
                  <Tag className="w-3 h-3 mr-1" />
                  {task.priority}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}