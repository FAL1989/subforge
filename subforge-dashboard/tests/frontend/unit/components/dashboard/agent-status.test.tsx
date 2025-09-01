import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import { AgentStatus } from '@/components/dashboard/agent-status'
import { useWebSocket } from '@/hooks/use-websocket'

// Mock the WebSocket hook
jest.mock('@/hooks/use-websocket')
const mockUseWebSocket = useWebSocket as jest.MockedFunction<typeof useWebSocket>

// Mock the utils
jest.mock('@/lib/utils', () => ({
  getStatusColor: (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'busy':
        return 'bg-blue-100 text-blue-800'
      case 'idle':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-red-100 text-red-800'
    }
  },
}))

// Mock the LoadingSpinner component
jest.mock('@/components/ui/loading-spinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner">Loading...</div>,
}))

// Mock fetch globally
const mockFetch = jest.fn()
global.fetch = mockFetch

describe('AgentStatus Component', () => {
  beforeEach(() => {
    mockUseWebSocket.mockReturnValue({
      data: null,
      isConnected: true,
      error: null,
      send: jest.fn(),
    })
    mockFetch.mockClear()
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('renders loading state initially', () => {
    mockUseWebSocket.mockReturnValue({
      data: null,
      isConnected: false,
      error: null,
      send: jest.fn(),
    })

    render(<AgentStatus />)
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('renders agent status title and description', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'))

    render(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('Agent Status')).toBeInTheDocument()
      expect(screen.getByText('Real-time monitoring of all active agents')).toBeInTheDocument()
    })
  })

  it('fetches and displays agent data successfully', async () => {
    const mockAgents = [
      {
        id: '1',
        name: 'Test Agent',
        type: 'Development',
        status: 'active',
        lastActive: '2 minutes ago',
        tasksCompleted: 10,
        currentTask: 'Test task'
      }
    ]

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ agents: mockAgents })
    })

    render(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('Test Agent')).toBeInTheDocument()
      expect(screen.getByText('Development • 2 minutes ago')).toBeInTheDocument()
      expect(screen.getByText('10 tasks')).toBeInTheDocument()
      expect(screen.getByText('Test task')).toBeInTheDocument()
      expect(screen.getByText('active')).toBeInTheDocument()
    })
  })

  it('falls back to mock data when API fails', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'))

    render(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('Frontend Developer')).toBeInTheDocument()
      expect(screen.getByText('Backend Developer')).toBeInTheDocument()
      expect(screen.getByText('Data Scientist')).toBeInTheDocument()
      expect(screen.getByText('DevOps Engineer')).toBeInTheDocument()
      expect(screen.getByText('Code Reviewer')).toBeInTheDocument()
      expect(screen.getByText('Test Engineer')).toBeInTheDocument()
    })
  })

  it('displays correct status colors for different agent statuses', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'))

    render(<AgentStatus />)

    await waitFor(() => {
      // Check for status indicators
      const activeStatus = screen.getAllByText('active')
      const busyStatus = screen.getAllByText('busy') 
      const idleStatus = screen.getAllByText('idle')
      const errorStatus = screen.getAllByText('error')

      expect(activeStatus.length).toBeGreaterThan(0)
      expect(busyStatus.length).toBeGreaterThan(0)
      expect(idleStatus.length).toBeGreaterThan(0)
      expect(errorStatus.length).toBeGreaterThan(0)
    })
  })

  it('shows current task when available', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'))

    render(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('Building React components')).toBeInTheDocument()
      expect(screen.getByText('API endpoint optimization')).toBeInTheDocument()
      expect(screen.getByText('Docker container updates')).toBeInTheDocument()
      expect(screen.getByText('Security audit review')).toBeInTheDocument()
    })
  })

  it('does not show current task when not available', async () => {
    const mockAgents = [
      {
        id: '1',
        name: 'Idle Agent',
        type: 'Development', 
        status: 'idle',
        lastActive: '15 minutes ago',
        tasksCompleted: 5
        // No currentTask
      }
    ]

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ agents: mockAgents })
    })

    render(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('Idle Agent')).toBeInTheDocument()
      expect(screen.getByText('5 tasks')).toBeInTheDocument()
      
      // Should not have a current task displayed
      const taskElements = screen.queryByText(/current.*task/i)
      expect(taskElements).not.toBeInTheDocument()
    })
  })

  it('updates agent status via WebSocket', async () => {
    // Start with mock data
    mockFetch.mockRejectedValueOnce(new Error('API Error'))

    const { rerender } = render(<AgentStatus />)

    // Wait for initial render
    await waitFor(() => {
      expect(screen.getByText('Frontend Developer')).toBeInTheDocument()
    })

    // Mock WebSocket update
    mockUseWebSocket.mockReturnValue({
      data: {
        type: 'agent_status_update',
        payload: {
          agentId: '1',
          status: 'busy',
          currentTask: 'Updated task',
          tasksCompleted: 25
        }
      },
      isConnected: true,
      error: null,
      send: jest.fn(),
    })

    rerender(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('Updated task')).toBeInTheDocument()
      expect(screen.getByText('25 tasks')).toBeInTheDocument()
    })
  })

  it('ignores WebSocket data of wrong type', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'))

    const { rerender } = render(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('Frontend Developer')).toBeInTheDocument()
    })

    // Mock WebSocket data with wrong type
    mockUseWebSocket.mockReturnValue({
      data: {
        type: 'other_update',
        payload: {
          agentId: '1',
          status: 'busy'
        }
      },
      isConnected: true,
      error: null,
      send: jest.fn(),
    })

    rerender(<AgentStatus />)

    // Should still show original data
    await waitFor(() => {
      expect(screen.getByText('23 tasks')).toBeInTheDocument() // Original value
    })
  })

  it('handles empty agent list', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ agents: [] })
    })

    render(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('Agent Status')).toBeInTheDocument()
      // Should not have any agent cards
      expect(screen.queryByText('tasks')).not.toBeInTheDocument()
    })
  })

  it('applies hover effects to agent cards', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'))

    render(<AgentStatus />)

    await waitFor(() => {
      const agentCards = screen.getAllByRole('generic').filter(el => 
        el.className.includes('hover:bg-gray-50')
      )
      expect(agentCards.length).toBeGreaterThan(0)
    })
  })

  it('displays correct task completion counts', async () => {
    const mockAgents = [
      {
        id: '1',
        name: 'Agent 1',
        type: 'Test',
        status: 'active',
        lastActive: '1 min ago',
        tasksCompleted: 0
      },
      {
        id: '2', 
        name: 'Agent 2',
        type: 'Test',
        status: 'active',
        lastActive: '1 min ago',
        tasksCompleted: 100
      }
    ]

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ agents: mockAgents })
    })

    render(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('0 tasks')).toBeInTheDocument()
      expect(screen.getByText('100 tasks')).toBeInTheDocument()
    })
  })

  it('handles network error gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    render(<AgentStatus />)

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to fetch agents:', expect.any(Error))
      // Should still render mock data
      expect(screen.getByText('Frontend Developer')).toBeInTheDocument()
    })

    consoleSpy.mockRestore()
  })

  it('updates multiple agents via WebSocket', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'))

    const { rerender } = render(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('Frontend Developer')).toBeInTheDocument()
    })

    // Update first agent
    mockUseWebSocket.mockReturnValue({
      data: {
        type: 'agent_status_update',
        payload: {
          agentId: '1',
          status: 'busy',
          tasksCompleted: 30
        }
      },
      isConnected: true,
      error: null,
      send: jest.fn(),
    })

    rerender(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('30 tasks')).toBeInTheDocument()
    })

    // Update second agent
    mockUseWebSocket.mockReturnValue({
      data: {
        type: 'agent_status_update',
        payload: {
          agentId: '2',
          currentTask: 'New backend task'
        }
      },
      isConnected: true,
      error: null,
      send: jest.fn(),
    })

    rerender(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('New backend task')).toBeInTheDocument()
      // First agent should still have updated value
      expect(screen.getByText('30 tasks')).toBeInTheDocument()
    })
  })

  it('handles malformed WebSocket data', async () => {
    mockFetch.mockRejectedValueOnce(new Error('API Error'))

    const { rerender } = render(<AgentStatus />)

    await waitFor(() => {
      expect(screen.getByText('Frontend Developer')).toBeInTheDocument()
    })

    // Mock malformed WebSocket data
    mockUseWebSocket.mockReturnValue({
      data: {
        type: 'agent_status_update'
        // Missing payload
      },
      isConnected: true,
      error: null,
      send: jest.fn(),
    })

    // Should not crash
    expect(() => rerender(<AgentStatus />)).not.toThrow()
  })
})