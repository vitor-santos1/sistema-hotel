"""Testa os cálculos da análise de dados com números conhecidos.

Executar a partir da pasta do projeto:  python tests/teste_analise.py
"""

import os
import sys
import tempfile
from datetime import date
from decimal import Decimal

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, RAIZ)

from analise import Analise
from modelos import Hotel, RegraNegocioErro

D = Decimal
hotel = Hotel()
ana = hotel.cadastrar_hospede("Ana Lima", "11122233344")
beto = hotel.cadastrar_hospede("Beto Souza", "55566677788")
hotel.cadastrar_quarto("101", "Standard", 2, "180")
hotel.cadastrar_quarto("201", "Luxo", 3, "300")
agua = hotel.cadastrar_servico("Água (frigobar)", "10")
lavanderia = hotel.cadastrar_servico("Lavanderia", "20")

r1 = hotel.reservar(ana.id, "101", date(2026, 3, 10), date(2026, 3, 13), 2)    # 3 diárias x 180 = 540
r1.check_in(); r1.lancar_consumo(agua, 4); r1.lancar_consumo(lavanderia, 1); r1.checkout()   # + 60 = 600
r2 = hotel.reservar(beto.id, "201", date(2026, 4, 1), date(2026, 4, 3), 2)     # 2 x 300 = 600
r2.check_in(); r2.checkout()
r3 = hotel.reservar(ana.id, "101", date(2026, 5, 1), date(2026, 5, 2), 1)
r3.cancelar()
hotel.reservar(beto.id, "101", date(2026, 12, 1), date(2026, 12, 3), 2)        # confirmada: 2 x 180 = 360

a = Analise(hotel)
assert a.faturamento_total() == D("1200.00")
assert a.faturamento_hospedagem() == D("1140.00") and a.faturamento_consumos() == D("60.00")
assert a.ticket_medio() == D("600.00")
assert a.receita_prevista() == D("360.00")
assert a.taxa_cancelamento() == 25.0                      # 1 de 4 reservas
assert a.duracao_media() == 2.5                           # (3 + 2) / 2
assert a.faturamento_por_mes() == [("mar/26", D("600.00")), ("abr/26", D("600.00"))]
assert dict(a.faturamento_por_quarto()) == {"101": D("600.00"), "201": D("600.00")}
assert a.consumo_por_servico() == [("Água (frigobar)", 4, D("40.00")), ("Lavanderia", 1, D("20.00"))]
assert [(n, q, t) for n, q, t in a.ranking_hospedes()] == [("Ana Lima", 1, D("600.00")), ("Beto Souza", 1, D("600.00"))]
assert a.periodo() == (date(2026, 3, 10), date(2026, 4, 3))
assert abs(a.taxa_ocupacao() - 5 / (24 * 2) * 100) < 1e-9   # 5 diárias vendidas de 48 possíveis

# ---------------- leitura de arquivo JSON ----------------
pasta = tempfile.mkdtemp()
caminho = os.path.join(pasta, "hotel.json")
hotel.arquivo = caminho
hotel.salvar()
antes = open(caminho, encoding="utf-8").read()
lida = Analise.de_arquivo(caminho)
assert lida.faturamento_total() == D("1200.00") and lida.origem == "hotel.json"
lida.hotel.salvar()                                          # arquivo=None: não pode gravar nada
assert open(caminho, encoding="utf-8").read() == antes

for conteudo in ('{"x": 1}', "isso nao e json", ""):
    ruim = os.path.join(pasta, "ruim.json")
    open(ruim, "w", encoding="utf-8").write(conteudo)
    try:
        Analise.de_arquivo(ruim)
        raise AssertionError("deveria recusar o arquivo")
    except RegraNegocioErro:
        pass
try:
    Analise.de_arquivo(os.path.join(pasta, "nao_existe.json"))
    raise AssertionError("deveria recusar")
except RegraNegocioErro:
    pass

# ---------------- exportação CSV ----------------
saida = os.path.join(pasta, "fat.csv")
assert a.exportar_csv(saida) == 2
linhas = open(saida, encoding="utf-8-sig").read().splitlines()
assert linhas[0].startswith("Reserva;Hóspede") and len(linhas) == 3
assert linhas[1].endswith(";600,00")

# ---------------- arquivo de exemplo que vai no projeto ----------------
exemplo = Analise.de_arquivo(os.path.join(RAIZ, "dados_exemplo.json"))
assert len(exemplo.concluidas) > 100 and exemplo.faturamento_total() > 0
assert len(exemplo.faturamento_por_mes()) == 11

# conta de um vazio não pode dar erro
vazio = Analise(Hotel())
assert vazio.faturamento_total() == 0 and vazio.ticket_medio() == 0 and vazio.taxa_ocupacao() == 0.0
assert vazio.faturamento_por_mes() == [] and vazio.ranking_hospedes() == []

print("Análise de dados: todos os testes passaram!")
