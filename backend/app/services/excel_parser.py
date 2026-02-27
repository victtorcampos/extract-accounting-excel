"""Parser de Excel para geração de TXT contábil."""

from __future__ import annotations

import base64
import io
from datetime import datetime
from typing import Any, Optional, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from python_calamine import CalamineWorkbook

from app.models.database_models import (
    AccountMapping,
    LayoutExcel,
    Protocolo,
    StagingEntry,
)


def _col_to_idx(col_letter: str) -> int:
    """Converte letra de coluna (A-Z) em índice (0-25)."""
    return ord(col_letter.upper()) - ord("A")


def _format_date(raw_date: Any, dia: Any) -> str:
    """Retorna DD/MM/YYYY a partir da data mensal e dia do lançamento."""
    if isinstance(raw_date, datetime):
        mes = raw_date.month
        ano = raw_date.year
    else:
        # Tenta parsear string YYYY-MM-DD
        s = str(raw_date).strip()
        try:
            dt = datetime.fromisoformat(s[:10])
            mes = dt.month
            ano = dt.year
        except ValueError:
            return s  # Fallback

    try:
        dia_int = int(float(str(dia)))
    except (ValueError, TypeError):
        dia_int = 1

    return f"{dia_int:02d}/{mes:02d}/{ano}"


def _format_valor_br(valor: float) -> str:
    """Formato brasileiro: 60.000,00."""
    formatted = f"{valor:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

def format_with_decimal(valor: float, decimals: int = 2, grouping: bool = True) -> str:
    """
    Formata número no padrão brasileiro com casas decimais customizáveis.
    
    Args:
        valor: Número a ser formatado
        decimals: Quantidade de casas decimais (padrão: 2)
        grouping: Se True, adiciona separador de milhar (padrão: True)
    
    Returns:
        String formatada no padrão brasileiro
        
    Exemplos:
        >>> format_with_decimal(60000.0, decimals=2)
        '60.000,00'
        >>> format_with_decimal(1234.56789, decimals=4)
        '1.234,5679'
        >>> format_with_decimal(12345, decimals=2, grouping=False)
        '12345,00'
        >>> format_with_decimal(0.1234, decimals=3)
        '0,123'
    """
    # Formata com precisão especificada usando f-string
    formatted = f"{valor:,.{decimals}f}" if grouping else f"{valor:.{decimals}f}"
    
    # Converte para padrão brasileiro: troca separadores
    # Passo 1: , (milhar inglês) → X (placeholder)
    # Passo 2: . (decimal inglês) → , (decimal BR)
    # Passo 3: X → . (milhar BR)
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

async def _get_conta_contabil(
    raw_acc: str,
    tipo: str,
    cnpj_protocolo: str,
    map_cache: Dict[str, Optional[str]],
    db: AsyncSession,
) -> Optional[str]:
    """Busca mapeamento com cache local."""
    cache_key = f"{cnpj_protocolo}:{tipo}:{raw_acc}"
    if cache_key in map_cache:
        return map_cache[cache_key]

    stmt = (
        select(AccountMapping.conta_contabilidade)
        .where(
            AccountMapping.cnpj_empresa == cnpj_protocolo,
            AccountMapping.conta_cliente == raw_acc,
            AccountMapping.tipo == tipo,
        )
        .limit(1)
    )
    res = (await db.execute(stmt)).scalar_one_or_none()
    map_cache[cache_key] = res
    return res


