import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Info, 
  User, 
  Clock, 
  Play,
  Square
} from 'lucide-react'
import { formatTime } from '@/lib/utils'
import type { WorkflowEvent } from '@/app/history/page'

interface WorkflowTimelineProps {
  events: WorkflowEvent[]
}

export function WorkflowTimeline({ events }: WorkflowTimelineProps) {
  const getEventIcon = (type: WorkflowEvent['type'], status: WorkflowEvent['status']) => {
    switch (type) {
      case 'task_completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'task_failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'task_created':
        return <Square className="w-5 h-5 text-blue-500" />
      case 'agent_assigned':
        return <User className="w-5 h-5 text-purple-500" />
      case 'workflow_started':
        return <Play className="w-5 h-5 text-blue-500" />
      case 'workflow_completed':
        return status === 'success' 
          ? <CheckCircle className="w-5 h-5 text-green-500" />
          : <AlertTriangle className="w-5 h-5 text-yellow-500" />
      default:
        return <Info className="w-5 h-5 text-gray-500" />
    }
  }

  const getEventColor = (status: WorkflowEvent['status']) => {
    switch (status) {
      case 'success':
        return 'border-green-500 bg-green-50 dark:bg-green-900/20'
      case 'error':
        return 'border-red-500 bg-red-50 dark:bg-red-900/20'
      case 'warning':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
      default:
        return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
    }
  }

  const formatEventTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (diffInSeconds < 60) return 'Just now'
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`
    
    return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString()
  }

  const getTypeLabel = (type: WorkflowEvent['type']) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  if (events.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
        <Info className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No Events Found
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          No workflow events match your current filters.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Event Timeline
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          {events.length} events found
        </p>
      </div>

      <div className="p-6">
        <div className="flow-root">
          <ul className="-mb-8">
            {events.map((event, eventIdx) => (
              <li key={event.id}>
                <div className="relative pb-8">
                  {eventIdx !== events.length - 1 ? (
                    <span
                      className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200 dark:bg-gray-600"
                      aria-hidden="true"
                    />
                  ) : null}
                  <div className="relative flex space-x-3">
                    <div>
                      <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white dark:ring-gray-800 ${
                        getEventColor(event.status).replace('bg-', 'bg-')
                      } border-2`}>
                        {getEventIcon(event.type, event.status)}
                      </span>
                    </div>
                    <div className={`min-w-0 flex-1 p-4 rounded-lg border-l-4 ${getEventColor(event.status)}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                              {getTypeLabel(event.type)}
                            </span>
                            {event.agent && (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                                <User className="w-3 h-3 mr-1" />
                                {event.agent}
                              </span>
                            )}
                            {event.duration && (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400">
                                <Clock className="w-3 h-3 mr-1" />
                                {formatTime(event.duration)}
                              </span>
                            )}
                          </div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            {event.title}
                          </h4>
                          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                            {event.description}
                          </p>
                          {event.task && (
                            <p className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                              Task: {event.task}
                            </p>
                          )}
                        </div>
                        <div className="ml-4 flex-shrink-0 text-right">
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {formatEventTime(event.timestamp)}
                          </p>
                        </div>
                      </div>

                      {/* Metadata */}
                      {event.metadata && Object.keys(event.metadata).length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(event.metadata).map(([key, value]) => (
                              key !== 'taskId' && key !== 'agentId' && key !== 'workflowId' && (
                                <span
                                  key={key}
                                  className="inline-flex items-center text-xs text-gray-600 dark:text-gray-400"
                                >
                                  <span className="font-medium">{key}:</span>
                                  <span className="ml-1">{String(value)}</span>
                                </span>
                              )
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}