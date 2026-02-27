# 🏗️ Proposta SOLID — extract-accounting-excel

> **Versão:** 1.0 | **Stack:** Python 3.12, FastAPI, SQLModel, SQLAlchemy 2.x  
> **Contexto:** Refatoração progressiva sem quebrar funcionalidade existente  
> **Estratégia:** 4 fases incrementais — cada fase é um PR independente

---

## 📊 Diagnóstico do Estado Atual

| Arquivo Atual | Violações SOLID | Impacto |
|---|---|---|
| `excel_parser.py` → `processar_excel_service()` | **SRP** — parsing + validação + mapeamento + geração num único função 230 linhas | Alto |
| `lote.py` → `criar_lote()`, `resolver_pendencia()` | **SRP** — lógica de negócio dentro do endpoint; **DIP** — `select(Protocolo)` direto no handler | Alto |
| `database_models.py` | **SRP** — todos os modelos num único arquivo | Médio |
| `lote.py` → `ResolvePendenciaRequest` | **ISP** — schema de request acoplado ao endpoint | Baixo |
| Sem `typing.Protocol` em nenhum lugar | **DIP** — zero abstrações, tudo concreto | Alto |

---

## 🎯 Estrutura de Arquivos Proposta

```
backend/app/
│
├── core/                          # 🆕 Abstrações e contratos (DIP + ISP)
│   ├── __init__.py
│   ├── protocols.py               # typing.Protocol — interfaces da aplicação
│   └── exceptions.py              # Exceções de domínio customizadas
│
├── models/                        # SRP — um arquivo por entidade
│   ├── __init__.py
│   ├── protocolo.py               # 🆕 class Protocolo(SQLModel, table=True)
│   ├── staging_entry.py           # 🆕 class StagingEntry(SQLModel, table=True)
│   ├── account_mapping.py         # 🆕 class AccountMapping(SQLModel, table=True)
│   └── layout_excel.py            # 🆕 class LayoutExcel(SQLModel, table=True)
│
├── schemas/                       # SRP — schemas por domínio
│   ├── __init__.py
│   ├── lote.py                    # LoteContabilCreate (existente, ok)
│   └── pendencia.py               # 🆕 ResolvePendenciaRequest (separado do endpoint)
│
├── repositories/                  # 🆕 Camada de acesso a dados (DIP)
│   ├── __init__.py
│   ├── protocolo_repository.py    # ProtocoloRepository
│   └── account_mapping_repository.py # AccountMappingRepository
│
├── services/                      # SRP — um serviço por responsabilidade
│   ├── __init__.py
│   ├── excel_parser.py            # ExcelParser — só parsing de bytes → linhas brutas
│   ├── periodo_validator.py       # 🆕 PeriodoValidator — só validação de datas
│   ├── conta_mapper.py            # 🆕 ContaMapper — só resolução de contas
│   └── lote_processor.py          # 🆕 LoteProcessor — orquestrador (usa os 3 acima)
│
├── api/v1/endpoints/
│   ├── lote.py                    # Só rotas HTTP, sem lógica de negócio
│   └── pendencia.py               # 🆕 Rotas de pendências separadas
│
├── database.py                    # Existente, ok
├── main.py                        # Existente, registrar novos routers
└── seed.py                        # Existente, ok
```

---

## 📐 Nomenclatura SOLID Adotada

| Tipo | Convenção | Exemplos do Projeto |
|---|---|---|
| **Arquivo** | `snake_case`, substantivo do domínio | `periodo_validator.py`, `conta_mapper.py` |
| **Classe Concreta** | `PascalCase`, substantivo | `ExcelParser`, `PeriodoValidator`, `ContaMapper` |
| **Protocolo/Interface** | `PascalCase` + sufixo `Protocol` ou substantivo | `LoteProcessorProtocol`, `RepositorioProtocol` |
| **Método/Função** | `snake_case`, verbo + substantivo | `parsear_linhas()`, `validar_periodo()`, `resolver_conta()` |
| **Exceção** | `PascalCase` + sufixo `Error` ou `Exception` | `PeriodoInvalidoError`, `LayoutNaoEncontradoError` |
| **Repositório** | `PascalCase` + sufixo `Repository` | `ProtocoloRepository`, `AccountMappingRepository` |
| **Schema entrada** | `PascalCase` + sufixo `Create`/`Request` | `LoteContabilCreate`, `ResolvePendenciaRequest` |

