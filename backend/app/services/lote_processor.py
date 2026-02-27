"""Orquestrador do processamento de lote contábil."""
import base64

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LayoutNaoEncontradoError
from app.models.layout_excel import LayoutExcel
from app.models.protocolo import Protocolo
from app.models.staging_entry import StagingEntry
from app.services.conta_mapper import ContaMapper
from app.services.excel_parser import ExcelParser
from app.services.periodo_validator import PeriodoValidator


class LoteProcessor:
    """Orquestra: layout → parser → validator → mapper → persistência."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def processar(
        self, protocolo_id: int, arquivo_base64: str, layout_nome: str
    ) -> None:
        try:
            layout = await self._carregar_layout(layout_nome)
            protocolo = (
                await self._db.execute(
                    select(Protocolo).where(Protocolo.id == protocolo_id)
                )
            ).scalar_one()

            validator = PeriodoValidator(protocolo.periodo)
            parser = ExcelParser(layout)
            mapper = ContaMapper(protocolo.cnpj, self._db)

            linhas = parser.parsear(arquivo_base64)

            erros_periodo: list[tuple[int, str]] = []
            pendencias: list[StagingEntry] = []
            linhas_txt: list[str] = []

            for idx, linha in enumerate(linhas, start=2):
                if not validator.validar_data(linha.data_formatada):
                    erros_periodo.append((idx, linha.data_formatada))
                    continue

                c_debito = await mapper.resolver(linha.conta_debito_raw, "DEBITO")
                c_credito = await mapper.resolver(linha.conta_credito_raw, "CREDITO")

                if not c_debito or not c_credito:
                    pendencias.append(
                        StagingEntry(
                            protocolo_id=protocolo_id,
                            data_lancamento=linha.data_formatada,
                            valor=linha.valor,
                            conta_debito_raw=linha.conta_debito_raw,
                            conta_credito_raw=linha.conta_credito_raw,
                            historico=linha.historico,
                            cod_historico=linha.cod_historico,
                        )
                    )
                else:
                    n_filial = str(protocolo.codigo_filial or "")
                    valor_br = f"{linha.valor:.2f}".replace(".", ",")
                    linhas_txt.extend(
                        [
                            "|6000|X||||",
                            f"|6100|{linha.data_formatada}|{c_debito}|{c_credito}|{valor_br}||{linha.historico}|VICTOR|{n_filial}||",
                        ]
                    )

            validator.validar_ou_falhar(erros_periodo)

            if pendencias:
                self._db.add_all(pendencias)
                protocolo.status = "WAITING_MAPPING"
            else:
                cabecalho = f"|0000|{protocolo.cnpj}|"
                txt_final = "\n".join([cabecalho, *linhas_txt])
                protocolo.arquivo_txt_base64 = base64.b64encode(
                    txt_final.encode()
                ).decode()
                protocolo.status = "COMPLETED"

            await self._db.commit()

        except Exception as e:
            await self._db.rollback()
            print(f"❌ ERRO [proto={protocolo_id}]: {e}")
            await self._salvar_erro(protocolo_id, str(e))

    async def _carregar_layout(self, nome: str) -> LayoutExcel:
        layout = (
            await self._db.execute(
                select(LayoutExcel).where(LayoutExcel.nome == nome)
            )
        ).scalar_one_or_none()
        if not layout:
            raise LayoutNaoEncontradoError(nome)
        return layout

    async def _salvar_erro(self, protocolo_id: int, mensagem: str) -> None:
        try:
            proto = (
                await self._db.execute(
                    select(Protocolo).where(Protocolo.id == protocolo_id)
                )
            ).scalar_one_or_none()
            if proto:
                proto.status = "ERROR"
                proto.error_message = mensagem[:1000]
                await self._db.commit()
        except Exception:
            pass
