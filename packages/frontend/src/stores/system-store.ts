import { create } from 'zustand'
import type { SystemMetrics } from '@/types'

interface SystemStore {
  metrics: SystemMetrics
  isConnected: boolean
  setMetrics: (metrics: SystemMetrics) => void
  setIsConnected: (isConnected: boolean) => void
}

const defaultMetrics: SystemMetrics = {
  cpu: { usage: 0, temperature: 0 },
  gpu: { usage: 0, temperature: 0, memory: 0 },
  ram: { used: 0, total: 0, percentage: 0 },
  disk: { used: 0, total: 0, percentage: 0 },
  battery: { percentage: 0, charging: false },
  network: { rx: 0, tx: 0 },
  model: { name: 'Loading...', tokenSpeed: 0, contextUsage: 0, latency: 0 },
}

export const useSystemStore = create<SystemStore>((set) => ({
  metrics: defaultMetrics,
  isConnected: false,
  setMetrics: (metrics) => set({ metrics, isConnected: true }),
  setIsConnected: (isConnected) => set({ isConnected }),
}))
