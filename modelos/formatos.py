"""APOIO: DINHEIRO E DATAS

ONDE ESTÁ O QUÊ
  dinheiro(valor) ...... texto ou número -> Decimal com 2 casas (nunca float para dinheiro)
  formatar_moeda(valor)  Decimal -> 'R$ 1.234,50'
  ler_data(texto) ...... 'dd/mm/aaaa' -> date (erro se a data for inválida)
  formatar_data(data) .. date -> 'dd/mm/aaaa'
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .erros import RegraNegocioErro


# Por que Decimal e não float? O float erra contas (0.1 + 0.2 = 0.30000000000000004).
# O Decimal faz conta exata, essencial para dinheiro.
# Esta função aceita '180', '180,50' ou 'R$ 1.234,56' e devolve um Decimal com 2 casas.
def dinheiro(valor) -> Decimal:
    """Converte texto/número para Decimal com 2 casas (nunca float para dinheiro)."""
    try:
        texto = str(valor).strip().replace("R$", "").replace(" ", "")
        if "," in texto:  # formato brasileiro: 1.234,56
            texto = texto.replace(".", "").replace(",", ".")
        d = Decimal(texto)
    except (InvalidOperation, ValueError):
        raise RegraNegocioErro(f"Valor monetário inválido: {valor!r}")
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def formatar_moeda(valor: Decimal) -> str:
    """Decimal('1234.5') -> 'R$ 1.234,50'"""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def ler_data(texto: str) -> date:
    """Lê uma data no formato dd/mm/aaaa."""
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        raise RegraNegocioErro(f"Data inválida: {texto!r} (use dd/mm/aaaa)")


def formatar_data(d: date) -> str:
    return d.strftime("%d/%m/%Y")
