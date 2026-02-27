from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, SQLModel


class StagingEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    protocolo_id: int = Field(foreign_key="protocolo.id")
    data_lancamento: str
    valor: float
    conta_debito_raw: str
    conta_credito_raw: str
    historico: str
    cod_historico: str = Field(default="")
    protocolo: Mapped["Protocolo"] = Relationship(
        sa_relationship=relationship(back_populates="entries")
    )
