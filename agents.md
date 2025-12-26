# Frontend setup (webapp)

## Location
- Frontend lives in `webapp/` (Vite + React + TypeScript + Tailwind).

## Entry points
- App shell: `webapp/src/App.tsx`
- Client bootstrap: `webapp/src/main.tsx`
- Styles: `webapp/src/styles.css` (Tailwind + app-level styles)
- API helpers: `webapp/src/api.ts`

## Environment
- API base URL comes from `VITE_API_URL` (defaults to `http://127.0.0.1:8000`).
- Configure via `.env` in `webapp/` or by exporting the env var before running Vite.

## Notes
- Tailwind config lives in `webapp/tailwind.config.cjs`.
- This app relies on keyboard shortcuts and quick navigation, so keep interactions snappy and avoid heavy layout thrash.
