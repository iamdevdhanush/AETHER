import { useState, useEffect, useRef, type FormEvent } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AICore } from '@/components/core/AICore'
import { GlassPanel } from '@/components/glass/GlassPanel'
import { GlassCard } from '@/components/glass/GlassCard'
import { GlassInput } from '@/components/glass/GlassInput'
import { useAICoreStore } from '@/stores/ai-core-store'
import { useSystemStore } from '@/stores/system-store'
import { useChatStore } from '@/stores/chat-store'

function Waveform() {
  const { state } = useAICoreStore()
  if (state !== 'listening' && state !== 'speaking') return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex items-center justify-center gap-[3px] h-8 my-4"
    >
      {Array.from({ length: 48 }).map((_, i) => (
        <motion.div
          key={i}
          className="w-[2px] bg-aether-accent/60 rounded-full"
          animate={{
            height: [4, Math.random() * 24 + 4, 4],
          }}
          transition={{
            duration: 0.8 + Math.random() * 0.4,
            repeat: Infinity,
            delay: i * 0.05,
            ease: 'easeInOut',
          }}
        />
      ))}
    </motion.div>
  )
}

function Greeting() {
  const [greeting, setGreeting] = useState('Good Evening')

  useEffect(() => {
    const hour = new Date().getHours()
    if (hour < 12) setGreeting('Good Morning')
    else if (hour < 17) setGreeting('Good Afternoon')
    else setGreeting('Good Evening')
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="text-center mt-8"
    >
      <h1 className="text-3xl font-thin tracking-wide text-aether-primary">
        {greeting}, Sir.
      </h1>
      <p className="text-sm text-aether-secondary mt-2 font-medium tracking-wide">
        How may I assist you today?
      </p>
    </motion.div>
  )
}

function HealthCard({ label, value, sub, color = 'text-aether-accent' }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-xs text-aether-secondary">{label}</span>
      <div className="text-right">
        <span className={`text-sm font-medium ${color}`}>{value}</span>
        {sub && <span className="text-[10px] text-aether-secondary/60 ml-1">{sub}</span>}
      </div>
    </div>
  )
}

function SystemHealthPanel() {
  const metrics = useSystemStore((state) => state.metrics)

  return (
    <GlassPanel className="w-full">
      <h4 className="text-[10px] uppercase tracking-widest text-aether-secondary/50 mb-3">System</h4>
      <HealthCard label="CPU" value={`${metrics.cpu.usage}%`} sub={`${metrics.cpu.temperature}°C`} />
      <HealthCard label="GPU" value={`${metrics.gpu.usage}%`} sub={`${metrics.gpu.temperature}°C`} />
      <HealthCard label="RAM" value={`${metrics.ram.percentage}%`} sub={`${Math.round(metrics.ram.used / 1024 / 1024 / 1024)}GB`} />
      <HealthCard label="Disk" value={`${metrics.disk.percentage}%`} sub={`${Math.round(metrics.disk.used / 1024 / 1024 / 1024)}GB`} />
      <div className="border-t border-white/5 mt-3 pt-3">
        <HealthCard label="Model" value={metrics.model.name} color="text-aether-primary" />
        <HealthCard label="Latency" value={`${metrics.model.latency}ms`} />
        <HealthCard label="Tokens/s" value={metrics.model.tokenSpeed.toString()} />
      </div>
    </GlassPanel>
  )
}

function RecentConversations() {
  const conversations = useChatStore((state) => state.conversations)
  const setActiveConversation = useChatStore((state) => state.setActiveConversation)
  const createConversation = useChatStore((state) => state.createConversation)

  return (
    <GlassPanel className="w-full">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-[10px] uppercase tracking-widest text-aether-secondary/50">Conversations</h4>
        <button
          onClick={createConversation}
          className="text-[10px] text-aether-accent hover:text-aether-primary transition-colors"
        >
          + New
        </button>
      </div>
      <div className="space-y-1">
        {conversations.slice(0, 5).map((conv) => (
          <button
            key={conv.id}
            onClick={() => setActiveConversation(conv.id)}
            className="w-full text-left text-xs text-aether-secondary hover:text-aether-primary py-1.5 transition-colors truncate"
          >
            {conv.title}
          </button>
        ))}
        {conversations.length === 0 && (
          <p className="text-xs text-aether-secondary/40 py-2">No conversations yet</p>
        )}
      </div>
    </GlassPanel>
  )
}

export function HomeScreen() {
  const [input, setInput] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const createConversation = useChatStore((state) => state.createConversation)
  const addMessage = useChatStore((state) => state.addMessage)
  const isStreaming = useChatStore((state) => state.isStreaming)
  const setState = useAICoreStore((state) => state.setState)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isStreaming) return

    createConversation()
    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: input.trim(),
      timestamp: Date.now(),
    })

    setState('thinking')
    setInput('')
  }

  return (
    <div className="w-full h-full flex flex-col items-center justify-center px-8 py-6">
      <div className="flex gap-6 w-full max-w-7xl flex-1">
        {/* Left panel */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="w-56 flex flex-col gap-4 pt-12"
        >
          <RecentConversations />
          <GlassPanel className="w-full">
            <h4 className="text-[10px] uppercase tracking-widest text-aether-secondary/50 mb-2">Quick Actions</h4>
            <div className="space-y-1">
              {['Take Screenshot', 'System Status', 'Open Terminal'].map((action) => (
                <button
                  key={action}
                  className="w-full text-left text-xs text-aether-secondary hover:text-aether-primary py-1.5 transition-colors"
                >
                  {action}
                </button>
              ))}
            </div>
          </GlassPanel>
        </motion.div>

        {/* Center area */}
        <div className="flex-1 flex flex-col items-center justify-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          >
            <AICore />
          </motion.div>
          <Greeting />
          <AnimatePresence>
            <Waveform />
          </AnimatePresence>

          {/* Input */}
          <motion.form
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6, ease: [0.16, 1, 0.3, 1] }}
            onSubmit={handleSubmit}
            className="w-full max-w-2xl mt-6"
          >
            <div className="glass rounded-full px-6 py-3 flex items-center gap-4 glow">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask AETHER anything..."
                className="flex-1 bg-transparent text-sm text-aether-primary placeholder:text-aether-secondary/40 outline-none"
              />
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
          </motion.form>
        </div>

        {/* Right panel - System health */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="w-56 flex flex-col gap-4 pt-12"
        >
          <SystemHealthPanel />
        </motion.div>
      </div>
    </div>
  )
}
