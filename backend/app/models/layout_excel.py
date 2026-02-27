from __future__ import annotations

from typing import Optional

from sqlmodel import Field, SQLModel


class LayoutExcel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(unique=True)
    col_data: str
    col_valor: str
    col_historico: str
    col_cod_historico: str = Field(default="N")
    col_conta_debito: str
    col_conta_credito: str
