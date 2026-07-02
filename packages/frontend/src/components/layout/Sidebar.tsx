import { type ReactNode } from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'

interface SidebarItemProps {
  icon: ReactNode
  label: string
  active?: boolean
  onClick?: () => void
  badge?: string | number
}

function SidebarItem({ icon, label, active, onClick, badge }: SidebarItemProps) {
  return (
    <motion.button
      whileHover={{ x: 4 }}
      onClick={onClick}
      className={clsx(
        'w-full flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-300 text-sm',
        active
          ? 'bg-aether-accent/10 text-aether-accent'
          : 'text-aether-secondary hover:text-aether-primary hover:bg-white/5'
      )}
    >
      <span className="w-4 h-4 flex items-center justify-center">{icon}</span>
      <span className="flex-1 text-left">{label}</span>
      {badge !== undefined && (
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-aether-accent/20 text-aether-accent">
          {badge}
        </span>
      )}
    </motion.button>
  )
}

interface SidebarSectionProps {
  title: string
  children: ReactNode
}

function SidebarSection({ title, children }: SidebarSectionProps) {
  return (
    <div className="space-y-1">
      <p className="text-[10px] uppercase tracking-widest text-aether-secondary/50 px-4 py-2">
        {title}
      </p>
      {children}
    </div>
  )
}

interface SidebarProps {
  items: Array<{
    section: string
    items: Array<{
      id: string
      icon: ReactNode
      label: string
      badge?: string | number
    }>
  }>
  activeItem: string
  onItemClick: (id: string) => void
}

export function Sidebar({ items, activeItem, onItemClick }: SidebarProps) {
  return (
    <motion.aside
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="w-56 h-full flex flex-col gap-6 py-6 overflow-y-auto"
    >
      {items.map((section) => (
        <SidebarSection key={section.section} title={section.section}>
          {section.items.map((item) => (
            <SidebarItem
              key={item.id}
              icon={item.icon}
              label={item.label}
              active={activeItem === item.id}
              badge={item.badge}
              onClick={() => onItemClick(item.id)}
            />
          ))}
        </SidebarSection>
      ))}
    </motion.aside>
  )
}
