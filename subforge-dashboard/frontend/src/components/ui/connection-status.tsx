'use client'

import { useWebSocket } from '@/components/providers/websocket-provider'
import { cn } from '@/lib/utils'

interface ConnectionStatusProps {
  className?: string
  showText?: boolean
}

export function ConnectionStatus({ className, showText = true }: ConnectionStatusProps) {
  const { connectionStatus, isConnected, error, reconnect } = useWebSocket()

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'bg-green-500'
      case 'connecting':
      case 'reconnecting':
        return 'bg-yellow-500 animate-pulse'
      case 'disconnected':
        return 'bg-gray-500'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected'
      case 'connecting':
        return 'Connecting...'
      case 'reconnecting':
        return 'Reconnecting...'
      case 'disconnected':
        return 'Disconnected'
      case 'error':
        return 'Connection Error'
      default:
        return 'Unknown'
    }
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className={cn('w-3 h-3 rounded-full', getStatusColor())} />
      {showText && (
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{getStatusText()}</span>
          {connectionStatus === 'error' && (
            <button
              onClick={reconnect}
              className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Retry
            </button>
          )}
        </div>
      )}
      {error && (
        <span className="text-xs text-red-500 max-w-xs truncate" title={error}>
          {error}
        </span>
      )}
    </div>
  )
}