from __future__ import annotations

from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class AccountMapping(SQLModel, table=True):
    """Mapeamento de De-Para de Contas por CNPJ"""
    id: Optional[int] = Field(default=None, primary_key=True)
    cnpj_empresa: str = Field(index=True, max_length=14)
    conta_cliente: str = Field(index=True)  # Conta vinda do Excel
    conta_contabilidade: str  # Conta reduzida do escritório
    tipo: str  # 'DEBITO' ou 'CREDITO'
    last_used: datetime = Field(default_factory=datetime.utcnow)


class Protocolo(SQLModel, table=True):
    """Controle de Lotes e Processamento"""
    id: Optional[int] = Field(default=None, primary_key=True)
    numero_protocolo: str = Field(index=True, unique=True)  # Epoch
    cnpj: str = Field(index=True)
    periodo: str  # YYYY-MM
    codigo_matriz: int = Field(default=0)
    codigo_filial: Optional[int] = Field(default=None)
    email_destinatario: str = Field(default="")
    lote_inicial: int = Field(default=1)
    status: str = Field(default="PENDING")  # PENDING, WAITING_MAPPING, COMPLETED, ERROR
    email_enviado: bool = Field(default=False)
    arquivo_txt_base64: Optional[str] = None  # Resultado final
    arquivo_base64_raw: Optional[str] = None  # Arquivo original para reprocessamento
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relacionamento com itens em espera
    staging_entries: List["StagingEntry"] = Relationship(back_populates="protocolo")


class StagingEntry(SQLModel, table=True):
    """Linhas do Excel que aguardam resolução de conta contábil"""
    id: Optional[int] = Field(default=None, primary_key=True)
    protocolo_id: int = Field(foreign_key="protocolo.id")

    # Dados crus da linha para re-processamento
    data_lancamento: str
    valor: float
    conta_debito_raw: str
    conta_credito_raw: str
    historico: str
    cod_historico: str = Field(default="")

    protocolo: Protocolo = Relationship(back_populates="staging_entries")


class LayoutExcel(SQLModel, table=True):
    """Configuração dinâmica de colunas do Excel"""
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(unique=True)  # ex: 'layout_brastelha_1'
    col_data: str  # 'E'
    col_valor: str  # 'L'
    col_historico: str  # 'O'
    col_cod_historico: str = Field(default="N")  # Coluna 'N' = Código Histórico
    col_conta_debito: str  # 'G'
    col_conta_credito: str  # 'H'
