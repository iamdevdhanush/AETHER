import { useEffect } from 'react'
import { useSystemStore } from '@/stores/system-store'
import { wsService } from '@/services/websocket'

export function useSystemMetrics() {
  const metrics = useSystemStore((state) => state.metrics)
  const isConnected = useSystemStore((state) => state.isConnected)

  useEffect(() => {
    wsService.connect()
    return () => wsService.disconnect()
  }, [])

  return { metrics, isConnected }
}
