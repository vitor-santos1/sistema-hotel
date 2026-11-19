"""CLASSE Quarto: um quarto do hotel.

DADOS: numero, categoria, capacidade, diaria

ONDE ESTÁ O QUÊ
  __init__ .............. cria o quarto e valida os dados
  diaria (property) ..... ENCAPSULAMENTO: o valor fica em _diaria; ler = getter
  diaria (setter) ....... só aceita valor maior que zero
  comporta(pessoas) ..... True se o grupo cabe no quarto
  para_dict ............. dicionário para o JSON
"""

from __future__ import annotations

from decimal import Decimal

from .erros import RegraNegocioErro
from .formatos import dinheiro
from .validacoes import LIMITES, validar_tamanho


class Quarto:
    """Quarto físico do hotel, com capacidade e diária atual."""

    def __init__(self, numero: str, categoria: str, capacidade: int, diaria,
                 validar: bool = True):
        if not str(numero).strip():
            raise RegraNegocioErro("O número do quarto é obrigatório.")
        if int(capacidade) <= 0:
            raise RegraNegocioErro("A capacidade deve ser maior que zero.")
        if validar:
            numero = validar_tamanho(numero, "numero_quarto", "O número do quarto")
            categoria = validar_tamanho(categoria, "categoria", "A categoria") if str(categoria).strip() else "Standard"
            if int(capacidade) > LIMITES["capacidade"]:
                raise RegraNegocioErro(f"A capacidade máxima é {LIMITES['capacidade']} pessoas.")
        self.numero = str(numero).strip()
        self.categoria = categoria.strip() or "Standard"
        self.capacidade = int(capacidade)
        self.diaria = diaria  # usa o setter abaixo (validação)

    # ENCAPSULAMENTO: o valor de verdade fica em self._diaria (o _ avisa 'não mexa direto').
    # Quem usa a classe lê e escreve  quarto.diaria : o getter (@property) devolve o valor e o setter valida antes de guardar.
    @property
    def diaria(self) -> Decimal:
        return self._diaria

    # Setter: roda quando alguém escreve  quarto.diaria = 200.  Se o valor for inválido lança erro e NADA é guardado.
    @diaria.setter
    def diaria(self, valor):
        valor = dinheiro(valor)
        if valor <= 0:
            raise RegraNegocioErro("A diária deve ser maior que zero.")
        self._diaria = valor

    # Devolve True ou False. '0 < pessoas <= capacidade' é uma comparação encadeada: maior que 0 E menor ou igual à capacidade.
    def comporta(self, pessoas: int) -> bool:
        return 0 < pessoas <= self.capacidade

    def __str__(self):
        return f"Quarto {self.numero} - {self.categoria}"

    def para_dict(self):
        return {"numero": self.numero, "categoria": self.categoria,
                "capacidade": self.capacidade, "diaria": str(self.diaria)}
