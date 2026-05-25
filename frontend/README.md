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

## Vercel environment variables

| Variable | Value |
|----------|--------|
| `NEXT_PUBLIC_API_URL` | Your **Render backend URL** (e.g. `https://document-extraction-i7qv.onrender.com`) |
| `BACKEND_URL` | Same Render URL (server-only; powers `/api/health` proxy) |

Set for **Production** (and Preview). Redeploy after changing.

`/extract` still calls Render directly (OCR can take several minutes; Vercel serverless cannot proxy that). `/api/health` on Vercel wakes the backend without browser CORS issues.

On **Render**, set `FRONTEND_URL` to this Vercel URL so the API accepts browser requests.

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