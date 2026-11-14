import type { Config } from 'tailwindcss';

// Ledgerwise theme: neutral light grey canvas, dark navy text,
// warm muted orange/gold accents, slate-blue gradient highlights.
const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#ECEEF1',
        surface: '#F8F9FB',
        line: '#D9DDE3',
        navy: { DEFAULT: '#14213D', soft: '#3A4660', mute: '#6B7487' },
        gold: { DEFAULT: '#D4973B', soft: '#EBCF9C', deep: '#B27A26' },
        slateblue: { 300: '#8D9BB8', 400: '#6B7C9E', 500: '#55668A', 600: '#3F4E70', 700: '#2E3A56' },
        ok: '#3E8E6A',
        warn: '#C98A2B',
        bad: '#B8493F',
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      backgroundImage: {
        'slate-gradient': 'linear-gradient(135deg, #6B7C9E 0%, #3F4E70 100%)',
        'gold-gradient': 'linear-gradient(135deg, #E2AE5A 0%, #B27A26 100%)',
      },
      boxShadow: {
        card: '0 1px 2px rgba(20,33,61,0.06), 0 8px 24px rgba(20,33,61,0.06)',
        lift: '0 2px 4px rgba(20,33,61,0.08), 0 16px 32px rgba(20,33,61,0.12)',
      },
    },
  },
  plugins: [],
};
export default config;
