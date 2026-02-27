"""Resolução de contas cliente → contabilidade."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account_mapping import AccountMapping


class ContaMapper:
    """Responsabilidade única: resolver códigos de conta via DB com cache."""

    def __init__(self, cnpj_empresa: str, db: AsyncSession) -> None:
        self._cnpj = cnpj_empresa
        self._db = db
        self._cache: dict[str, Optional[str]] = {}

    async def resolver(self, conta_raw: str, tipo: str) -> Optional[str]:
        """Retorna conta contábil mapeada ou None se pendente."""
        cache_key = f"{self._cnpj}:{tipo}:{conta_raw}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        stmt = (
            select(AccountMapping.conta_contabilidade)
            .where(
                AccountMapping.cnpj_empresa == self._cnpj,
                AccountMapping.conta_cliente == conta_raw,
                AccountMapping.tipo == tipo,
            )
            .limit(1)
        )
        resultado = (await self._db.execute(stmt)).scalar_one_or_none()
        self._cache[cache_key] = resultado
        return resultado
