"""CLASSE Servico: um item do catálogo de extras (frigobar, lavanderia...).

DADOS: id, descricao, preco

ONDE ESTÁ O QUÊ
  __init__ .............. cria o serviço e valida descrição e preço
  para_dict ............. dicionário para o JSON
"""

from __future__ import annotations

from .erros import RegraNegocioErro
from .formatos import dinheiro, formatar_moeda
from .validacoes import validar_tamanho


class Servico:
    """Item do catálogo de extras (frigobar, lavanderia...)."""

    # Servico é o item do CATÁLOGO (ex.: Água, R$ 10,00). O preço pode mudar depois; por isso o Consumo guarda uma cópia do preço.
    def __init__(self, id: int, descricao: str, preco, validar: bool = True):
        if validar:
            descricao = validar_tamanho(descricao, "descricao", "A descrição do serviço", minimo=2)
        if not descricao.strip():
            raise RegraNegocioErro("A descrição do serviço é obrigatória.")
        preco = dinheiro(preco)
        if preco < 0:
            raise RegraNegocioErro("O preço não pode ser negativo.")
        self.id = id
        self.descricao = descricao.strip()
        self.preco = preco

    def __str__(self):
        return f"{self.descricao} - {formatar_moeda(self.preco)}"

    def para_dict(self):
        return {"id": self.id, "descricao": self.descricao, "preco": str(self.preco)}
