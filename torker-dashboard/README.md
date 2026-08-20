# Torker Dashboard (React)

Dashboard moderno con **React + Vite + Tailwind + Lucide React**.

## Desarrollo

```powershell
cd torker-dashboard
npm install
npm run dev
```

Abre `http://localhost:5173` — el API se proxea a `http://127.0.0.1:8000/api`.

Login previo en Torker (`/pages/torker/`) para tener tokens Supabase en localStorage.

## Producción local (Django)

```powershell
npm run build
```

Genera estáticos en `pages/dashboard/app/`. Django los sirve en:

`http://127.0.0.1:8000/pages/dashboard/app/`

## Stack

- React 19 + TypeScript
- React Router
- Tailwind CSS 3
- Lucide React (iconos)
