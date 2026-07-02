import { VideoBackground } from './VideoBackground'
import { Navigation } from './Navigation'
import { SearchBox } from './SearchBox'
import { Star } from '@/utils/icons'

const VIDEO_URL = 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260329_050842_be71947f-f16e-4a14-810c-06e83d23ddb5.mp4'

export function HeroSection() {
  return (
    <div className="relative w-full min-h-screen overflow-hidden bg-white">
      <VideoBackground src={VIDEO_URL} />

      <Navigation />

      <div className="relative z-10 px-[120px] -mt-[50px]">
        <div className="flex flex-col items-center" style={{ gap: '60px' }}>
          {/* Hero content */}
          <div className="flex flex-col items-center" style={{ gap: '44px' }}>
            {/* Header group */}
            <div className="flex flex-col items-center" style={{ gap: '34px' }}>
              {/* Badge */}
              <div className="flex items-center gap-3">
                <div
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
                  style={{ background: '#0e1311' }}
                >
                  <Star size={14} />
                  <span
                    className="text-white text-sm"
                    style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '14px' }}
                  >
                    New
                  </span>
                </div>
                <div
                  className="px-3 py-1.5 rounded-full"
                  style={{
                    background: '#f8f8f8',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                  }}
                >
                  <span
                    className="text-sm"
                    style={{ fontFamily: "'Inter', sans-serif", fontWeight: 400, fontSize: '14px', color: '#505050' }}
                  >
                    Discover what's possible
                  </span>
                </div>
              </div>

              {/* Main headline */}
              <h1
                className="text-center text-black leading-none m-0 p-0"
                style={{
                  fontFamily: "'Fustat', sans-serif",
                  fontWeight: 700,
                  fontSize: '80px',
                  letterSpacing: '-4.8px',
                  lineHeight: '0.9',
                }}
              >
                Transform Data Quickly
              </h1>

              {/* Subtitle */}
              <p
                className="text-center m-0"
                style={{
                  fontFamily: "'Fustat', sans-serif",
                  fontWeight: 500,
                  fontSize: '20px',
                  letterSpacing: '-0.4px',
                  color: '#505050',
                  maxWidth: '736px',
                  width: '542px',
                }}
              >
                Upload your information and get powerful insights right away. Work smarter and achieve goals effortlessly.
              </p>
            </div>

            {/* Search box */}
            <SearchBox />
          </div>
        </div>
      </div>
    </div>
  )
}
