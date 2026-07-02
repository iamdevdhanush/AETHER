import { type InputHTMLAttributes, forwardRef } from 'react'
import clsx from 'clsx'

interface GlassInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
}

export const GlassInput = forwardRef<HTMLInputElement, GlassInputProps>(
  ({ label, className, ...props }, ref) => {
    return (
      <div className="space-y-2">
        {label && (
          <label className="block text-xs font-medium text-aether-secondary uppercase tracking-wider">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={clsx(
            'w-full px-4 py-3 text-sm',
            'glass rounded-xl',
            'text-aether-primary placeholder:text-aether-secondary/50',
            'focus:outline-none focus:border-aether-accent/30 focus:glow',
            'transition-all duration-300',
            className
          )}
          {...props}
        />
      </div>
    )
  }
)
GlassInput.displayName = 'GlassInput'
