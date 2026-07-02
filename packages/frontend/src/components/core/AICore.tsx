import { useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAICoreStore } from '@/stores/ai-core-store'

interface Particle {
  id: number
  x: number
  y: number
  size: number
  opacity: number
  speed: number
  angle: number
}

export function AICore() {
  const { state, amplitude } = useAICoreStore()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const particlesRef = useRef<Particle[]>([])
  const animationFrameRef = useRef<number>(0)
  const timeRef = useRef<number>(0)

  const getColor = useCallback(() => {
    switch (state) {
      case 'listening': return '#A8D8FF'
      case 'thinking': return '#A8D8FF'
      case 'speaking': return '#A8D8FF'
      case 'executing': return '#00D27A'
      case 'error': return '#FF5A5A'
      case 'success': return '#00D27A'
      default: return 'rgba(255,255,255,0.55)'
    }
  }, [state])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = 320
    canvas.height = 320

    // Initialize particles
    const particleCount = 40
    particlesRef.current = Array.from({ length: particleCount }, (_, i) => ({
      id: i,
      x: Math.random() * 320,
      y: Math.random() * 320,
      size: Math.random() * 2 + 1,
      opacity: Math.random() * 0.5 + 0.1,
      speed: Math.random() * 0.3 + 0.1,
      angle: Math.random() * Math.PI * 2,
    }))

    const animate = (timestamp: number) => {
      timeRef.current = timestamp
      ctx.clearRect(0, 0, 320, 320)

      const centerX = 160
      const centerY = 160
      const color = getColor()
      const baseRadius = 40
      const breatheRadius = state === 'idle'
        ? Math.sin(timestamp / 2000) * 3
        : state === 'listening' || state === 'speaking'
        ? amplitude * 15
        : 0
      const radius = baseRadius + breatheRadius

      // Draw outer glow layers
      const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius + 60)
      gradient.addColorStop(0, color.replace(')', ',0.15)').replace('rgb', 'rgba'))
      gradient.addColorStop(0.5, color.replace(')', ',0.05)').replace('rgb', 'rgba'))
      gradient.addColorStop(1, 'transparent')
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(centerX, centerY, radius + 60, 0, Math.PI * 2)
      ctx.fill()

      // Draw main orb with glow
      const orbGradient = ctx.createRadialGradient(
        centerX - radius * 0.3, centerY - radius * 0.3, 0,
        centerX, centerY, radius
      )
      orbGradient.addColorStop(0, 'rgba(255,255,255,0.9)')
      orbGradient.addColorStop(0.3, color.replace(')', ',0.6)').replace('rgb', 'rgba'))
      orbGradient.addColorStop(0.7, color.replace(')', ',0.3)').replace('rgb', 'rgba'))
      orbGradient.addColorStop(1, 'rgba(255,255,255,0.05)')
      
      ctx.fillStyle = orbGradient
      ctx.beginPath()
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2)
      ctx.fill()

      // Draw ring
      if (state === 'thinking' || state === 'executing') {
        const ringProgress = state === 'executing' ? (timestamp % 3000) / 3000 : undefined
        ctx.strokeStyle = color
        ctx.lineWidth = 1.5
        ctx.globalAlpha = 0.3
        
        if (ringProgress !== undefined) {
          ctx.beginPath()
          ctx.arc(centerX, centerY, radius + 12, -Math.PI / 2, -Math.PI / 2 + ringProgress * Math.PI * 2)
          ctx.stroke()
        } else {
          ctx.beginPath()
          ctx.arc(centerX, centerY, radius + 12, 0, Math.PI * 2)
          ctx.stroke()
        }
        ctx.globalAlpha = 1
      }

      // Draw and update particles
      if (state === 'thinking' || state === 'listening') {
        particlesRef.current.forEach((particle) => {
          particle.angle += particle.speed * 0.02
          particle.x += Math.cos(particle.angle) * particle.speed
          particle.y += Math.sin(particle.angle) * particle.speed

          // Keep particles near the orb
          const dx = particle.x - centerX
          const dy = particle.y - centerY
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist > 120) {
            particle.angle += Math.PI
          }

          ctx.fillStyle = color
          ctx.globalAlpha = particle.opacity * (0.5 + Math.sin(timestamp / 1000 + particle.id) * 0.5)
          ctx.beginPath()
          ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
          ctx.fill()
        })
        ctx.globalAlpha = 1
      }

      // Draw waveform for listening/speaking
      if (state === 'listening' || state === 'speaking') {
        const bars = 32
        const barWidth = 3
        const gap = 2
        const totalWidth = bars * (barWidth + gap)
        const startX = centerX - totalWidth / 2

        ctx.fillStyle = color
        ctx.globalAlpha = 0.4

        for (let i = 0; i < bars; i++) {
          const barHeight = amplitude * 40 * (0.3 + Math.sin(timestamp / 200 + i * 0.5) * 0.7) + 2
          const x = startX + i * (barWidth + gap)
          const y = centerY + radius + 15 + (40 - barHeight)
          
          ctx.fillRect(x, y, barWidth, barHeight)
        }
        ctx.globalAlpha = 1
      }

      animationFrameRef.current = requestAnimationFrame(animate)
    }

    animationFrameRef.current = requestAnimationFrame(animate)

    return () => {
      cancelAnimationFrame(animationFrameRef.current)
    }
  }, [state, amplitude, getColor])

  return (
    <div className="relative w-80 h-80 flex items-center justify-center">
      <canvas
        ref={canvasRef}
        width={320}
        height={320}
        className="w-80 h-80"
      />
      <AnimatePresence mode="wait">
        {state === 'listening' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="absolute -bottom-8 text-xs text-aether-secondary tracking-widest uppercase"
          >
            Listening
          </motion.div>
        )}
        {state === 'thinking' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="absolute -bottom-8 text-xs text-aether-accent tracking-widest uppercase"
          >
            Thinking
          </motion.div>
        )}
        {state === 'executing' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="absolute -bottom-8 text-xs text-aether-success tracking-widest uppercase"
          >
            Executing
          </motion.div>
        )}
        {state === 'error' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="absolute -bottom-8 text-xs text-aether-danger tracking-widest uppercase"
          >
            Error
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
