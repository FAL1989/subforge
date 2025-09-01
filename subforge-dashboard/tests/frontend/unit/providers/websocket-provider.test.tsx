import React from 'react'
import { render, screen, act, waitFor } from '@testing-library/react'
import { WebSocketProvider, useWebSocket } from '@/components/providers/websocket-provider'

// Create a test component that uses the WebSocket hook
const TestComponent = () => {
  const { data, isConnected, error, send } = useWebSocket()
  
  return (
    <div>
      <div data-testid="connection-status">
        {isConnected ? 'Connected' : 'Disconnected'}
      </div>
      <div data-testid="data">
        {data ? JSON.stringify(data) : 'No data'}
      </div>
      <div data-testid="error">
        {error ? error.message : 'No error'}
      </div>
      <button 
        data-testid="send-button" 
        onClick={() => send({ type: 'test', payload: 'hello' })}
      >
        Send Message
      </button>
    </div>
  )
}

// Mock WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  readyState: WebSocket.OPEN,
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
}

const mockWebSocketConstructor = jest.fn(() => mockWebSocket)
global.WebSocket = mockWebSocketConstructor as any

describe('WebSocketProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockWebSocket.readyState = WebSocket.OPEN
  })

  afterEach(() => {
    jest.clearAllTimers()
  })

  it('provides initial state correctly', () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    expect(screen.getByTestId('connection-status')).toHaveTextContent('Disconnected')
    expect(screen.getByTestId('data')).toHaveTextContent('No data')
    expect(screen.getByTestId('error')).toHaveTextContent('No error')
  })

  it('establishes WebSocket connection on mount', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    expect(mockWebSocketConstructor).toHaveBeenCalledWith(
      expect.stringContaining('ws://localhost:8000')
    )
  })

  it('handles WebSocket connection open', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    // Simulate WebSocket open event
    const openHandler = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'open'
    )?.[1]

    act(() => {
      openHandler?.({ type: 'open' })
    })

    await waitFor(() => {
      expect(screen.getByTestId('connection-status')).toHaveTextContent('Connected')
    })
  })

  it('handles WebSocket message reception', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )?.[1]

    const testMessage = { type: 'agent_update', payload: { id: '1', status: 'active' } }

    act(() => {
      messageHandler?.({
        type: 'message',
        data: JSON.stringify(testMessage)
      })
    })

    await waitFor(() => {
      expect(screen.getByTestId('data')).toHaveTextContent(JSON.stringify(testMessage))
    })
  })

  it('handles WebSocket error', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    const errorHandler = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'error'
    )?.[1]

    const testError = { message: 'Connection failed' }

    act(() => {
      errorHandler?.(testError)
    })

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Connection failed')
    })
  })

  it('handles WebSocket close', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    // First open the connection
    const openHandler = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'open'
    )?.[1]

    act(() => {
      openHandler?.({ type: 'open' })
    })

    await waitFor(() => {
      expect(screen.getByTestId('connection-status')).toHaveTextContent('Connected')
    })

    // Then close it
    const closeHandler = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'close'
    )?.[1]

    mockWebSocket.readyState = WebSocket.CLOSED

    act(() => {
      closeHandler?.({ type: 'close' })
    })

    await waitFor(() => {
      expect(screen.getByTestId('connection-status')).toHaveTextContent('Disconnected')
    })
  })

  it('sends messages through WebSocket', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    // Open connection first
    const openHandler = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'open'
    )?.[1]

    act(() => {
      openHandler?.({ type: 'open' })
    })

    await waitFor(() => {
      expect(screen.getByTestId('connection-status')).toHaveTextContent('Connected')
    })

    // Send message
    const sendButton = screen.getByTestId('send-button')

    act(() => {
      sendButton.click()
    })

    expect(mockWebSocket.send).toHaveBeenCalledWith(
      JSON.stringify({ type: 'test', payload: 'hello' })
    )
  })

  it('does not send messages when disconnected', async () => {
    mockWebSocket.readyState = WebSocket.CLOSED

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    const sendButton = screen.getByTestId('send-button')

    act(() => {
      sendButton.click()
    })

    expect(mockWebSocket.send).not.toHaveBeenCalled()
  })

  it('handles malformed JSON messages', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )?.[1]

    act(() => {
      messageHandler?.({
        type: 'message',
        data: 'invalid json{'
      })
    })

    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to parse WebSocket message:',
      expect.any(Error)
    )

    // Should not crash or update data
    expect(screen.getByTestId('data')).toHaveTextContent('No data')

    consoleSpy.mockRestore()
  })

  it('cleans up WebSocket on unmount', () => {
    const { unmount } = render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    unmount()

    expect(mockWebSocket.close).toHaveBeenCalled()
  })

  it('attempts reconnection after close with delay', async () => {
    jest.useFakeTimers()

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    // Simulate close
    const closeHandler = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'close'
    )?.[1]

    act(() => {
      closeHandler?.({ type: 'close', code: 1000, wasClean: true })
    })

    // Fast-forward time to trigger reconnection
    act(() => {
      jest.advanceTimersByTime(5000)
    })

    // Should attempt to create new connection
    expect(mockWebSocketConstructor).toHaveBeenCalledTimes(2)

    jest.useRealTimers()
  })

  it('limits reconnection attempts', async () => {
    jest.useFakeTimers()

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    const closeHandler = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'close'
    )?.[1]

    // Simulate multiple closes
    for (let i = 0; i < 10; i++) {
      act(() => {
        closeHandler?.({ type: 'close', code: 1006, wasClean: false })
      })

      act(() => {
        jest.advanceTimersByTime(5000)
      })
    }

    // Should limit reconnection attempts
    expect(mockWebSocketConstructor.mock.calls.length).toBeLessThan(10)

    jest.useRealTimers()
  })

  it('handles connection timeout', async () => {
    jest.useFakeTimers()

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    // Don't trigger open event, let it timeout
    act(() => {
      jest.advanceTimersByTime(10000) // Connection timeout
    })

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent(/timeout|failed/i)
    })

    jest.useRealTimers()
  })

  it('uses correct WebSocket URL from environment', () => {
    const originalEnv = process.env.NEXT_PUBLIC_WS_URL
    process.env.NEXT_PUBLIC_WS_URL = 'ws://custom-host:9000/ws'

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    expect(mockWebSocketConstructor).toHaveBeenCalledWith(
      'ws://custom-host:9000/ws'
    )

    process.env.NEXT_PUBLIC_WS_URL = originalEnv
  })

  it('handles send error gracefully', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})
    mockWebSocket.send.mockImplementation(() => {
      throw new Error('Send failed')
    })

    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    // Open connection
    const openHandler = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'open'
    )?.[1]

    act(() => {
      openHandler?.({ type: 'open' })
    })

    const sendButton = screen.getByTestId('send-button')

    act(() => {
      sendButton.click()
    })

    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to send WebSocket message:',
      expect.any(Error)
    )

    consoleSpy.mockRestore()
  })

  it('provides hook outside provider throws error', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      render(<TestComponent />)
    }).toThrow('useWebSocket must be used within a WebSocketProvider')

    consoleSpy.mockRestore()
  })

  it('handles rapid message updates', async () => {
    render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'message'
    )?.[1]

    // Send multiple rapid messages
    const messages = [
      { type: 'update1', data: 'first' },
      { type: 'update2', data: 'second' },
      { type: 'update3', data: 'third' }
    ]

    messages.forEach((message, index) => {
      act(() => {
        messageHandler?.({
          type: 'message',
          data: JSON.stringify(message)
        })
      })
    })

    // Should show the last message
    await waitFor(() => {
      expect(screen.getByTestId('data')).toHaveTextContent(JSON.stringify(messages[2]))
    })
  })

  it('maintains connection state across re-renders', async () => {
    const { rerender } = render(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    // Open connection
    const openHandler = mockWebSocket.addEventListener.mock.calls.find(
      call => call[0] === 'open'
    )?.[1]

    act(() => {
      openHandler?.({ type: 'open' })
    })

    await waitFor(() => {
      expect(screen.getByTestId('connection-status')).toHaveTextContent('Connected')
    })

    // Re-render
    rerender(
      <WebSocketProvider>
        <TestComponent />
      </WebSocketProvider>
    )

    // Should maintain connection state
    expect(screen.getByTestId('connection-status')).toHaveTextContent('Connected')
  })
})