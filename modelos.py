"""
MODELOS: as classes do hotel (Orientação a Objetos).

Quem se relaciona com quem:
    Reserva guarda um Hospede, um Quarto e uma lista de Consumo.
    Cada Consumo aponta para um Servico.
    O Hotel guarda tudo e salva os dados em um arquivo JSON.

Toda regra e todo cálculo do sistema estão aqui. As telas (app.py) só chamam estas classes.
"""

import json
import os
from datetime import date
from decimal import Decimal, InvalidOperation

# As situações possíveis de uma reserva
CONFIRMADA = "Confirmada"
EM_HOSPEDAGEM = "Em hospedagem"
CONCLUIDA = "Concluída"
CANCELADA = "Cancelada"


class RegraNegocioErro(Exception):
    """Erro lançado quando uma regra do hotel é violada. A tela mostra a mensagem."""


def dinheiro(valor):
    """Converte '180' ou '180,50' em Decimal. Decimal é um número exato (o float erra contas)."""
    try:
        return Decimal(str(valor).replace(",", "."))
    except InvalidOperation:
        raise RegraNegocioErro(f"Valor inválido: {valor}")


def reais(valor):
    """Decimal('600') -> 'R$ 600,00'"""
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
        if int(capacidade) <= 0:
            raise RegraNegocioErro("A capacidade deve ser maior que zero.")
        self.numero = str(numero).strip()
        self.categoria = categoria.strip() or "Standard"
        self.capacidade = int(capacidade)
        self.diaria = diaria  # isto chama o "setter" abaixo, que valida o valor

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

    def comporta(self, pessoas):
        """True se o grupo cabe no quarto."""
        return 0 < pessoas <= self.capacidade


class Servico:
    """Um item do catálogo de extras (frigobar, lavanderia...)."""

    def __init__(self, id, descricao, preco):
        if not descricao.strip():
            raise RegraNegocioErro("A descrição do serviço é obrigatória.")
        self.id = id
        self.descricao = descricao.strip()
        self.preco = dinheiro(preco)

    def __str__(self):
        return f"{self.descricao} - {reais(self.preco)}"


class Consumo:
    """Quanto de um Servico foi usado em uma reserva. Guarda o preço do momento."""

    def __init__(self, servico, quantidade, preco_unitario=None):
        if int(quantidade) <= 0:
            raise RegraNegocioErro("A quantidade deve ser maior que zero.")
        self.servico = servico
        self.quantidade = int(quantidade)
        # Preço "congelado": se o catálogo mudar depois, a conta não muda.
        self.preco_unitario = servico.preco if preco_unitario is None else dinheiro(preco_unitario)

    @property
    def subtotal(self):
        """CÁLCULO: quantidade x preço."""
        return self.quantidade * self.preco_unitario


class Reserva:
    """O centro do sistema: liga um Hospede a um Quarto e guarda os Consumos."""

    def __init__(self, id, hospede, quarto, entrada, saida, pessoas,
                 diaria_contratada=None, status=CONFIRMADA):
        if saida <= entrada:
            raise RegraNegocioErro("A data de saída deve ser depois da entrada.")
        if not quarto.comporta(pessoas):
            raise RegraNegocioErro(f"O quarto {quarto.numero} comporta no máximo {quarto.capacidade} pessoa(s).")
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
    def valor_consumos(self):
        return sum((c.subtotal for c in self.consumos), Decimal("0"))

    @property
    def total(self):
        return self.valor_hospedagem + self.valor_consumos

    # ---------------- regras ----------------
    @property
    def ativa(self):
        """Só reservas Confirmadas ou Em hospedagem ocupam o quarto."""
        return self.status in (CONFIRMADA, EM_HOSPEDAGEM)

    def conflita_com(self, entrada, saida):
        """REGRA DE DATAS. Há conflito quando a nova entrada é ANTES da nossa saída
        E a nova saída é DEPOIS da nossa entrada. Quem sai dia 22 libera o quarto para quem entra dia 22."""
        return self.ativa and entrada < self.saida and saida > self.entrada

    def check_in(self):
        if self.status != CONFIRMADA:
            raise RegraNegocioErro("Check-in só é permitido em reserva confirmada.")
        self.status = EM_HOSPEDAGEM

    def lancar_consumo(self, servico, quantidade):
        if self.status != EM_HOSPEDAGEM:
            raise RegraNegocioErro("Consumos só podem ser lançados durante a hospedagem.")
        self.consumos.append(Consumo(servico, quantidade))

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
        linhas = [f"Reserva nº {self.id} - {self.status}",
                  f"Hóspede: {self.hospede.nome}",
                  f"Quarto {self.quarto.numero} - {self.entrada:%d/%m/%Y} a {self.saida:%d/%m/%Y}",
                  "-" * 44,
                  f"Hospedagem: {self.qtd_diarias} diária(s) x {reais(self.diaria_contratada)} = {reais(self.valor_hospedagem)}"]
        for c in self.consumos:
            linhas.append(f"{c.servico.descricao}: {c.quantidade} x {reais(c.preco_unitario)} = {reais(c.subtotal)}")
        linhas += ["-" * 44, f"TOTAL: {reais(self.total)}"]
        return "\n".join(linhas)


