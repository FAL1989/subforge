'use client'

import { useState, useEffect, useCallback } from 'react'
import { useWebSocket } from './use-websocket'
import {
  WorkflowData,
  WorkflowSummary,
  SubForgeMetrics,
  SubForgeStatus,
  WorkflowPhases,
  WorkflowTasks,
  WorkflowActivities,
  SubForgeWebSocketMessage,
  SubForgeInitialData,
  AgentActivity
} from '@/types/subforge'

const API_BASE_URL = 'http://localhost:8000/api/subforge'

interface UseSubForgeState {
  workflows: WorkflowSummary[]
  currentWorkflow: WorkflowData | null
  metrics: SubForgeMetrics | null
  status: SubForgeStatus | null
  recentActivities: AgentActivity[]
  loading: boolean
  error: string | null
}

interface UseSubForgeActions {
  fetchWorkflows: () => Promise<void>
  fetchWorkflow: (workflowId: string) => Promise<WorkflowData | null>
  fetchMetrics: () => Promise<void>
  fetchStatus: () => Promise<void>
  fetchWorkflowPhases: (workflowId: string) => Promise<WorkflowPhases | null>
  fetchWorkflowTasks: (workflowId: string) => Promise<WorkflowTasks | null>
  fetchWorkflowActivities: (workflowId: string) => Promise<WorkflowActivities | null>
  startIntegration: () => Promise<void>
  stopIntegration: () => Promise<void>
  scanWorkflows: (forceRescan?: boolean) => Promise<void>
  subscribeToWorkflow: (workflowId: string) => void
  unsubscribeFromWorkflow: (workflowId: string) => void
  refreshData: () => Promise<void>
}

export type UseSubForgeReturn = UseSubForgeState & UseSubForgeActions

