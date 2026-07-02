import { type ReactNode } from 'react'
import { motion } from 'framer-motion'
import { Sparkle } from '@/utils/icons'

interface MainLayoutProps {
  sidebar: ReactNode
  children: ReactNode
  rightPanel?: ReactNode
}

function TopBar() {
  return (
    <div
      className="flex items-center justify-between h-12 px-5 shrink-0 select-none"
      style={{
        background: 'rgba(255,255,255,0.02)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <div className="flex items-center gap-4">
        <span
          className="text-white text-[15px] font-semibold tracking-[-0.5px]"
          style={{ fontFamily: "'Schibsted Grotesk', sans-serif" }}
        >
          AETHER
        </span>
        <div className="w-px h-4 bg-white/10" />
        <div className="flex items-center gap-1.5">
          <Sparkle size={11} />
          <span className="text-[11px] text-[#A0A0A0] font-medium" style={{ fontFamily: "'Inter', sans-serif" }}>
            Llama 3.2
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <StatusDot />
        <span className="text-[11px] text-[#00D27A] font-medium" style={{ fontFamily: "'Inter', sans-serif" }}>Ollama</span>
        <div className="w-px h-3 bg-white/10" />
        <span className="text-[11px] text-[#A0A0A0] font-medium" style={{ fontFamily: "'Inter', sans-serif" }}>Voice</span>
        <div className="w-px h-3 bg-white/10" />
        <span className="text-[11px] text-[#A0A0A0] font-medium" style={{ fontFamily: "'Inter', sans-serif" }}>Settings</span>
      </div>
    </div>
  )
}

function StatusDot() {
  return (
    <motion.div
      animate={{ opacity: [1, 0.4, 1] }}
      transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
      className="w-2 h-2 rounded-full bg-[#00D27A]"
    />
  )
}

export function MainLayout({ sidebar, children, rightPanel }: MainLayoutProps) {
  return (
    <div className="w-full h-screen flex flex-col overflow-hidden" style={{ background: '#050505' }}>
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        {sidebar}
        <motion.main
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="flex-1 flex overflow-hidden"
        >
          <div className="flex-1 overflow-y-auto">
            {children}
          </div>
          {rightPanel && (
            <motion.aside
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
              className="w-64 shrink-0 overflow-y-auto border-l border-white/5"
            >
              {rightPanel}
            </motion.aside>
          )}
        </motion.main>
      </div>
    </div>
  )
}
