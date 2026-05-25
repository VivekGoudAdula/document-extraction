# Dev server: reload only watches app/ (not venv — avoids reload storms during pip install)
Set-Location $PSScriptRoot
& .\venv\Scripts\python.exe -m uvicorn app.main:app `
  --reload `
  --reload-dir app `
  --reload-exclude "venv/*" `
  --host 0.0.0.0 `
  --port 8000