export function useSubForge(): UseSubForgeReturn {
  const [state, setState] = useState<UseSubForgeState>({
    workflows: [],
    currentWorkflow: null,
    metrics: null,
    status: null,
    recentActivities: [],
    loading: false,
    error: null
  })

  const { isConnected, data, sendMessage } = useWebSocket()

  // API utility function
  const apiCall = useCallback(async <T>(endpoint: string, options?: RequestInit): Promise<T | null> => {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers
        },
        ...options
      })

      if (!response.ok) {
        throw new Error(`API call failed: ${response.status} ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error(`API call to ${endpoint} failed:`, error)
      setState(prev => ({ ...prev, error: error instanceof Error ? error.message : 'Unknown error' }))
      return null
    }
  }, [])

  // Fetch workflows
  const fetchWorkflows = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))
    
    const workflows = await apiCall<WorkflowSummary[]>('/workflows')
    if (workflows) {
      setState(prev => ({ ...prev, workflows, loading: false }))
    } else {
      setState(prev => ({ ...prev, loading: false }))
    }
  }, [apiCall])

  // Fetch specific workflow
  const fetchWorkflow = useCallback(async (workflowId: string): Promise<WorkflowData | null> => {
    setState(prev => ({ ...prev, loading: true, error: null }))
    
    const workflow = await apiCall<WorkflowData>(`/workflow/${workflowId}`)
    if (workflow) {
      setState(prev => ({ 
        ...prev, 
        currentWorkflow: workflow,
        recentActivities: workflow.agent_activities.slice(-10),
        loading: false 
      }))
      return workflow
    } else {
      setState(prev => ({ ...prev, loading: false }))
      return null
    }
  }, [apiCall])

  // Fetch metrics
  const fetchMetrics = useCallback(async () => {
    const metrics = await apiCall<SubForgeMetrics>('/metrics')
    if (metrics) {
      setState(prev => ({ ...prev, metrics }))
    }
  }, [apiCall])

  // Fetch status
  const fetchStatus = useCallback(async () => {
    const status = await apiCall<SubForgeStatus>('/status')
    if (status) {
      setState(prev => ({ ...prev, status }))
    }
  }, [apiCall])

  // Fetch workflow phases
  const fetchWorkflowPhases = useCallback(async (workflowId: string): Promise<WorkflowPhases | null> => {
    return await apiCall<WorkflowPhases>(`/workflow/${workflowId}/phases`)
  }, [apiCall])

  // Fetch workflow tasks
  const fetchWorkflowTasks = useCallback(async (workflowId: string): Promise<WorkflowTasks | null> => {
    return await apiCall<WorkflowTasks>(`/workflow/${workflowId}/tasks`)
  }, [apiCall])

  // Fetch workflow activities
  const fetchWorkflowActivities = useCallback(async (workflowId: string): Promise<WorkflowActivities | null> => {
    return await apiCall<WorkflowActivities>(`/workflow/${workflowId}/activities`)
  }, [apiCall])

  // Start integration
  const startIntegration = useCallback(async () => {
    await apiCall('/start', { method: 'POST' })
    await fetchStatus()
  }, [apiCall, fetchStatus])

  // Stop integration
  const stopIntegration = useCallback(async () => {
    await apiCall('/stop', { method: 'POST' })
    await fetchStatus()
  }, [apiCall, fetchStatus])

  // Scan workflows
  const scanWorkflows = useCallback(async (forceRescan = false) => {
    await apiCall('/scan', {
      method: 'POST',
      body: JSON.stringify({ 
        force_rescan: forceRescan, 
        include_inactive: true 
      })
    })
  }, [apiCall])

  // WebSocket subscription management
  const subscribeToWorkflow = useCallback((workflowId: string) => {
    if (isConnected) {
      sendMessage('subscribe_workflow', { workflow_id: workflowId })
    }
  }, [isConnected, sendMessage])

  const unsubscribeFromWorkflow = useCallback((workflowId: string) => {
    if (isConnected) {
      sendMessage('unsubscribe_workflow', { workflow_id: workflowId })
    }
  }, [isConnected, sendMessage])

  // Refresh all data
  const refreshData = useCallback(async () => {
    await Promise.all([
      fetchWorkflows(),
      fetchMetrics(),
      fetchStatus()
    ])
  }, [fetchWorkflows, fetchMetrics, fetchStatus])

  // Handle WebSocket messages
  useEffect(() => {
    if (!data) return

    const message = data as SubForgeWebSocketMessage

    switch (message.type) {
      case 'subforge_initial_data':
        const initialData = message.data as SubForgeInitialData
        setState(prev => ({
          ...prev,
          workflows: initialData.workflows.map(w => ({
            project_id: w.project_id,
            user_request: w.user_request,
            status: w.status,
            progress_percentage: w.progress_percentage,
            created_at: w.created_at,
            updated_at: w.updated_at,
            current_phase: w.phase_results ? Object.keys(w.phase_results).find(phase => 
              w.phase_results[phase].status === 'in_progress'
            ) : undefined,
            total_phases: w.total_phases,
            completed_phases: w.completed_phases,
            failed_phases: w.failed_phases,
            agent_count: w.deployed_agents.length
          })),
          metrics: initialData.metrics
        }))
        break

      case 'workflow_event':
      case 'subforge_workflow_update':
        // Workflow updated, refresh workflows list
        fetchWorkflows()
        break

      case 'subforge_scan_complete':
        // Scan completed, refresh data
        setState(prev => ({ ...prev, error: null }))
        fetchWorkflows()
        break

      case 'subforge_scan_error':
        setState(prev => ({ 
          ...prev, 
          error: `Scan failed: ${message.data.error}` 
        }))
        break

      case 'workflow_subscribed':
        if (message.data.workflow) {
          setState(prev => ({ 
            ...prev, 
            currentWorkflow: message.data.workflow,
            recentActivities: message.data.workflow.agent_activities?.slice(-10) || []
          }))
        }
        break

      case 'workflow_unsubscribed':
        // Handle unsubscription if needed
        break

      case 'agent_activity_update':
        // Update recent activities
        setState(prev => ({
          ...prev,
          recentActivities: [message.data, ...prev.recentActivities].slice(0, 10)
        }))
        break

      default:
        console.debug('Unhandled SubForge WebSocket message:', message.type)
    }
  }, [data, fetchWorkflows])

  // Initial data fetch
  useEffect(() => {
    refreshData()
  }, [refreshData])

  // Auto-refresh when WebSocket connects
  useEffect(() => {
    if (isConnected) {
      refreshData()
    }
  }, [isConnected, refreshData])

  return {
    ...state,
    fetchWorkflows,
    fetchWorkflow,
    fetchMetrics,
    fetchStatus,
    fetchWorkflowPhases,
    fetchWorkflowTasks,
    fetchWorkflowActivities,
    startIntegration,
    stopIntegration,
    scanWorkflows,
    subscribeToWorkflow,
    unsubscribeFromWorkflow,
    refreshData
  }
}