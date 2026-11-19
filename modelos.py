"""
MODELOS: as classes do hotel (Orientação a Objetos). Toda regra e todo cálculo estão aqui.

Reserva guarda um Hospede, um Quarto e uma lista de Consumo.
O Hotel guarda tudo e salva os dados em um arquivo JSON.
"""

import json
import os
from datetime import date
from decimal import Decimal, InvalidOperation

CONFIRMADA, EM_HOSPEDAGEM, CONCLUIDA, CANCELADA = "Confirmada", "Em hospedagem", "Concluída", "Cancelada"

# Catálogo de serviços extras: nome -> preço
SERVICOS = {"Água": "10", "Refrigerante": "8", "Lavanderia": "20", "Café da manhã": "35"}


class RegraNegocioErro(Exception):
    """Erro lançado quando uma regra do hotel é violada. A tela mostra a mensagem."""


def dinheiro(valor):
    """'180,50' -> Decimal('180.50'). Decimal é um número exato (o float erra contas)."""
    try:
        return Decimal(str(valor).replace(",", "."))
    except InvalidOperation:
        raise RegraNegocioErro(f"Valor inválido: {valor}")


def reais(valor):
    return f"R$ {valor:.2f}".replace(".", ",")


class Hospede:
    """A pessoa responsável pela reserva."""

    def __init__(self, id, nome, documento, telefone=""):
        if not nome.strip() or not documento.strip():
            raise RegraNegocioErro("Nome e documento são obrigatórios.")
        self.id = id
        self.nome = nome.strip()
        self.documento = documento.strip()
        self.telefone = telefone.strip()


class Quarto:
    """Um quarto do hotel, com capacidade e diária."""

    def __init__(self, numero, categoria, capacidade, diaria):
        self.numero = str(numero).strip()
        self.categoria = categoria.strip() or "Standard"
        self.capacidade = int(capacidade)
        self.diaria = diaria  # isto chama o setter abaixo, que valida o valor

    # ENCAPSULAMENTO: o valor de verdade fica em _diaria e só muda pelo setter.
    @property
    def diaria(self):
        return self._diaria

    @diaria.setter
    def diaria(self, valor):
        valor = dinheiro(valor)
        if valor <= 0:
            raise RegraNegocioErro("A diária deve ser maior que zero.")
        self._diaria = valor


class Consumo:
    """Um extra usado na hospedagem. Guarda o preço do momento: se o catálogo mudar, a conta não muda."""

    def __init__(self, descricao, quantidade, preco_unitario):
        self.descricao = descricao
        self.quantidade = quantidade
        self.preco_unitario = preco_unitario

    @property
    def subtotal(self):
        """CÁLCULO: quantidade x preço."""
        return self.quantidade * self.preco_unitario


class Reserva:
    """O centro do sistema: liga um Hospede a um Quarto e guarda os Consumos."""

    def __init__(self, id, hospede, quarto, entrada, saida, pessoas, diaria_contratada=None, status=CONFIRMADA):
        if saida <= entrada:
            raise RegraNegocioErro("A data de saída deve ser depois da entrada.")
        if not 0 < pessoas <= quarto.capacidade:
            raise RegraNegocioErro(f"O quarto {quarto.numero} comporta de 1 a {quarto.capacidade} pessoa(s).")
        self.id = id
        self.hospede = hospede  # ASSOCIAÇÃO: a reserva aponta para um Hospede...
        self.quarto = quarto    # ...e para um Quarto
        self.entrada = entrada
        self.saida = saida
        self.pessoas = pessoas
        # PREÇO CONTRATADO: copia a diária de agora. Se o hotel mudar o preço depois, esta reserva não muda.
        self.diaria_contratada = quarto.diaria if diaria_contratada is None else dinheiro(diaria_contratada)
        self.status = status
        self.consumos = []      # COMPOSIÇÃO: os consumos vivem dentro da reserva

    # ---------------- cálculos ----------------
    @property
    def qtd_diarias(self):
        return (self.saida - self.entrada).days

    @property
    def valor_hospedagem(self):
        return self.qtd_diarias * self.diaria_contratada

    @property
    def total(self):
        return self.valor_hospedagem + sum((c.subtotal for c in self.consumos), Decimal("0"))

    # ---------------- regras ----------------
    def conflita_com(self, entrada, saida):
        """REGRA DE DATAS: só reservas Confirmadas ou Em hospedagem ocupam o quarto. Há conflito quando a nova
        entrada é ANTES da nossa saída E a nova saída é DEPOIS da nossa entrada.
        Quem sai dia 22 libera o quarto para quem entra dia 22."""
        ocupa = self.status in (CONFIRMADA, EM_HOSPEDAGEM)
        return ocupa and entrada < self.saida and saida > self.entrada

    def check_in(self):
        if self.status != CONFIRMADA:
            raise RegraNegocioErro("Check-in só é permitido em reserva confirmada.")
        self.status = EM_HOSPEDAGEM

    def lancar_consumo(self, descricao, quantidade):
        if self.status != EM_HOSPEDAGEM:
            raise RegraNegocioErro("Consumos só podem ser lançados durante a hospedagem.")
        if quantidade <= 0:
            raise RegraNegocioErro("A quantidade deve ser maior que zero.")
        self.consumos.append(Consumo(descricao, quantidade, dinheiro(SERVICOS[descricao])))

    def checkout(self):
        if self.status != EM_HOSPEDAGEM:
            raise RegraNegocioErro("Checkout só é permitido durante a hospedagem.")
        self.status = CONCLUIDA

    def cancelar(self):
        if self.status != CONFIRMADA:
            raise RegraNegocioErro("Só reservas confirmadas podem ser canceladas.")
        self.status = CANCELADA

    def extrato(self):
        """O texto da conta, mostrado na tela."""
        linhas = [f"Reserva {self.id} - {self.status}",
                  f"{self.hospede.nome} - quarto {self.quarto.numero}",
                  f"Hospedagem: {self.qtd_diarias} x {reais(self.diaria_contratada)} = {reais(self.valor_hospedagem)}"]
        linhas += [f"{c.descricao}: {c.quantidade} x {reais(c.preco_unitario)} = {reais(c.subtotal)}" for c in self.consumos]
        return "\n".join(linhas + [f"TOTAL: {reais(self.total)}"])


