from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated

from app.database import get_session, engine # Importamos o engine para a task
from app.models.database_models import Protocolo
from app.schemas.lote import LoteContabilCreate
from app.services.excel_parser import processar_excel_service # Import do parser

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Função auxiliar para gerenciar a sessão dentro da task de background
async def run_parsing_task(protocolo_id: int, arquivo_base64: str, layout_nome: str):
    from sqlalchemy.orm import sessionmaker
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        await processar_excel_service(protocolo_id, arquivo_base64, layout_nome, db)

@router.post("/lancamento_lote_contabil")
async def criar_lote(
    lote: LoteContabilCreate, 
    db: SessionDep,
    background_tasks: BackgroundTasks
):
    """
    Recebe o formulário da Página 1, registra o protocolo e 
    inicia o processamento do Excel em background.
    """
    # 1. Verificar se protocolo já existe
    query = select(Protocolo).where(Protocolo.numero_protocolo == lote.protocolo)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Protocolo já existente.")

    # 2. Criar registro inicial (Status PENDING)
    novo_protocolo = Protocolo(
        numero_protocolo=lote.protocolo,
        cnpj=lote.cnpj,
        periodo=lote.periodo,
        status="PENDING"
    )
    db.add(novo_protocolo)
    await db.commit()
    await db.refresh(novo_protocolo)

    # 3. Disparar o parsing em background (BackgroundTasks)
    background_tasks.add_task(
        run_parsing_task, 
        novo_protocolo.id, 
        lote.arquivo_base64, 
        lote.layout_nome
    )

    return {"sucesso": True, "protocolo": lote.protocolo} #

@router.get("/lancamento_lote_contabil")
async def consultar_lote(
    db: SessionDep,
    protocolo: Annotated[str | None, Query()] = None,
    cnpj: Annotated[str | None, Query()] = None
):
    """
    Retorna detalhes de um protocolo específico ou lista protocolos por CNPJ.
    """
    if protocolo:
        query = select(Protocolo).where(Protocolo.numero_protocolo == protocolo)
        result = await db.execute(query)
        p = result.scalar_one_or_none()
        
        if not p:
            raise HTTPException(status_code=404, detail="Protocolo não encontrado")
        
        # Resposta conforme o status
        conteudo = p.arquivo_txt_base64 if p.status == "COMPLETED" else "pendente"
        
        return {
            "sucesso": True, 
            "protocolo": p.numero_protocolo, 
            "status": p.status,
            "resultado": conteudo
        }

    if cnpj:
        query = select(Protocolo).where(Protocolo.cnpj == cnpj)
        result = await db.execute(query)
        protocolos = result.scalars().all()
        return {
            "sucesso": True, 
            "protocolos": [
                {"protocolo": p.numero_protocolo, "status": p.status, "data": p.created_at} 
                for p in protocolos
            ]
        } # Melhorei o retorno para ser mais útil na Página 3

    raise HTTPException(status_code=400, detail="Informe protocolo ou cnpj")