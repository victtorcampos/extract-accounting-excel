"""Parser de bytes Excel → lista de linhas brutas."""
import base64
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Any

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

        idx_data = self._col_idx(self._layout.col_data)
        idx_dia = 5  # Fixo: V_Dia Lancamento
        idx_debito = self._col_idx(self._layout.col_conta_debito)
        idx_credito = self._col_idx(self._layout.col_conta_credito)
        idx_valor = self._col_idx(self._layout.col_valor)
        idx_cod = self._col_idx(self._layout.col_cod_historico)
        idx_hist = self._col_idx(self._layout.col_historico)

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
