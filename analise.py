"""
Análise de dados do hotel.

A classe Analise LÊ um arquivo JSON (o mesmo formato do dados_hotel.json) e calcula
indicadores sobre as hospedagens: faturamento, ocupação, ranking e consumo.
Ela só consulta os dados: nunca altera nem grava o arquivo.

Reaproveita as classes de modelos.py (Hotel, Reserva, Consumo...), por isso os
valores vêm dos cálculos que já existem nelas (Reserva.total, Consumo.subtotal...).
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from datetime import date
from decimal import Decimal

from modelos import Hotel, RegraNegocioErro, StatusReserva

ZERO = Decimal("0.00")
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


class Analise:
    """Indicadores calculados a partir das reservas de um Hotel."""

    def __init__(self, hotel: Hotel, origem: str = "Dados do hotel"):
        self.hotel = hotel
        self.origem = origem

    # ---------------- leitura do arquivo ----------------
    @classmethod
    def de_arquivo(cls, caminho: str) -> "Analise":
        """Abre um arquivo .json e monta a análise. Mostra um erro claro se o arquivo não servir."""
        if not os.path.isfile(caminho):
            raise RegraNegocioErro(f"Arquivo não encontrado: {caminho}")
        try:
            hotel = Hotel.carregar(caminho)
        except (ValueError, KeyError, TypeError, AttributeError):
            # ValueError inclui JSON malformado; KeyError/TypeError: faltam campos do formato esperado
            raise RegraNegocioErro("Esse arquivo não tem o formato de dados do hotel (JSON inválido ou incompleto).")
        hotel.arquivo = None  # análise é só leitura: nada será gravado de volta
        return cls(hotel, origem=os.path.basename(caminho))

    # ---------------- grupos de reservas ----------------
    def _com_status(self, *status: StatusReserva) -> list:
        return [r for r in self.hotel.reservas.values() if r.status in status]

    @property
    def concluidas(self) -> list:
        return self._com_status(StatusReserva.CONCLUIDA)

    @property
    def total_reservas(self) -> int:
        return len(self.hotel.reservas)

    # ---------------- indicadores de dinheiro ----------------
    def faturamento_total(self) -> Decimal:
        return sum((r.total for r in self.concluidas), ZERO)

    def faturamento_hospedagem(self) -> Decimal:
        return sum((r.valor_hospedagem for r in self.concluidas), ZERO)

    def faturamento_consumos(self) -> Decimal:
        return sum((r.valor_consumos for r in self.concluidas), ZERO)

    def ticket_medio(self) -> Decimal:
        """Quanto cada hospedagem concluída rendeu, em média."""
        n = len(self.concluidas)
        return (self.faturamento_total() / n).quantize(Decimal("0.01")) if n else ZERO

    def receita_prevista(self) -> Decimal:
        """Valor das hospedagens já reservadas, mas que ainda não aconteceram."""
        return sum((r.valor_hospedagem for r in self._com_status(StatusReserva.CONFIRMADA)), ZERO)

    # ---------------- indicadores de ocupação ----------------
    def periodo(self) -> tuple[date, date] | None:
        """Do primeiro check-in ao último check-out das hospedagens realizadas."""
        realizadas = self._com_status(StatusReserva.CONCLUIDA, StatusReserva.EM_HOSPEDAGEM)
        if not realizadas:
            return None
        return min(r.entrada for r in realizadas), max(r.saida for r in realizadas)

    def taxa_ocupacao(self) -> float:
        """Diárias vendidas ÷ diárias disponíveis (quartos × dias do período), em %."""
        periodo = self.periodo()
        if not periodo or not self.hotel.quartos:
            return 0.0
        dias = (periodo[1] - periodo[0]).days
        vendidas = sum(r.qtd_diarias for r in self._com_status(StatusReserva.CONCLUIDA,
                                                                StatusReserva.EM_HOSPEDAGEM))
        return min(100.0, vendidas / (dias * len(self.hotel.quartos)) * 100)

    def taxa_cancelamento(self) -> float:
        if not self.total_reservas:
            return 0.0
        return len(self._com_status(StatusReserva.CANCELADA)) / self.total_reservas * 100

    def duracao_media(self) -> float:
        """Média de diárias por hospedagem concluída."""
        concluidas = self.concluidas
        return sum(r.qtd_diarias for r in concluidas) / len(concluidas) if concluidas else 0.0

    # ---------------- agrupamentos (para gráficos e tabelas) ----------------
    def faturamento_por_mes(self) -> list[tuple[str, Decimal]]:
        """[('jan/26', Decimal), ...] em ordem de data. O mês é o do check-out."""
        soma: dict[tuple[int, int], Decimal] = defaultdict(lambda: ZERO)
        for r in self.concluidas:
            soma[(r.saida.year, r.saida.month)] += r.total
        return [(f"{MESES[m - 1]}/{a % 100:02d}", valor) for (a, m), valor in sorted(soma.items())]

    def faturamento_por_quarto(self) -> list[tuple[str, Decimal]]:
        soma: dict[str, Decimal] = defaultdict(lambda: ZERO)
        for r in self.concluidas:
            soma[r.quarto.numero] += r.total
        return sorted(soma.items(), key=lambda item: item[1], reverse=True)

    def consumo_por_servico(self) -> list[tuple[str, int, Decimal]]:
        """[(descrição, quantidade, valor)] do que mais rendeu para o que menos rendeu."""
        qtd: dict[str, int] = defaultdict(int)
        valor: dict[str, Decimal] = defaultdict(lambda: ZERO)
        for r in self.concluidas:
            for c in r.consumos:
                qtd[c.servico.descricao] += c.quantidade
                valor[c.servico.descricao] += c.subtotal
        return sorted(((d, qtd[d], valor[d]) for d in qtd), key=lambda item: item[2], reverse=True)

    def ranking_hospedes(self, quantos: int = 5) -> list[tuple[str, int, Decimal]]:
        """[(nome, hospedagens, total gasto)] de quem mais gastou."""
        qtd: dict[int, int] = defaultdict(int)
        total: dict[int, Decimal] = defaultdict(lambda: ZERO)
        for r in self.concluidas:
            qtd[r.hospede.id] += 1
            total[r.hospede.id] += r.total
        ordem = sorted(total, key=lambda hid: total[hid], reverse=True)[:quantos]
        return [(self.hotel.hospedes[hid].nome, qtd[hid], total[hid]) for hid in ordem]

    # ---------------- exportação ----------------
    def exportar_csv(self, caminho: str) -> int:
        """Grava as hospedagens concluídas em CSV (abre direto no Excel). Retorna quantas linhas."""
        def num(valor: Decimal) -> str:
            return str(valor).replace(".", ",")  # Excel em português usa vírgula decimal

        linhas = sorted(self.concluidas, key=lambda r: (r.saida, r.id))
        with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
            escritor = csv.writer(f, delimiter=";")
            escritor.writerow(["Reserva", "Hóspede", "Quarto", "Entrada", "Saída", "Diárias",
                               "Valor da diária", "Hospedagem", "Consumos", "Total"])
            for r in linhas:
                escritor.writerow([r.id, r.hospede.nome, r.quarto.numero,
                                   r.entrada.strftime("%d/%m/%Y"), r.saida.strftime("%d/%m/%Y"),
                                   r.qtd_diarias, num(r.diaria_contratada), num(r.valor_hospedagem),
                                   num(r.valor_consumos), num(r.total)])
        return len(linhas)
