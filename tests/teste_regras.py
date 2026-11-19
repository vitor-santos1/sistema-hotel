"""Confere as regras do hotel com o roteiro da apresentação.   Executar:  python tests/teste_regras.py"""

import os
import sys
import tempfile
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from modelos import Hotel, RegraNegocioErro, CONCLUIDA


def deve_falhar(acao):
    """A ação precisa lançar RegraNegocioErro; se não lançar, o teste falha."""
    try:
        acao()
    except RegraNegocioErro:
        return
    raise AssertionError("deveria ter sido bloqueado")


hotel = Hotel()  # sem arquivo: não grava nada
hotel.cadastrar_hospede("Maria Silva", "12345678900", "11999990000")
hotel.cadastrar_quarto("101", "Standard", 2, "180")
quarto = hotel.quartos["101"]

# Reserva de 3 diárias
hotel.reservar(1, "101", date(2026, 11, 19), date(2026, 11, 22), 2)
reserva = hotel.reservas[1]
assert reserva.qtd_diarias == 3 and reserva.valor_hospedagem == Decimal("540")

# Conflito de datas: 20/11 a 23/11 bloqueia; 22/11 a 24/11 e 17/11 a 19/11 liberam
deve_falhar(lambda: hotel.reservar(1, "101", date(2026, 11, 20), date(2026, 11, 23), 1))
assert hotel.quarto_livre(quarto, date(2026, 11, 22), date(2026, 11, 24))
assert hotel.quarto_livre(quarto, date(2026, 11, 17), date(2026, 11, 19))

# Situações: consumo antes do check-in é proibido
deve_falhar(lambda: reserva.lancar_consumo("Água", 1))
reserva.check_in()
reserva.lancar_consumo("Água", 4)
reserva.lancar_consumo("Lavanderia", 1)

# Preço contratado: mudar a diária do quarto não muda a conta da reserva
quarto.diaria = "999"
assert reserva.total == Decimal("600"), reserva.total   # 3 x 180 + 40 + 20

reserva.checkout()
assert reserva.status == CONCLUIDA
deve_falhar(lambda: reserva.lancar_consumo("Água", 1))     # depois do checkout não lança mais

# Outras regras
deve_falhar(lambda: reserva.lancar_consumo("Água", 0))                                      # quantidade zero (já concluída também bloqueia)
deve_falhar(lambda: hotel.reservar(1, "101", date(2026, 12, 1), date(2026, 12, 2), 3))   # acima da capacidade
deve_falhar(lambda: hotel.reservar(1, "101", date(2026, 12, 5), date(2026, 12, 5), 1))   # saída = entrada
deve_falhar(lambda: setattr(quarto, "diaria", "-5"))                                      # diária negativa
deve_falhar(lambda: hotel.cadastrar_hospede("", "123"))                                   # nome vazio

# Cancelada não bloqueia o quarto
hotel.reservar(1, "101", date(2026, 12, 10), date(2026, 12, 12), 2)
hotel.reservas[2].cancelar()
hotel.reservar(1, "101", date(2026, 12, 10), date(2026, 12, 12), 2)

# Salvar e carregar o JSON: os dados voltam iguais
arquivo = os.path.join(tempfile.mkdtemp(), "hotel.json")
hotel.arquivo = arquivo
hotel.salvar()
de_novo = Hotel.carregar(arquivo)
assert de_novo.reservas[1].total == Decimal("600") and de_novo.reservas[1].status == CONCLUIDA
assert len(de_novo.reservas) == 3 and len(de_novo.hospedes) == 1

print(reserva.extrato())
print("\nTodos os testes passaram!")
