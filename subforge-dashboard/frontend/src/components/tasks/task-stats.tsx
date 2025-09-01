import { CheckCircle, Clock, AlertTriangle, PlayCircle } from 'lucide-react'
import type { Task } from '@/app/tasks/page'

interface TaskStatsProps {
  tasks: Task[]
}

export function TaskStats({ tasks }: TaskStatsProps) {
  const stats = {
    total: tasks.length,
    todo: tasks.filter(task => task.status === 'todo').length,
    inProgress: tasks.filter(task => task.status === 'in_progress').length,
    review: tasks.filter(task => task.status === 'review').length,
    done: tasks.filter(task => task.status === 'done').length,
    highPriority: tasks.filter(task => task.priority === 'high').length,
    overdue: tasks.filter(task => 
      task.dueDate && new Date(task.dueDate) < new Date()
    ).length,
  }

  const completionRate = stats.total > 0 ? Math.round((stats.done / stats.total) * 100) : 0

  const statCards = [
    {
      title: 'Total Tasks',
      value: stats.total,
      icon: Clock,
      color: 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/20',
      bgColor: 'bg-blue-50 dark:bg-blue-900/10'
    },
    {
      title: 'In Progress',
      value: stats.inProgress,
      icon: PlayCircle,
      color: 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/20',
      bgColor: 'bg-yellow-50 dark:bg-yellow-900/10'
    },
    {
      title: 'Completed',
      value: stats.done,
      icon: CheckCircle,
      color: 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/20',
      bgColor: 'bg-green-50 dark:bg-green-900/10'
    },
    {
      title: 'High Priority',
      value: stats.highPriority,
      icon: AlertTriangle,
      color: 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/20',
      bgColor: 'bg-red-50 dark:bg-red-900/10'
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {statCards.map((stat, index) => (
        <div
          key={index}
          className={`${stat.bgColor} rounded-lg p-6 border border-gray-200 dark:border-gray-700`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {stat.title}
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {stat.value}
              </p>
            </div>
            <div className={`p-3 rounded-lg ${stat.color}`}>
              <stat.icon className="w-6 h-6" />
            </div>
          </div>
          
          {stat.title === 'Completed' && (
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-gray-400">Progress</span>
                <span className="text-gray-900 dark:text-white">{completionRate}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${completionRate}%` }}
                />
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}