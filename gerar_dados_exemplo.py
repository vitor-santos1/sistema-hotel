"""
Gera o arquivo dados_exemplo.json: movimento fictício do hotel em 2026 (janeiro a novembro),
para a tela de Análise de dados ter números de verdade na demonstração.

Executar:  python gerar_dados_exemplo.py

Usa as mesmas classes do sistema (Hotel, Reserva...) e uma semente fixa: toda vez que rodar,
o arquivo sai igual. Os nomes e documentos são inventados.
"""

import os
import random
from datetime import date, timedelta
from decimal import Decimal

from modelos import Hotel

HOJE = date(2026, 11, 18)
ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados_exemplo.json")

PRIMEIROS = ["Ana", "Bruno", "Carla", "Daniel", "Elisa", "Felipe", "Gabriela", "Henrique", "Isabela",
             "João", "Karina", "Lucas", "Mariana", "Nicolas", "Olívia", "Paulo", "Rafaela", "Sérgio",
             "Tatiana", "Vitor"]
SOBRENOMES = ["Silva", "Souza", "Oliveira", "Santos", "Pereira", "Lima", "Costa", "Ribeiro", "Almeida",
              "Carvalho", "Gomes", "Martins", "Araújo", "Barbosa", "Rocha"]
QUARTOS = [("101", "Standard", 2, "180"), ("102", "Standard", 2, "180"), ("103", "Standard", 2, "180"),
           ("201", "Luxo", 3, "280"), ("202", "Luxo", 3, "280"),
           ("301", "Família", 5, "350"), ("302", "Família", 5, "350")]
SERVICOS = [("Água (frigobar)", "10"), ("Refrigerante (frigobar)", "8"), ("Cerveja (frigobar)", "14"),
            ("Lavanderia", "20"), ("Café da manhã no quarto", "35"), ("Estacionamento", "25")]
# Alta temporada: a diária sobe (e a reserva guarda o preço contratado)
MULTIPLICADOR = {1: Decimal("1.25"), 2: Decimal("1.10"), 7: Decimal("1.20"), 12: Decimal("1.30")}


def gerar(caminho: str = ARQUIVO) -> Hotel:
    rnd = random.Random(2026)
    hotel = Hotel(nome="Hotel Paradigmas (dados de exemplo)")  # sem arquivo: grava só no final

    for numero, categoria, capacidade, diaria in QUARTOS:
        hotel.cadastrar_quarto(numero, categoria, capacidade, diaria)
    for descricao, preco in SERVICOS:
        hotel.cadastrar_servico(descricao, preco)

    hospedes, documentos, nomes = [], set(), set()
    while len(hospedes) < 45:
        doc = "".join(rnd.choice("0123456789") for _ in range(11))
        nome = f"{rnd.choice(PRIMEIROS)} {rnd.choice(SOBRENOMES)}"
        if doc in documentos or nome in nomes:  # sem nomes repetidos, para o ranking não confundir
            continue
        documentos.add(doc)
        nomes.add(nome)
        hospedes.append(hotel.cadastrar_hospede(nome, doc, "119" + "".join(rnd.choice("0123456789") for _ in range(8))))
    pesos = [1 / (i + 1) ** 0.25 for i in range(len(hospedes))]  # alguns hóspedes voltam mais vezes

    for quarto in hotel.quartos.values():
        base = quarto.diaria
        dia = date(2026, 1, 1) + timedelta(days=rnd.randint(0, 3))
        while dia < HOJE + timedelta(days=25):
            noites = rnd.choices([1, 2, 3, 4, 5, 7], [10, 25, 28, 18, 12, 7])[0]
            saida = dia + timedelta(days=noites)
            quarto.diaria = base * MULTIPLICADOR.get(dia.month, Decimal("1"))
            r = hotel.reservar(rnd.choices(hospedes, pesos)[0].id, quarto.numero, dia, saida,
                               rnd.randint(1, quarto.capacidade))
            quarto.diaria = base

            if saida <= HOJE:                       # já terminou
                if rnd.random() < 0.08:
                    r.cancelar()
                else:
                    r.check_in()
                    _lancar_consumos(rnd, hotel, r)
                    r.checkout()
            elif dia <= HOJE:                       # hospedado agora
                r.check_in()
                _lancar_consumos(rnd, hotel, r)
            # senão: continua Confirmada (reserva futura)

            dia = saida + timedelta(days=rnd.choice([0, 0, 1, 1, 2, 3]))

    hotel.arquivo = caminho
    hotel.salvar()
    return hotel


def _lancar_consumos(rnd, hotel, reserva):
    for _ in range(rnd.choices([0, 1, 2, 3], [30, 35, 25, 10])[0]):
        reserva.lancar_consumo(rnd.choice(list(hotel.servicos.values())), rnd.randint(1, 4))


if __name__ == "__main__":
    h = gerar()
    print(f"Arquivo gerado: {ARQUIVO}")
    print(f"{len(h.quartos)} quartos, {len(h.hospedes)} hóspedes, {len(h.reservas)} reservas")
