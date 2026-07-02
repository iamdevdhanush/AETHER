import { type ReactNode, type ComponentPropsWithoutRef } from 'react'
import { motion } from 'framer-motion'
import clsx from 'clsx'

type MotionButtonProps = ComponentPropsWithoutRef<typeof motion.button>

interface GlassButtonProps extends Omit<MotionButtonProps, 'children'> {
  children: ReactNode
  variant?: 'default' | 'primary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

export function GlassButton({
  children,
  variant = 'default',
  size = 'md',
  isLoading,
  className,
  disabled,
  ...props
}: GlassButtonProps) {
  return (
    <motion.button
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      className={clsx(
        'rounded-full font-medium transition-all duration-300 select-none',
        'border border-transparent',
        {
          'glass glass-hover text-aether-primary': variant === 'default',
          'bg-aether-accent/20 text-aether-accent border-aether-accent/30 hover:bg-aether-accent/30': variant === 'primary',
          'bg-aether-danger/20 text-aether-danger border-aether-danger/30 hover:bg-aether-danger/30': variant === 'danger',
          'text-aether-secondary hover:text-aether-primary': variant === 'ghost',
          'px-3 py-1.5 text-xs': size === 'sm',
          'px-5 py-2 text-sm': size === 'md',
          'px-8 py-3 text-base': size === 'lg',
          'opacity-50 cursor-not-allowed': disabled || isLoading,
        },
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="flex items-center gap-2">
          <motion.span
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="inline-block w-4 h-4 border-2 border-aether-accent/30 border-t-aether-accent rounded-full"
          />
          {children}
        </span>
      ) : (
        children
      )}
    </motion.button>
  )
}
