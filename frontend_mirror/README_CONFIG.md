# Config files explained

| File | What it does |
|---|---|
| `package.json` | Dependencies (React 18, Framer Motion, lucide-react; dev: Vite, TypeScript, Tailwind 3) and scripts `dev`, `build`, `preview`. |
| `vite.config.ts` | Vite build tool with the React plugin; dev server on port 5173. |
| `tsconfig.json` | TypeScript strict mode, JSX `react-jsx`, includes `src` and the two root `.ts` configs. Uses `vite/client` types so `import.meta.env` is typed. |
| `tailwind.config.ts` | Ledgerwise theme tokens: `canvas` (light grey), `navy` (text), `gold` (accent), `slateblue` (gradients), `ok/warn/bad` (status), Inter font, `slate-gradient` / `gold-gradient` backgrounds, `shadow-card` / `shadow-lift`. |
| `postcss.config.js` | Runs Tailwind and Autoprefixer on the CSS. |
| `index.html` | Page shell: loads the Inter font from Google Fonts and mounts `src/main.tsx` into `#root`. |
| `.env.example` | Copy to `.env`. Only variable: `VITE_API_BASE_URL` (the backend URL, no trailing slash). On Vercel set it in Project Settings, Environment Variables. |

## Headers on source files

Every `.ts` / `.tsx` / `.css` file under `src/` starts with a comment block: `Inputs`, `Outputs`, `File explanation`.
Files with real content (not just a header): `src/shared/types.ts`, `src/shared/constants.ts`, `src/api/endpoints.ts`. They are the contracts every other file connects through.
