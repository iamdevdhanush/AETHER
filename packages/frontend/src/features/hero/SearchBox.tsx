import { ArrowUp, Paperclip, Microphone, SearchIcon, Sparkle } from '@/utils/icons'

export function SearchBox() {
  return (
    <div
      className="mx-auto rounded-[18px] p-5 flex flex-col gap-3"
      style={{
        maxWidth: '728px',
        width: '100%',
        height: '200px',
        background: 'rgba(0,0,0,0.24)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
      }}
    >
      {/* Top row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className="text-white font-medium"
            style={{ fontFamily: "'Schibsted Grotesk', sans-serif", fontSize: '12px' }}
          >
            60/450 credits
          </span>
          <button
            className="px-2 py-0.5 rounded text-[11px] font-medium text-black leading-none"
            style={{ background: 'rgba(90,225,76,0.89)' }}
          >
            Upgrade
          </button>
        </div>
        <div className="flex items-center gap-1.5">
          <Sparkle size={14} />
          <span
            className="text-white font-medium"
            style={{ fontFamily: "'Schibsted Grotesk', sans-serif", fontSize: '12px' }}
          >
            Powered by GPT-4o
          </span>
        </div>
      </div>

      {/* Main input */}
      <div
        className="flex items-center gap-3 px-4 py-2.5 rounded-[12px] bg-white"
        style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}
      >
        <input
          type="text"
          placeholder="Type question..."
          className="flex-1 bg-transparent outline-none text-base"
          style={{
            fontFamily: "'Inter', sans-serif",
            color: 'rgba(0,0,0,0.6)',
          }}
        />
        <button
          className="w-9 h-9 rounded-full bg-black flex items-center justify-center text-white hover:bg-black/80 transition-colors shrink-0"
        >
          <ArrowUp size={16} />
        </button>
      </div>

      {/* Bottom row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] text-white/80 hover:text-white transition-colors"
            style={{ background: 'rgba(255,255,255,0.1)' }}
          >
            <Paperclip size={14} />
            <span className="text-xs font-medium" style={{ fontFamily: "'Inter', sans-serif" }}>Attach</span>
          </button>
          <button
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] text-white/80 hover:text-white transition-colors"
            style={{ background: 'rgba(255,255,255,0.1)' }}
          >
            <Microphone size={14} />
            <span className="text-xs font-medium" style={{ fontFamily: "'Inter', sans-serif" }}>Voice</span>
          </button>
          <button
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] text-white/80 hover:text-white transition-colors"
            style={{ background: 'rgba(255,255,255,0.1)' }}
          >
            <SearchIcon size={14} />
            <span className="text-xs font-medium" style={{ fontFamily: "'Inter', sans-serif" }}>Prompts</span>
          </button>
        </div>
        <span
          className="text-xs text-white/60"
          style={{ fontFamily: "'Inter', sans-serif" }}
        >
          0/3,000
        </span>
      </div>
    </div>
  )
}
