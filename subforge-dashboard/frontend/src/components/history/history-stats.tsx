import { Activity, CheckCircle, XCircle, Clock, TrendingUp } from 'lucide-react'
import type { WorkflowEvent } from '@/app/history/page'

interface HistoryStatsProps {
  events: WorkflowEvent[]
}

export function HistoryStats({ events }: HistoryStatsProps) {
  const stats = {
    total: events.length,
    successful: events.filter(e => e.status === 'success').length,
    failed: events.filter(e => e.status === 'error').length,
    warnings: events.filter(e => e.status === 'warning').length,
    tasksCompleted: events.filter(e => e.type === 'task_completed').length,
    averageDuration: events
      .filter(e => e.duration)
      .reduce((acc, e) => acc + (e.duration || 0), 0) / 
      events.filter(e => e.duration).length || 0,
  }

  const successRate = stats.total > 0 ? Math.round((stats.successful / stats.total) * 100) : 0

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`
    return `${Math.round(seconds / 3600 * 10) / 10}h`
  }

  const statCards = [
    {
      title: 'Total Events',
      value: stats.total,
      icon: Activity,
      color: 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/20',
      bgColor: 'bg-blue-50 dark:bg-blue-900/10'
    },
    {
      title: 'Success Rate',
      value: `${successRate}%`,
      icon: TrendingUp,
      color: 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/20',
      bgColor: 'bg-green-50 dark:bg-green-900/10'
    },
    {
      title: 'Tasks Completed',
      value: stats.tasksCompleted,
      icon: CheckCircle,
      color: 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/20',
      bgColor: 'bg-green-50 dark:bg-green-900/10'
    },
    {
      title: 'Avg Duration',
      value: stats.averageDuration > 0 ? formatDuration(stats.averageDuration) : 'N/A',
      icon: Clock,
      color: 'text-purple-600 bg-purple-100 dark:text-purple-400 dark:bg-purple-900/20',
      bgColor: 'bg-purple-50 dark:bg-purple-900/10'
    },
  ]

  // Event distribution for the last 24 hours
  const last24Hours = events.filter(e => {
    const eventTime = new Date(e.timestamp)
    const now = new Date()
    return now.getTime() - eventTime.getTime() < 24 * 60 * 60 * 1000
  })

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
          
          {/* Additional info for specific cards */}
          {stat.title === 'Total Events' && last24Hours.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
              <p className="text-xs text-gray-600 dark:text-gray-400">
                {last24Hours.length} events in last 24h
              </p>
            </div>
          )}
          
          {stat.title === 'Success Rate' && (
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-gray-400">Success</span>
                <span className="text-gray-900 dark:text-white">{successRate}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${successRate}%` }}
                />
              </div>
            </div>
          )}
          
          {stat.title === 'Tasks Completed' && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
              <div className="flex justify-between text-xs">
                <span className="text-green-600 dark:text-green-400">
                  ✓ {stats.successful}
                </span>
                {stats.failed > 0 && (
                  <span className="text-red-600 dark:text-red-400">
                    ✗ {stats.failed}
                  </span>
                )}
                {stats.warnings > 0 && (
                  <span className="text-yellow-600 dark:text-yellow-400">
                    ⚠ {stats.warnings}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}