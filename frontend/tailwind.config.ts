import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: 'class',
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // ═══════════════════════════════════════════════════════════════
      // NEURAL HARMONY COLOR SYSTEM - Psychology Inspired
      // ═══════════════════════════════════════════════════════════════

      colors: {
        // ── Neural Teal - Primary (Mindfulness, Balance) ──────────────
        neural: {
          50:  '#CCFBF1',
          100: '#99F6E4',
          200: '#5EEAD4',
          300: '#2DD4BF',
          400: '#14B8A6',
          500: '#0D9488',  // PRIMARY
          600: '#0F766E',
          700: '#115E59',
          800: '#134E4A',
          900: '#042F2E',
          950: '#021019',
        },

        // ── Cortex Violet - Secondary (Creativity, Intelligence) ───────
        cortex: {
          50:  '#EDE9FE',
          100: '#DDD6FE',
          200: '#C4B5FD',
          300: '#A78BFA',
          400: '#8B5CF6',
          500: '#7C3AED',
          600: '#6D28D9',
          700: '#5B21B6',
          800: '#4C1D95',
          900: '#2E1065',
          950: '#1A0533',
        },

        // ── Dopamine Amber - Accent (Energy, Motivation) ───────────────
        dopamine: {
          50:  '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },

        // ── Semantic Colors ──────────────────────────────────────────
        success: {
          DEFAULT: '#10B981',
          light: '#D1FAE5',
          dark: '#065F46',
        },
        warning: {
          DEFAULT: '#F59E0B',
          light: '#FEF3C7',
          dark: '#92400E',
        },
        error: {
          DEFAULT: '#EF4444',
          light: '#FEE2E2',
          dark: '#991B1B',
        },
        info: {
          DEFAULT: '#38BDF8',
          light: '#E0F2FE',
          dark: '#0369A1',
        },

        // ── Warm Grays (không quá lạnh) ──────────────────────────────
        gray: {
          50:  '#FAFAF9',
          100: '#F5F5F4',
          200: '#E7E5E4',
          300: '#D6D3D1',
          400: '#A8A29E',
          500: '#78716C',
          600: '#57534E',
          700: '#44403C',
          800: '#292524',
          850: '#1C1917',
          900: '#1C1917',
        },

        // ── Electric Colors (cho highlights) ──────────────────────────
        electric: {
          blue:   '#00D4FF',
          cyan:   '#00FFF7',
          pink:   '#FF2D92',
          green:  '#00FF88',
        },

        // ── Brand Colors ─────────────────────────────────────────────
        brand: {
          50:  '#CCFBF1',
          100: '#99F6E4',
          500: '#0D9488',
          600: '#0F766E',
          700: '#115E59',
          900: '#042F2E',
        },

        // ── Semantic Psychology Colors ───────────────────────────────
        psychology: {
          clinical:    '#6366F1',  // Indigo - Clinical Psychology
          cognitive:   '#3B82F6',  // Blue - Cognitive Psychology
          behavioral:  '#10B981',  // Emerald - Behavioral
          developmental: '#F59E0B', // Amber - Developmental
          social:      '#EC4899',  // Pink - Social Psychology
          neuroscience: '#06B6D4', // Cyan - Neuroscience
          therapy:     '#8B5CF6',  // Violet - Therapy
          diagnosis:   '#EF4444', // Red - Diagnosis
        },

        // ── Glass Surface Tokens ──────────────────────────────────────
        glass: {
          white:  'rgba(255,255,255,0.72)',
          light:  'rgba(248,250,252,0.85)',
          border: 'rgba(255,255,255,0.25)',
          dark:   'rgba(15,23,42,0.60)',
        },

        // ── Dark Mode Surfaces ────────────────────────────────────────
        surface: {
          base:      '#0A0F1A',   // Deep space blue-black
          elevated:  '#111827',   // Cards, modals
          overlay:   '#1F2937',   // Dropdowns, tooltips
          muted:     '#374151',   // Disabled states
        },
      },

      // ═══════════════════════════════════════════════════════════════
      // BACKGROUND IMAGES & GRADIENTS
      // ═══════════════════════════════════════════════════════════════
      backgroundImage: {
        // Mesh gradients cho landing page
        'mesh-neural':
          'radial-gradient(at 20% 30%, rgba(13, 148, 136, 0.15) 0, transparent 50%), radial-gradient(at 80% 70%, rgba(124, 58, 237, 0.12) 0, transparent 50%), radial-gradient(at 50% 50%, rgba(245, 158, 11, 0.08) 0, transparent 50%)',

        'mesh-cortex':
          'radial-gradient(at 10% 20%, rgba(124, 58, 237, 0.2) 0, transparent 40%), radial-gradient(at 90% 80%, rgba(13, 148, 136, 0.15) 0, transparent 40%), radial-gradient(at 50% 50%, rgba(168, 85, 247, 0.1) 0, transparent 60%)',

        'mesh-dark':
          'radial-gradient(at 20% 20%, rgba(13, 148, 136, 0.15) 0, transparent 40%), radial-gradient(at 80% 80%, rgba(124, 58, 237, 0.12) 0, transparent 40%)',

        // Glow effects
        'glow-neural':   'radial-gradient(ellipse at center, rgba(13, 148, 136, 0.3) 0%, transparent 70%)',
        'glow-cortex':  'radial-gradient(ellipse at center, rgba(124, 58, 237, 0.3) 0%, transparent 70%)',
        'glow-dopamine':'radial-gradient(ellipse at center, rgba(245, 158, 11, 0.3) 0%, transparent 70%)',

        // Neural gradient (primary gradient)
        'gradient-neural': 'linear-gradient(135deg, #0D9488 0%, #14B8A6 100%)',
        'gradient-cortex': 'linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%)',
        'gradient-hero': 'linear-gradient(135deg, #0D9488 0%, #7C3AED 50%, #F59E0B 100%)',

        // Radial backgrounds
        'radial-neural':   'radial-gradient(circle at center, rgba(13, 148, 136, 0.1) 0, transparent 50%)',
        'radial-cortex':  'radial-gradient(circle at center, rgba(124, 58, 237, 0.1) 0, transparent 50%)',
      },

      // ═══════════════════════════════════════════════════════════════
      // ANIMATION SYSTEM
      // ═══════════════════════════════════════════════════════════════
      animation: {
        // ── Basic Animations ────────────────────────────────────────
        'fade-in':      'fadeIn 0.3s ease forwards',
        'fade-in-up':   'fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards',
        'fade-in-down': 'fadeInDown 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards',
        'scale-in':     'scaleIn 0.2s cubic-bezier(0.4, 0, 0.2, 1) forwards',
        'slide-in-right': 'slideInRight 0.3s ease forwards',
        'slide-in-left': 'slideInLeft 0.3s ease forwards',

        // ── Floating & Breathing ─────────────────────────────────────
        'float':        'float 6s ease-in-out infinite',
        'float-slow':   'floatSlow 10s ease-in-out infinite',
        'breathe':      'breathe 4s ease-in-out infinite',
        'pulse-soft':   'pulseSoft 3s ease-in-out infinite',

        // ── Glowing Effects ───────────────────────────────────────────
        'glow':         'glow 2s ease-in-out infinite',
        'glow-pulse':   'glowPulse 3s ease-in-out infinite',
        'neon-pulse':   'neonPulse 2s ease-in-out infinite',

        // ── Loading States ───────────────────────────────────────────
        'shimmer':      'shimmer 2.5s linear infinite',
        'spin-slow':    'spin 8s linear infinite',
        'bounce-soft':  'bounceSoft 1.5s ease-in-out infinite',
        'dots-pulse':   'dotsPulse 1.4s ease-in-out infinite',

        // ── Border Animations ─────────────────────────────────────────
        'border-spin':  'borderSpin 4s linear infinite',
        'gradient-shift': 'gradientShift 8s ease infinite',

        // ── Page Transitions ─────────────────────────────────────────
        'page-enter':   'pageEnter 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards',
        'page-exit':    'pageExit 0.2s ease forwards',

        // ── Special Effects ──────────────────────────────────────────
        'typing':       'typing 3.5s steps(40, end), blink 0.75s step-end infinite',
        'orbit':        'orbit 12s linear infinite',
        'particle':     'particleMove 8s linear infinite',
        'wave':         'wave 1.5s ease-in-out infinite',
        'electric':     'electric 1.5s ease-in-out infinite',

        // ── AI Specific ───────────────────────────────────────────────
        'token-appear': 'tokenAppear 0.15s ease forwards',
        'thinking-dots': 'thinkingDots 1.4s infinite',
        'stream-line':  'streamLine 2s linear infinite',
      },

      keyframes: {
        // ── Fade Animations ──────────────────────────────────────────
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        fadeInUp: {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInDown: {
          from: { opacity: '0', transform: 'translateY(-20px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          from: { opacity: '0', transform: 'scale(0.95)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        slideInRight: {
          from: { opacity: '0', transform: 'translateX(20px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        slideInLeft: {
          from: { opacity: '0', transform: 'translateX(-20px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },

        // ── Float & Breathe ──────────────────────────────────────────
        float: {
          '0%,100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        floatSlow: {
          '0%,100%': { transform: 'translateY(0px) rotate(0deg)' },
          '33%': { transform: 'translateY(-8px) rotate(1deg)' },
          '66%': { transform: 'translateY(4px) rotate(-0.5deg)' },
        },
        breathe: {
          '0%,100%': { transform: 'scale(1)', opacity: '0.8' },
          '50%': { transform: 'scale(1.05)', opacity: '1' },
        },
        pulseSoft: {
          '0%,100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },

        // ── Glow Effects ──────────────────────────────────────────────
        glow: {
          '0%,100%': { boxShadow: '0 0 20px rgba(13, 148, 136, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(13, 148, 136, 0.6)' },
        },
        glowPulse: {
          '0%,100%': { boxShadow: '0 0 20px rgba(13, 148, 136, 0.3), 0 0 40px rgba(124, 58, 237, 0.15)' },
          '50%': { boxShadow: '0 0 40px rgba(13, 148, 136, 0.5), 0 0 80px rgba(124, 58, 237, 0.3)' },
        },
        neonPulse: {
          '0%,100%': { opacity: '1', filter: 'brightness(1)' },
          '50%': { opacity: '0.7', filter: 'brightness(1.4)' },
        },

        // ── Loading States ────────────────────────────────────────────
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        bounceSoft: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        dotsPulse: {
          '0%,80%,100%': { transform: 'scale(0.6)', opacity: '0.5' },
          '40%': { transform: 'scale(1)', opacity: '1' },
        },

        // ── Border Animations ─────────────────────────────────────────
        borderSpin: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
        gradientShift: {
          '0%,100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },

        // ── Page Transitions ─────────────────────────────────────────
        pageEnter: {
          from: { opacity: '0', transform: 'translateY(10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        pageExit: {
          from: { opacity: '1' },
          to: { opacity: '0' },
        },

        // ── Special Effects ───────────────────────────────────────────
        typing: {
          from: { width: '0' },
          to: { width: '100%' },
        },
        blink: {
          'from,to': { borderColor: 'transparent' },
          '50%': { borderColor: 'currentColor' },
        },
        particleMove: {
          '0%': { transform: 'translateY(100vh) translateX(0)', opacity: '0' },
          '10%': { opacity: '1' },
          '90%': { opacity: '1' },
          '100%': { transform: 'translateY(-100px) translateX(20px)', opacity: '0' },
        },
        wave: {
          '0%,100%': { transform: 'scaleY(1)' },
          '50%': { transform: 'scaleY(1.1)' },
        },
        electric: {
          '0%,100%': { opacity: '1' },
          '25%': { opacity: '0.6' },
          '50%': { opacity: '1' },
          '75%': { opacity: '0.8' },
        },

        // ── AI Specific ───────────────────────────────────────────────
        tokenAppear: {
          from: { opacity: '0', transform: 'translateY(4px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        thinkingDots: {
          '0%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
          '100%': { transform: 'translateY(0)' },
        },
        streamLine: {
          from: { backgroundPosition: '200% 0' },
          to: { backgroundPosition: '-200% 0' },
        },
      },

      // ═══════════════════════════════════════════════════════════════
      // BOX SHADOWS
      // ═══════════════════════════════════════════════════════════════
      boxShadow: {
        // ── Glass Shadows ────────────────────────────────────────────
        'glass':         '0 8px 32px rgba(0, 0, 0, 0.08), 0 1px 0 rgba(255, 255, 255, 0.5) inset',
        'glass-md':      '0 16px 48px rgba(0, 0, 0, 0.12), 0 1px 0 rgba(255, 255, 255, 0.6) inset',
        'glass-lg':      '0 24px 64px rgba(0, 0, 0, 0.16), 0 1px 0 rgba(255, 255, 255, 0.7) inset',

        // ── Glow Shadows ─────────────────────────────────────────────
        'glow-neural':   '0 0 20px rgba(13, 148, 136, 0.4), 0 0 60px rgba(13, 148, 136, 0.15)',
        'glow-cortex':   '0 0 20px rgba(124, 58, 237, 0.4), 0 0 60px rgba(124, 58, 237, 0.15)',
        'glow-dopamine': '0 0 20px rgba(245, 158, 11, 0.4), 0 0 60px rgba(245, 158, 11, 0.15)',
        'glow-soft':     '0 4px 20px rgba(0, 0, 0, 0.08)',

        // ── Card Shadows ─────────────────────────────────────────────
        'card':          '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03)',
        'card-hover':    '0 20px 60px rgba(13, 148, 136, 0.12), 0 8px 24px rgba(0, 0, 0, 0.06)',
        'card-neural':   '0 4px 24px rgba(13, 148, 136, 0.15)',

        // ── Button Shadows ───────────────────────────────────────────
        'btn-neural':    '0 4px 14px rgba(13, 148, 136, 0.35)',
        'btn-cortex':    '0 4px 14px rgba(124, 58, 237, 0.35)',

        // ── Neon Shadows ─────────────────────────────────────────────
        'neon-teal':     '0 0 5px #0D9488, 0 0 20px #0D948860, 0 0 40px #0D948830',
        'neon-violet':   '0 0 5px #7C3AED, 0 0 20px #7C3AED60, 0 0 40px #7C3AED30',
      },

      // ═══════════════════════════════════════════════════════════════
      // BACKDROP BLUR
      // ═══════════════════════════════════════════════════════════════
      backdropBlur: {
        'xs':  '2px',
        'sm':  '4px',
        'md':  '8px',
        'lg':  '12px',
        'xl':  '16px',
        '2xl': '24px',
        '3xl': '32px',
      },

      // ═══════════════════════════════════════════════════════════════
      // BORDER RADIUS
      // ═══════════════════════════════════════════════════════════════
      borderRadius: {
        'xs': '4px',
        'sm': '6px',
        'DEFAULT': '8px',
        'md': '10px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '20px',
        '3xl': '24px',
        '4xl': '32px',
      },

      // ═══════════════════════════════════════════════════════════════
      // SPACING (8px grid)
      // ═══════════════════════════════════════════════════════════════
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '26': '6.5rem',
        '30': '7.5rem',
      },

      // ═══════════════════════════════════════════════════════════════
      // TRANSITION TIMING
      // ═══════════════════════════════════════════════════════════════
      transitionTimingFunction: {
        'bounce-in':  'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'smooth':     'cubic-bezier(0.4, 0, 0.2, 1)',
        'gentle':     'cubic-bezier(0.25, 0.1, 0.25, 1)',
      },

      // ═══════════════════════════════════════════════════════════════
      // Z-INDEX SCALE
      // ═══════════════════════════════════════════════════════════════
      zIndex: {
        'dropdown': '100',
        'sticky':   '200',
        'modal':    '300',
        'popover':  '400',
        'tooltip':  '500',
        'toast':    '600',
      },
    },
  },
  plugins: [],
};

export default config;
