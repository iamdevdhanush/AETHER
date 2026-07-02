import { type ReactNode } from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'

interface GlassCardProps {
  children: ReactNode
  title?: string
  subtitle?: string
  icon?: ReactNode
  className?: string
  onClick?: () => void
}

export function GlassCard({ children, title, subtitle, icon, className, onClick }: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      whileHover={onClick ? { y: -2 } : undefined}
      onClick={onClick}
      className={clsx(
        'glass rounded-aether p-5',
        onClick && 'cursor-pointer glass-hover',
        className
      )}
    >
      {(title || icon) && (
        <div className="flex items-start justify-between mb-4">
          <div>
            {title && <h3 className="text-sm font-medium text-aether-primary">{title}</h3>}
            {subtitle && <p className="text-xs text-aether-secondary mt-0.5">{subtitle}</p>}
          </div>
          {icon && <div className="text-aether-secondary">{icon}</div>}
        </div>
      )}
      {children}
    </motion.div>
  )
}
