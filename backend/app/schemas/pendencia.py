from typing import Literal

from pydantic import BaseModel


class ResolvePendenciaRequest(BaseModel):
    protocolo_id: int
    conta_cliente: str
    conta_contabilidade: str
    tipo: Literal["DEBITO", "CREDITO"]
    cnpj_empresa: str
