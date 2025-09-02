/**
 * WebSocket connection test utility
 * Use this to verify WebSocket connectivity in development
 */

export interface WebSocketTestResult {
  connected: boolean
  latency?: number
  events_received: string[]
  errors: string[]
  timestamp: string
}

export class WebSocketTester {
  private results: WebSocketTestResult[] = []
  
  async testConnection(url: string = 'http://localhost:8000', timeout: number = 10000): Promise<WebSocketTestResult> {
    const startTime = Date.now()
    const result: WebSocketTestResult = {
      connected: false,
      events_received: [],
      errors: [],
      timestamp: new Date().toISOString()
    }
    
    try {
      // Dynamic import to avoid SSR issues
      const { io } = await import('socket.io-client')
      
      const socket = io(url, {
        transports: ['websocket', 'polling'],
        autoConnect: true,
        timeout: timeout
      })
      
      return new Promise((resolve) => {
        const cleanup = () => {
          socket.disconnect()
          resolve(result)
        }
        
        // Set timeout
        const timeoutId = setTimeout(() => {
          result.errors.push(`Connection timeout after ${timeout}ms`)
          cleanup()
        }, timeout)
        
        socket.on('connect', () => {
          result.connected = true
          result.latency = Date.now() - startTime
          result.events_received.push('connect')
          console.log('✅ WebSocket connected successfully')
          
          // Test ping
          socket.emit('ping', { test: true })
        })
        
        socket.on('pong', (data) => {
          result.events_received.push('pong')
          console.log('🏓 Received pong:', data)
          clearTimeout(timeoutId)
          setTimeout(cleanup, 1000) // Give time for other events
        })
        
        socket.on('connect_error', (error) => {
          result.errors.push(`Connection error: ${error.message}`)
          console.error('❌ WebSocket connection error:', error)
          clearTimeout(timeoutId)
          cleanup()
        })
        
        socket.on('disconnect', (reason) => {
          result.events_received.push('disconnect')
          console.log('🔌 WebSocket disconnected:', reason)
        })
        
        // Listen for expected events
        const events = ['agent_status_update', 'task_update', 'system_metrics_update', 'workflow_event']
        events.forEach(event => {
          socket.on(event, (data) => {
            result.events_received.push(event)
            console.log(`📨 Received ${event}:`, data)
          })
        })
      })
      
    } catch (error) {
      result.errors.push(`Test error: ${error instanceof Error ? error.message : String(error)}`)
      console.error('❌ WebSocket test error:', error)
    }
    
    this.results.push(result)
    return result
  }
  
  getResults(): WebSocketTestResult[] {
    return this.results
  }
  
  getLatestResult(): WebSocketTestResult | null {
    return this.results.length > 0 ? this.results[this.results.length - 1] : null
  }
  
  clearResults(): void {
    this.results = []
  }
}

// Singleton instance
export const websocketTester = new WebSocketTester()

// Convenience function for quick testing
export async function testWebSocketConnection(url?: string): Promise<WebSocketTestResult> {
  return websocketTester.testConnection(url)
}