"""
Modelos (classes) do Sistema de Hotel.

Paradigma: Orientação a Objetos.
- Associação: Reserva referencia um Hospede e um Quarto.
- Composição: Reserva contém seus objetos Consumo (eles não existem sem ela).
- Cálculos dentro das classes: Consumo.subtotal, Reserva.qtd_diarias,
  Reserva.valor_hospedagem, Reserva.valor_consumos e Reserva.total.
- Hotel é a classe que gerencia tudo (cadastros, disponibilidade, arquivo JSON).
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

class RegraNegocioErro(Exception):
    """Erro lançado quando uma regra do hotel é violada."""


def dinheiro(valor) -> Decimal:
    """Converte texto/número para Decimal com 2 casas (nunca float para dinheiro)."""
    try:
        texto = str(valor).strip().replace("R$", "").replace(" ", "")
        if "," in texto:  # formato brasileiro: 1.234,56
            texto = texto.replace(".", "").replace(",", ".")
        d = Decimal(texto)
    except (InvalidOperation, ValueError):
        raise RegraNegocioErro(f"Valor monetário inválido: {valor!r}")
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def formatar_moeda(valor: Decimal) -> str:
    """Decimal('1234.5') -> 'R$ 1.234,50'"""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def ler_data(texto: str) -> date:
    """Lê uma data no formato dd/mm/aaaa."""
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        raise RegraNegocioErro(f"Data inválida: {texto!r} (use dd/mm/aaaa)")


def formatar_data(d: date) -> str:
    return d.strftime("%d/%m/%Y")


# ---------------------------------------------------------------------------
# Limites de tamanho e validações de texto (as telas usam os mesmos limites)
# ---------------------------------------------------------------------------

LIMITES = {"nome": 60, "documento": 14, "telefone": 15,
           "numero_quarto": 6, "categoria": 20, "capacidade": 10, "descricao": 40}


def validar_nome(nome: str) -> str:
    """Nome com 3 a 60 caracteres, só letras (aceita espaço, apóstrofo, hífen e ponto)."""
    nome = " ".join(str(nome).split())  # tira espaços repetidos
    if not nome:
        raise RegraNegocioErro("O nome do hóspede é obrigatório.")
    if len(nome) < 3:
        raise RegraNegocioErro("O nome deve ter pelo menos 3 caracteres.")
    if len(nome) > LIMITES["nome"]:
        raise RegraNegocioErro(f"O nome deve ter no máximo {LIMITES['nome']} caracteres.")
    if not all(c.isalpha() or c in " '-." for c in nome):
        raise RegraNegocioErro("O nome deve conter apenas letras.")
    return nome


def limpar_documento(documento: str) -> str:
    """CPF tem 11 dígitos; RG tem de 7 a 9 (pode terminar em X). Guarda só os caracteres úteis."""
    limpo = "".join(c for c in str(documento).upper() if c.isalnum())
    if not limpo:
        raise RegraNegocioErro("O documento do hóspede é obrigatório.")
    so_numeros = limpo.isdigit() or (limpo[:-1].isdigit() and limpo.endswith("X"))
    if not so_numeros:
        raise RegraNegocioErro("O documento deve ter apenas números (o RG pode terminar em X).")
    if len(limpo) not in (7, 8, 9, 11):
        raise RegraNegocioErro("Documento inválido: o CPF tem 11 dígitos e o RG de 7 a 9.")
    return limpo


def formatar_documento(documento: str) -> str:
    """12345678900 -> 123.456.789-00 (CPF);  123456789 -> 12.345.678-9 (RG de 9)."""
    d = documento
    if len(d) == 11 and d.isdigit():
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    if len(d) == 9:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}-{d[8]}"
    return d


def limpar_telefone(telefone: str) -> str:
    """Opcional. Se informado, precisa de DDD + número (10 ou 11 dígitos)."""
    digitos = "".join(c for c in str(telefone) if c.isdigit())
    if not digitos:
        return ""
    if len(digitos) not in (10, 11):
        raise RegraNegocioErro("Telefone inválido: informe o DDD e o número (10 ou 11 dígitos).")
    return digitos


def formatar_telefone(telefone: str) -> str:
    """11999990000 -> (11) 99999-0000"""
    if len(telefone) == 11:
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
    if len(telefone) == 10:
        return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
    return telefone


def validar_tamanho(texto: str, campo: str, rotulo: str, minimo: int = 1) -> str:
    texto = " ".join(str(texto).split())
    if len(texto) < minimo:
        raise RegraNegocioErro(f"{rotulo} é obrigatório(a)." if minimo == 1
                               else f"{rotulo} deve ter pelo menos {minimo} caracteres.")
    if len(texto) > LIMITES[campo]:
        raise RegraNegocioErro(f"{rotulo} deve ter no máximo {LIMITES[campo]} caracteres.")
    return texto


# ---------------------------------------------------------------------------
# Classes do domínio
# ---------------------------------------------------------------------------

class Hospede:
    """Hóspede responsável pela reserva."""

    def __init__(self, id: int, nome: str, documento: str, telefone: str = "",
                 validar: bool = True):
        self.id = id
        if validar:
            self.nome = validar_nome(nome)
            self.documento = limpar_documento(documento)
            self.telefone = limpar_telefone(telefone)
        else:  # dados antigos do arquivo: carrega como estão, sem derrubar o programa
            self.nome, self.documento, self.telefone = nome.strip(), documento.strip(), telefone.strip()

    @property
    def documento_formatado(self) -> str:
        return formatar_documento(self.documento)

    @property
    def telefone_formatado(self) -> str:
        return formatar_telefone(self.telefone)

    def __str__(self):
        return f"{self.nome} ({self.documento_formatado})"

    def para_dict(self):
        return {"id": self.id, "nome": self.nome,
                "documento": self.documento, "telefone": self.telefone}


class Quarto:
    """Quarto físico do hotel, com capacidade e diária atual."""

    def __init__(self, numero: str, categoria: str, capacidade: int, diaria,
                 validar: bool = True):
        if not str(numero).strip():
            raise RegraNegocioErro("O número do quarto é obrigatório.")
        if int(capacidade) <= 0:
            raise RegraNegocioErro("A capacidade deve ser maior que zero.")
        if validar:
            numero = validar_tamanho(numero, "numero_quarto", "O número do quarto")
            categoria = validar_tamanho(categoria, "categoria", "A categoria") if str(categoria).strip() else "Standard"
            if int(capacidade) > LIMITES["capacidade"]:
                raise RegraNegocioErro(f"A capacidade máxima é {LIMITES['capacidade']} pessoas.")
        self.numero = str(numero).strip()
        self.categoria = categoria.strip() or "Standard"
        self.capacidade = int(capacidade)
        self.diaria = diaria  # usa o setter abaixo (validação)

    @property
    def diaria(self) -> Decimal:
        return self._diaria

    @diaria.setter
    def diaria(self, valor):
        valor = dinheiro(valor)
        if valor <= 0:
            raise RegraNegocioErro("A diária deve ser maior que zero.")
        self._diaria = valor

    def comporta(self, pessoas: int) -> bool:
        return 0 < pessoas <= self.capacidade

    def __str__(self):
        return f"Quarto {self.numero} - {self.categoria}"

    def para_dict(self):
        return {"numero": self.numero, "categoria": self.categoria,
                "capacidade": self.capacidade, "diaria": str(self.diaria)}


class Servico:
    """Item do catálogo de extras (frigobar, lavanderia...)."""

    def __init__(self, id: int, descricao: str, preco, validar: bool = True):
        if validar:
            descricao = validar_tamanho(descricao, "descricao", "A descrição do serviço", minimo=2)
        if not descricao.strip():
            raise RegraNegocioErro("A descrição do serviço é obrigatória.")
        preco = dinheiro(preco)
        if preco < 0:
            raise RegraNegocioErro("O preço não pode ser negativo.")
        self.id = id
        self.descricao = descricao.strip()
        self.preco = preco

    def __str__(self):
        return f"{self.descricao} - {formatar_moeda(self.preco)}"

    def para_dict(self):
        return {"id": self.id, "descricao": self.descricao, "preco": str(self.preco)}


class Consumo:
    """Consumo lançado em uma reserva. Guarda o preço contratado no momento."""

    def __init__(self, servico: Servico, quantidade: int, preco_unitario=None):
        if int(quantidade) <= 0:
            raise RegraNegocioErro("A quantidade deve ser positiva.")
        self.servico = servico
        self.quantidade = int(quantidade)
        # Preço "congelado": se o catálogo mudar depois, a conta não muda.
        self.preco_unitario = dinheiro(servico.preco if preco_unitario is None
                                       else preco_unitario)

    @property
    def subtotal(self) -> Decimal:
        return self.quantidade * self.preco_unitario

    def para_dict(self):
        return {"servico_id": self.servico.id, "quantidade": self.quantidade,
                "preco_unitario": str(self.preco_unitario)}


class StatusReserva(Enum):
    CONFIRMADA = "Confirmada"
    EM_HOSPEDAGEM = "Em hospedagem"
    CONCLUIDA = "Concluída"
    CANCELADA = "Cancelada"


class Reserva:
    """Centro do sistema: liga Hospede + Quarto e reúne os Consumos."""

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
        self.diaria_contratada = dinheiro(quarto.diaria if diaria_contratada is None
                                          else diaria_contratada)
        self.status = status
        self.consumos: list[Consumo] = []   # composição

    # ---------------- cálculos ----------------
    @property
    def qtd_diarias(self) -> int:
        return (self.saida - self.entrada).days

    @property
    def valor_hospedagem(self) -> Decimal:
        return self.qtd_diarias * self.diaria_contratada

    @property
    def valor_consumos(self) -> Decimal:
        return sum((c.subtotal for c in self.consumos), Decimal("0.00"))

    @property
    def total(self) -> Decimal:
        return self.valor_hospedagem + self.valor_consumos

    # ---------------- regras ----------------
    @property
    def ativa(self) -> bool:
        """Reservas canceladas ou concluídas não bloqueiam o quarto."""
        return self.status in (StatusReserva.CONFIRMADA, StatusReserva.EM_HOSPEDAGEM)

    def conflita_com(self, entrada: date, saida: date) -> bool:
        """Há conflito se: nova entrada < saída existente E nova saída > entrada existente.
        A saída é exclusiva: quem sai dia 22 libera o quarto para quem entra dia 22."""
        return self.ativa and entrada < self.saida and saida > self.entrada

    def check_in(self):
        if self.status != StatusReserva.CONFIRMADA:
            raise RegraNegocioErro("Check-in só é permitido em reserva confirmada.")
        self.status = StatusReserva.EM_HOSPEDAGEM

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


# ---------------------------------------------------------------------------
# Classe gerenciadora
# ---------------------------------------------------------------------------

class Hotel:
    """Guarda todos os objetos e aplica as regras que envolvem várias reservas."""

    def __init__(self, nome: str = "Hotel", arquivo: str | None = None):
        self.nome = nome
        self.arquivo = arquivo
        self.hospedes: dict[int, Hospede] = {}
        self.quartos: dict[str, Quarto] = {}
        self.servicos: dict[int, Servico] = {}
        self.reservas: dict[int, Reserva] = {}

    def _proximo_id(self, colecao: dict) -> int:
        return max(colecao.keys(), default=0) + 1

    # ---------------- cadastros ----------------
    def cadastrar_hospede(self, nome, documento, telefone="") -> Hospede:
        h = Hospede(self._proximo_id(self.hospedes), nome, documento, telefone)  # valida
        if any(outro.documento == h.documento for outro in self.hospedes.values()):
            raise RegraNegocioErro("Já existe hóspede com esse documento.")
        self.hospedes[h.id] = h
        self.salvar()
        return h

    def cadastrar_quarto(self, numero, categoria, capacidade, diaria) -> Quarto:
        q = Quarto(numero, categoria, capacidade, diaria)  # valida
        if q.numero in self.quartos:
            raise RegraNegocioErro("Já existe quarto com esse número.")
        self.quartos[q.numero] = q
        self.salvar()
        return q

    def cadastrar_servico(self, descricao, preco) -> Servico:
        s = Servico(self._proximo_id(self.servicos), descricao, preco)
        self.servicos[s.id] = s
        self.salvar()
        return s

    # ---------------- exclusões ----------------
    # Regra: não se exclui um cadastro que tem reserva ativa ou histórico de hospedagem,
    # senão a conta de uma reserva ficaria sem hóspede/quarto/serviço (integridade dos dados).
    # Reservas CANCELADAS não têm valor financeiro, então são apagadas junto.
    def _remover_canceladas(self, reservas: list[Reserva]):
        for r in reservas:
            del self.reservas[r.id]

    def excluir_hospede(self, hospede_id: int) -> Hospede:
        h = self.hospedes.get(hospede_id)
        if h is None:
            raise RegraNegocioErro("Hóspede não encontrado.")
        suas = [r for r in self.reservas.values() if r.hospede is h]
        if any(r.status != StatusReserva.CANCELADA for r in suas):
            raise RegraNegocioErro(f"{h.nome} possui reservas (ativas ou concluídas) e não pode ser excluído(a). "
                                   "Cancele as reservas confirmadas antes.")
        self._remover_canceladas(suas)
        del self.hospedes[hospede_id]
        self.salvar()
        return h

    def excluir_quarto(self, numero: str) -> Quarto:
        q = self.quartos.get(numero)
        if q is None:
            raise RegraNegocioErro("Quarto não encontrado.")
        suas = [r for r in self.reservas.values() if r.quarto is q]
        if any(r.status != StatusReserva.CANCELADA for r in suas):
            raise RegraNegocioErro(f"O quarto {q.numero} possui reservas (ativas ou concluídas) e não pode ser "
                                   "excluído. Cancele as reservas confirmadas antes.")
        self._remover_canceladas(suas)
        del self.quartos[numero]
        self.salvar()
        return q

    def excluir_servico(self, servico_id: int) -> Servico:
        s = self.servicos.get(servico_id)
        if s is None:
            raise RegraNegocioErro("Serviço não encontrado.")
        if any(c.servico is s for r in self.reservas.values() for c in r.consumos):
            raise RegraNegocioErro(f"'{s.descricao}' já foi lançado em hospedagens e não pode ser excluído.")
        del self.servicos[servico_id]
        self.salvar()
        return s

    # ---------------- disponibilidade e reservas ----------------
    def quarto_livre(self, quarto: Quarto, entrada: date, saida: date) -> bool:
        return not any(r.quarto is quarto and r.conflita_com(entrada, saida)
                       for r in self.reservas.values())

    def quartos_disponiveis(self, entrada: date, saida: date, pessoas: int) -> list[Quarto]:
        if saida <= entrada:
            raise RegraNegocioErro("A data de saída deve ser posterior à entrada.")
        return [q for q in self.quartos.values()
                if q.comporta(pessoas) and self.quarto_livre(q, entrada, saida)]

    def reservar(self, hospede_id: int, numero_quarto: str,
                 entrada: date, saida: date, pessoas: int) -> Reserva:
        hospede = self.hospedes[hospede_id]
        quarto = self.quartos[numero_quarto]
        if not self.quarto_livre(quarto, entrada, saida):
            raise RegraNegocioErro(
                f"O quarto {quarto.numero} já está reservado nesse período.")
        r = Reserva(self._proximo_id(self.reservas), hospede, quarto,
                    entrada, saida, pessoas)
        self.reservas[r.id] = r
        self.salvar()
        return r

    # ---------------- painel ----------------
    def situacao_quarto(self, quarto: Quarto, hoje: date | None = None) -> str:
        """'Ocupado' se há hóspede no quarto; 'Reservado' se há reserva para hoje; senão 'Livre'."""
        hoje = hoje or date.today()
        situacao = "Livre"
        for r in self.reservas.values():
            if r.quarto is not quarto:
                continue
            if r.status == StatusReserva.EM_HOSPEDAGEM:
                return "Ocupado"
            if r.status == StatusReserva.CONFIRMADA and r.entrada <= hoje < r.saida:
                situacao = "Reservado"
        return situacao

    def resumo(self, hoje: date | None = None) -> dict:
        hoje = hoje or date.today()
        ativas = [r for r in self.reservas.values() if r.ativa]
        ocupados = {r.quarto.numero for r in ativas if r.entrada <= hoje < r.saida}
        return {
            "em_hospedagem": [r for r in ativas if r.status == StatusReserva.EM_HOSPEDAGEM],
            "entradas_hoje": [r for r in ativas
                              if r.status == StatusReserva.CONFIRMADA and r.entrada == hoje],
            "saidas_hoje": [r for r in ativas
                            if r.status == StatusReserva.EM_HOSPEDAGEM and r.saida == hoje],
            "ocupacao": (len(ocupados) / len(self.quartos) * 100) if self.quartos else 0.0,
            "faturamento": sum((r.total for r in self.reservas.values()
                                if r.status == StatusReserva.CONCLUIDA), Decimal("0.00")),
        }

    # ---------------- persistência (JSON) ----------------
    def salvar(self):
        if not self.arquivo:
            return
        dados = {
            "nome": self.nome,
            "hospedes": [h.para_dict() for h in self.hospedes.values()],
            "quartos": [q.para_dict() for q in self.quartos.values()],
            "servicos": [s.para_dict() for s in self.servicos.values()],
            "reservas": [r.para_dict() for r in self.reservas.values()],
        }
        with open(self.arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    @classmethod
    def carregar(cls, arquivo: str) -> "Hotel":
        hotel = cls(arquivo=arquivo)
        if not os.path.exists(arquivo):
            hotel._dados_iniciais()
            return hotel
        with open(arquivo, encoding="utf-8") as f:
            dados = json.load(f)
        hotel.nome = dados.get("nome", "Hotel")
        for d in dados["hospedes"]:
            hotel.hospedes[d["id"]] = Hospede(d["id"], d["nome"], d["documento"], d["telefone"], validar=False)
        for d in dados["quartos"]:
            hotel.quartos[d["numero"]] = Quarto(d["numero"], d["categoria"],
                                                d["capacidade"], d["diaria"], validar=False)
        for d in dados["servicos"]:
            hotel.servicos[d["id"]] = Servico(d["id"], d["descricao"], d["preco"], validar=False)
        for d in dados["reservas"]:
            r = Reserva(d["id"], hotel.hospedes[d["hospede_id"]],
                        hotel.quartos[d["quarto_numero"]],
                        date.fromisoformat(d["entrada"]), date.fromisoformat(d["saida"]),
                        d["pessoas"], d["diaria_contratada"], StatusReserva[d["status"]])
            for c in d["consumos"]:
                r.consumos.append(Consumo(hotel.servicos[c["servico_id"]],
                                          c["quantidade"], c["preco_unitario"]))
            hotel.reservas[r.id] = r
        return hotel

    def _dados_iniciais(self):
        """Quartos e serviços de exemplo para a primeira execução."""
        self.nome = "Hotel Paradigmas"
        for numero, cat, cap, diaria in [("101", "Standard", 2, "180.00"),
                                         ("102", "Standard", 2, "180.00"),
                                         ("201", "Luxo", 3, "280.00"),
                                         ("301", "Família", 5, "350.00")]:
            self.quartos[numero] = Quarto(numero, cat, cap, diaria)
        for i, (desc, preco) in enumerate([("Água (frigobar)", "10.00"),
                                           ("Refrigerante (frigobar)", "8.00"),
                                           ("Lavanderia", "20.00"),
                                           ("Café da manhã no quarto", "35.00")], start=1):
            self.servicos[i] = Servico(i, desc, preco)
        self.salvar()
