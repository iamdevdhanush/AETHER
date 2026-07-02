import { ChevronDown } from '@/utils/icons'

const menuItems = [
  { label: 'Platform', href: '#' },
  { label: 'Features', href: '#', hasDropdown: true },
  { label: 'Projects', href: '#' },
  { label: 'Community', href: '#' },
  { label: 'Contact', href: '#' },
]

export function Navigation() {
  return (
    <nav className="flex items-center justify-between px-[120px] py-4 relative z-10">
      <div className="flex items-center gap-12">
        <a
          href="#"
          className="text-[24px] font-semibold tracking-[-1.44px] text-black"
          style={{ fontFamily: "'Schibsted Grotesk', sans-serif" }}
        >
          Logoipsum
        </a>

        <div className="flex items-center gap-8">
          {menuItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="flex items-center gap-1.5 text-black text-base font-medium"
              style={{
                fontFamily: "'Schibsted Grotesk', sans-serif",
                letterSpacing: '-0.2px',
              }}
            >
              {item.label}
              {item.hasDropdown && <ChevronDown size={14} />}
            </a>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button
          className="h-10 text-black text-base font-medium rounded-[10px] border border-black/20 hover:bg-black/5 transition-colors"
          style={{
            width: '82px',
            fontFamily: "'Schibsted Grotesk', sans-serif",
            letterSpacing: '-0.2px',
          }}
        >
          Sign Up
        </button>
        <button
          className="h-10 text-white text-base font-medium rounded-[10px] bg-black hover:bg-black/90 transition-colors"
          style={{
            width: '101px',
            fontFamily: "'Schibsted Grotesk', sans-serif",
            letterSpacing: '-0.2px',
          }}
        >
          Log In
        </button>
      </div>
    </nav>
  )
}
