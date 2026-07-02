import { useState } from 'react'
import { motion } from 'framer-motion'
import { GlassCard } from '@/components/glass/GlassCard'

interface PluginItem {
  id: string
  name: string
  description: string
  version: string
  enabled: boolean
  type: 'system' | 'user'
}

const defaultPlugins: PluginItem[] = [
  { id: 'conversation', name: 'Conversation', description: 'Natural conversation with LLM', version: '1.0.0', enabled: true, type: 'system' },
  { id: 'voice', name: 'Voice', description: 'Speech-to-text and text-to-speech', version: '1.0.0', enabled: true, type: 'system' },
  { id: 'memory', name: 'Memory', description: 'Conversation history and vector search', version: '1.0.0', enabled: true, type: 'system' },
  { id: 'automation', name: 'Desktop Automation', description: 'Launch, close, and manage applications', version: '1.0.0', enabled: true, type: 'system' },
  { id: 'files', name: 'File System', description: 'Search, read, and manage files', version: '1.0.0', enabled: true, type: 'system' },
  { id: 'code', name: 'Developer Mode', description: 'Code understanding and generation', version: '1.0.0', enabled: false, type: 'system' },
  { id: 'vision', name: 'Vision', description: 'Screenshot understanding and OCR', version: '1.0.0', enabled: false, type: 'system' },
  { id: 'system', name: 'System Monitor', description: 'CPU, RAM, GPU, disk monitoring', version: '1.0.0', enabled: true, type: 'system' },
]

function Toggle({ enabled, onChange }: { enabled: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`relative w-10 h-5 rounded-full transition-colors duration-300 ${
        enabled ? 'bg-aether-accent/40' : 'bg-white/10'
      }`}
    >
      <motion.div
        animate={{ x: enabled ? 20 : 2 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        className="absolute top-1 w-3 h-3 bg-white rounded-full"
      />
    </button>
  )
}

export function Plugins() {
  const [plugins, setPlugins] = useState(defaultPlugins)

  const togglePlugin = (id: string) => {
    setPlugins((prev) =>
      prev.map((p) => (p.id === id ? { ...p, enabled: !p.enabled } : p))
    )
  }

  return (
    <div className="w-full h-full overflow-y-auto px-8 py-6">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="max-w-3xl mx-auto space-y-6"
      >
        <div>
          <h1 className="text-2xl font-thin text-aether-primary">Plugins</h1>
          <p className="text-sm text-aether-secondary mt-1">Enable or disable AETHER capabilities</p>
        </div>

        <div className="space-y-3">
          {plugins.map((plugin) => (
            <GlassCard key={plugin.id}>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-medium text-aether-primary">{plugin.name}</h3>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      plugin.type === 'system' ? 'bg-aether-accent/10 text-aether-accent' : 'bg-aether-success/10 text-aether-success'
                    }`}>
                      {plugin.type}
                    </span>
                    <span className="text-[10px] text-aether-secondary/50">v{plugin.version}</span>
                  </div>
                  <p className="text-xs text-aether-secondary mt-0.5">{plugin.description}</p>
                </div>
                <Toggle enabled={plugin.enabled} onChange={() => togglePlugin(plugin.id)} />
              </div>
            </GlassCard>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