async def processar_excel_service(
    protocolo_id: int, arquivo_base64: str, layout_nome: str, db: AsyncSession
) -> None:
    """Processa Excel → pendências ou TXT final."""
    try:
        # 1. Layout
        stmt_layout = select(LayoutExcel).where(LayoutExcel.nome == layout_nome)
        layout = (await db.execute(stmt_layout)).scalar_one_or_none()
        if not layout:
            raise ValueError(f"Layout '{layout_nome}' não cadastrado.")

        # 2. Protocolo
        stmt_prot = select(Protocolo).where(Protocolo.id == protocolo_id)
        protocolo = (await db.execute(stmt_prot)).scalar_one()
        cnpj_protocolo = protocolo.cnpj

        # 3. ✅ CORREÇÃO: Base64 → BytesIO → Workbook
        raw_b64 = arquivo_base64.split(",")[-1] if "," in arquivo_base64 else arquivo_base64
        file_bytes = base64.b64decode(raw_b64)
        workbook = CalamineWorkbook.from_filelike(io.BytesIO(file_bytes))  # ✅ from_filelike!
        sheet = workbook.get_sheet_by_index(0)

        # 4. Colunas
        idx_data = _col_to_idx(layout.col_data)
        idx_dia = 5  # Fixo: V_Dia Lancamento
        idx_debito = _col_to_idx(layout.col_conta_debito)
        idx_credito = _col_to_idx(layout.col_conta_credito)
        idx_valor = _col_to_idx(layout.col_valor)
        idx_cod_hist = _col_to_idx(layout.col_cod_historico)
        idx_hist = _col_to_idx(layout.col_historico)

        map_cache: Dict[str, Optional[str]] = {}
        linhas_txt: list[str] = []
        pendencias: list[StagingEntry] = []

        rows = list(sheet.to_python())
        for row in rows[1:]:  # Pula header
            if not row or len(row) <= max(idx_data, idx_dia, idx_debito, idx_credito, idx_valor):
                continue

            try:
                data_val = _format_date(row[idx_data], row[idx_dia])
                valor_raw = str(row[idx_valor]).replace(",", ".")
                valor_float = float(valor_raw)
                valor_br = format_with_decimal(valor_float, decimals=2, grouping=False)
                print(valor_br)
                conta_d_raw = _normalize_account(row[idx_debito])
                conta_c_raw = _normalize_account(row[idx_credito])
                cod_hist_val = str(row[idx_cod_hist] if len(row) > idx_cod_hist else "")
                hist_val = str(row[idx_hist] if len(row) > idx_hist else "")
            except (ValueError, IndexError, TypeError):
                continue

            if not all([conta_d_raw, conta_c_raw]):
                continue

            c_debito = await _get_conta_contabil(conta_d_raw, "DEBITO", cnpj_protocolo, map_cache, db)
            c_credito = await _get_conta_contabil(conta_c_raw, "CREDITO", cnpj_protocolo, map_cache, db)

            if not c_debito or not c_credito:
                pendencias.append(StagingEntry(
                    protocolo_id=protocolo_id,
                    data_lancamento=data_val,
                    valor=valor_float,
                    conta_debito_raw=conta_d_raw,
                    conta_credito_raw=conta_c_raw,
                    historico=hist_val,
                    cod_historico=cod_hist_val,
                ))
            else:
                n_filial = str(protocolo.codigo_filial or "")
                linha = f"|6100|{data_val}|{c_debito}|{c_credito}|{valor_br}||{hist_val}|VICTOR|{n_filial}||"
                # linha = f"|6100|{data_val}|{c_debito}|{c_credito}|{valor_br}|{cod_hist_val}|{hist_val}|VICTOR|{n_filial}||"
                linhas_txt.extend(["|6000|X||||", linha])

        # Finalizar
        if pendencias:
            db.add_all(pendencias)
            protocolo.status = "WAITING_MAPPING"
        else:
            cabecalho = f"|0000|{protocolo.cnpj}|"
            txt_final = "\n".join([cabecalho, *linhas_txt])
            protocolo.arquivo_txt_base64 = base64.b64encode(txt_final.encode()).decode()
            protocolo.status = "COMPLETED"

        await db.commit()

    except Exception as e:
        await db.rollback()
        # Log estruturado
        print(f"❌ ERRO PROCESSAMENTO [proto={protocolo_id}, layout={layout_nome}]: {e}")
        try:
            stmt_err = select(Protocolo).where(Protocolo.id == protocolo_id)
            proto_err = (await db.execute(stmt_err)).scalar_one_or_none()
            if proto_err:
                proto_err.status = "ERROR"
                await db.commit()
        except:
            pass

def _normalize_account(value: Any) -> str:
    """Converte valor de conta para string sem .0 se for numérico inteiro."""
    if isinstance(value, (int, float)):
        # Se for float sem parte decimal (3145.0 → 3145), converte pra int
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
    # Se já for string ou outro tipo, retorna como string limpa
    return str(value).strip()

def _normalize_account(value: Any) -> str:
    """Converte valor de conta para string sem .0 se for numérico inteiro."""
    if isinstance(value, (int, float)):
        # Se for float sem parte decimal (3145.0 → 3145), converte pra int
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
    # Se já for string ou outro tipo, retorna como string limpa
    return str(value).strip()