"""Rotas HTTP de lançamento de lote — sem lógica de negócio."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_session
from app.models.protocolo import Protocolo
from app.repositories.protocolo_repository import ProtocoloRepository
from app.schemas.lote import LoteContabilCreate
from app.services.lote_processor import LoteProcessor

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _run_background(protocolo_id: int, arquivo: str, layout: str) -> None:
    from sqlalchemy.orm import sessionmaker

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        await LoteProcessor(db).processar(protocolo_id, arquivo, layout)


@router.post("/lancamento_lote_contabil")
async def criar_lote(
    lote: LoteContabilCreate, db: SessionDep, bg: BackgroundTasks
) -> dict:
    repo = ProtocoloRepository(db)
    if await repo.buscar_por_numero(lote.protocolo):
        raise HTTPException(400, "Protocolo já existente.")

    novo = await repo.salvar(
        Protocolo(
            numero_protocolo=lote.protocolo,
            cnpj=lote.cnpj,
            periodo=lote.periodo,
            codigo_matriz=lote.codigo_matriz,
            codigo_filial=lote.codigo_filial,
            email_destinatario=lote.email_destinatario,
            lote_inicial=lote.lote_inicial,
            arquivo_base64_raw=lote.arquivo_base64,
            status="PENDING",
        )
    )
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
            "sucesso": True,
            "protocolo": p.numero_protocolo,
            "status": p.status,
            "resultado": p.arquivo_txt_base64 if p.status == "COMPLETED" else "pendente",
            "error_message": p.error_message if p.status == "ERROR" else None,
        }

    if cnpj:
        protocolos = await repo.buscar_por_cnpj(cnpj)
        return {
            "sucesso": True,
            "protocolos": [
                {
                    "id": p.id,
                    "protocolo": p.numero_protocolo,
                    "status": p.status,
                    "data": p.created_at,
                    "error_message": p.error_message if p.status == "ERROR" else None,
                }
                for p in protocolos
            ],
        }

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
    return {
        "sucesso": True,
        "mensagem": f"Protocolo {p.numero_protocolo} excluído.",
        "entries_deletados": entries_count,
    }
