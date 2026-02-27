"""Exceções de domínio da aplicação contábil."""


class LoteProcessamentoError(Exception):
    """Erro genérico no processamento de lote."""


class LayoutNaoEncontradoError(LoteProcessamentoError):
    """Layout Excel não cadastrado no banco."""

    def __init__(self, nome: str):
        super().__init__(f"Layout '{nome}' não encontrado.")


class PeriodoInvalidoError(LoteProcessamentoError):
    """Período no formato inválido ou fora do range."""


class LancamentoForaDoPeriodoError(LoteProcessamentoError):
    """Lançamentos encontrados fora do período declarado."""

    def __init__(self, total: int, periodo: str, exemplos: list[str]):
        detalhe = ", ".join(exemplos[:5])
        sufixo = f" (+{total - 5} mais)" if total > 5 else ""
        super().__init__(
            f"Arquivo contém {total} lançamento(s) fora do período {periodo}. "
            f"Exemplos: {detalhe}{sufixo}"
        )
