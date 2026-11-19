"""StatusReserva e CLASSE Reserva: o CENTRO do sistema.

A Reserva liga um Hospede a um Quarto (ASSOCIAÇÃO) e guarda a lista de Consumo (COMPOSIÇÃO).

ONDE ESTÁ O QUÊ
  StatusReserva ......... as situações: Confirmada, Em hospedagem, Concluída, Cancelada
  Reserva.__init__ ...... cria a reserva e recusa datas, pessoas ou capacidade inválidas
  CÁLCULOS: qtd_diarias, valor_hospedagem, valor_consumos, total
  REGRAS:   ativa, conflita_com (regra das datas), check_in, lancar_consumo, checkout, cancelar
  extrato ............... texto da conta (o recibo mostrado na tela)
  para_dict ............. dicionário para o JSON
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum

from .consumo import Consumo
from .erros import RegraNegocioErro
from .formatos import dinheiro, formatar_data, formatar_moeda
from .hospede import Hospede
from .quarto import Quarto
from .servico import Servico


class StatusReserva(Enum):
    """Situações possíveis de uma reserva: Confirmada -> Em hospedagem -> Concluída (ou Cancelada)."""

    # Enum = lista FECHADA de valores. Em vez de textos soltos ('confirmada', 'Confirmada'...) que dariam erro de digitação,
    # usamos StatusReserva.CONFIRMADA. O texto bonito fica em .value ('Em hospedagem') e o nome em .name ('EM_HOSPEDAGEM').
    CONFIRMADA = "Confirmada"
    EM_HOSPEDAGEM = "Em hospedagem"
    CONCLUIDA = "Concluída"
    CANCELADA = "Cancelada"


class Reserva:
    """Centro do sistema: liga Hospede + Quarto e reúne os Consumos."""

    # A Reserva é o CENTRO do sistema. Recebe os objetos Hospede e Quarto já prontos e guarda a referência a eles.
    # As 3 verificações abaixo impedem uma reserva inválida: saída antes da entrada, sem pessoas ou acima da capacidade.
    def __init__(self, id: int, hospede: Hospede, quarto: Quarto,
                 entrada: date, saida: date, pessoas: int,
                 diaria_contratada=None, status=StatusReserva.CONFIRMADA):
        if saida <= entrada:
            raise RegraNegocioErro("A data de saída deve ser posterior à entrada.")
        if int(pessoas) <= 0:
            raise RegraNegocioErro("A quantidade de pessoas deve ser positiva.")
        if not quarto.comporta(int(pessoas)):
            raise RegraNegocioErro(
                f"O quarto {quarto.numero} comporta no máximo {quarto.capacidade} pessoa(s).")
        self.id = id
        self.hospede = hospede              # associação
        self.quarto = quarto                # associação
        self.entrada = entrada
        self.saida = saida
        self.pessoas = int(pessoas)
        # PREÇO CONTRATADO: copia a diária do quarto NESTE momento. Se o hotel mudar o preço depois, esta reserva não muda.
        # 'A if condição else B' é um if em uma linha: usa o valor informado, ou a diária atual do quarto se não houver.
        self.diaria_contratada = dinheiro(quarto.diaria if diaria_contratada is None
                                          else diaria_contratada)
        self.status = status
        self.consumos: list[Consumo] = []   # composição

    # ---------------- cálculos ----------------
    # Subtrair duas datas dá um 'timedelta'; .days é o número de dias. Ex.: 22/11 - 19/11 = 3 diárias.
    @property
    def qtd_diarias(self) -> int:
        return (self.saida - self.entrada).days

    @property
    def valor_hospedagem(self) -> Decimal:
        return self.qtd_diarias * self.diaria_contratada

    # sum(... for c in self.consumos) soma o subtotal de cada consumo da lista. O Decimal('0.00') é o ponto de partida da soma.
    @property
    def valor_consumos(self) -> Decimal:
        return sum((c.subtotal for c in self.consumos), Decimal("0.00"))

    # TOTAL DA CONTA = hospedagem + consumos. Exemplo do roteiro: 540 + 60 = R$ 600,00.
    @property
    def total(self) -> Decimal:
        return self.valor_hospedagem + self.valor_consumos

    # ---------------- regras ----------------
    # 'in' confere se o valor está dentro da tupla. Só reservas Confirmadas ou Em hospedagem seguram o quarto.
    @property
    def ativa(self) -> bool:
        """Reservas canceladas ou concluídas não bloqueiam o quarto."""
        return self.status in (StatusReserva.CONFIRMADA, StatusReserva.EM_HOSPEDAGEM)

    # REGRA DE DATAS. Exemplo com uma reserva existente de 19/11 a 22/11:
    #   nova 20/11 a 23/11 -> CONFLITA     (20 < 22 e 23 > 19)
    #   nova 22/11 a 24/11 -> não conflita (22 < 22 é falso)
    #   nova 17/11 a 19/11 -> não conflita (19 > 19 é falso)
    def conflita_com(self, entrada: date, saida: date) -> bool:
        """Há conflito se: nova entrada < saída existente E nova saída > entrada existente.
        A saída é exclusiva: quem sai dia 22 libera o quarto para quem entra dia 22."""
        return self.ativa and entrada < self.saida and saida > self.entrada

    # Cada ação só é permitida numa certa situação (a reserva funciona como uma máquina de situações).
    # Aqui: check-in só se estiver Confirmada. Se não estiver, 'raise' interrompe o método e a tela mostra a mensagem.
    # Se estiver, muda o status para Em hospedagem.
    def check_in(self):
        if self.status != StatusReserva.CONFIRMADA:
            raise RegraNegocioErro("Check-in só é permitido em reserva confirmada.")
        self.status = StatusReserva.EM_HOSPEDAGEM

    # COMPOSIÇÃO: o Consumo é criado aqui dentro e guardado na lista self.consumos desta reserva.
    def lancar_consumo(self, servico: Servico, quantidade: int) -> Consumo:
        if self.status != StatusReserva.EM_HOSPEDAGEM:
            raise RegraNegocioErro("Consumos só podem ser lançados durante a hospedagem.")
        consumo = Consumo(servico, quantidade)
        self.consumos.append(consumo)
        return consumo

    def checkout(self) -> Decimal:
        if self.status != StatusReserva.EM_HOSPEDAGEM:
            raise RegraNegocioErro("Checkout só é permitido durante a hospedagem.")
        self.status = StatusReserva.CONCLUIDA
        return self.total

    def cancelar(self):
        if self.status != StatusReserva.CONFIRMADA:
            raise RegraNegocioErro("Somente reservas confirmadas podem ser canceladas.")
        self.status = StatusReserva.CANCELADA

    # Monta o texto da conta (o recibo que aparece na tela). Cada linha é uma f-string: f'...{valor}...' troca {valor} pelo conteúdo.
    def extrato(self) -> str:
        """Texto da conta para mostrar na tela de fechamento."""
        linhas = [
            f"Reserva nº {self.id}  -  {self.status.value}",
            f"Hóspede: {self.hospede}",
            f"{self.quarto}  |  {self.pessoas} pessoa(s)",
            f"Período: {formatar_data(self.entrada)} a {formatar_data(self.saida)}",
            "-" * 46,
            f"Hospedagem: {self.qtd_diarias} diária(s) x "
            f"{formatar_moeda(self.diaria_contratada)} = {formatar_moeda(self.valor_hospedagem)}",
        ]
        for c in self.consumos:
            linhas.append(f"{c.servico.descricao}: {c.quantidade} x "
                          f"{formatar_moeda(c.preco_unitario)} = {formatar_moeda(c.subtotal)}")
        linhas += ["-" * 46,
                   f"Consumos: {formatar_moeda(self.valor_consumos)}",
                   f"TOTAL:    {formatar_moeda(self.total)}"]
        return "\n".join(linhas)

    def para_dict(self):
        return {"id": self.id, "hospede_id": self.hospede.id,
                "quarto_numero": self.quarto.numero,
                "entrada": self.entrada.isoformat(), "saida": self.saida.isoformat(),
                "pessoas": self.pessoas, "diaria_contratada": str(self.diaria_contratada),
                "status": self.status.name,
                "consumos": [c.para_dict() for c in self.consumos]}
