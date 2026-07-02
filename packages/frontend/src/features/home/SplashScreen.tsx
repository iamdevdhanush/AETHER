import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface LoadingStep {
  label: string
  status: 'pending' | 'loading' | 'done'
}

const steps: LoadingStep[] = [
  { label: 'Loading AI Engine', status: 'pending' },
  { label: 'Connecting to Ollama', status: 'pending' },
  { label: 'Initializing Voice Engine', status: 'pending' },
  { label: 'Loading Memory', status: 'pending' },
  { label: 'Loading Plugins', status: 'pending' },
  { label: 'System Ready', status: 'pending' },
]

export function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [currentSteps, setSteps] = useState<LoadingStep[]>(
    steps.map((s, i) => ({ ...s, status: i === 0 ? ('loading' as const) : ('pending' as const) }))
  )

  useEffect(() => {
    let cancelled = false

    const run = async () => {
      for (let i = 0; i < steps.length; i++) {
        await new Promise((r) => setTimeout(r, 400))
        if (cancelled) return
        setSteps((prev) => prev.map((s, idx) => (idx === i ? { ...s, status: 'loading' as const } : s)))
        await new Promise((r) => setTimeout(r, 500))
        if (cancelled) return
        setSteps((prev) => prev.map((s, idx) => (idx === i ? { ...s, status: 'done' as const } : s)))
      }

      await new Promise((r) => setTimeout(r, 600))
      if (!cancelled) onComplete()
    }

    run()
    return () => { cancelled = true }
  }, [onComplete])

  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center"
      style={{ background: '#050505' }}
    >
      {/* Ambient glow */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(168,216,255,0.06) 0%, transparent 70%)',
          filter: 'blur(60px)',
        }}
      />

      <div className="relative flex flex-col items-center gap-12">
        {/* Logo + title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col items-center gap-4"
        >
          {/* Animated orb */}
          <motion.div
            animate={{ scale: [1, 1.05, 1], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            className="w-16 h-16 rounded-full"
            style={{
              background: 'radial-gradient(circle at 35% 35%, rgba(168,216,255,0.8), rgba(168,216,255,0.2) 60%, transparent 80%)',
              boxShadow: '0 0 40px rgba(168,216,255,0.15)',
            }}
          />
          <h1
            className="text-3xl font-semibold text-white tracking-[-1px]"
            style={{ fontFamily: "'Schibsted Grotesk', sans-serif" }}
          >
            AETHER
          </h1>
          <p className="text-sm text-[#A0A0A0] -mt-2" style={{ fontFamily: "'Inter', sans-serif" }}>
            Initializing...
          </p>
        </motion.div>

        {/* Loading steps */}
        <div className="flex flex-col gap-3 min-w-[260px]">
          <AnimatePresence>
            {currentSteps.map((step, i) => (
              <motion.div
                key={step.label}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1, duration: 0.3 }}
                className="flex items-center gap-3"
              >
                {step.status === 'loading' && (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-4 h-4 rounded-full border-2 shrink-0"
                    style={{ borderColor: 'rgba(168,216,255,0.3)', borderTopColor: '#A8D8FF' }}
                  />
                )}
                {step.status === 'done' && (
                  <motion.svg
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-4 h-4 text-[#00D27A] shrink-0"
                    viewBox="0 0 16 16"
                    fill="none"
                  >
                    <path d="M4 8L7 11L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </motion.svg>
                )}
                {step.status === 'pending' && (
                  <div className="w-4 h-4 rounded-full shrink-0" style={{ border: '1.5px solid rgba(255,255,255,0.1)' }} />
                )}
                <span
                  className="text-sm"
                  style={{
                    fontFamily: "'Inter', sans-serif",
                    color: step.status === 'done' ? '#00D27A' : step.status === 'loading' ? '#A8D8FF' : '#A0A0A0',
                  }}
                >
                  {step.label}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  )
}
