'use client'

import { useState } from 'react'
import { useWebSocket } from '@/components/providers/websocket-provider'
import { testWebSocketConnection, WebSocketTestResult } from '@/utils/websocket-test'

/**
 * WebSocket Debug Component
 * Add this component to any page during development to debug WebSocket connections
 * Remove in production builds
 */
export function WebSocketDebug() {
  const { 
    isConnected, 
    connectionStatus, 
    data, 
    error, 
    sendMessage, 
    reconnect 
  } = useWebSocket()
  
  const [testResult, setTestResult] = useState<WebSocketTestResult | null>(null)
  const [isVisible, setIsVisible] = useState(false)
  
  if (process.env.NODE_ENV === 'production') {
    return null
  }
  
  const handleTestConnection = async () => {
    const result = await testWebSocketConnection()
    setTestResult(result)
  }
  
  const handleSendTestMessage = () => {
    sendMessage('ping', { test: true, timestamp: new Date().toISOString() })
  }
  
  if (!isVisible) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setIsVisible(true)}
          className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium shadow-lg hover:bg-blue-700 transition-colors"
        >
          WebSocket Debug
        </button>
      </div>
    )
  }
  
  return (
    <div className="fixed bottom-4 right-4 z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-4 max-w-md max-h-96 overflow-auto">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold">WebSocket Debug</h3>
        <button
          onClick={() => setIsVisible(false)}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        >
          ✕
        </button>
      </div>
      
      <div className="space-y-3 text-xs">
        {/* Connection Status */}
        <div>
          <div className="font-medium mb-1">Connection Status</div>
          <div className={`px-2 py-1 rounded text-white text-center ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}>
            {connectionStatus.toUpperCase()}
          </div>
        </div>
        
        {/* Error Display */}
        {error && (
          <div>
            <div className="font-medium mb-1 text-red-600">Error</div>
            <div className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 p-2 rounded text-xs">
              {error}
            </div>
          </div>
        )}
        
        {/* Latest Data */}
        {data && (
          <div>
            <div className="font-medium mb-1">Latest Event</div>
            <div className="bg-gray-50 dark:bg-gray-900 p-2 rounded">
              <div className="font-mono text-xs">
                <div><strong>Type:</strong> {data.type}</div>
                <div><strong>Time:</strong> {new Date(data.timestamp).toLocaleTimeString()}</div>
                <details className="mt-1">
                  <summary className="cursor-pointer">Payload</summary>
                  <pre className="mt-1 whitespace-pre-wrap break-words">
                    {JSON.stringify(data.payload, null, 2)}
                  </pre>
                </details>
              </div>
            </div>
          </div>
        )}
        
        {/* Controls */}
        <div className="flex gap-2">
          <button
            onClick={handleTestConnection}
            className="flex-1 px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
          >
            Test Connection
          </button>
          <button
            onClick={handleSendTestMessage}
            disabled={!isConnected}
            className="flex-1 px-2 py-1 bg-green-500 text-white rounded text-xs hover:bg-green-600 disabled:bg-gray-400"
          >
            Send Ping
          </button>
          <button
            onClick={reconnect}
            className="flex-1 px-2 py-1 bg-orange-500 text-white rounded text-xs hover:bg-orange-600"
          >
            Reconnect
          </button>
        </div>
        
        {/* Test Results */}
        {testResult && (
          <div>
            <div className="font-medium mb-1">Test Results</div>
            <div className="bg-gray-50 dark:bg-gray-900 p-2 rounded">
              <div className={`font-medium ${testResult.connected ? 'text-green-600' : 'text-red-600'}`}>
                {testResult.connected ? '✅ Connected' : '❌ Failed'}
              </div>
              {testResult.latency && (
                <div>Latency: {testResult.latency}ms</div>
              )}
              {testResult.events_received.length > 0 && (
                <div>Events: {testResult.events_received.join(', ')}</div>
              )}
              {testResult.errors.length > 0 && (
                <div className="text-red-600 mt-1">
                  Errors: {testResult.errors.join(', ')}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}