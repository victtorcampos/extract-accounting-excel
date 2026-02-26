from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path

from app.database import init_db
from app.app.api.v1.endpoints import lote # Ajustado para o caminho das pastas atuais

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_PATH = BASE_DIR / "frontend" / "index.html"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa o banco (cria tabelas) na subida do app
    await init_db()
    yield

app = FastAPI(title="Escritório Contábil Sorriso API", lifespan=lifespan)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, substitua pelo IP/Porta específico do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_PATH)

app.include_router(lote.router, tags=["Lançamentos"])
# app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend"), name="static")