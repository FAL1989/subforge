export interface WebSocketConfig {
  url: string
  transports: ('websocket' | 'polling')[]
  autoConnect: boolean
  reconnection: boolean
  reconnectionAttempts: number
  reconnectionDelay: number
  reconnectionDelayMax: number
  randomizationFactor: number
  timeout: number
}

export const websocketConfig: WebSocketConfig = {
  url: process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'http://localhost:8000',
  transports: ['websocket', 'polling'],
  autoConnect: true,
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  randomizationFactor: 0.5,
  timeout: 20000,
}

export default websocketConfig