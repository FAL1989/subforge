'use client'

import { useEffect, useState } from 'react'
import { useSubForge } from '@/hooks/use-subforge'
import { WorkflowSummary, WorkflowStatus, PhaseStatus } from '@/types/subforge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { 
  CheckCircle2, 
  Circle, 
  AlertCircle, 
  Clock, 
  Play, 
  Pause, 
  XCircle,
  Users,
  Activity,
  TrendingUp,
  Eye
} from 'lucide-react'

interface WorkflowMonitorProps {
  className?: string
  maxItems?: number
}

export function WorkflowMonitor({ className = '', maxItems = 5 }: WorkflowMonitorProps) {
  const { 
    workflows, 
    loading, 
    error, 
    fetchWorkflows, 
    subscribeToWorkflow,
    refreshData 
  } = useSubForge()
  
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null)

  useEffect(() => {
    // Refresh workflows every 30 seconds
    const interval = setInterval(() => {
      fetchWorkflows()
    }, 30000)

    return () => clearInterval(interval)
  }, [fetchWorkflows])

  const getStatusIcon = (status: WorkflowStatus) => {
    switch (status) {
      case WorkflowStatus.ACTIVE:
        return <Play className="w-4 h-4 text-blue-500" />
      case WorkflowStatus.COMPLETED:
        return <CheckCircle2 className="w-4 h-4 text-green-500" />
      case WorkflowStatus.FAILED:
        return <XCircle className="w-4 h-4 text-red-500" />
      case WorkflowStatus.PAUSED:
        return <Pause className="w-4 h-4 text-yellow-500" />
      case WorkflowStatus.CANCELLED:
        return <XCircle className="w-4 h-4 text-gray-500" />
      default:
        return <Circle className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: WorkflowStatus) => {
    switch (status) {
      case WorkflowStatus.ACTIVE:
        return 'text-blue-600 bg-blue-50'
      case WorkflowStatus.COMPLETED:
        return 'text-green-600 bg-green-50'
      case WorkflowStatus.FAILED:
        return 'text-red-600 bg-red-50'
      case WorkflowStatus.PAUSED:
        return 'text-yellow-600 bg-yellow-50'
      case WorkflowStatus.CANCELLED:
        return 'text-gray-600 bg-gray-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const formatDuration = (startDate?: string, endDate?: string) => {
    if (!startDate) return 'N/A'
    
    const start = new Date(startDate)
    const end = endDate ? new Date(endDate) : new Date()
    const diffMs = end.getTime() - start.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMins / 60)
    
    if (diffHours > 0) {
      return `${diffHours}h ${diffMins % 60}m`
    }
    return `${diffMins}m`
  }

  const handleWorkflowClick = (workflowId: string) => {
    setSelectedWorkflow(workflowId)
    subscribeToWorkflow(workflowId)
  }

  const activeWorkflows = workflows
    .filter(w => w.status === WorkflowStatus.ACTIVE)
    .slice(0, maxItems)
  
  const recentWorkflows = workflows
    .sort((a, b) => {
      const dateA = new Date(a.updated_at || a.created_at || 0)
      const dateB = new Date(b.updated_at || b.created_at || 0)
      return dateB.getTime() - dateA.getTime()
    })
    .slice(0, maxItems)

  if (loading && workflows.length === 0) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 ${className}`}>
        <div className="flex items-center justify-center h-32">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Activity className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Workflow Monitor
            </h3>
          </div>
          <button
            onClick={refreshData}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <TrendingUp className="w-4 h-4" />
          </button>
        </div>
        
        {error && (
          <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-red-500" />
              <span className="text-sm text-red-700 dark:text-red-300">{error}</span>
            </div>
          </div>
        )}
      </div>

      {/* Active Workflows Section */}
      {activeWorkflows.length > 0 && (
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-900 dark:text-white">
              Active Workflows ({activeWorkflows.length})
            </h4>
          </div>
          
          <div className="space-y-3">
            {activeWorkflows.map((workflow) => (
              <div
                key={workflow.project_id}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-300 dark:hover:border-blue-600 transition-colors cursor-pointer"
                onClick={() => handleWorkflowClick(workflow.project_id)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(workflow.status)}
                    <span className="font-medium text-gray-900 dark:text-white">
                      {workflow.project_id}
                    </span>
                    {workflow.current_phase && (
                      <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">
                        {workflow.current_phase}
                      </span>
                    )}
                  </div>
                  <Eye className="w-4 h-4 text-gray-400" />
                </div>
                
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                  {workflow.user_request}
                </p>
                
                {/* Progress Bar */}
                <div className="mb-3">
                  <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                    <span>Progress</span>
                    <span>{Math.round(workflow.progress_percentage)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${workflow.progress_percentage}%` }}
                    />
                  </div>
                </div>
                
                {/* Metrics */}
                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-1">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>{workflow.completed_phases}/{workflow.total_phases} phases</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Users className="w-3 h-3" />
                      <span>{workflow.agent_count} agents</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>{formatDuration(workflow.created_at, workflow.updated_at)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Workflows Section */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
            Recent Workflows
          </h4>
          <button
            onClick={fetchWorkflows}
            className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
          >
            View All
          </button>
        </div>
        
        {recentWorkflows.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No workflows found</p>
            <p className="text-xs mt-1">Workflows will appear here when SubForge is active</p>
          </div>
        ) : (
          <div className="space-y-2">
            {recentWorkflows.map((workflow) => (
              <div
                key={workflow.project_id}
                className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors"
                onClick={() => handleWorkflowClick(workflow.project_id)}
              >
                <div className="flex items-center space-x-3 min-w-0 flex-1">
                  {getStatusIcon(workflow.status)}
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {workflow.project_id}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      {workflow.user_request}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(workflow.status)}`}>
                    {workflow.status}
                  </span>
                  <div className="text-xs text-gray-500 dark:text-gray-400 text-right">
                    <div>{Math.round(workflow.progress_percentage)}%</div>
                    <div className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{formatDuration(workflow.created_at, workflow.updated_at)}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}