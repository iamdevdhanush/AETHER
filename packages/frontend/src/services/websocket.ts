import { useSystemStore } from '@/stores/system-store'
import { useChatStore } from '@/stores/chat-store'
import { useAICoreStore } from '@/stores/ai-core-store'
import type { SystemMetrics } from '@/types'

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private url: string

  constructor() {
    this.url = `ws://${window.location.hostname}:8000/ws`
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('[AETHER] WebSocket connected')
        useSystemStore.getState().setIsConnected(true)
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (e) {
          console.error('[AETHER] Failed to parse message:', e)
        }
      }

      this.ws.onclose = () => {
        console.log('[AETHER] WebSocket disconnected')
        useSystemStore.getState().setIsConnected(false)
        this.scheduleReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('[AETHER] WebSocket error:', error)
      }
    } catch (error) {
      console.error('[AETHER] Failed to connect WebSocket:', error)
      this.scheduleReconnect()
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.ws?.close()
    this.ws = null
  }

  send(data: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  private handleMessage(data: Record<string, unknown>) {
    const { type, payload } = data

    switch (type) {
      case 'system_metrics':
        useSystemStore.getState().setMetrics(payload as SystemMetrics)
        break
      case 'ai_state':
        useAICoreStore.getState().setState(payload as any)
        break
      case 'stream_chunk':
        useChatStore.getState().updateLastMessage(payload as string)
        break
      case 'execution_step':
        const step = payload as any
        useChatStore.getState().updateExecutionStep(step.id, step.status, step.details)
        break
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, 3000)
  }
}

export const wsService = new WebSocketService()
