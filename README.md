# Sketchify Studio

Convert photos into eight sketch styles (Classic Pencil, Fine Pencil, Dark Pencil, Charcoal, Ink Outline, Line Art, Crosshatch, Cartoon Sketch) using classical computer vision. React + Vite frontend, FastAPI + OpenCV backend. No auth, no database, nothing stored on the server.

## Run locally

Backend (Python 3.11+):

```bash
cd backend
python -m venv venv
venv/Scripts/activate        # Windows; use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env         # set VITE_API_BASE_URL
npm run dev
```

Open http://localhost:5173 (the backend's `FRONTEND_ORIGIN` must match the origin you use).

## Tests

```bash
cd backend
python -m pytest
```

## Regenerating style thumbnails

The style-card thumbnails in `frontend/public/styles/` are produced by the app's own algorithms from a procedural sample scene:

```bash
cd backend
python scripts/make_thumbnails.py
```

## API

- `GET /api/health`
- `POST /api/sketch` (multipart): `file`, `style`, `width`, `height`, `format` (`png`|`jpg`), optional `preserve_aspect_ratio`, `quality` (10–100), `options` (JSON, each key 0–100: `intensity`, `line_thickness`, `contrast`, `detail`, `shading`).

Errors are JSON: `{"error": {"code", "message"}}` with statuses 400, 413, 415, 422, 500, plus 503 (server busy) and 504 (timeout).

## Deployment notes

- Frontend: `npm run build`, deploy `dist/` (set `VITE_API_BASE_URL` at build time).
- Backend: run `uvicorn app.main:app` without `--reload`, set `FRONTEND_ORIGIN` to the production origin(s), pin dependency versions, and enforce request-size limits at the proxy as well.