---

## 🚀 Fases de Implementação

---

### FASE 1 — Fundação: `core/` + Modelos separados
**Princípios:** SRP  
**Esforço:** Baixo (renomeação + move de código)

**1.1 — `backend/app/core/exceptions.py`**
```python
"""Exceções de domínio da aplicação contábil."""

class LoteProcessamentoError(Exception):
    """Erro genérico no processamento de lote."""

class LayoutNaoEncontradoError(LoteProcessamentoError):
    """Layout Excel não cadastrado no banco."""
    def __init__(self, nome: str):
        super().__init__(f"Layout '{nome}' não encontrado.")

class PeriodoInvalidoError(LoteProcessamentoError):
    """Período no formato inválido ou fora do range."""

class LancamentoForaDoPeriodoError(LoteProcessamentoError):
    """Lançamentos encontrados fora do período declarado."""
    def __init__(self, total: int, periodo: str, exemplos: list[str]):
        detalhe = ", ".join(exemplos[:5])
        sufixo = f" (+{total-5} mais)" if total > 5 else ""
        super().__init__(
            f"Arquivo contém {total} lançamento(s) fora do período {periodo}. "
            f"Exemplos: {detalhe}{sufixo}"
        )
```

**1.2 — Separar `database_models.py` em 4 arquivos**  
Move cada classe para seu próprio arquivo em `models/`.  
Crie `models/__init__.py` re-exportando tudo para não quebrar imports existentes:

```python
# backend/app/models/__init__.py
from app.models.protocolo import Protocolo
from app.models.staging_entry import StagingEntry
from app.models.account_mapping import AccountMapping
from app.models.layout_excel import LayoutExcel

__all__ = ["Protocolo", "StagingEntry", "AccountMapping", "LayoutExcel"]
```

**Commit:**
```bash
git commit -m "refactor(models): separar database_models.py em módulos SRP

- feat(core): criar exceptions.py com hierarquia de erros de domínio
- refactor(models): Protocolo → models/protocolo.py
- refactor(models): StagingEntry → models/staging_entry.py
- refactor(models): AccountMapping → models/account_mapping.py
- refactor(models): LayoutExcel → models/layout_excel.py
- refactor(models): __init__.py preserva imports existentes (zero breaking change)"
```

---

### FASE 2 — Serviços: Decomposição do `excel_parser.py`
**Princípios:** SRP, OCP  
**Esforço:** Médio (extrair responsabilidades)

A função `processar_excel_service()` atual faz 5 coisas distintas. Cada uma vira um serviço:

**2.1 — `services/periodo_validator.py`** (SRP)
```python
"""Validação de período contábil."""
from app.core.exceptions import PeriodoInvalidoError, LancamentoForaDoPeriodoError
from datetime import datetime

class PeriodoValidator:
    """Responsabilidade única: validar se datas pertencem ao período declarado."""

    def __init__(self, periodo_str: str) -> None:
        self._periodo = self._parsear(periodo_str)

    @staticmethod
    def _parsear(periodo_str: str) -> tuple[int, int]:
        try:
            ano, mes = periodo_str.strip().split("-")
            ano_int, mes_int = int(ano), int(mes)
            if not (1 <= mes_int <= 12):
                raise PeriodoInvalidoError(f"Mês inválido: {mes_int}")
            if not (2000 <= ano_int <= 2100):
                raise PeriodoInvalidoError(f"Ano fora do range: {ano_int}")
            return (ano_int, mes_int)
        except (ValueError, AttributeError) as e:
            raise PeriodoInvalidoError(f"Formato inválido '{periodo_str}'. Use YYYY-MM.") from e

    def validar_data(self, data_str: str) -> bool:
        """Retorna True se DD/MM/YYYY pertence ao período."""
        try:
            dt = datetime.strptime(data_str, "%d/%m/%Y")
            ano_esp, mes_esp = self._periodo
            return dt.year == ano_esp and dt.month == mes_esp
        except (ValueError, AttributeError):
            return False

    def validar_ou_falhar(self, erros: list[tuple[int, str]]) -> None:
        """Lança LancamentoForaDoPeriodoError se houver erros acumulados."""
        if not erros:
            return
        ano, mes = self._periodo
        periodo_fmt = f"{mes:02d}/{ano}"
        exemplos = [f"Linha {l}: {d}" for l, d in erros]
        raise LancamentoForaDoPeriodoError(len(erros), periodo_fmt, exemplos)
```

