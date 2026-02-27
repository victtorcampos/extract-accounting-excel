from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_mapping import AccountMapping


class AccountMappingRepository:
    """Responsabilidade única: acesso a dados de AccountMapping."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def buscar(
        self, cnpj_empresa: str, conta_cliente: str, tipo: str
    ) -> Optional[AccountMapping]:
        return (
            await self._db.execute(
                select(AccountMapping).where(
                    AccountMapping.cnpj_empresa == cnpj_empresa,
                    AccountMapping.conta_cliente == conta_cliente,
                    AccountMapping.tipo == tipo,
                )
            )
        ).scalar_one_or_none()

    async def salvar_ou_atualizar(
        self,
        cnpj_empresa: str,
        conta_cliente: str,
        conta_contabilidade: str,
        tipo: str,
    ) -> AccountMapping:
        existing = await self.buscar(cnpj_empresa, conta_cliente, tipo)
        if existing:
            existing.conta_contabilidade = conta_contabilidade
            await self._db.commit()
            return existing
        novo = AccountMapping(
            cnpj_empresa=cnpj_empresa,
            conta_cliente=conta_cliente,
            conta_contabilidade=conta_contabilidade,
            tipo=tipo,
        )
        self._db.add(novo)
        await self._db.commit()
        await self._db.refresh(novo)
        return novo
