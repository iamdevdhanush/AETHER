import { motion } from 'framer-motion'
import { GlassCard } from '@/components/glass/GlassCard'
import { GlassPanel } from '@/components/glass/GlassPanel'
import { useSystemStore } from '@/stores/system-store'

interface MetricBarProps {
  label: string
  value: number
  color?: string
  format?: string
}

function MetricBar({ label, value, color = 'bg-aether-accent', format = 'value' }: MetricBarProps) {
  const displayValue = format === 'percentage' ? `${value}%` : value.toString()

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs text-aether-secondary">{label}</span>
        <span className="text-xs font-medium text-aether-primary">{displayValue}</span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(value, 100)}%` }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className={`h-full rounded-full ${color}`}
        />
      </div>
    </div>
  )
}

function ProcessList() {
  const processes = [
    { name: 'AETHER Core', cpu: 2.1, ram: 128 },
    { name: 'Ollama', cpu: 45.3, ram: 2048 },
    { name: 'Code', cpu: 8.7, ram: 512 },
    { name: 'Terminal', cpu: 1.2, ram: 64 },
  ]

  return (
    <GlassCard title="Running Processes" subtitle="Active system processes">
      <div className="space-y-2">
        {processes.map((proc) => (
          <div key={proc.name} className="flex items-center justify-between py-1">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-aether-success" />
              <span className="text-xs text-aether-primary">{proc.name}</span>
            </div>
            <div className="flex items-center gap-3 text-[10px] text-aether-secondary">
              <span>{proc.cpu}% CPU</span>
              <span>{proc.ram}MB</span>
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  )
}

export function Dashboard() {
  const metrics = useSystemStore((state) => state.metrics)

  return (
    <div className="w-full h-full overflow-y-auto px-8 py-6">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
        className="max-w-4xl mx-auto space-y-6"
      >
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h1 className="text-2xl font-thin text-aether-primary">System Dashboard</h1>
          <p className="text-sm text-aether-secondary mt-1">Real-time system monitoring</p>
        </motion.div>

        {/* CPU, RAM, GPU, Disk */}
        <div className="grid grid-cols-2 gap-4">
          <GlassCard title="CPU" subtitle={`${metrics.cpu.temperature}°C`}>
            <MetricBar label="Usage" value={metrics.cpu.usage} color="bg-aether-accent" />
          </GlassCard>
          <GlassCard title="GPU" subtitle={`${metrics.gpu.temperature}°C`}>
            <MetricBar label="Usage" value={metrics.gpu.usage} color="bg-aether-accent" />
          </GlassCard>
          <GlassCard title="Memory" subtitle={`${Math.round(metrics.ram.used / 1024 / 1024 / 1024)}GB / ${Math.round(metrics.ram.total / 1024 / 1024 / 1024)}GB`}>
            <MetricBar label="Usage" value={metrics.ram.percentage} color="bg-aether-warning" />
          </GlassCard>
          <GlassCard title="Disk" subtitle={`${Math.round(metrics.disk.used / 1024 / 1024 / 1024)}GB / ${Math.round(metrics.disk.total / 1024 / 1024 / 1024)}GB`}>
            <MetricBar label="Usage" value={metrics.disk.percentage} color="bg-aether-success" />
          </GlassCard>
        </div>

        {/* Model Info */}
        <GlassCard title="AI Model" subtitle="Current inference status">
          <div className="grid grid-cols-3 gap-4 mt-2">
            <div>
              <p className="text-[10px] text-aether-secondary uppercase tracking-wider">Model</p>
              <p className="text-sm text-aether-primary mt-1">{metrics.model.name}</p>
            </div>
            <div>
              <p className="text-[10px] text-aether-secondary uppercase tracking-wider">Token Speed</p>
              <p className="text-sm text-aether-primary mt-1">{metrics.model.tokenSpeed} t/s</p>
            </div>
            <div>
              <p className="text-[10px] text-aether-secondary uppercase tracking-wider">Latency</p>
              <p className="text-sm text-aether-primary mt-1">{metrics.model.latency}ms</p>
            </div>
          </div>
        </GlassCard>

        {/* Battery & Network */}
        <div className="grid grid-cols-2 gap-4">
          <GlassCard title="Battery">
            <div className="flex items-center gap-3 mt-1">
              <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${metrics.battery.percentage}%` }}
                  transition={{ duration: 1 }}
                  className={`h-full rounded-full ${metrics.battery.percentage > 20 ? 'bg-aether-success' : 'bg-aether-danger'}`}
                />
              </div>
              <span className="text-sm font-medium text-aether-primary">{metrics.battery.percentage}%</span>
              {metrics.battery.charging && (
                <span className="text-[10px] text-aether-success uppercase">Charging</span>
              )}
            </div>
          </GlassCard>
          <GlassCard title="Network">
            <div className="space-y-1 mt-1">
              <div className="flex justify-between text-xs">
                <span className="text-aether-secondary">Download</span>
                <span className="text-aether-primary">{Math.round(metrics.network.rx / 1024)} KB/s</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-aether-secondary">Upload</span>
                <span className="text-aether-primary">{Math.round(metrics.network.tx / 1024)} KB/s</span>
              </div>
            </div>
          </GlassCard>
        </div>

        <ProcessList />
      </motion.div>
    </div>
  )
}