**2.2 — `services/conta_mapper.py`** (SRP + DIP)
```python
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
```

**2.3 — `services/excel_parser.py`** (SRP — só parsing de bytes)
```python
"""Parser de bytes Excel → lista de linhas brutas."""
import base64
import io
from dataclasses import dataclass
from typing import Any
from datetime import datetime
from python_calamine import CalamineWorkbook
from app.models.layout_excel import LayoutExcel

@dataclass
class LinhaBruta:
    """Linha de lançamento extraída do Excel, sem enriquecimento."""
    data_formatada: str
    valor: float
    conta_debito_raw: str
    conta_credito_raw: str
    historico: str
    cod_historico: str

class ExcelParser:
    """Responsabilidade única: converter arquivo Excel em lista de LinhaBruta."""

    def __init__(self, layout: LayoutExcel) -> None:
        self._layout = layout

    def parsear(self, arquivo_base64: str) -> list[LinhaBruta]:
        """Decodifica base64 e extrai linhas brutas do Excel."""
        raw_b64 = arquivo_base64.split(",")[-1] if "," in arquivo_base64 else arquivo_base64
        file_bytes = base64.b64decode(raw_b64)
        workbook = CalamineWorkbook.from_filelike(io.BytesIO(file_bytes))
        sheet = workbook.get_sheet_by_index(0)

        idx_data    = self._col_idx(self._layout.col_data)
        idx_dia     = 5  # Fixo: V_Dia Lancamento
        idx_debito  = self._col_idx(self._layout.col_conta_debito)
        idx_credito = self._col_idx(self._layout.col_conta_credito)
        idx_valor   = self._col_idx(self._layout.col_valor)
        idx_cod     = self._col_idx(self._layout.col_cod_historico)
        idx_hist    = self._col_idx(self._layout.col_historico)

        linhas: list[LinhaBruta] = []
        min_cols = max(idx_data, idx_dia, idx_debito, idx_credito, idx_valor)

        for row in list(sheet.to_python())[1:]:
            if not row or len(row) <= min_cols:
                continue
            try:
                linha = LinhaBruta(
                    data_formatada=self._formatar_data(row[idx_data], row[idx_dia]),
                    valor=float(str(row[idx_valor]).replace(",", ".")),
                    conta_debito_raw=self._normalizar_conta(row[idx_debito]),
                    conta_credito_raw=self._normalizar_conta(row[idx_credito]),
                    historico=str(row[idx_hist] if len(row) > idx_hist else ""),
                    cod_historico=str(row[idx_cod] if len(row) > idx_cod else ""),
                )
                if linha.conta_debito_raw and linha.conta_credito_raw:
                    linhas.append(linha)
            except (ValueError, IndexError, TypeError):
                continue

        return linhas

    @staticmethod
    def _col_idx(letra: str) -> int:
        return ord(letra.upper()) - ord("A")

    @staticmethod
    def _normalizar_conta(value: Any) -> str:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value).strip()

    @staticmethod
    def _formatar_data(raw_date: Any, dia: Any) -> str:
        if isinstance(raw_date, datetime):
            mes, ano = raw_date.month, raw_date.year
        else:
            s = str(raw_date).strip()
            try:
                dt = datetime.fromisoformat(s[:10])
                mes, ano = dt.month, dt.year
            except ValueError:
                return s
        try:
            dia_int = int(float(str(dia)))
        except (ValueError, TypeError):
            dia_int = 1
        return f"{dia_int:02d}/{mes:02d}/{ano}"
```

