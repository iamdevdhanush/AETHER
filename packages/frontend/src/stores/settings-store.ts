import { create } from 'zustand'
import type { AppSettings } from '@/types'

interface SettingsStore {
  settings: AppSettings
  isOpen: boolean
  updateSettings: (partial: Partial<AppSettings>) => void
  toggleSettings: () => void
  setOpen: (open: boolean) => void
}

const defaultSettings: AppSettings = {
  voice: {
    wakeWord: true,
    continuousListening: false,
    pushToTalk: true,
    voice: 'default',
    speed: 1.0,
  },
  models: {
    provider: 'ollama',
    model: 'llama3.2',
    baseUrl: 'http://localhost:11434',
  },
  memory: {
    enabled: true,
    vectorSearch: true,
  },
  appearance: {
    theme: 'dark',
    accentColor: '#A8D8FF',
    reducedMotion: false,
  },
  permissions: {
    executeCommands: false,
    fileOperations: false,
    systemControl: false,
  },
  hotkeys: {
    toggleAether: 'Alt+Space',
    pushToTalk: 'Alt+V',
    screenshot: 'Alt+S',
  },
  system: {
    startOnBoot: false,
    minimizeToTray: true,
  },
}

export const useSettingsStore = create<SettingsStore>((set) => ({
  settings: defaultSettings,
  isOpen: false,
  updateSettings: (partial) =>
    set((state) => ({
      settings: { ...state.settings, ...partial },
    })),
  toggleSettings: () => set((state) => ({ isOpen: !state.isOpen })),
  setOpen: (open) => set({ isOpen: open }),
}))
