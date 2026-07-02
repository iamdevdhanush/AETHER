import { type ReactNode } from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'

interface GlassPanelProps {
  children: ReactNode
  className?: string
  hover?: boolean
  glow?: boolean
  padding?: 'sm' | 'md' | 'lg'
}

const paddingMap = {
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-8',
}

export function GlassPanel({ children, className, hover, glow, padding = 'md' }: GlassPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className={clsx(
        'glass rounded-aether',
        paddingMap[padding],
        hover && 'glass-hover cursor-pointer',
        glow && 'glow',
        className
      )}
    >
      {children}
    </motion.div>
  )
}