**2.4 — `services/lote_processor.py`** (SRP — orquestrador)
```python
"""Orquestrador do processamento de lote contábil."""
import base64
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LayoutNaoEncontradoError
from app.models.protocolo import Protocolo
from app.models.staging_entry import StagingEntry
from app.models.layout_excel import LayoutExcel
from app.services.excel_parser import ExcelParser
from app.services.periodo_validator import PeriodoValidator
from app.services.conta_mapper import ContaMapper

class LoteProcessor:
    """Orquestra: layout → parser → validator → mapper → persistência."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def processar(self, protocolo_id: int, arquivo_base64: str, layout_nome: str) -> None:
        try:
            layout = await self._carregar_layout(layout_nome)
            protocolo = (await self._db.execute(
                select(Protocolo).where(Protocolo.id == protocolo_id)
            )).scalar_one()

            validator = PeriodoValidator(protocolo.periodo)
            parser    = ExcelParser(layout)
            mapper    = ContaMapper(protocolo.cnpj, self._db)

            linhas = parser.parsear(arquivo_base64)

            erros_periodo: list[tuple[int, str]] = []
            pendencias: list[StagingEntry] = []
            linhas_txt: list[str] = []

            for idx, linha in enumerate(linhas, start=2):
                if not validator.validar_data(linha.data_formatada):
                    erros_periodo.append((idx, linha.data_formatada))
                    continue

                c_debito  = await mapper.resolver(linha.conta_debito_raw, "DEBITO")
                c_credito = await mapper.resolver(linha.conta_credito_raw, "CREDITO")

                if not c_debito or not c_credito:
                    pendencias.append(StagingEntry(
                        protocolo_id=protocolo_id,
                        data_lancamento=linha.data_formatada,
                        valor=linha.valor,
                        conta_debito_raw=linha.conta_debito_raw,
                        conta_credito_raw=linha.conta_credito_raw,
                        historico=linha.historico,
                        cod_historico=linha.cod_historico,
                    ))
                else:
                    n_filial = str(protocolo.codigo_filial or "")
                    valor_br = f"{linha.valor:.2f}".replace(".", ",")
                    linhas_txt.extend([
                        "|6000|X||||",
                        f"|6100|{linha.data_formatada}|{c_debito}|{c_credito}|{valor_br}||{linha.historico}|VICTOR|{n_filial}||"
                    ])

            validator.validar_ou_falhar(erros_periodo)

            if pendencias:
                self._db.add_all(pendencias)
                protocolo.status = "WAITING_MAPPING"
            else:
                cabecalho = f"|0000|{protocolo.cnpj}|"
                txt_final = "\n".join([cabecalho, *linhas_txt])
                protocolo.arquivo_txt_base64 = base64.b64encode(txt_final.encode()).decode()
                protocolo.status = "COMPLETED"

            await self._db.commit()

        except Exception as e:
            await self._db.rollback()
            print(f"❌ ERRO [proto={protocolo_id}]: {e}")
            await self._salvar_erro(protocolo_id, str(e))

    async def _carregar_layout(self, nome: str) -> LayoutExcel:
        layout = (await self._db.execute(
            select(LayoutExcel).where(LayoutExcel.nome == nome)
        )).scalar_one_or_none()
        if not layout:
            raise LayoutNaoEncontradoError(nome)
        return layout

    async def _salvar_erro(self, protocolo_id: int, mensagem: str) -> None:
        try:
            proto = (await self._db.execute(
                select(Protocolo).where(Protocolo.id == protocolo_id)
            )).scalar_one_or_none()
            if proto:
                proto.status = "ERROR"
                proto.error_message = mensagem[:1000]
                await self._db.commit()
        except Exception:
            pass
```

