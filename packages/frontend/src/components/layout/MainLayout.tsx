import { type ReactNode } from 'react'
import { motion } from 'framer-motion'

interface MainLayoutProps {
  sidebar: ReactNode
  children: ReactNode
  rightPanel?: ReactNode
}

export function MainLayout({ sidebar, children, rightPanel }: MainLayoutProps) {
  return (
    <div className="w-full h-screen flex overflow-hidden bg-aether-bg">
      {sidebar}
      <motion.main
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="flex-1 flex overflow-hidden"
      >
        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
        {rightPanel && (
          <motion.aside
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
            className="w-72 border-l border-white/5 overflow-y-auto"
          >
            {rightPanel}
          </motion.aside>
        )}
      </motion.main>
    </div>
  )
}
