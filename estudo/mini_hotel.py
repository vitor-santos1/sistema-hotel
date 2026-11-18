"""
MINI HOTEL: uma versão bem pequena do sistema, para entender as ideias ANTES de ler o modelos.py.

Aqui tem só o essencial: Hospede, Quarto, Consumo e Reserva (sem telas, sem arquivo, sem validações).
Execute e leia a saída junto com o código:

    python estudo/mini_hotel.py

Exercícios no final do arquivo.
"""

from datetime import date
from decimal import Decimal


class Hospede:
    def __init__(self, nome):          # __init__ = construtor: roda quando criamos Hospede("Maria")
        self.nome = nome               # self.nome guarda o dado DENTRO do objeto


class Quarto:
    def __init__(self, numero, diaria):
        self.numero = numero
        self.diaria = Decimal(diaria)  # Decimal: número exato, próprio para dinheiro


class Consumo:
    def __init__(self, descricao, quantidade, preco_unitario):
        self.descricao = descricao
        self.quantidade = quantidade
        self.preco_unitario = Decimal(preco_unitario)

    @property                          # permite usar consumo.subtotal (sem parênteses)
    def subtotal(self):
        return self.quantidade * self.preco_unitario


class Reserva:
    def __init__(self, hospede, quarto, entrada, saida):
        self.hospede = hospede                    # ASSOCIAÇÃO: a reserva aponta para um Hospede...
        self.quarto = quarto                      # ...e para um Quarto, que existem por conta própria
        self.entrada = entrada
        self.saida = saida
        self.diaria_contratada = quarto.diaria    # copia o preço de AGORA (preço contratado)
        self.consumos = []                        # COMPOSIÇÃO: os consumos vivem dentro da reserva

    @property
    def qtd_diarias(self):
        return (self.saida - self.entrada).days   # data - data = número de dias

    @property
    def total(self):
        consumos = sum(c.subtotal for c in self.consumos)
        return self.qtd_diarias * self.diaria_contratada + consumos

    def conflita_com(self, entrada, saida):
        # Há conflito quando a nova entrada é ANTES da nossa saída E a nova saída é DEPOIS da nossa entrada.
        return entrada < self.saida and saida > self.entrada


# ---------------------------------------------------------------------------
# Demonstração (o roteiro da apresentação, em pequeno)
# ---------------------------------------------------------------------------

maria = Hospede("Maria Silva")
q101 = Quarto("101", "180.00")

reserva = Reserva(maria, q101, date(2026, 11, 19), date(2026, 11, 22))
print(f"Reserva de {reserva.hospede.nome} no quarto {reserva.quarto.numero}: {reserva.qtd_diarias} diárias")

reserva.consumos.append(Consumo("Água (frigobar)", 4, "10.00"))
reserva.consumos.append(Consumo("Lavanderia", 1, "20.00"))
print("Total da conta: R$", reserva.total, " (3 x 180 + 40 + 20)")

print("\nConflito de datas (reserva existente: 19/11 a 22/11):")
testes = [("20/11 a 23/11", date(2026, 11, 20), date(2026, 11, 23)),
          ("22/11 a 24/11", date(2026, 11, 22), date(2026, 11, 24)),
          ("17/11 a 19/11", date(2026, 11, 17), date(2026, 11, 19))]
for nome, entrada, saida in testes:
    print(f"  nova reserva {nome}:", "CONFLITA" if reserva.conflita_com(entrada, saida) else "livre")

q101.diaria = Decimal("999.00")   # o hotel aumenta o preço do quarto depois...
print("\nDepois de mudar a diária do quarto para 999, a conta continua:", reserva.total)

# ---------------------------------------------------------------------------
# EXERCÍCIOS (mude o código acima e rode de novo)
# 1. Troque a data de saída para 23/11. Quanto passa a custar?
# 2. Acrescente um consumo de 2 "Refrigerante" a R$ 8,00. Qual o novo total?
# 3. Descubra por que 22/11 a 24/11 não conflita. Troque "<" por "<=" em conflita_com e veja o que acontece.
# 4. Crie um segundo hóspede e uma segunda reserva no mesmo quarto, nas datas 22/11 a 24/11.
# 5. Dica: tente imprimir reserva.consumos[0].subtotal.
# ---------------------------------------------------------------------------
