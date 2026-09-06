# CalorieQ — Frontend

**Stack:** React 19 · TypeScript · Vite 8 · Tailwind CSS v4 · shadcn/ui · TanStack Query v5 · Zustand · Recharts · React Router v6

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Node.js | **≥20.19** (LTS recommended) | https://nodejs.org |
| npm | ≥10 (ships with Node) | — |

> Vite 8 and its bundler (rolldown) require Node ≥20.19. Earlier versions will fail at build time.

The backend must be running on `http://localhost:8000` before you start the frontend. See `backend/README.md`.

---

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # default points to http://localhost:8000/api/v1
npm run dev
```

App opens at `http://localhost:5173`.

---

## Available Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Start dev server with HMR |
| `npm run build` | Type-check + production build → `dist/` |
| `npm run preview` | Serve the production build locally |

---

## Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Backend API base URL |

---

## Project Structure

```
frontend/
├── src/
│   ├── api/          # Axios client + per-resource query/mutation hooks
│   ├── components/
│   │   ├── layouts/  # AppLayout (navbar), AuthLayout
│   │   └── ui/       # shadcn-generated primitives
│   ├── pages/        # Route-level components
│   ├── store/        # Zustand slices (authStore, dateStore)
│   ├── lib/          # cn(), tz constant, formatters
│   ├── types/        # API response/request types
│   └── hooks/        # Shared custom hooks
├── docs/
│   ├── requirements.md   # UI/UX design spec
│   └── build-plan.md     # Incremental build phases + status
├── .env.example
└── vite.config.ts
```

---

## Design System

Dark-only theme inspired by Samsung Health. CSS variables in `src/index.css` via Tailwind v4 `@theme`. Key tokens:

| Token | Value | Usage |
|---|---|---|
| `--primary` | Green `oklch(0.72 0.18 145)` | Accent, CTAs, focus ring |
| `--background` | Deep navy | Page background |
| `--card` | Slightly lighter navy | Card surfaces |
| `--muted-foreground` | Subdued slate | Secondary text |

---

## Build Progress

See `docs/build-plan.md` for the full 12-phase plan and current status.
