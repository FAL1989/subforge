'use client'

import { useState, useEffect } from 'react'
import { useSubForge } from '@/hooks/use-subforge'
import { LoadingSpinner } from '@/components/ui/loading-spinner'
import { 
  WorkflowSummary, 
  WorkflowData, 
  WorkflowStatus, 
  PhaseStatus,
  WorkflowPhases,
  WorkflowActivities 
} from '@/types/subforge'
import {
  Search,
  Filter,
  Activity,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Users,
  Play,
  Pause,
  RotateCcw,
  ArrowRight,
  Calendar,
  TrendingUp,
  Eye,
  X
} from 'lucide-react'

export default function WorkflowsPage() {
  const { 
    workflows, 
    currentWorkflow,
    loading, 
    error,
    fetchWorkflows,
    fetchWorkflow,
    fetchWorkflowPhases,
    fetchWorkflowActivities,
    subscribeToWorkflow,
    unsubscribeFromWorkflow,
    refreshData
  } = useSubForge()

  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null)
  const [workflowPhases, setWorkflowPhases] = useState<WorkflowPhases | null>(null)
  const [workflowActivities, setWorkflowActivities] = useState<WorkflowActivities | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<WorkflowStatus | 'all'>('all')
  const [detailsLoading, setDetailsLoading] = useState(false)

  useEffect(() => {
    refreshData()
  }, [refreshData])

  const handleWorkflowSelect = async (workflowId: string) => {
    setSelectedWorkflow(workflowId)
    setDetailsLoading(true)
    subscribeToWorkflow(workflowId)
    
    try {
      const [workflow, phases, activities] = await Promise.all([
        fetchWorkflow(workflowId),
        fetchWorkflowPhases(workflowId),
        fetchWorkflowActivities(workflowId)
      ])
      
      setWorkflowPhases(phases)
      setWorkflowActivities(activities)
    } catch (error) {
      console.error('Error fetching workflow details:', error)
    } finally {
      setDetailsLoading(false)
    }
  }

  const handleCloseDetails = () => {
    if (selectedWorkflow) {
      unsubscribeFromWorkflow(selectedWorkflow)
    }
    setSelectedWorkflow(null)
    setWorkflowPhases(null)
    setWorkflowActivities(null)
  }

  const filteredWorkflows = workflows.filter(workflow => {
    const matchesSearch = workflow.project_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         workflow.user_request.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'all' || workflow.status === statusFilter
    return matchesSearch && matchesStatus
  })

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
        return <Activity className="w-4 h-4 text-gray-400" />
    }
  }

  const getPhaseStatusIcon = (status: PhaseStatus) => {
    switch (status) {
      case PhaseStatus.COMPLETED:
        return <CheckCircle2 className="w-4 h-4 text-green-500" />
      case PhaseStatus.IN_PROGRESS:
        return <Play className="w-4 h-4 text-blue-500" />
      case PhaseStatus.FAILED:
        return <XCircle className="w-4 h-4 text-red-500" />
      case PhaseStatus.SKIPPED:
        return <ArrowRight className="w-4 h-4 text-gray-400" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  const formatDuration = (duration?: number) => {
    if (!duration) return 'N/A'
    const minutes = Math.floor(duration / 60)
    const seconds = Math.floor(duration % 60)
    return `${minutes}m ${seconds}s`
  }

  if (loading && workflows.length === 0) {
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
            SubForge Workflows
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor and analyze your SubForge workflow executions
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => refreshData()}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700 dark:text-red-300">{error}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workflows List */}
        <div className={`${selectedWorkflow ? 'lg:col-span-1' : 'lg:col-span-3'} transition-all duration-300`}>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
            {/* Search and Filter */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search workflows..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                  />
                </div>
                <div className="relative">
                  <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as WorkflowStatus | 'all')}
                    className="pl-10 pr-8 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white appearance-none"
                  >
                    <option value="all">All Status</option>
                    <option value={WorkflowStatus.ACTIVE}>Active</option>
                    <option value={WorkflowStatus.COMPLETED}>Completed</option>
                    <option value={WorkflowStatus.FAILED}>Failed</option>
                    <option value={WorkflowStatus.PAUSED}>Paused</option>
                    <option value={WorkflowStatus.CANCELLED}>Cancelled</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Workflows List */}
            <div className="p-6">
              {filteredWorkflows.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No workflows found</p>
                  <p className="text-xs mt-1">
                    {workflows.length === 0 
                      ? 'Start using SubForge to see workflows here' 
                      : 'Try adjusting your search or filter criteria'
                    }
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredWorkflows.map((workflow) => (
                    <div
                      key={workflow.project_id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedWorkflow === workflow.project_id
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600'
                      }`}
                      onClick={() => handleWorkflowSelect(workflow.project_id)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(workflow.status)}
                          <span className="font-medium text-gray-900 dark:text-white">
                            {workflow.project_id}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full">
                            {workflow.status}
                          </span>
                          <Eye className="w-4 h-4 text-gray-400" />
                        </div>
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
                      
                      {/* Metadata */}
                      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                        <div className="flex items-center space-x-3">
                          <div className="flex items-center space-x-1">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>{workflow.completed_phases}/{workflow.total_phases}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Users className="w-3 h-3" />
                            <span>{workflow.agent_count}</span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Calendar className="w-3 h-3" />
                          <span>{formatDateTime(workflow.updated_at || workflow.created_at)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Workflow Details */}
        {selectedWorkflow && (
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
              {/* Details Header */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Activity className="w-5 h-5 text-blue-500" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Workflow Details
                    </h3>
                  </div>
                  <button
                    onClick={handleCloseDetails}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {detailsLoading ? (
                <div className="p-6 flex items-center justify-center">
                  <LoadingSpinner size="lg" />
                </div>
              ) : (
                <div className="p-6 space-y-6">
                  {/* Workflow Info */}
                  {currentWorkflow && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                        Workflow Information
                      </h4>
                      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">Project ID</span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {currentWorkflow.project_id}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">Status</span>
                          <div className="flex items-center space-x-1">
                            {getStatusIcon(currentWorkflow.status)}
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              {currentWorkflow.status}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-start justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">Request</span>
                          <span className="text-sm text-gray-900 dark:text-white text-right max-w-xs">
                            {currentWorkflow.user_request}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Phase Timeline */}
                  {workflowPhases && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                        Phase Timeline ({workflowPhases.completed_phases}/{workflowPhases.total_phases} completed)
                      </h4>
                      <div className="space-y-3">
                        {workflowPhases.phases.map((phase, index) => (
                          <div key={phase.name} className="flex items-start space-x-3">
                            <div className="flex flex-col items-center">
                              {getPhaseStatusIcon(phase.status)}
                              {index < workflowPhases.phases.length - 1 && (
                                <div className="w-px h-8 bg-gray-200 dark:bg-gray-700 mt-2" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <h5 className="text-sm font-medium text-gray-900 dark:text-white">
                                  {phase.name}
                                </h5>
                                <span className="text-xs text-gray-500 dark:text-gray-400">
                                  {formatDuration(phase.duration)}
                                </span>
                              </div>
                              {phase.errors.length > 0 && (
                                <div className="mt-1 text-xs text-red-600 dark:text-red-400">
                                  {phase.errors.length} error(s)
                                </div>
                              )}
                              {phase.warnings.length > 0 && (
                                <div className="mt-1 text-xs text-yellow-600 dark:text-yellow-400">
                                  {phase.warnings.length} warning(s)
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recent Activities */}
                  {workflowActivities && workflowActivities.activities.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                        Recent Activities ({workflowActivities.total_activities} total)
                      </h4>
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {workflowActivities.activities.slice(0, 10).map((activity, index) => (
                          <div key={index} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {activity.agent_name}
                              </span>
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {formatDateTime(activity.timestamp)}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {activity.description || activity.activity_type}
                            </p>
                            {activity.duration && (
                              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Duration: {formatDuration(activity.duration)}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}