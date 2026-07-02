/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        aether: {
          bg: '#050505',
          surface: '#101010',
          glass: 'rgba(255,255,255,0.04)',
          primary: '#FFFFFF',
          secondary: '#9A9A9A',
          glow: 'rgba(255,255,255,0.55)',
          accent: '#A8D8FF',
          success: '#00D27A',
          warning: '#FFC857',
          danger: '#FF5A5A',
        },
      },
      fontFamily: {
        sans: ['Inter Variable', 'Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        aether: '28px',
      },
      backdropBlur: {
        aether: '32px',
      },
      animation: {
        'breathing': 'breathing 4s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow-pulse': 'glow-pulse 3s ease-in-out infinite',
        'spin-slow': 'spin 8s linear infinite',
      },
      keyframes: {
        breathing: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.4' },
          '50%': { transform: 'scale(1.05)', opacity: '0.6' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'glow-pulse': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(168, 216, 255, 0.2)' },
          '50%': { boxShadow: '0 0 40px rgba(168, 216, 255, 0.4)' },
        },
      },
    },
  },
  plugins: [],
}
