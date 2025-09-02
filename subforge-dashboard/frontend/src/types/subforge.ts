export enum WorkflowStatus {
  ACTIVE = 'active',
  COMPLETED = 'completed',
  FAILED = 'failed',
  PAUSED = 'paused',
  CANCELLED = 'cancelled'
}

export enum PhaseStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  SKIPPED = 'skipped'
}

export interface PhaseResult {
  phase: string
  status: PhaseStatus
  duration?: number
  start_time?: string
  end_time?: string
  outputs: Record<string, any>
  errors: string[]
  warnings: string[]
  metadata: Record<string, any>
}

export interface ProjectProfile {
  languages: string[]
  frameworks: string[]
  architecture?: string
  complexity_score?: number
  team_size_estimate?: number
  file_count?: number
  lines_of_code?: number
  patterns: string[]
  dependencies: Record<string, any>
}

export interface AgentTemplate {
  name: string
  role: string
  specialization: string
  domain: string
  description?: string
  tools: string[]
  model: string
  priority: number
  execution_instructions?: string
  context_requirements: string[]
}

export interface Task {
  id: string
  title: string
  description?: string
  status: string
  priority: number
  phase?: string
  assigned_agent?: string
  created_at?: string
  updated_at?: string
  completed_at?: string
  duration?: number
  dependencies: string[]
  tags: string[]
  metadata: Record<string, any>
}

export interface AgentActivity {
  agent_id: string
  agent_name: string
  activity_type: string
  description?: string
  timestamp: string
  duration?: number
  status: string
  task_id?: string
  workflow_id?: string
  metadata: Record<string, any>
}

export interface WorkflowData {
  project_id: string
  user_request: string
  project_path: string
  communication_dir: string
  status: WorkflowStatus
  created_at?: string
  updated_at?: string
  completed_at?: string
  phase_results: Record<string, PhaseResult>
  project_profile?: ProjectProfile
  recommended_agents: AgentTemplate[]
  deployed_agents: AgentTemplate[]
  tasks: Task[]
  agent_activities: AgentActivity[]
  total_phases: number
  completed_phases: number
  failed_phases: number
  progress_percentage: number
  metadata: Record<string, any>
  configuration: Record<string, any>
}

export interface WorkflowSummary {
  project_id: string
  user_request: string
  status: WorkflowStatus
  progress_percentage: number
  created_at?: string
  updated_at?: string
  current_phase?: string
  total_phases: number
  completed_phases: number
  failed_phases: number
  agent_count: number
}

export interface SubForgeMetrics {
  total_workflows: number
  active_workflows: number
  completed_workflows: number
  failed_workflows: number
  average_completion_time?: number
  success_rate: number
  most_common_phases: Array<Record<string, any>>
  agent_utilization: Record<string, number>
  recent_activities: AgentActivity[]
}

export interface SubForgeStatus {
  service_status: 'active' | 'inactive'
  monitoring_enabled: boolean
  file_watching_enabled: boolean
  total_workflows: number
  active_workflows: number
  subforge_directory: string
  subforge_directory_exists: boolean
  last_scan?: string
  configuration: {
    scan_interval: number
    max_workflows: number
    cleanup_after_days: number
    enable_real_time_monitoring: boolean
  }
}

// WebSocket message types for SubForge events
export interface SubForgeWebSocketMessage {
  type: string
  data: any
  timestamp?: string
}

export interface SubForgeInitialData {
  workflows: WorkflowData[]
  metrics: SubForgeMetrics
  status: string
}

export interface WorkflowPhases {
  workflow_id: string
  total_phases: number
  completed_phases: number
  failed_phases: number
  current_phase?: string
  phases: Array<{
    name: string
    status: PhaseStatus
    duration?: number
    start_time?: string
    end_time?: string
    outputs: Record<string, any>
    errors: string[]
    warnings: string[]
  }>
}

export interface WorkflowTasks {
  workflow_id: string
  total_tasks: number
  tasks: Task[]
}

export interface WorkflowActivities {
  workflow_id: string
  total_activities: number
  activities: AgentActivity[]
}