class Hotel:
    """Guarda tudo (em dicionários) e aplica as regras que envolvem várias reservas."""

    def __init__(self, arquivo=None):
        self.arquivo = arquivo   # onde os dados são salvos (None = não salva)
        self.hospedes = {}       # id -> Hospede
        self.quartos = {}        # número -> Quarto
        self.servicos = {}       # id -> Servico
        self.reservas = {}       # id -> Reserva

    def _proximo_id(self, colecao):
        return max(colecao, default=0) + 1

    # ---------------- cadastros ----------------
    # Padrão: 1) cria o objeto (o construtor valida)  2) guarda no dicionário  3) salva
    def cadastrar_hospede(self, nome, documento, telefone=""):
        hospede = Hospede(self._proximo_id(self.hospedes), nome, documento, telefone)
        self.hospedes[hospede.id] = hospede
        self.salvar()

    def cadastrar_quarto(self, numero, categoria, capacidade, diaria):
        quarto = Quarto(numero, categoria, capacidade, diaria)
        if quarto.numero in self.quartos:
            raise RegraNegocioErro("Já existe um quarto com esse número.")
        self.quartos[quarto.numero] = quarto
        self.salvar()

    def cadastrar_servico(self, descricao, preco):
        servico = Servico(self._proximo_id(self.servicos), descricao, preco)
        self.servicos[servico.id] = servico
        self.salvar()

    # ---------------- disponibilidade e reservas ----------------
    def quarto_livre(self, quarto, entrada, saida):
        """Pergunta a cada reserva deste quarto se ela conflita com as datas."""
        return not any(r.quarto is quarto and r.conflita_com(entrada, saida) for r in self.reservas.values())

    def quartos_disponiveis(self, entrada, saida, pessoas):
        """Os quartos que comportam o grupo e estão livres no período."""
        if saida <= entrada:
            raise RegraNegocioErro("A data de saída deve ser depois da entrada.")
        return [q for q in self.quartos.values()
                if q.comporta(pessoas) and self.quarto_livre(q, entrada, saida)]

    def reservar(self, hospede_id, numero_quarto, entrada, saida, pessoas):
        quarto = self.quartos[numero_quarto]
        if not self.quarto_livre(quarto, entrada, saida):
            raise RegraNegocioErro(f"O quarto {quarto.numero} já está reservado nesse período.")
        reserva = Reserva(self._proximo_id(self.reservas), self.hospedes[hospede_id], quarto,
                          entrada, saida, pessoas)
        self.reservas[reserva.id] = reserva
        self.salvar()

    # ---------------- arquivo JSON ----------------
    def salvar(self):
        """Transforma os objetos em dicionários simples e grava tudo no arquivo JSON."""
        if not self.arquivo:
            return
        dados = {
            "hospedes": [{"id": h.id, "nome": h.nome, "documento": h.documento, "telefone": h.telefone}
                         for h in self.hospedes.values()],
            "quartos": [{"numero": q.numero, "categoria": q.categoria, "capacidade": q.capacidade,
                         "diaria": str(q.diaria)} for q in self.quartos.values()],
            "servicos": [{"id": s.id, "descricao": s.descricao, "preco": str(s.preco)}
                         for s in self.servicos.values()],
            "reservas": [{"id": r.id, "hospede_id": r.hospede.id, "quarto": r.quarto.numero,
                          "entrada": r.entrada.isoformat(), "saida": r.saida.isoformat(),
                          "pessoas": r.pessoas, "diaria_contratada": str(r.diaria_contratada),
                          "status": r.status,
                          "consumos": [{"servico_id": c.servico.id, "quantidade": c.quantidade,
                                        "preco_unitario": str(c.preco_unitario)} for c in r.consumos]}
                         for r in self.reservas.values()],
        }
        with open(self.arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    @classmethod
    def carregar(cls, arquivo):
        """O caminho de volta: lê o JSON e recria os objetos, na ordem certa
        (primeiro hóspedes, quartos e serviços; depois as reservas, que dependem deles)."""
        hotel = cls(arquivo)
        if not os.path.exists(arquivo):  # primeira vez: cria alguns quartos e serviços de exemplo
            for numero, categoria, capacidade, diaria in [("101", "Standard", 2, "180"), ("102", "Standard", 2, "180"),
                                                         ("201", "Luxo", 3, "280"), ("301", "Família", 5, "350")]:
                hotel.cadastrar_quarto(numero, categoria, capacidade, diaria)
            for descricao, preco in [("Água (frigobar)", "10"), ("Refrigerante (frigobar)", "8"),
                                     ("Lavanderia", "20"), ("Café da manhã no quarto", "35")]:
                hotel.cadastrar_servico(descricao, preco)
            return hotel
        with open(arquivo, encoding="utf-8") as f:
            dados = json.load(f)
        for d in dados["hospedes"]:
            hotel.hospedes[d["id"]] = Hospede(d["id"], d["nome"], d["documento"], d["telefone"])
        for d in dados["quartos"]:
            hotel.quartos[d["numero"]] = Quarto(d["numero"], d["categoria"], d["capacidade"], d["diaria"])
        for d in dados["servicos"]:
            hotel.servicos[d["id"]] = Servico(d["id"], d["descricao"], d["preco"])
        for d in dados["reservas"]:
            reserva = Reserva(d["id"], hotel.hospedes[d["hospede_id"]], hotel.quartos[d["quarto"]],
                              date.fromisoformat(d["entrada"]), date.fromisoformat(d["saida"]),
                              d["pessoas"], d["diaria_contratada"], d["status"])
            for c in d["consumos"]:
                reserva.consumos.append(Consumo(hotel.servicos[c["servico_id"]], c["quantidade"], c["preco_unitario"]))
            hotel.reservas[reserva.id] = reserva
        return hotel
