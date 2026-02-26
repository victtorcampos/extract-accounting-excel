from __future__ import annotations

import base64
import io
from datetime import datetime
from typing import Any, Optional

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
    return ord(col_letter.upper()) - 65


def _format_date(raw_date: Any, dia: Any) -> str:
    """Retorna DD/MM/YYYY a partir da data mensal e do dia do lançamento."""
    if isinstance(raw_date, datetime):
        mes = raw_date.month
        ano = raw_date.year
    else:
        # Tenta parsear string no formato YYYY-MM-DD ou similares
        s = str(raw_date).strip()
        try:
            dt = datetime.fromisoformat(s[:10])
            mes = dt.month
            ano = dt.year
        except ValueError:
            # Fallback: retorna a string como está
            return s

    try:
        dia_int = int(float(str(dia)))
    except (ValueError, TypeError):
        dia_int = 1

    return f"{dia_int:02d}/{mes:02d}/{ano}"


def _format_valor_br(valor: float) -> str:
    """Retorna valor no formato brasileiro: 60000,00"""
    # Formata com 2 casas decimais e troca separadores
    formatted = f"{valor:,.2f}"  # ex: "60,000.00"
    # Troca . por placeholder, , por ., então placeholder por ,
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted


async def _get_conta_contabil(
    raw_acc: str,
    tipo: str,
    cnpj_protocolo: str,
    map_cache: dict[str, Optional[str]],
    db: AsyncSession,
) -> Optional[str]:
    """Busca conta contábil mapeada filtrando por CNPJ e tipo."""
    cache_key = f"{cnpj_protocolo}:{tipo}:{raw_acc}"
    if cache_key in map_cache:
        return map_cache[cache_key]
    stmt = select(AccountMapping.conta_contabilidade).where(
        AccountMapping.cnpj_empresa == cnpj_protocolo,
        AccountMapping.conta_cliente == raw_acc,
        AccountMapping.tipo == tipo,
    )
    res = (await db.execute(stmt)).scalar_one_or_none()
    map_cache[cache_key] = res
    return res


async def processar_excel_service(
    protocolo_id: int,
    arquivo_base64: str,
    layout_nome: str,
    db: AsyncSession,
) -> None:
    try:
        # 1. Recuperar o Layout
        stmt_layout = select(LayoutExcel).where(LayoutExcel.nome == layout_nome)
        layout = (await db.execute(stmt_layout)).scalar_one_or_none()
        if not layout:
            raise ValueError(f"Layout {layout_nome} não cadastrado.")

        # 2. Recuperar o Protocolo para obter CNPJ e filial
        stmt_prot = select(Protocolo).where(Protocolo.id == protocolo_id)
        protocolo = (await db.execute(stmt_prot)).scalar_one()
        cnpj_protocolo = protocolo.cnpj

        # 3. Decodificar Base64
        raw_b64 = arquivo_base64.split(",")[-1] if "," in arquivo_base64 else arquivo_base64
        file_bytes = base64.b64decode(raw_b64)
        workbook = CalamineWorkbook.from_fileload(io.BytesIO(file_bytes))
        sheet = workbook.get_sheet_by_index(0)  # Assume primeira aba

        # Índices das colunas (calculados uma vez)
        idx_data = _col_to_idx(layout.col_data)          # E -> 4  (mes/ano)
        idx_dia = 5                                         # F -> 5  (V_Dia Lancamento)
        idx_debito = _col_to_idx(layout.col_conta_debito)  # G -> 6
        idx_credito = _col_to_idx(layout.col_conta_credito)  # H -> 7
        idx_valor = _col_to_idx(layout.col_valor)          # L -> 11
        idx_cod_hist = _col_to_idx(layout.col_cod_historico)  # N -> 13
        idx_hist = _col_to_idx(layout.col_historico)       # O -> 14

        # Cache local para evitar queries repetitivas no mesmo lote
        map_cache: dict[str, Optional[str]] = {}
        linhas_txt: list[str] = []
        pendencias: list[StagingEntry] = []

        # 4. Iterar linhas — pula cabeçalho (linha 0)
        rows = list(sheet.to_python())
        for row in rows[1:]:
            if not row:
                continue

            # Verifica tamanho mínimo para acessar colunas necessárias
            max_idx = max(idx_data, idx_dia, idx_debito, idx_credito, idx_valor, idx_hist)
            if len(row) <= max_idx:
                continue

            try:
                data_val = _format_date(row[idx_data], row[idx_dia])
                valor_raw = str(row[idx_valor]).replace(",", ".")
                valor_float = float(valor_raw)
                valor_br = _format_valor_br(valor_float)
                conta_d_raw = str(row[idx_debito]).strip()
                conta_c_raw = str(row[idx_credito]).strip()
                cod_hist_val = str(row[idx_cod_hist]).strip() if len(row) > idx_cod_hist else ""
                hist_val = str(row[idx_hist]).strip() if len(row) > idx_hist else ""
            except (IndexError, ValueError):
                continue

            # Pula linhas sem dados relevantes
            if not conta_d_raw or not conta_c_raw or conta_d_raw == "None":
                continue

            # 5. Validar Mapeamento de Contas (com filtro por CNPJ e tipo)
            c_debito = await _get_conta_contabil(conta_d_raw, "DEBITO", cnpj_protocolo, map_cache, db)
            c_credito = await _get_conta_contabil(conta_c_raw, "CREDITO", cnpj_protocolo, map_cache, db)

            if not c_debito or not c_credito:
                # Se faltar mapeamento, vira pendência
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
                # Filial: campo 9 do registro 6100
                n_filial = str(protocolo.codigo_filial) if protocolo.codigo_filial is not None else ""

                # Formato: |6100|DD/MM/YYYY|c_debito|c_credito|valor_br|n_historico|historico_compl||n_filial||
                linha = f"|6100|{data_val}|{c_debito}|{c_credito}|{valor_br}|{cod_hist_val}|{hist_val}||{n_filial}||"
                linhas_txt.append("|6000|X||||")  # Registro pai
                linhas_txt.append(linha)

        # 6. Finalização do Processamento
        if pendencias:
            db.add_all(pendencias)
            protocolo.status = "WAITING_MAPPING"
        else:
            # Gerar TXT Final
            cabecalho = f"|0000|{protocolo.cnpj}|"
            txt_final = cabecalho + "\n" + "\n".join(linhas_txt)
            protocolo.arquivo_txt_base64 = base64.b64encode(txt_final.encode()).decode()
            protocolo.status = "COMPLETED"

        await db.commit()

    except Exception as e:
        await db.rollback()
        # Atualiza status para erro para não travar o front
        try:
            stmt_err = select(Protocolo).where(Protocolo.id == protocolo_id)
            protocolo_err = (await db.execute(stmt_err)).scalar_one_or_none()
            if protocolo_err:
                protocolo_err.status = "ERROR"
                await db.commit()
        except Exception:
            pass
        print(f"Erro no processamento: {e}")
