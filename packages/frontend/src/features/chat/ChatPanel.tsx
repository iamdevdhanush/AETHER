import { useEffect, useRef, type FormEvent } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useChatStore } from '@/stores/chat-store'
import { useAICoreStore } from '@/stores/ai-core-store'
import { GlassPanel } from '@/components/glass/GlassPanel'

function MessageBubble({ content, role, isStreaming }: { content: string; role: 'user' | 'assistant' | 'system'; isStreaming?: boolean }) {
  const isUser = role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div
        className={`max-w-[80%] px-5 py-3 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-aether-accent/10 text-aether-primary'
            : 'glass text-aether-primary'
        }`}
      >
        {content}
        {isStreaming && (
          <motion.span
            animate={{ opacity: [1, 0] }}
            transition={{ duration: 0.8, repeat: Infinity }}
            className="inline-block w-2 h-4 bg-aether-accent ml-1 rounded-full"
          />
        )}
      </div>
    </motion.div>
  )
}

function ExecutionSteps() {
  const executionSteps = useChatStore((state) => state.executionSteps)

  if (executionSteps.length === 0) return null

  return (
    <GlassPanel padding="sm" className="mb-4">
      <div className="space-y-2">
        {executionSteps.map((step) => (
          <div key={step.id} className="flex items-center gap-3 px-2 py-1">
            {step.status === 'running' && (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-3 h-3 border-2 border-aether-accent/30 border-t-aether-accent rounded-full shrink-0"
              />
            )}
            {step.status === 'completed' && (
              <svg className="w-3 h-3 text-aether-success shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <path d="M20 6L9 17L4 12" />
              </svg>
            )}
            {step.status === 'failed' && (
              <svg className="w-3 h-3 text-aether-danger shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <path d="M18 6L6 18M6 6L18 18" />
              </svg>
            )}
            {step.status === 'pending' && (
              <div className="w-3 h-3 border border-white/10 rounded-full shrink-0" />
            )}
            <span className={`text-xs ${
              step.status === 'completed' ? 'text-aether-success' :
              step.status === 'failed' ? 'text-aether-danger' :
              step.status === 'running' ? 'text-aether-accent' :
              'text-aether-secondary/50'
            }`}>
              {step.label}
              {step.details && <span className="text-aether-secondary/40 ml-1">— {step.details}</span>}
            </span>
          </div>
        ))}
      </div>
    </GlassPanel>
  )
}

export function ChatPanel() {
  const activeConversationId = useChatStore((state) => state.activeConversationId)
  const conversations = useChatStore((state) => state.conversations)
  const isStreaming = useChatStore((state) => state.isStreaming)
  const addMessage = useChatStore((state) => state.addMessage)
  const createConversation = useChatStore((state) => state.createConversation)
  const setState = useAICoreStore((state) => state.setState)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const activeConversation = conversations.find((c) => c.id === activeConversationId)
  const messages = activeConversation?.messages ?? []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const input = inputRef.current
    if (!input || !input.value.trim() || isStreaming) return

    const message = input.value.trim()
    input.value = ''

    if (!activeConversationId) {
      createConversation()
    }

    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: message,
      timestamp: Date.now(),
    })

    setState('thinking')
  }

  return (
    <div className="w-full h-full flex flex-col">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="max-w-3xl mx-auto">
          <ExecutionSteps />
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <p className="text-aether-secondary/40 text-sm">Start a conversation with AETHER</p>
            </div>
          ) : (
            messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                content={msg.content}
                role={msg.role}
                isStreaming={isStreaming && msg === messages[messages.length - 1] && msg.role === 'assistant'}
              />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="px-8 pb-6">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div className="glass rounded-full px-6 py-3 flex items-center gap-4">
            <input
              ref={inputRef}
              type="text"
              placeholder="Message AETHER..."
              className="flex-1 bg-transparent text-sm text-aether-primary placeholder:text-aether-secondary/40 outline-none"
            />
            <div className="flex items-center gap-2">
              <motion.button
                type="button"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="w-8 h-8 rounded-full glass flex items-center justify-center text-aether-secondary hover:text-aether-primary transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              </motion.button>
              <motion.button
                type="submit"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="w-8 h-8 rounded-full bg-aether-accent/20 flex items-center justify-center text-aether-accent hover:bg-aether-accent/30 transition-colors"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 2L11 13" />
                  <path d="M22 2L15 22L11 13L2 9L22 2Z" />
                </svg>
              </motion.button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
