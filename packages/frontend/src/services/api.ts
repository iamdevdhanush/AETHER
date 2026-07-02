const API_BASE = '/api'

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`)
  }
  return response.json()
}

export const api = {
  system: {
    metrics: () => request<Record<string, unknown>>('/system/metrics'),
    processes: () => request<Record<string, unknown>[]>('/system/processes'),
  },
  chat: {
    send: (message: string, conversationId?: string) =>
      request<{ response: string }>('/chat', {
        method: 'POST',
        body: JSON.stringify({ message, conversationId }),
      }),
  },
  files: {
    list: (path: string) => request<Record<string, unknown>[]>(`/files?path=${encodeURIComponent(path)}`),
    read: (path: string) => request<{ content: string }>(`/files/read?path=${encodeURIComponent(path)}`),
  },
  automation: {
    launchApp: (name: string) => request<{ success: boolean }>('/automation/launch', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),
    closeApp: (name: string) => request<{ success: boolean }>('/automation/close', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),
  },
  plugins: {
    list: () => request<Record<string, unknown>[]>('/plugins'),
    toggle: (id: string, enabled: boolean) => request<{ success: boolean }>(`/plugins/${id}/toggle`, {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    }),
  },
  memory: {
    search: (query: string) => request<Record<string, unknown>[]>(`/memory/search?q=${encodeURIComponent(query)}`),
  },
}
