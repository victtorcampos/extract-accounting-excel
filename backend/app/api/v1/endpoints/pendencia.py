"""Rotas HTTP de pendências de mapeamento de contas."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_session
from app.models.account_mapping import AccountMapping
from app.models.protocolo import Protocolo
from app.models.staging_entry import StagingEntry
from app.repositories.account_mapping_repository import AccountMappingRepository
from app.repositories.protocolo_repository import ProtocoloRepository
from app.schemas.pendencia import ResolvePendenciaRequest
from app.services.lote_processor import LoteProcessor

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def _run_background(protocolo_id: int, arquivo: str, layout: str) -> None:
    from sqlalchemy.orm import sessionmaker

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        await LoteProcessor(db).processar(protocolo_id, arquivo, layout)


@router.get("/pendencias")
async def listar_pendencias(db: SessionDep) -> dict:
    """Lista todos os StagingEntry de protocolos com status WAITING_MAPPING."""
    repo = ProtocoloRepository(db)
    protocolos = await repo.buscar_por_status("WAITING_MAPPING")

    pendencias_list = []
    for p in protocolos:
        entries = list(
            (
                await db.execute(
                    select(StagingEntry).where(StagingEntry.protocolo_id == p.id)
                )
            ).scalars().all()
        )
        pendencias_list.append(
            {
                "protocolo_id": p.id,
                "numero_protocolo": p.numero_protocolo,
                "cnpj": p.cnpj,
                "entries": [
                    {
                        "id": e.id,
                        "conta_debito_raw": e.conta_debito_raw,
                        "conta_credito_raw": e.conta_credito_raw,
                        "data_lancamento": e.data_lancamento,
                        "valor": e.valor,
                        "historico": e.historico,
                        "cod_historico": e.cod_historico,
                    }
                    for e in entries
                ],
            }
        )

    return {"sucesso": True, "pendencias": pendencias_list}


@router.post("/pendencias/resolver")
async def resolver_pendencia(
    payload: ResolvePendenciaRequest,
    db: SessionDep,
    bg: BackgroundTasks,
) -> dict:
    """Persiste mapeamento de conta e reprocessa se todas as pendências forem resolvidas."""
    mapping_repo = AccountMappingRepository(db)
    await mapping_repo.salvar_ou_atualizar(
        cnpj_empresa=payload.cnpj_empresa,
        conta_cliente=payload.conta_cliente,
        conta_contabilidade=payload.conta_contabilidade,
        tipo=payload.tipo,
    )

    proto_repo = ProtocoloRepository(db)
    protocolo = await proto_repo.buscar_por_id(payload.protocolo_id)
    if not protocolo:
        raise HTTPException(404, "Protocolo não encontrado.")

    entries = list(
        (
            await db.execute(
                select(StagingEntry).where(
                    StagingEntry.protocolo_id == payload.protocolo_id
                )
            )
        ).scalars().all()
    )

    contas_sem_mapa: list[str] = []
    for entry in entries:
        for conta_raw, tipo in [
            (entry.conta_debito_raw, "DEBITO"),
            (entry.conta_credito_raw, "CREDITO"),
        ]:
            mapeamento = (
                await db.execute(
                    select(AccountMapping).where(
                        AccountMapping.cnpj_empresa == protocolo.cnpj,
                        AccountMapping.conta_cliente == conta_raw,
                        AccountMapping.tipo == tipo,
                    )
                )
            ).scalar_one_or_none()
            if not mapeamento:
                contas_sem_mapa.append(f"{tipo}:{conta_raw}")

    if not contas_sem_mapa:
        if protocolo.arquivo_base64_raw:
            for entry in entries:
                await db.delete(entry)
            await db.commit()
            bg.add_task(
                _run_background,
                protocolo.id,
                protocolo.arquivo_base64_raw,
                "layout_brastelha_1",
            )
            return {
                "sucesso": True,
                "mensagem": "Todas as pendências foram resolvidas. Reprocessando o arquivo...",
                "reprocessando": True,
            }
        return {
            "sucesso": True,
            "mensagem": "Mapeamento salvo. Arquivo original não disponível para reprocessamento.",
            "reprocessando": False,
        }

    return {
        "sucesso": True,
        "mensagem": f"Mapeamento salvo. Ainda restam {len(set(contas_sem_mapa))} conta(s) sem mapeamento.",
        "reprocessando": False,
        "contas_pendentes": list(set(contas_sem_mapa)),
    }
