"""Validação de período contábil."""
from datetime import datetime

from app.core.exceptions import LancamentoForaDoPeriodoError, PeriodoInvalidoError


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
            raise PeriodoInvalidoError(
                f"Formato inválido '{periodo_str}'. Use YYYY-MM."
            ) from e

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
