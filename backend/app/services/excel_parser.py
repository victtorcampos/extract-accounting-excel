import base64
import io
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from python_calamine import CalamineWorkbook
from app.models.database_models import Protocolo, AccountMapping, StagingEntry, LayoutExcel

async def processar_excel_service(protocolo_id: int, arquivo_base64: str, layout_nome: str, db: AsyncSession):
    try:
        # 1. Recuperar o Layout
        stmt_layout = select(LayoutExcel).where(LayoutExcel.nome == layout_nome)
        layout = (await db.execute(stmt_layout)).scalar_one_or_none()
        if not layout:
            raise ValueError(f"Layout {layout_nome} não cadastrado.")

        # 2. Decodificar Base64
        file_bytes = base64.b64decode(arquivo_base64.split(",")[-1] if "," in arquivo_base64 else arquivo_base64)
        workbook = CalamineWorkbook.from_fileload(io.BytesIO(file_bytes))
        sheet = workbook.get_sheet_by_index(0) # Assume primeira aba
        
        # Cache local para evitar queries repetitivas no mesmo lote
        map_cache = {}
        linhas_txt = []
        pendencias = []
        
        # 3. Iterar linhas (Pula cabeçalho se necessário)
        for row in sheet.to_python():
            if not row or len(row) < 5: continue # Pula linhas vazias
            
            # Mapeamento dinâmico baseado no Layout
            # Ex: col_data='E' -> índice 4
            idx_data = ord(layout.col_data.upper()) - 65
            idx_valor = ord(layout.col_valor.upper()) - 65
            idx_debito = ord(layout.col_conta_debito.upper()) - 65
            idx_credito = ord(layout.col_conta_credito.upper()) - 65
            idx_hist = ord(layout.col_historico.upper()) - 65

            try:
                data_val = str(row[idx_data])
                valor_val = float(str(row[idx_valor]).replace(',', '.'))
                conta_d_raw = str(row[idx_debito])
                conta_c_raw = str(row[idx_credito])
                hist_val = str(row[idx_hist])
            except (IndexError, ValueError):
                continue

            # 4. Validar Mapeamento de Contas
            async def get_conta_contabil(raw_acc):
                if raw_acc in map_cache: return map_cache[raw_acc]
                stmt = select(AccountMapping.conta_contabilidade).where(AccountMapping.conta_cliente == raw_acc)
                res = (await db.execute(stmt)).scalar_one_or_none()
                map_cache[raw_acc] = res
                return res

            c_debito = await get_conta_contabil(conta_d_raw)
            c_credito = await get_conta_contabil(conta_c_raw)

            if not c_debito or not c_credito:
                # Se faltar mapeamento, vira pendência
                pendencias.append(StagingEntry(
                    protocolo_id=protocolo_id,
                    data_lancamento=data_val,
                    valor=valor_val,
                    conta_debito_raw=conta_d_raw,
                    conta_credito_raw=conta_c_raw,
                    historico=hist_val
                ))
            else:
                # Se tudo OK, formata linha do Registro 6100
                # Formato: |6100|data|debito|credito|valor|0|historico|USUARIO|FILIAL||
                linha = f"|6100|{data_val}|{c_debito}|{c_credito}|{valor_val}|0|{hist_val}||||"
                linhas_txt.append("|6000|X||||") # Registro pai
                linhas_txt.append(linha)

        # 5. Finalização do Processamento
        stmt_prot = select(Protocolo).where(Protocolo.id == protocolo_id)
        protocolo = (await db.execute(stmt_prot)).scalar_one()

        if pendencias:
            db.add_all(pendencias)
            protocolo.status = "WAITING_MAPPING" #
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
        stmt_err = select(Protocolo).where(Protocolo.id == protocolo_id)
        protocolo = (await db.execute(stmt_err)).scalar_one_or_none()
        if protocolo:
            protocolo.status = "ERROR"
            await db.commit()
        print(f"Erro no processamento: {e}")