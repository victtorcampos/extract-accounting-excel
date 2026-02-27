from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_session
from app.models.database_models import AccountMapping, Protocolo, StagingEntry
from app.schemas.lote import LoteContabilCreate
from app.services.excel_parser import processar_excel_service

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class ResolvePendenciaRequest(BaseModel):
    protocolo_id: int
    conta_cliente: str
    conta_contabilidade: str
    tipo: Literal["DEBITO", "CREDITO"]
    cnpj_empresa: str


# Função auxiliar para gerenciar a sessão dentro da task de background
async def run_parsing_task(protocolo_id: int, arquivo_base64: str, layout_nome: str) -> None:
    from sqlalchemy.orm import sessionmaker

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        await processar_excel_service(protocolo_id, arquivo_base64, layout_nome, db)


@router.post("/lancamento_lote_contabil")
async def criar_lote(
    lote: LoteContabilCreate,
    db: SessionDep,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Recebe o formulário da Página 1, registra o protocolo e
    inicia o processamento do Excel em background.
    """
    # 1. Verificar se protocolo já existe
    query = select(Protocolo).where(Protocolo.numero_protocolo == lote.protocolo)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Protocolo já existente.")

    # 2. Criar registro inicial (Status PENDING) com todos os campos
    novo_protocolo = Protocolo(
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
    db.add(novo_protocolo)
    await db.commit()
    await db.refresh(novo_protocolo)

    # 3. Disparar o parsing em background (BackgroundTasks)
    background_tasks.add_task(
        run_parsing_task,
        novo_protocolo.id,
        lote.arquivo_base64,
        lote.layout_nome,
    )

    return {"sucesso": True, "protocolo": lote.protocolo}


@router.get("/lancamento_lote_contabil")
async def consultar_lote(
    db: SessionDep,
    protocolo: Annotated[str | None, Query()] = None,
    cnpj: Annotated[str | None, Query()] = None,
) -> dict:
    """
    Retorna detalhes de um protocolo específico ou lista protocolos por CNPJ.
    """
    if protocolo:
        query = select(Protocolo).where(Protocolo.numero_protocolo == protocolo)
        result = await db.execute(query)
        p = result.scalar_one_or_none()

        if not p:
            raise HTTPException(status_code=404, detail="Protocolo não encontrado")

        conteudo = p.arquivo_txt_base64 if p.status == "COMPLETED" else "pendente"

        return {
            "sucesso": True,
            "protocolo": p.numero_protocolo,
            "status": p.status,
            "resultado": conteudo,
            "error_message": p.error_message if p.status == "ERROR" else None  # ✅ Incluir mensagem de erro se status for ERROR
        }

    if cnpj:
        query = select(Protocolo).where(Protocolo.cnpj == cnpj)
        result = await db.execute(query)
        protocolos = result.scalars().all()
        return {
            "sucesso": True,
            "protocolos": [
                {"protocolo": p.numero_protocolo, "status": p.status, "data": p.created_at, "error_message": p.error_message if p.status == "ERROR" else None}
                for p in protocolos
            ],
        }

    raise HTTPException(status_code=400, detail="Informe protocolo ou cnpj")


@router.get("/pendencias")
async def listar_pendencias(db: SessionDep) -> dict:
    """
    Lista todos os StagingEntry de protocolos com status WAITING_MAPPING,
    agrupados por protocolo. Usado pela Página 2.
    """ 
    stmt = select(Protocolo).where(Protocolo.status == "WAITING_MAPPING")
    result = await db.execute(stmt)
    protocolos = result.scalars().all()

    pendencias_list = []
    for p in protocolos:
        stmt_entries = select(StagingEntry).where(StagingEntry.protocolo_id == p.id)
        entries_result = await db.execute(stmt_entries)
        entries = entries_result.scalars().all()

        pendencias_list.append({
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
        })

    return {"sucesso": True, "pendencias": pendencias_list}

@router.delete("/lancamento_lote_contabil/{numero_protocolo}")
async def delete_protocolo(
    numero_protocolo: Annotated[int, Path(gt=0, description="ID interno do protocolo (auto-increment)")],
    db: SessionDep,
) -> dict:
    """
    Exclui um protocolo e seus StagingEntry associados (cascade).
    Retorna erro 404 se protocolo não existir.
    Retorna erro 409 se protocolo estiver em processamento (PENDING).
    """
    # 1. Buscar protocolo
    stmt = select(Protocolo).where(Protocolo.numero_protocolo == numero_protocolo)
    
    protocolo : Protocolo = (await db.execute(stmt)).scalar_one_or_none()
        
    if not protocolo:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado.")
    
    # 2. Validação de segurança: impedir exclusão durante processamento
    if protocolo.status == "PENDING":
        raise HTTPException(
            status_code=409,
            detail="Protocolo em processamento. Aguarde finalização antes de excluir."
        )
    
    # 3. Deletar StagingEntry manualmente (SQLite não tem CASCADE automático via FK)
    stmt_entries = select(StagingEntry).where(StagingEntry.protocolo_id == numero_protocolo)
    entries = (await db.execute(stmt_entries)).scalars().all()
    
    for entry in entries:
        await db.delete(entry)
    
    # 4. Deletar protocolo
    await db.delete(protocolo)
    await db.commit()
    
    return {
        "sucesso": True,
        "mensagem": f"Protocolo {protocolo.numero_protocolo} excluído com sucesso.",
        "entries_deletados": len(entries)
    }

@router.post("/pendencias/resolver")
async def resolver_pendencia(
    payload: ResolvePendenciaRequest,
    db: SessionDep,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Recebe o mapeamento de uma conta e persiste em AccountMapping.
    Se todas as pendências do protocolo forem resolvidas, reprocessa e gera o TXT.
    """
    # 1. Verificar se o mapeamento já existe; se não, criar
    stmt_existing = select(AccountMapping).where(
        AccountMapping.cnpj_empresa == payload.cnpj_empresa,
        AccountMapping.conta_cliente == payload.conta_cliente,
        AccountMapping.tipo == payload.tipo,
    )
    existing = (await db.execute(stmt_existing)).scalar_one_or_none()

    if existing:
        existing.conta_contabilidade = payload.conta_contabilidade
    else:
        novo_mapping = AccountMapping(
            cnpj_empresa=payload.cnpj_empresa,
            conta_cliente=payload.conta_cliente,
            conta_contabilidade=payload.conta_contabilidade,
            tipo=payload.tipo,
        )
        db.add(novo_mapping)

    await db.commit()

    # 2. Verificar se ainda restam pendências sem mapeamento no protocolo
    stmt_prot = select(Protocolo).where(Protocolo.id == payload.protocolo_id)
    protocolo = (await db.execute(stmt_prot)).scalar_one_or_none()
    if not protocolo:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado.")

    stmt_entries = select(StagingEntry).where(StagingEntry.protocolo_id == payload.protocolo_id)
    entries = (await db.execute(stmt_entries)).scalars().all()

    # Verifica quais contas ainda não têm mapeamento
    contas_sem_mapa: list[str] = []
    for entry in entries:
        for conta_raw, tipo in [
            (entry.conta_debito_raw, "DEBITO"),
            (entry.conta_credito_raw, "CREDITO"),
        ]:
            stmt_check = select(AccountMapping).where(
                AccountMapping.cnpj_empresa == protocolo.cnpj,
                AccountMapping.conta_cliente == conta_raw,
                AccountMapping.tipo == tipo,
            )
            mapeamento = (await db.execute(stmt_check)).scalar_one_or_none()
            if not mapeamento:
                contas_sem_mapa.append(f"{tipo}:{conta_raw}")

    if not contas_sem_mapa:
        # Todas as pendências foram resolvidas — reprocessar em background
        if protocolo.arquivo_base64_raw:
            # Deletar staging entries antigas antes de reprocessar
            for entry in entries:
                await db.delete(entry)
            await db.commit()

            background_tasks.add_task(
                run_parsing_task,
                protocolo.id,
                protocolo.arquivo_base64_raw,
                "layout_brastelha_1",
            )
            return {
                "sucesso": True,
                "mensagem": "Todas as pendências foram resolvidas. Reprocessando o arquivo...",
                "reprocessando": True,
            }
        else:
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
