export type AICoreState = 'idle' | 'listening' | 'thinking' | 'executing' | 'speaking' | 'error' | 'success'

export interface SystemMetrics {
  cpu: { usage: number; temperature: number }
  gpu: { usage: number; temperature: number; memory: number }
  ram: { used: number; total: number; percentage: number }
  disk: { used: number; total: number; percentage: number }
  battery: { percentage: number; charging: boolean }
  network: { rx: number; tx: number }
  model: { name: string; tokenSpeed: number; contextUsage: number; latency: number }
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  metadata?: Record<string, unknown>
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: number
  updatedAt: number
}

export interface Plugin {
  id: string
  name: string
  description: string
  version: string
  enabled: boolean
  type: 'system' | 'user'
}

export interface Memory {
  id: string
  content: string
  type: 'conversation' | 'preference' | 'project' | 'note'
  timestamp: number
  embeddings?: number[]
}

export interface AppSettings {
  voice: {
    wakeWord: boolean
    continuousListening: boolean
    pushToTalk: boolean
    voice: string
    speed: number
  }
  models: {
    provider: 'ollama' | 'openai'
    model: string
    baseUrl: string
  }
  memory: {
    enabled: boolean
    vectorSearch: boolean
  }
  appearance: {
    theme: 'dark'
    accentColor: string
    reducedMotion: boolean
  }
  permissions: {
    executeCommands: boolean
    fileOperations: boolean
    systemControl: boolean
  }
  hotkeys: {
    toggleAether: string
    pushToTalk: string
    screenshot: string
  }
  system: {
    startOnBoot: boolean
    minimizeToTray: boolean
  }
}

export interface ExecutionStep {
  id: string
  label: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  details?: string
}
