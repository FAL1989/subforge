'use client'

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'
import { websocketConfig } from '@/config/websocket'

interface WebSocketMessage {
  type: string
  payload: any
  timestamp: string
}

interface WebSocketContextType {
  socket: Socket | null
  isConnected: boolean
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error'
  data: WebSocketMessage | null
  error: string | null
  sendMessage: (type: string, payload: any) => void
  reconnect: () => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

interface WebSocketProviderProps {
  children: ReactNode
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error'>('disconnected')
  const [data, setData] = useState<WebSocketMessage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reconnectAttempt, setReconnectAttempt] = useState(0)

  const connectSocket = useCallback(() => {
    setConnectionStatus('connecting')
    setError(null)
    
    const newSocket = io(websocketConfig.url, {
      transports: websocketConfig.transports,
      autoConnect: websocketConfig.autoConnect,
      reconnection: websocketConfig.reconnection,
      reconnectionAttempts: websocketConfig.reconnectionAttempts,
      reconnectionDelay: websocketConfig.reconnectionDelay,
      reconnectionDelayMax: websocketConfig.reconnectionDelayMax,
      randomizationFactor: websocketConfig.randomizationFactor,
      timeout: websocketConfig.timeout,
    })

    newSocket.on('connect', () => {
      console.log('Connected to WebSocket server')
      setIsConnected(true)
      setConnectionStatus('connected')
      setError(null)
      setReconnectAttempt(0)
    })

    newSocket.on('disconnect', (reason) => {
      console.log('Disconnected from WebSocket server:', reason)
      setIsConnected(false)
      setConnectionStatus('disconnected')
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, reconnect manually
        newSocket.connect()
      }
    })

    newSocket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error)
      setError(error.message || 'Connection failed')
      setConnectionStatus('error')
      setIsConnected(false)
    })

    newSocket.on('reconnect', (attemptNumber) => {
      console.log(`Reconnected to WebSocket server (attempt ${attemptNumber})`)
      setIsConnected(true)
      setConnectionStatus('connected')
      setError(null)
    })

    newSocket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`Attempting to reconnect to WebSocket server (attempt ${attemptNumber})`)
      setConnectionStatus('reconnecting')
      setReconnectAttempt(attemptNumber)
    })

    newSocket.on('reconnect_error', (error) => {
      console.error('WebSocket reconnection error:', error)
      setError(error.message || 'Reconnection failed')
      setConnectionStatus('error')
    })

    newSocket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed after maximum attempts')
      setError('Unable to reconnect to server')
      setConnectionStatus('error')
      setIsConnected(false)
    })

    // Event handlers for backend events
    newSocket.on('agent_status_update', (payload) => {
      setData({
        type: 'agent_status_update',
        payload,
        timestamp: new Date().toISOString(),
      })
    })

    newSocket.on('task_update', (payload) => {
      setData({
        type: 'task_update',
        payload,
        timestamp: new Date().toISOString(),
      })
    })

    newSocket.on('system_metrics_update', (payload) => {
      setData({
        type: 'system_metrics_update',
        payload,
        timestamp: new Date().toISOString(),
      })
    })

    newSocket.on('workflow_event', (payload) => {
      setData({
        type: 'workflow_event',
        payload,
        timestamp: new Date().toISOString(),
      })
    })

    // Additional event handlers for legacy compatibility
    newSocket.on('dashboard_update', (payload) => {
      setData({
        type: 'dashboard_update',
        payload,
        timestamp: new Date().toISOString(),
      })
    })

    newSocket.on('system_alert', (payload) => {
      setData({
        type: 'system_alert',
        payload,
        timestamp: new Date().toISOString(),
      })
    })

    setSocket(newSocket)
    return newSocket
  }, [])

  const reconnect = useCallback(() => {
    if (socket) {
      socket.disconnect()
      setSocket(null)
    }
    const newSocket = connectSocket()
    setSocket(newSocket)
  }, [socket, connectSocket])

  useEffect(() => {
    const newSocket = connectSocket()
    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [connectSocket])

  const sendMessage = (type: string, payload: any) => {
    if (socket && isConnected) {
      socket.emit(type, payload)
    } else {
      console.warn('Cannot send message: WebSocket not connected')
    }
  }

  return (
    <WebSocketContext.Provider 
      value={{ 
        socket, 
        isConnected, 
        connectionStatus, 
        data, 
        error, 
        sendMessage, 
        reconnect 
      }}
    >
      {children}
    </WebSocketContext.Provider>
  )
}

export const useWebSocket = () => {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}