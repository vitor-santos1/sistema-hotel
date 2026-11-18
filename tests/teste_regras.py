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

# ---------------- validações de cadastro ----------------
def deve_falhar(funcao, *args):
    try:
        funcao(*args)
    except RegraNegocioErro:
        return
    raise AssertionError(f"deveria bloquear: {args}")

deve_falhar(hotel.cadastrar_hospede, "Al", "11122233344")                   # nome curto
deve_falhar(hotel.cadastrar_hospede, "Ana123", "11122233344")               # número no nome
deve_falhar(hotel.cadastrar_hospede, "A" * 61, "11122233344")               # nome longo
deve_falhar(hotel.cadastrar_hospede, "Ana Lima", "123")                     # documento curto
deve_falhar(hotel.cadastrar_hospede, "Ana Lima", "123456789012")            # documento longo
deve_falhar(hotel.cadastrar_hospede, "Ana Lima", "ABC12345")                # letras no documento
deve_falhar(hotel.cadastrar_hospede, "Ana Lima", "11122233344", "123")      # telefone curto
deve_falhar(hotel.cadastrar_hospede, "Outra", "123.456.789-00")             # CPF repetido (com máscara)
ana = hotel.cadastrar_hospede("Ana D'Ávila-Lima", "12.345.678-X", "(11) 3333-4444")
assert ana.documento == "12345678X" and ana.telefone == "1133334444"
assert hotel.cadastrar_hospede("Bia Souza", "111.222.333-44", "").documento_formatado == "111.222.333-44"
deve_falhar(hotel.cadastrar_quarto, "1234567", "Standard", 2, "100")        # número longo
deve_falhar(hotel.cadastrar_quarto, "999", "C" * 21, 2, "100")              # categoria longa
deve_falhar(hotel.cadastrar_quarto, "999", "Standard", 11, "100")           # capacidade acima do limite
deve_falhar(hotel.cadastrar_servico, "X", "5")                              # descrição curta
deve_falhar(hotel.cadastrar_servico, "S" * 41, "5")                         # descrição longa

# ---------------- exclusões ----------------
deve_falhar(hotel.excluir_hospede, hospede.id)       # tem reserva concluída
deve_falhar(hotel.excluir_quarto, "101")             # tem reserva concluída
deve_falhar(hotel.excluir_servico, agua.id)          # já lançado em hospedagem
hotel.excluir_servico(hotel.cadastrar_servico("Jornal", "5").id)   # nunca usado: pode excluir
hotel.cadastrar_quarto("500", "Luxo", 2, "300")
rc = hotel.reservar(ana.id, "500", date(2026, 12, 1), date(2026, 12, 3), 2)
deve_falhar(hotel.excluir_hospede, ana.id)           # reserva confirmada bloqueia
deve_falhar(hotel.excluir_quarto, "500")
rc.cancelar()
hotel.excluir_hospede(ana.id)                        # cancelada: apaga o hóspede e a reserva
assert rc.id not in hotel.reservas and ana.id not in hotel.hospedes
hotel.excluir_quarto("500")
assert "500" not in hotel.quartos
deve_falhar(hotel.excluir_hospede, 999)

# ---------------- fechamento de caixa ----------------
from datetime import datetime
import tempfile, os
assert hotel.faturamento_caixa_aberto() == Decimal("600.00")         # a reserva do roteiro
f1 = hotel.fechar_caixa(datetime(2026, 11, 19, 22, 0))
assert f1.numero == 1 and f1.quantidade == 1 and f1.total == Decimal("600.00")
assert f1.valor_hospedagem == Decimal("540.00") and f1.valor_consumos == Decimal("60.00")
assert hotel.faturamento_caixa_aberto() == Decimal("0.00")           # painel volta a zero
assert hotel.resumo()["faturamento"] == Decimal("0.00")
deve_falhar(hotel.fechar_caixa)                                       # nada novo para fechar
assert "TOTAL:" in f1.relatorio("Hotel Teste") and "R$ 600,00" in f1.relatorio()
pasta = tempfile.mkdtemp()
caminho = f1.salvar_relatorio(pasta, "Hotel Teste")
assert os.path.basename(caminho) == "caixa_001.txt" and "FECHAMENTO DE CAIXA" in open(caminho, encoding="utf-8").read()
# o fechamento vai para o JSON e volta igual
hotel.arquivo = os.path.join(pasta, "d.json"); hotel.salvar()
de_novo = Hotel.carregar(hotel.arquivo)
assert len(de_novo.fechamentos) == 1 and de_novo.ultimo_fechamento.total == Decimal("600.00")
assert de_novo.faturamento_caixa_aberto() == Decimal("0.00")
hotel.arquivo = None

print(r.extrato())
print("\nTodos os testes passaram!")
