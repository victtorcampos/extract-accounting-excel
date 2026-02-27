from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, SQLModel


class Protocolo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    numero_protocolo: str = Field(index=True, unique=True)
    cnpj: str = Field(index=True)
    periodo: str
    codigo_matriz: int = Field(default=0)
    codigo_filial: Optional[int] = Field(default=None)
    email_destinatario: str = Field(default="")
    status: str = Field(default="PENDING")
    arquivo_txt_base64: Optional[str] = None
    arquivo_base64_raw: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = Field(default=None, max_length=1000)
    lote_inicial: Optional[int] = Field(default=None)
    entries: Mapped[list["StagingEntry"]] = Relationship(
        sa_relationship=relationship(back_populates="protocolo")
    )