class Hotel:
    """Guarda tudo (em dicionários) e aplica as regras que envolvem várias reservas."""

    def __init__(self, arquivo=None):
        self.arquivo = arquivo  # onde os dados são salvos (None = não salva)
        self.hospedes = {}      # id -> Hospede
        self.quartos = {}       # número -> Quarto
        self.reservas = {}      # id -> Reserva

    def cadastrar_hospede(self, nome, documento, telefone=""):
        hospede = Hospede(max(self.hospedes, default=0) + 1, nome, documento, telefone)
        self.hospedes[hospede.id] = hospede
        self.salvar()

    def cadastrar_quarto(self, numero, categoria, capacidade, diaria):
        quarto = Quarto(numero, categoria, capacidade, diaria)
        if quarto.numero in self.quartos:
            raise RegraNegocioErro("Já existe um quarto com esse número.")
        self.quartos[quarto.numero] = quarto
        self.salvar()

    def quarto_livre(self, quarto, entrada, saida):
        """Pergunta a cada reserva deste quarto se ela conflita com as datas."""
        return not any(r.quarto is quarto and r.conflita_com(entrada, saida) for r in self.reservas.values())

    def quartos_disponiveis(self, entrada, saida, pessoas):
        """Os quartos que comportam o grupo e estão livres no período."""
        if saida <= entrada:
            raise RegraNegocioErro("A data de saída deve ser depois da entrada.")
        return [q for q in self.quartos.values()
                if 0 < pessoas <= q.capacidade and self.quarto_livre(q, entrada, saida)]

    def reservar(self, hospede_id, numero_quarto, entrada, saida, pessoas):
        quarto = self.quartos[numero_quarto]
        if not self.quarto_livre(quarto, entrada, saida):
            raise RegraNegocioErro(f"O quarto {quarto.numero} já está reservado nesse período.")
        reserva = Reserva(max(self.reservas, default=0) + 1, self.hospedes[hospede_id], quarto, entrada, saida, pessoas)
        self.reservas[reserva.id] = reserva
        self.salvar()

    # ---------------- arquivo JSON ----------------
    def salvar(self):
        """Transforma os objetos em dicionários simples e grava no arquivo JSON."""
        if not self.arquivo:
            return
        dados = {
            "hospedes": [vars(h) for h in self.hospedes.values()],
            "quartos": [{"numero": q.numero, "categoria": q.categoria, "capacidade": q.capacidade, "diaria": q.diaria}
                        for q in self.quartos.values()],
            "reservas": [{"id": r.id, "hospede": r.hospede.id, "quarto": r.quarto.numero, "entrada": r.entrada,
                          "saida": r.saida, "pessoas": r.pessoas, "diaria_contratada": r.diaria_contratada,
                          "status": r.status, "consumos": [vars(c) for c in r.consumos]}
                         for r in self.reservas.values()],
        }
        with open(self.arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False, default=str)  # default=str: Decimal e data viram texto

    @classmethod
    def carregar(cls, arquivo):
        """O caminho de volta: lê o JSON e recria os objetos (primeiro hóspedes e quartos, depois as reservas)."""
        hotel = cls(arquivo)
        if not os.path.exists(arquivo):  # primeira vez: cria alguns quartos de exemplo
            for numero, categoria, capacidade, diaria in [("101", "Standard", 2, "180"), ("102", "Standard", 2, "180"),
                                                         ("201", "Luxo", 3, "280"), ("301", "Família", 5, "350")]:
                hotel.cadastrar_quarto(numero, categoria, capacidade, diaria)
            return hotel
        with open(arquivo, encoding="utf-8") as f:
            dados = json.load(f)
        for d in dados["hospedes"]:
            hotel.hospedes[d["id"]] = Hospede(**d)
        for d in dados["quartos"]:
            hotel.quartos[d["numero"]] = Quarto(**d)
        for d in dados["reservas"]:
            reserva = Reserva(d["id"], hotel.hospedes[d["hospede"]], hotel.quartos[d["quarto"]],
                              date.fromisoformat(d["entrada"]), date.fromisoformat(d["saida"]),
                              d["pessoas"], d["diaria_contratada"], d["status"])
            reserva.consumos = [Consumo(c["descricao"], c["quantidade"], dinheiro(c["preco_unitario"]))
                                for c in d["consumos"]]
            hotel.reservas[reserva.id] = reserva
        return hotel
