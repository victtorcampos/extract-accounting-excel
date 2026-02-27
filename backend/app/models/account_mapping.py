from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AccountMapping(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cnpj_empresa: str = Field(index=True, max_length=14)
    conta_cliente: str = Field(index=True)
    conta_contabilidade: str
    tipo: str  # 'DEBITO' ou 'CREDITO'
    last_used: datetime = Field(default_factory=datetime.utcnow)
