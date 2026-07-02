import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GlassCard } from '@/components/glass/GlassCard'
import { GlassPanel } from '@/components/glass/GlassPanel'
import { GlassInput } from '@/components/glass/GlassInput'
import { GlassButton } from '@/components/glass/GlassButton'
import { useSettingsStore } from '@/stores/settings-store'

const sections = [
  { id: 'voice', label: 'Voice', icon: '🎤' },
  { id: 'models', label: 'Models', icon: '🧠' },
  { id: 'memory', label: 'Memory', icon: '💾' },
  { id: 'appearance', label: 'Appearance', icon: '🎨' },
  { id: 'permissions', label: 'Permissions', icon: '🔒' },
  { id: 'hotkeys', label: 'Hotkeys', icon: '⌨️' },
  { id: 'system', label: 'System', icon: '⚙️' },
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

export function Settings() {
  const { settings, updateSettings, setOpen } = useSettingsStore()
  const [activeSection, setActiveSection] = useState('voice')

  return (
    <div className="w-full h-full flex overflow-hidden">
      {/* Sidebar */}
      <div className="w-48 border-r border-white/5 py-6 overflow-y-auto shrink-0">
        {sections.map((section) => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
              activeSection === section.id
                ? 'text-aether-accent bg-aether-accent/5 border-r-2 border-aether-accent'
                : 'text-aether-secondary hover:text-aether-primary'
            }`}
          >
            <span>{section.icon}</span>
            <span>{section.label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeSection}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="max-w-2xl space-y-6"
          >
            {activeSection === 'voice' && (
              <>
                <h2 className="text-xl font-thin text-aether-primary">Voice Settings</h2>
                <GlassCard>
                  <div className="space-y-4">
                    {(['wakeWord', 'continuousListening', 'pushToTalk'] as const).map((key) => (
                      <div key={key} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-aether-primary">
                            {key === 'wakeWord' ? 'Wake Word Detection' : key === 'continuousListening' ? 'Continuous Listening' : 'Push to Talk'}
                          </p>
                          <p className="text-xs text-aether-secondary">
                            {key === 'wakeWord' ? 'Listen for "Aether" wake word' : key === 'continuousListening' ? 'Always listen for commands' : 'Press hotkey to activate voice'}
                          </p>
                        </div>
                        <Toggle
                          enabled={settings.voice[key]}
                          onChange={(v) => updateSettings({ voice: { ...settings.voice, [key]: v } })}
                        />
                      </div>
                    ))}
                  </div>
                </GlassCard>
              </>
            )}

            {activeSection === 'models' && (
              <>
                <h2 className="text-xl font-thin text-aether-primary">Model Settings</h2>
                <GlassCard>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-aether-primary">Provider</p>
                        <p className="text-xs text-aether-secondary">AI provider backend</p>
                      </div>
                      <select
                        value={settings.models.provider}
                        onChange={(e) => updateSettings({ models: { ...settings.models, provider: e.target.value as any } })}
                        className="glass rounded-xl px-4 py-2 text-sm text-aether-primary outline-none"
                      >
                        <option value="ollama">Ollama (Local)</option>
                        <option value="openai">OpenAI</option>
                      </select>
                    </div>
                    <GlassInput
                      label="Model Name"
                      value={settings.models.model}
                      onChange={(e) => updateSettings({ models: { ...settings.models, model: e.target.value } })}
                    />
                    <GlassInput
                      label="Base URL"
                      value={settings.models.baseUrl}
                      onChange={(e) => updateSettings({ models: { ...settings.models, baseUrl: e.target.value } })}
                    />
                  </div>
                </GlassCard>
              </>
            )}

            {activeSection === 'appearance' && (
              <>
                <h2 className="text-xl font-thin text-aether-primary">Appearance</h2>
                <GlassCard>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-aether-primary">Reduced Motion</p>
                        <p className="text-xs text-aether-secondary">Disable animations</p>
                      </div>
                      <Toggle
                        enabled={settings.appearance.reducedMotion}
                        onChange={(v) => updateSettings({ appearance: { ...settings.appearance, reducedMotion: v } })}
                      />
                    </div>
                  </div>
                </GlassCard>
              </>
            )}

            {activeSection === 'permissions' && (
              <>
                <h2 className="text-xl font-thin text-aether-primary">Permissions</h2>
                <GlassCard>
                  <div className="space-y-4">
                    {(['executeCommands', 'fileOperations', 'systemControl'] as const).map((key) => (
                      <div key={key} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-aether-primary">
                            {key === 'executeCommands' ? 'Execute Commands' : key === 'fileOperations' ? 'File Operations' : 'System Control'}
                          </p>
                          <p className="text-xs text-aether-secondary">
                            {key === 'executeCommands' ? 'Allow running terminal commands' : key === 'fileOperations' ? 'Allow file read/write/delete' : 'Allow shutdown, restart, sleep'}
                          </p>
                        </div>
                        <Toggle
                          enabled={settings.permissions[key]}
                          onChange={(v) => updateSettings({ permissions: { ...settings.permissions, [key]: v } })}
                        />
                      </div>
                    ))}
                  </div>
                </GlassCard>
              </>
            )}

            {activeSection === 'hotkeys' && (
              <>
                <h2 className="text-xl font-thin text-aether-primary">Hotkeys</h2>
                <GlassCard>
                  <div className="space-y-4">
                    {(['toggleAether', 'pushToTalk', 'screenshot'] as const).map((key) => (
                      <GlassInput
                        key={key}
                        label={key === 'toggleAether' ? 'Toggle AETHER' : key === 'pushToTalk' ? 'Push to Talk' : 'Screenshot'}
                        value={settings.hotkeys[key]}
                        onChange={(e) => updateSettings({ hotkeys: { ...settings.hotkeys, [key]: e.target.value } })}
                      />
                    ))}
                  </div>
                </GlassCard>
              </>
            )}

            {activeSection === 'memory' && (
              <>
                <h2 className="text-xl font-thin text-aether-primary">Memory</h2>
                <GlassCard>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-aether-primary">Memory Enabled</p>
                        <p className="text-xs text-aether-secondary">Store conversation history</p>
                      </div>
                      <Toggle
                        enabled={settings.memory.enabled}
                        onChange={(v) => updateSettings({ memory: { ...settings.memory, enabled: v } })}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-aether-primary">Vector Search</p>
                        <p className="text-xs text-aether-secondary">Semantic memory search</p>
                      </div>
                      <Toggle
                        enabled={settings.memory.vectorSearch}
                        onChange={(v) => updateSettings({ memory: { ...settings.memory, vectorSearch: v } })}
                      />
                    </div>
                  </div>
                </GlassCard>
              </>
            )}

            {activeSection === 'system' && (
              <>
                <h2 className="text-xl font-thin text-aether-primary">System</h2>
                <GlassCard>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-aether-primary">Start on Boot</p>
                        <p className="text-xs text-aether-secondary">Launch AETHER on system startup</p>
                      </div>
                      <Toggle
                        enabled={settings.system.startOnBoot}
                        onChange={(v) => updateSettings({ system: { ...settings.system, startOnBoot: v } })}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-aether-primary">Minimize to Tray</p>
                        <p className="text-xs text-aether-secondary">Keep running in system tray</p>
                      </div>
                      <Toggle
                        enabled={settings.system.minimizeToTray}
                        onChange={(v) => updateSettings({ system: { ...settings.system, minimizeToTray: v } })}
                      />
                    </div>
                  </div>
                </GlassCard>
              </>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}
