export function ChevronDown({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M4 6L8 10L12 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function ArrowUp({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M8 12V4M8 4L4 8M8 4L12 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function Sparkle({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M8 0L9.5 5.5L15 7L9.5 8.5L8 14L6.5 8.5L1 7L6.5 5.5L8 0Z" fill="currentColor" />
    </svg>
  )
}

export function Paperclip({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M8.5 4.5L5 8.5C4.5 9 4.5 10 5 10.5C5.5 11 6.5 11 7 10.5L11 5.5C12 4.5 12 3 11 2C10 1 8.5 1 7.5 2L3 7C1.5 8.5 1.5 11 3 12.5C4.5 14 7 14 8.5 12.5L13 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function Microphone({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <rect x="5.5" y="1" width="5" height="8" rx="2.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M3 7.5C3 9.5 5 12 8 12C11 12 13 9.5 13 7.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M8 12V15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

export function SearchIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

export function EyeIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M8 3C4.5 3 1.5 5.5 0 8C1.5 10.5 4.5 13 8 13C11.5 13 14.5 10.5 16 8C14.5 5.5 11.5 3 8 3Z" stroke="currentColor" strokeWidth="1.2" />
      <circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  )
}

export function CodeIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M6 4L2 8L6 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M10 4L14 8L10 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function AutomationIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M8 3V1M8 15V13M3 8H1M15 8H13M5.5 5.5L4 4M12 12L10.5 10.5M10.5 5.5L12 4M4 12L5.5 10.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  )
}

export function MemoryIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M6 2V14M10 2V14M2 6H14M2 10H14" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  )
}

export function TerminalIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M3 4L7 8L3 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 12H13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

export function BrowserIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <rect x="1.5" y="3" width="13" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
      <path d="M1.5 6.5H14.5" stroke="currentColor" strokeWidth="1.2" />
      <circle cx="4" cy="5" r="0.8" fill="currentColor" />
      <circle cx="5.5" cy="5" r="0.8" fill="currentColor" />
    </svg>
  )
}

export function SettingsIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M8 1.5V3M8 13V14.5M1.5 8H3M13 8H14.5M3.5 3.5L4.5 4.5M11.5 11.5L12.5 12.5M12.5 3.5L11.5 4.5M4.5 11.5L3.5 12.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  )
}

export function PowerIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M8 1V8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M12 3.5C13.5 5 14.5 7 14.5 9.5C14.5 13 11.5 15.5 8 15.5C4.5 15.5 1.5 13 1.5 9.5C1.5 7 2.5 5 4 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

export function FolderIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M1.5 4.5V12.5C1.5 13.3 2.2 14 3 14H13C13.8 14 14.5 13.3 14.5 12.5V6C14.5 5.2 13.8 4.5 13 4.5H8L6.5 3H3C2.2 3 1.5 3.7 1.5 4.5Z" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  )
}

export function PinIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M10 1L15 6L11 7L9 9L8 13L6 10L3 8L7 7L9 5L10 1Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
    </svg>
  )
}

export function StatusDot({ size = 6, color = '#00D27A' }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 6 6" fill="none">
      <circle cx="3" cy="3" r="3" fill={color} />
    </svg>
  )
}
