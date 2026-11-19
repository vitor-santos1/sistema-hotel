"""CLASSE FechamentoCaixa: o fechamento de caixa.

Reúne as hospedagens concluídas desde o fechamento anterior. NÃO apaga nada: só registra
até onde o caixa foi contado (o painel passa a contar do zero).

ONDE ESTÁ O QUÊ
  CÁLCULOS: quantidade, valor_hospedagem, valor_consumos, total
  relatorio ............. texto no formato de cupom
  salvar_relatorio ...... grava o relatório em fechamentos/caixa_001.txt
  para_dict ............. dicionário para o JSON
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import os

from .formatos import formatar_moeda
from .reserva import Reserva


class FechamentoCaixa:
    """Fechamento de caixa: reúne as hospedagens concluídas desde o fechamento anterior.

    O faturamento não é apagado. Ele fica registrado no fechamento, e o painel passa a
    contar do zero a partir dele. O histórico completo continua na Análise de dados.
    """

    LARGURA = 42  # caracteres por linha do relatório (formato de cupom)

    # O fechamento guarda: o número, quando foi feito e QUAIS reservas entraram nele.
    # list(reservas) faz uma cópia da lista, para mudanças futuras não afetarem o fechamento.
    def __init__(self, numero: int, data_hora: datetime, reservas: list[Reserva]):
        self.numero = numero
        self.data_hora = data_hora
        self.reservas = list(reservas)

    # ---------------- cálculos ----------------
    @property
    def quantidade(self) -> int:
        return len(self.reservas)

    @property
    def valor_hospedagem(self) -> Decimal:
        return sum((r.valor_hospedagem for r in self.reservas), Decimal("0.00"))

    @property
    def valor_consumos(self) -> Decimal:
        return sum((r.valor_consumos for r in self.reservas), Decimal("0.00"))

    # Mesma ideia da Reserva: o total do caixa é a soma das hospedagens com os consumos de todas as reservas fechadas.
    @property
    def total(self) -> Decimal:
        return self.valor_hospedagem + self.valor_consumos

    # ---------------- relatório ----------------
    # Monta o relatório no formato de cupom (42 colunas). ljust e center alinham o texto à esquerda e ao centro.
    def relatorio(self, nome_hotel: str = "Hotel") -> str:
        """Texto no formato de cupom, pronto para salvar em .txt ou imprimir."""
        L = self.LARGURA

        def linha(esquerda: str, direita: str) -> str:
            return esquerda[:L - len(direita) - 1].ljust(L - len(direita)) + direita

        texto = ["=" * L, nome_hotel.upper().center(L),
                 f"FECHAMENTO DE CAIXA Nº {self.numero:03d}".center(L),
                 self.data_hora.strftime("%d/%m/%Y %H:%M").center(L), "=" * L,
                 linha("Res. Hóspede", "Total"), "-" * L]
        for r in sorted(self.reservas, key=lambda r: r.id):
            texto.append(linha(f"{r.id:>4} {r.hospede.nome[:22]} ({r.quarto.numero})", formatar_moeda(r.total)))
        texto += ["-" * L,
                  linha("Hospedagens:", str(self.quantidade)),
                  linha("Diárias:", formatar_moeda(self.valor_hospedagem)),
                  linha("Consumos:", formatar_moeda(self.valor_consumos)),
                  linha("TOTAL:", formatar_moeda(self.total)),
                  "=" * L]
        return "\n".join(texto)

    def salvar_relatorio(self, pasta: str, nome_hotel: str = "Hotel") -> str:
        """Grava o relatório em <pasta>/caixa_001.txt e devolve o caminho do arquivo."""
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, f"caixa_{self.numero:03d}.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(self.relatorio(nome_hotel) + "\n")
        return caminho

    def para_dict(self):
        return {"numero": self.numero, "data_hora": self.data_hora.isoformat(),
                "reservas": [r.id for r in self.reservas]}
