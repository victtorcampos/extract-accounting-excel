from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.protocolo import Protocolo
from app.models.staging_entry import StagingEntry


class ProtocoloRepository:
    """Responsabilidade única: acesso a dados de Protocolo."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def buscar_por_numero(self, numero: str) -> Optional[Protocolo]:
        return (
            await self._db.execute(
                select(Protocolo).where(Protocolo.numero_protocolo == numero)
            )
        ).scalar_one_or_none()

    async def buscar_por_id(self, id: int) -> Optional[Protocolo]:
        return (
            await self._db.execute(
                select(Protocolo).where(Protocolo.id == id)
            )
        ).scalar_one_or_none()

    async def buscar_por_cnpj(self, cnpj: str) -> list[Protocolo]:
        return list(
            (
                await self._db.execute(
                    select(Protocolo).where(Protocolo.cnpj == cnpj)
                )
            ).scalars().all()
        )

    async def buscar_por_status(self, status: str) -> list[Protocolo]:
        return list(
            (
                await self._db.execute(
                    select(Protocolo).where(Protocolo.status == status)
                )
            ).scalars().all()
        )

    async def salvar(self, protocolo: Protocolo) -> Protocolo:
        self._db.add(protocolo)
        await self._db.commit()
        await self._db.refresh(protocolo)
        return protocolo

    async def deletar(self, protocolo: Protocolo, deletar_entries: bool = True) -> int:
        entries_count = 0
        if deletar_entries:
            entries = list(
                (
                    await self._db.execute(
                        select(StagingEntry).where(
                            StagingEntry.protocolo_id == protocolo.id
                        )
                    )
                ).scalars().all()
            )
            for entry in entries:
                await self._db.delete(entry)
            entries_count = len(entries)
        await self._db.delete(protocolo)
        await self._db.commit()
        return entries_count
