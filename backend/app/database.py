import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlmodel import SQLModel

# 1. Localiza a raiz do projeto de forma absoluta
BASE_DIR = (
    Path(__file__).resolve().parent.parent.parent
)  # Sobe de app para backend para raiz
DATA_DIR = BASE_DIR / "data"

print(DATA_DIR)

# 2. Garante que a pasta 'data' existe (Cria se não existir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "database.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(text("PRAGMA journal_mode=WAL;"))


async def get_session() -> AsyncSession:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