**Commit:**
```bash
git commit -m "refactor(services): decompor excel_parser.py em serviços SRP

- feat(services): PeriodoValidator — validação de datas isolada
- feat(services): ContaMapper — resolução de contas com cache
- refactor(services): ExcelParser — só parsing bytes → LinhaBruta
- feat(services): LoteProcessor — orquestrador de alto nível
- feat(core): LancamentoForaDoPeriodoError, LayoutNaoEncontradoError"
```

---

### FASE 3 — Repositórios: Camada de Dados (DIP)
**Princípios:** DIP, SRP  
**Esforço:** Médio

**3.1 — `core/protocols.py`**
```python
"""Protocolos (interfaces) da aplicação — DIP via typing.Protocol."""
from typing import Protocol, Optional
from app.models.protocolo import Protocolo

class ProtocoloRepositoryProtocol(Protocol):
    async def buscar_por_numero(self, numero: str) -> Optional[Protocolo]: ...
    async def buscar_por_id(self, id: int) -> Optional[Protocolo]: ...
    async def salvar(self, protocolo: Protocolo) -> Protocolo: ...
    async def deletar(self, protocolo: Protocolo, deletar_entries: bool = True) -> int: ...
```

**3.2 — `repositories/protocolo_repository.py`**
```python
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.protocolo import Protocolo
from app.models.staging_entry import StagingEntry

class ProtocoloRepository:
    """Responsabilidade única: acesso a dados de Protocolo."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def buscar_por_numero(self, numero: str) -> Optional[Protocolo]:
        return (await self._db.execute(
            select(Protocolo).where(Protocolo.numero_protocolo == numero)
        )).scalar_one_or_none()

    async def buscar_por_cnpj(self, cnpj: str) -> list[Protocolo]:
        return list((await self._db.execute(
            select(Protocolo).where(Protocolo.cnpj == cnpj)
        )).scalars().all())

    async def buscar_por_status(self, status: str) -> list[Protocolo]:
        return list((await self._db.execute(
            select(Protocolo).where(Protocolo.status == status)
        )).scalars().all())

    async def salvar(self, protocolo: Protocolo) -> Protocolo:
        self._db.add(protocolo)
        await self._db.commit()
        await self._db.refresh(protocolo)
        return protocolo

    async def deletar(self, protocolo: Protocolo, deletar_entries: bool = True) -> int:
        entries_count = 0
        if deletar_entries:
            entries = list((await self._db.execute(
                select(StagingEntry).where(StagingEntry.protocolo_id == protocolo.id)
            )).scalars().all())
            for entry in entries:
                await self._db.delete(entry)
            entries_count = len(entries)
        await self._db.delete(protocolo)
        await self._db.commit()
        return entries_count
```

**Commit:**
```bash
git commit -m "feat(repositories): camada de acesso a dados — DIP

- feat(repositories): ProtocoloRepository com CRUD completo
- feat(core): ProtocoloRepositoryProtocol (typing.Protocol)
- refactor(lote.py): substituir select() inline por ProtocoloRepository"
```

---

### FASE 4 — Endpoints: Limpar Handlers (SRP + DIP)
**Princípios:** SRP, DIP  
**Esforço:** Baixo

