"""CLASSE Consumo: quanto de um Servico foi usado em uma reserva.

DADOS: servico, quantidade, preco_unitario (o preço do momento, que não muda depois)

ONDE ESTÁ O QUÊ
  __init__ .............. cria o consumo e congela o preço
  subtotal .............. CÁLCULO: quantidade x preço unitário
  para_dict ............. dicionário para o JSON
"""

from __future__ import annotations

from decimal import Decimal

from .erros import RegraNegocioErro
from .formatos import dinheiro
from .servico import Servico


class Consumo:
    """Consumo lançado em uma reserva. Guarda o preço contratado no momento."""

    # Consumo = quanto de um Servico foi usado numa reserva. Guarda uma REFERÊNCIA ao Servico (associação) e a quantidade.
    # preco_unitario=None significa 'se ninguém informar, use o preço atual do catálogo'.
    def __init__(self, servico: Servico, quantidade: int, preco_unitario=None):
        if int(quantidade) <= 0:
            raise RegraNegocioErro("A quantidade deve ser positiva.")
        self.servico = servico
        self.quantidade = int(quantidade)
        # Preço "congelado": se o catálogo mudar depois, a conta não muda.
        self.preco_unitario = dinheiro(servico.preco if preco_unitario is None
                                       else preco_unitario)

    # CÁLCULO dentro da classe: subtotal = quantidade x preço unitário. Usa-se assim: consumo.subtotal
    @property
    def subtotal(self) -> Decimal:
        return self.quantidade * self.preco_unitario

    def para_dict(self):
        return {"servico_id": self.servico.id, "quantidade": self.quantidade,
                "preco_unitario": str(self.preco_unitario)}
