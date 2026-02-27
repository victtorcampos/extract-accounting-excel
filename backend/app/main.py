import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.api.v1.endpoints import lote, pendencia

# FRONTEND_DIR: env var para Docker (/app/frontend) ou fallback para dev
_dev_frontend = Path(__file__).resolve().parent.parent.parent / "frontend"
FRONTEND_DIR = Path(os.environ.get("FRONTEND_DIR") or _dev_frontend)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Escritório Contábil Sorriso API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes (prefixo /api para não colidir com rotas do React Router) ──────
app.include_router(lote.router, prefix="/api", tags=["Lançamentos"])
app.include_router(pendencia.router, prefix="/api", tags=["Pendências"])

# ── Assets estáticos do build React (/assets/, /favicon.svg) ─────────────────
_assets_dir = FRONTEND_DIR / "assets"
if _assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

_favicon = FRONTEND_DIR / "favicon.svg"


@app.get("/favicon.svg", include_in_schema=False)
async def favicon():
    if _favicon.exists():
        return FileResponse(_favicon)
    raise HTTPException(404)


# ── SPA catch-all: todas as rotas não-API devolvem index.html ─────────────────
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    raise HTTPException(
        status_code=404,
        detail="Frontend não encontrado. Execute 'npm run build' na pasta frontend/.",
    )
