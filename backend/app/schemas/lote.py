from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
import re

class LoteContabilCreate(BaseModel):
    protocolo: str = Field(..., description="Epoch Timestamp") #
    cnpj: str = Field(..., pattern=r"^\d{14}$") # Valida 14 dígitos
    codigo_matriz: int = Field(..., ge=1, le=10000)
    codigo_filial: Optional[int] = Field(None, ge=1, le=10000)
    periodo: str = Field(..., description="YYYY-MM") #
    lote_inicial: int = Field(default=1)
    email_destinatario: EmailStr #
    layout_nome: str # ex: layout_brastelha_1
    arquivo_base64: str = Field(..., description="Conteúdo do Excel em Base64") #

    @field_validator('cnpj')
    @classmethod
    def validate_cnpj_length(cls, v: str) -> str:
        if len(v) != 14:
            raise ValueError("CNPJ deve ter 14 dígitos")
        return v