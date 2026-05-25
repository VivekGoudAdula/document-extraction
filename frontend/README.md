# Document Intelligence — Frontend

Modern Next.js UI for the AI-powered document extraction platform.

## Features

- Drag-and-drop and browse upload (PDF, PNG, JPG, JPEG)
- Live file preview (images + PDF iframe)
- Extraction prompt textarea
- Axios integration with FastAPI `POST /extract`
- Loading states and overlay spinner
- Collapsible JSON viewer with copy-to-clipboard
- Toast notifications (Sonner)
- Responsive enterprise layout (Tailwind CSS)

## Setup

```powershell
cd frontend
npm install
copy .env.example .env.local
```

Set `NEXT_PUBLIC_API_URL` to your FastAPI server (default `http://localhost:8000`).

Ensure the backend has CORS enabled for your frontend origin (default `*`).

## Run

```powershell
npm run dev
```

Open http://localhost:3000

### Turbopack cache errors (`Compaction failed`, `os error 3`, `GET / 404`)

These come from a corrupted `.next` dev cache (often after stopping dev mid-write or running two `npm run dev` instances).

1. Stop the dev server (`Ctrl+C`).
2. Close any other terminal running `next dev` on port 3000.
3. Clean and restart:

```powershell
npm run dev:clean
```

If issues persist, use webpack instead: `npm run dev:webpack`

## Stack

- Next.js 16 (App Router)
- React 19
- Tailwind CSS v4
- Axios
- Sonner (toasts)
