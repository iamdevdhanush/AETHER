import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MainLayout } from '@/components/layout/MainLayout'
import { Sidebar } from '@/components/layout/Sidebar'
import { HomeScreen } from '@/features/home/HomeScreen'
import { ChatPanel } from '@/features/chat/ChatPanel'
import { Dashboard } from '@/features/dashboard/Dashboard'
import { Settings } from '@/features/settings/Settings'
import { Plugins } from '@/features/plugins/Plugins'
import { HeroSection } from '@/features/hero/HeroSection'
import { useSystemMetrics } from '@/hooks/use-system-metrics'

type View = 'home' | 'chat' | 'dashboard' | 'settings' | 'plugins' | 'hero'

function AppIcon({ path }: { path: string }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      {path === 'home' && <><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></>}
      {path === 'chat' && <><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></>}
      {path === 'dashboard' && <><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /></>}
      {path === 'settings' && <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" /></>}
      {path === 'plugins' && <><path d="M12 2L2 7l10 5 10-5-10-5z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" /></>}
    </svg>
  )
}

export default function App() {
  const [currentView, setCurrentView] = useState<View>('home')
  useSystemMetrics()

  const sidebarItems = [
    {
      section: 'Navigation',
      items: [
        { id: 'home', icon: <AppIcon path="home" />, label: 'Home' },
        { id: 'chat', icon: <AppIcon path="chat" />, label: 'Conversations' },
        { id: 'dashboard', icon: <AppIcon path="dashboard" />, label: 'Dashboard' },
        { id: 'hero', icon: <AppIcon path="home" />, label: 'Hero' },
        { id: 'plugins', icon: <AppIcon path="plugins" />, label: 'Plugins' },
        { id: 'settings', icon: <AppIcon path="settings" />, label: 'Settings' },
      ],
    },
  ]

  const handleItemClick = useCallback((id: string) => {
    setCurrentView(id as View)
  }, [])

  const renderView = () => {
    switch (currentView) {
      case 'hero':
        return <HeroSection />
      case 'home':
        return <HomeScreen />
      case 'chat':
        return <ChatPanel />
      case 'dashboard':
        return <Dashboard />
      case 'settings':
        return <Settings />
      case 'plugins':
        return <Plugins />
      default:
        return <HomeScreen />
    }
  }

  return (
    <div className="w-full h-screen bg-aether-bg text-aether-primary font-sans antialiased overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-aether-accent/5 blur-[120px] rounded-full pointer-events-none" />
      <MainLayout
        sidebar={
          <Sidebar
            items={sidebarItems}
            activeItem={currentView}
            onItemClick={handleItemClick}
          />
        }
        rightPanel={null}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={currentView}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="w-full h-full"
          >
            {renderView()}
          </motion.div>
        </AnimatePresence>
      </MainLayout>
    </div>
  )
}
