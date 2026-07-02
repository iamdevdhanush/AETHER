import { create } from 'zustand'
import type { Message, Conversation, ExecutionStep } from '@/types'

interface ChatStore {
  conversations: Conversation[]
  activeConversationId: string | null
  isStreaming: boolean
  executionSteps: ExecutionStep[]
  
  setActiveConversation: (id: string | null) => void
  addMessage: (message: Message) => void
  updateLastMessage: (content: string) => void
  setIsStreaming: (isStreaming: boolean) => void
  setExecutionSteps: (steps: ExecutionStep[]) => void
  updateExecutionStep: (id: string, status: ExecutionStep['status'], details?: string) => void
  createConversation: () => string
}

export const useChatStore = create<ChatStore>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  isStreaming: false,
  executionSteps: [],

  setActiveConversation: (id) => set({ activeConversationId: id }),

  addMessage: (message) => {
    const { conversations, activeConversationId } = get()
    if (!activeConversationId) return

    set({
      conversations: conversations.map((conv) =>
        conv.id === activeConversationId
          ? { ...conv, messages: [...conv.messages, message], updatedAt: Date.now() }
          : conv
      ),
    })
  },

  updateLastMessage: (content) => {
    const { conversations, activeConversationId } = get()
    if (!activeConversationId) return

    set({
      conversations: conversations.map((conv) => {
        if (conv.id !== activeConversationId) return conv
        const messages = [...conv.messages]
        const lastMessage = messages[messages.length - 1]
        if (lastMessage && lastMessage.role === 'assistant') {
          messages[messages.length - 1] = { ...lastMessage, content }
        }
        return { ...conv, messages, updatedAt: Date.now() }
      }),
    })
  },

  setIsStreaming: (isStreaming) => set({ isStreaming }),

  setExecutionSteps: (steps) => set({ executionSteps: steps }),

  updateExecutionStep: (id, status, details) => {
    set((state) => ({
      executionSteps: state.executionSteps.map((step) =>
        step.id === id ? { ...step, status, details } : step
      ),
    }))
  },

  createConversation: () => {
    const id = crypto.randomUUID()
    const conversation: Conversation = {
      id,
      title: 'New Conversation',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    }
    set((state) => ({
      conversations: [conversation, ...state.conversations],
      activeConversationId: id,
    }))
    return id
  },
}))
