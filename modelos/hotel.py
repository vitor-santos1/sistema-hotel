"""CLASSE Hotel: guarda todos os objetos e aplica as regras que envolvem várias reservas.

ONDE ESTÁ O QUÊ
  CADASTROS ......... cadastrar_hospede, cadastrar_quarto, cadastrar_servico
  EXCLUSÕES ......... excluir_hospede, excluir_quarto, excluir_servico
  DISPONIBILIDADE ... quarto_livre, quartos_disponiveis, reservar
  CAIXA ............. reservas_caixa_aberto, faturamento_caixa_aberto, fechar_caixa
  PAINEL ............ situacao_quarto, resumo
  ARQUIVO JSON ...... salvar (grava os dados), carregar (lê e recria os objetos)
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import json
import os

from .caixa import FechamentoCaixa
from .consumo import Consumo
from .erros import RegraNegocioErro
from .hospede import Hospede
from .quarto import Quarto
from .reserva import Reserva, StatusReserva
from .servico import Servico


class Hotel:
    """Guarda todos os objetos e aplica as regras que envolvem várias reservas."""

    # O Hotel guarda tudo em DICIONÁRIOS: self.hospedes[3] devolve o hóspede de id 3; self.quartos['101'] devolve o quarto 101.
    # 'arquivo' é o caminho do JSON onde os dados são gravados. Sem arquivo (None), nada é gravado (útil nos testes).
    def __init__(self, nome: str = "Hotel", arquivo: str | None = None):
        self.nome = nome
        self.arquivo = arquivo
        self.hospedes: dict[int, Hospede] = {}
        self.quartos: dict[str, Quarto] = {}
        self.servicos: dict[int, Servico] = {}
        self.reservas: dict[int, Reserva] = {}
        self.fechamentos: list[FechamentoCaixa] = []

    # Descobre o próximo número livre: o maior id existente + 1 (ou 1 se ainda não houver nenhum).
    def _proximo_id(self, colecao: dict) -> int:
        return max(colecao.keys(), default=0) + 1

    # ---------------- cadastros ----------------
    # Padrão de TODOS os cadastros: 1) cria o objeto (o construtor valida)  2) confere duplicidade  3) guarda no dicionário  4) salva no JSON.
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

    # Só exclui se o hóspede não tiver reservas ativas ou concluídas (senão a conta ficaria sem dono).
    # 'is' compara se é o MESMO objeto (não só igual). any(...) é True se pelo menos um item passa no teste.
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
    # Pergunta a CADA reserva deste quarto se ela conflita com as datas. Se alguma conflita, o quarto não está livre.
    # 'not any(...)' lê-se: 'nenhuma conflita'.
    def quarto_livre(self, quarto: Quarto, entrada: date, saida: date) -> bool:
        return not any(r.quarto is quarto and r.conflita_com(entrada, saida)
                       for r in self.reservas.values())

    # Lista só os quartos que comportam o grupo E estão livres no período (uma lista em uma linha com filtro).
    def quartos_disponiveis(self, entrada: date, saida: date, pessoas: int) -> list[Quarto]:
        if saida <= entrada:
            raise RegraNegocioErro("A data de saída deve ser posterior à entrada.")
        return [q for q in self.quartos.values()
                if q.comporta(pessoas) and self.quarto_livre(q, entrada, saida)]

    # O caminho completo de uma reserva: acha o hóspede e o quarto, confere o conflito de datas, cria a Reserva, guarda e salva.
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

    # ---------------- caixa ----------------
    # 'fechadas' é um conjunto (set) com os ids das reservas que já entraram em algum fechamento. O caixa aberto é o resto.
    def reservas_caixa_aberto(self) -> list[Reserva]:
        """Hospedagens concluídas que ainda não entraram em nenhum fechamento."""
        fechadas = {r.id for f in self.fechamentos for r in f.reservas}
        return [r for r in self.reservas.values()
                if r.status == StatusReserva.CONCLUIDA and r.id not in fechadas]

    def faturamento_caixa_aberto(self) -> Decimal:
        return sum((r.total for r in self.reservas_caixa_aberto()), Decimal("0.00"))

    @property
    def ultimo_fechamento(self) -> FechamentoCaixa | None:
        return self.fechamentos[-1] if self.fechamentos else None

    # Fecha o caixa: junta as reservas concluídas ainda não contadas num FechamentoCaixa. Não apaga nada, só registra.
    def fechar_caixa(self, agora: datetime | None = None) -> FechamentoCaixa:
        pendentes = self.reservas_caixa_aberto()
        if not pendentes:
            raise RegraNegocioErro("Não há hospedagens concluídas desde o último fechamento de caixa.")
        fechamento = FechamentoCaixa(len(self.fechamentos) + 1,
                                     agora or datetime.now().replace(microsecond=0), pendentes)
        self.fechamentos.append(fechamento)
        self.salvar()
        return fechamento

    # ---------------- painel ----------------
    # Usado no mapa de quartos do painel (Livre / Reservado / Ocupado).
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

    # Junta os números do painel num dicionário. A tela só lê os resultados.
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
            "faturamento": self.faturamento_caixa_aberto(),  # desde o último fechamento de caixa
        }

    # ---------------- persistência (JSON) ----------------
    # SALVAR: transforma cada objeto em dicionário (para_dict) e grava tudo num arquivo JSON. É chamado a cada alteração.
    def salvar(self):
        if not self.arquivo:
            return
        dados = {
            "nome": self.nome,
            "hospedes": [h.para_dict() for h in self.hospedes.values()],
            "quartos": [q.para_dict() for q in self.quartos.values()],
            "servicos": [s.para_dict() for s in self.servicos.values()],
            "reservas": [r.para_dict() for r in self.reservas.values()],
            "fechamentos": [f.para_dict() for f in self.fechamentos],
        }
        with open(self.arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    # CARREGAR: faz o caminho inverso. Lê o JSON e recria os objetos NA ORDEM CERTA: primeiro hóspedes, quartos e serviços,
    # depois as reservas (que dependem deles) e por fim consumos e fechamentos.
    # 'cls' é a própria classe Hotel (por isso @classmethod: o método não precisa de um Hotel já criado).
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
        for d in dados.get("fechamentos", []):  # arquivos antigos não têm fechamentos
            hotel.fechamentos.append(FechamentoCaixa(
                d["numero"], datetime.fromisoformat(d["data_hora"]),
                [hotel.reservas[i] for i in d["reservas"] if i in hotel.reservas]))
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
