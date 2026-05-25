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
numpy 1.26.x
cv2 4.6.0.66
paddleocr 2.7.3
Downloading PaddleOCR models (one-time at build)...
PaddleOCR models cached under /opt/render/.paddleocr
=== Build OK ===
```

If you see `Model cache failed` or `No module named 'cv2'`, the build did not bake models into the image. The first `/extract` will download ~16MB from China (2–5+ minutes) and often time out.

Set **Environment** → `HOME` = `/opt/render` (also in `render.yaml`).

## Health check

`GET https://your-service.onrender.com/health` should show:

- `"paddleocr_version": "2.7.3"`
- `"numpy_ok_for_paddle": true`
- `"opencv_ok": true`
- After ~1–2 minutes of uptime: `"paddleocr_loaded": true` (background warmup)

## Upload times out / server restarts in logs

Typical causes on the **512MB free** plan:

1. **Models not cached at build** — logs show `download https://paddleocr.bj.bcebos.com/...` on the first request. Redeploy after build logs show successful model cache.
2. **First OCR is slow** — detection alone can take 30–60s on CPU. Wait until `/health` shows `paddleocr_loaded: true`, then upload.
3. **OOM kill** — if logs show `Running 'uvicorn...'` again right after `dt_boxes`, the process was killed for memory. Upgrade to **Starter (512MB+)** or disable heavy steps; TrOCR is off when `OCR_LOW_MEMORY=true`.

Frontend allows up to **10 minutes** for `/extract`; keep the tab open on the first run.
