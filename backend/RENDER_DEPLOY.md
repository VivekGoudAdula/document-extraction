# Render deployment checklist

## Service settings

| Setting | Value |
|---------|--------|
| **Root Directory** | `backend` |
| **Build Command** | `bash render-build.sh` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

Do **not** prefix the build command with `backend/` if Root Directory is already `backend`.

Wrong: `backend/ $ bash render-build.sh`  
Right: `bash render-build.sh`

## Required environment variables

- `OPENAI_API_KEY`
- `MONGO_URI` (MongoDB Atlas)
- `FRONTEND_URL` = `https://document-extraction-ultrion.vercel.app`
- `OCR_LOW_MEMORY` = `true`
- `PYTHON_VERSION` = `3.11.11`

## Build log must show

```
cv2 OK 4.6.0.66
paddleocr 2.7.3
=== Build OK ===
```

## Health check

`GET /health` should show `"paddleocr_version": "2.7.3"` and `"numpy_ok_for_paddle": true`.
