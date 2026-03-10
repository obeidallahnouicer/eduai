/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Void Space palette
        vs: {
          bg:        '#0d1117',
          surface:   '#161b22',
          border:    '#30363d',
          muted:     '#8b949e',
          text:      '#c9d1d9',
          bright:    '#e6edf3',
          primary:   '#58a6ff',
          secondary: '#79c0ff',
          accent:    '#f78166',
          success:   '#3fb950',
          warning:   '#d29922',
          danger:    '#f85149',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Helvetica', 'Arial', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem' }],
      },
      boxShadow: {
        sm: '0 1px 3px rgba(0,0,0,0.3)',
        DEFAULT: '0 2px 8px rgba(0,0,0,0.4)',
      },
      borderRadius: {
        DEFAULT: '6px',
        md: '6px',
        lg: '8px',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in':  'fade-in 150ms ease',
        'slide-up': 'slide-up 150ms ease',
      },
    },
  },
  plugins: [],
}
