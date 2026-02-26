from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, SQLModel

# 1. Tabela de Mapeamento (OK)
class AccountMapping(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cnpj_empresa: str = Field(index=True, max_length=14)
    conta_cliente: str = Field(index=True)
    conta_contabilidade: str
    tipo: str  # 'DEBITO' ou 'CREDITO'
    last_used: datetime = Field(default_factory=datetime.utcnow)

# 2. Tabela de Protocolos
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
    entries: Mapped[list["StagingEntry"]] = Relationship(
        sa_relationship=relationship(back_populates="protocolo")
    )

# 3. Tabela de Itens Pendentes (Staging)

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

# 4. Configuração de Layout (OK)
class LayoutExcel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(unique=True)
    col_data: str
    col_valor: str
    col_historico: str
    col_cod_historico: str = Field(default="N")
    col_conta_debito: str
    col_conta_credito: str