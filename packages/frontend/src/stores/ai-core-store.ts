import { create } from 'zustand'
import type { AICoreState } from '@/types'

interface AICoreStore {
  state: AICoreState
  amplitude: number
  isListening: boolean
  isSpeaking: boolean
  setState: (state: AICoreState) => void
  setAmplitude: (amplitude: number) => void
  setIsListening: (isListening: boolean) => void
  setIsSpeaking: (isSpeaking: boolean) => void
}

export const useAICoreStore = create<AICoreStore>((set) => ({
  state: 'idle',
  amplitude: 0,
  isListening: false,
  isSpeaking: false,
  setState: (state) => set({ state }),
  setAmplitude: (amplitude) => set({ amplitude }),
  setIsListening: (isListening) => set({ isListening }),
  setIsSpeaking: (isSpeaking) => set({ isSpeaking }),
}))
