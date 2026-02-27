"""Popula banco de dados com layouts iniciais."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from app.database import engine, init_db
from app.models.database_models import LayoutExcel


async def seed() -> None:
    """Insere layout padrão no banco se não existir."""
    await init_db()

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Verifica se já existe
        stmt = select(LayoutExcel).where(LayoutExcel.nome == "layout_brastelha_1")
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if not existing:
            layout = LayoutExcel(
                nome="layout_brastelha_1",
                col_data="E",
                col_valor="L",
                col_historico="O",
                col_cod_historico="N",
                col_conta_debito="G",
                col_conta_credito="H",
            )
            session.add(layout)
            await session.commit()
            print("✅ Layout 'layout_brastelha_1' inserido com sucesso!")
        else:
            print("ℹ️  Layout já existe no banco.")


if __name__ == "__main__":
    asyncio.run(seed())
