'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { io, Socket } from 'socket.io-client'

interface WebSocketMessage {
  type: string
  payload: any
  timestamp: string
}

interface WebSocketContextType {
  socket: Socket | null
  isConnected: boolean
  data: WebSocketMessage | null
  sendMessage: (type: string, payload: any) => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

interface WebSocketProviderProps {
  children: ReactNode
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [data, setData] = useState<WebSocketMessage | null>(null)

  useEffect(() => {
    const newSocket = io('http://localhost:8000', {
      transports: ['websocket', 'polling'],
      autoConnect: true,
    })

    newSocket.on('connect', () => {
      console.log('Connected to WebSocket server')
      setIsConnected(true)
    })

    newSocket.on('disconnect', () => {
      console.log('Disconnected from WebSocket server')
      setIsConnected(false)
    })

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

    newSocket.on('metrics_update', (payload) => {
      setData({
        type: 'metrics_update',
        payload,
        timestamp: new Date().toISOString(),
      })
    })

    newSocket.on('dashboard_update', (payload) => {
      setData({
        type: 'dashboard_update',
        payload,
        timestamp: new Date().toISOString(),
      })
    })

    newSocket.on('workflow_update', (payload) => {
      setData({
        type: 'workflow_update',
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

    return () => {
      newSocket.close()
    }
  }, [])

  const sendMessage = (type: string, payload: any) => {
    if (socket && isConnected) {
      socket.emit(type, payload)
    }
  }

  return (
    <WebSocketContext.Provider value={{ socket, isConnected, data, sendMessage }}>
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