**4.1 — `api/v1/endpoints/lote.py`** (refatorado)
```python
"""Rotas HTTP de lançamento de lote — sem lógica de negócio."""
from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_session
from app.schemas.lote import LoteContabilCreate
from app.models.protocolo import Protocolo
from app.repositories.protocolo_repository import ProtocoloRepository
from app.services.lote_processor import LoteProcessor

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _run_background(protocolo_id: int, arquivo: str, layout: str) -> None:
    from sqlalchemy.orm import sessionmaker
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        await LoteProcessor(db).processar(protocolo_id, arquivo, layout)


@router.post("/lancamento_lote_contabil")
async def criar_lote(lote: LoteContabilCreate, db: SessionDep, bg: BackgroundTasks) -> dict:
    repo = ProtocoloRepository(db)
    if await repo.buscar_por_numero(lote.protocolo):
        raise HTTPException(400, "Protocolo já existente.")

    novo = await repo.salvar(Protocolo(
        numero_protocolo=lote.protocolo,
        cnpj=lote.cnpj,
        periodo=lote.periodo,
        codigo_matriz=lote.codigo_matriz,
        codigo_filial=lote.codigo_filial,
        email_destinatario=lote.email_destinatario,
        lote_inicial=lote.lote_inicial,
        arquivo_base64_raw=lote.arquivo_base64,
        status="PENDING",
    ))
    bg.add_task(_run_background, novo.id, lote.arquivo_base64, lote.layout_nome)
    return {"sucesso": True, "protocolo": lote.protocolo}


@router.get("/lancamento_lote_contabil")
async def consultar_lote(
    db: SessionDep,
    protocolo: Annotated[str | None, Query()] = None,
    cnpj: Annotated[str | None, Query()] = None,
) -> dict:
    repo = ProtocoloRepository(db)

    if protocolo:
        p = await repo.buscar_por_numero(protocolo)
        if not p:
            raise HTTPException(404, "Protocolo não encontrado.")
        return {
            "sucesso": True, "protocolo": p.numero_protocolo, "status": p.status,
            "resultado": p.arquivo_txt_base64 if p.status == "COMPLETED" else "pendente",
            "error_message": p.error_message if p.status == "ERROR" else None,
        }

    if cnpj:
        protocolos = await repo.buscar_por_cnpj(cnpj)
        return {"sucesso": True, "protocolos": [
            {"id": p.id, "protocolo": p.numero_protocolo, "status": p.status,
             "data": p.created_at, "error_message": p.error_message if p.status == "ERROR" else None}
            for p in protocolos
        ]}

    raise HTTPException(400, "Informe protocolo ou cnpj.")


@router.delete("/lancamento_lote_contabil/{numero_protocolo}")
async def deletar_protocolo(
    numero_protocolo: Annotated[str, Path(description="Número do protocolo")],
    db: SessionDep,
) -> dict:
    repo = ProtocoloRepository(db)
    p = await repo.buscar_por_numero(numero_protocolo)
    if not p:
        raise HTTPException(404, "Protocolo não encontrado.")
    if p.status == "PENDING":
        raise HTTPException(409, "Aguarde o processamento antes de excluir.")
    entries_count = await repo.deletar(p)
    return {"sucesso": True, "mensagem": f"Protocolo {p.numero_protocolo} excluído.", "entries_deletados": entries_count}
```

**Commit:**
```bash
git commit -m "refactor(endpoints): handlers limpos usando Repository + LoteProcessor

- refactor(lote.py): eliminar select() inline nos handlers
- refactor(lote.py): criar_lote usa ProtocoloRepository.salvar()
- refactor(lote.py): consultar_lote usa ProtocoloRepository.buscar_*()
- refactor(lote.py): deletar_protocolo usa ProtocoloRepository.deletar()
- refactor(lote.py): background usa LoteProcessor.processar()"
```

---

## 📋 Mapeamento SOLID → Arquivo

| Princípio | Onde se aplica |
|---|---|
| **S** — Single Responsibility | `models/` 1 arquivo/entidade; `services/` 1 classe/responsabilidade |
| **O** — Open/Closed | `ExcelParser` extensível (novo `LayoutExcel` = novo `ExcelParser`); `ContaMapper` extensível para cache externo |
| **L** — Liskov Substitution | `PeriodoValidator`, `ContaMapper`, `LoteProcessor` são substituíveis por mocks em testes |
| **I** — Interface Segregation | `schemas/pendencia.py` separado de `lote.py`; `ProtocoloRepositoryProtocol` focado |
| **D** — Dependency Inversion | `LoteProcessor(db)` injeta `AsyncSession`; endpoints recebem `ProtocoloRepository` |

---

## ⚡ Ordem de Execução (Sem Quebrar Nada)

```
Fase 1 → Fase 2 → Fase 3 → Fase 4

Fase 1: Sem risco — só mover código, __init__.py preserva imports
Fase 2: Baixo risco — serviços novos, excel_parser.py atual pode coexistir
Fase 3: Médio risco — substituir select() inline por Repository nos endpoints
Fase 4: Médio risco — refatorar handlers para usar novas classes
```

---
