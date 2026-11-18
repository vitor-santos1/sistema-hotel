"""Testa o roteiro da apresentação sem abrir as telas.

Executar a partir da pasta do projeto:  python tests/teste_regras.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from datetime import date
from decimal import Decimal

from modelos import Hotel, RegraNegocioErro, StatusReserva

hotel = Hotel()  # sem arquivo: não grava nada
hospede = hotel.cadastrar_hospede("Maria Silva", "123.456.789-00", "(11) 99999-0000")
hotel.cadastrar_quarto("101", "Standard", 2, "180,00")
agua = hotel.cadastrar_servico("Água (frigobar)", "10,00")
lavanderia = hotel.cadastrar_servico("Lavanderia", "20,00")

r = hotel.reservar(hospede.id, "101", date(2026, 11, 19), date(2026, 11, 22), 2)
assert r.qtd_diarias == 3
assert r.valor_hospedagem == Decimal("540.00")

# Conflitos (tabela da proposta)
quarto = hotel.quartos["101"]
assert not hotel.quarto_livre(quarto, date(2026, 11, 20), date(2026, 11, 23))  # bloquear
assert hotel.quarto_livre(quarto, date(2026, 11, 22), date(2026, 11, 24))      # permitir
assert hotel.quarto_livre(quarto, date(2026, 11, 17), date(2026, 11, 19))      # permitir
try:
    hotel.reservar(hospede.id, "101", date(2026, 11, 20), date(2026, 11, 23), 1)
    raise AssertionError("deveria bloquear")
except RegraNegocioErro:
    pass

# Consumo antes do check-in é proibido
try:
    r.lancar_consumo(agua, 1)
    raise AssertionError("deveria bloquear")
except RegraNegocioErro:
    pass

r.check_in()
r.lancar_consumo(agua, 4)
r.lancar_consumo(lavanderia, 1)

# Mudar o preço do catálogo não altera a conta já contratada
quarto.diaria = "999"
agua.preco = Decimal("50.00")
assert r.total == Decimal("600.00"), r.total

assert r.checkout() == Decimal("600.00")
assert r.status == StatusReserva.CONCLUIDA
try:
    r.lancar_consumo(agua, 1)
    raise AssertionError("deveria bloquear")
except RegraNegocioErro:
    pass

# Excesso de pessoas
try:
    hotel.reservar(hospede.id, "101", date(2026, 12, 1), date(2026, 12, 2), 3)
    raise AssertionError("deveria bloquear")
except RegraNegocioErro:
    pass

print(r.extrato())
print("\nTodos os testes passaram!")
