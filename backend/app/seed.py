import asyncio
from sqlmodel import Session, select
from app.database import engine, init_db
from app.models.database_models import LayoutExcel

async def seed():
    await init_db()
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

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
                col_conta_debito="G",
                col_conta_credito="H"
            )
            session.add(layout)
            await session.commit()
            print("Layout 'layout_brastelha_1' inserido com sucesso!")
        else:
            print("Layout já existe no banco.")

if __name__ == "__main__":
    asyncio.run(seed())