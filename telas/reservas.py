"""TELA RESERVAS (menu: Operação > Reservas).

ONDE ESTÁ O QUÊ
  Botão 'Consultar quartos livres' ... PaginaReservas.consultar -> Hotel.quartos_disponiveis
  Botão 'Confirmar reserva' .......... PaginaReservas.reservar  -> Hotel.reservar
  Botão 'Cancelar reserva' ........... PaginaReservas.cancelar  -> Reserva.cancelar
"""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from modelos import RegraNegocioErro, formatar_data, formatar_moeda, ler_data

from .componentes import Cartao, Formulario, Tabela, botao, so_numeros
from .pagina import Pagina


class PaginaReservas(Pagina):
    """Tela de reservas: consulta quartos livres (Hotel.quartos_disponiveis), reserva e cancela."""

    titulo = "Reservas"
    subtitulo = "Consulte a disponibilidade e reserve um quarto"

    def __init__(self, master, app):
        super().__init__(master, app)
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x")

        busca = Cartao(topo, "Pesquisar disponibilidade")
        busca.pack(side="left", fill="y", padx=(0, 12))
        f = Formulario(busca, largura=260)
        f.pack(padx=16, pady=(0, 16))
        self.hospede = f.lista("Hóspede")
        datas = ctk.CTkFrame(f, fg_color="transparent")
        datas.pack(anchor="w")
        f_entrada, f_saida = Formulario(datas, 124), Formulario(datas, 124)
        f_entrada.pack(side="left", padx=(0, 12))
        f_saida.pack(side="left")
        self.entrada = f_entrada.campo("Entrada", "dd/mm/aaaa")
        self.saida = f_saida.campo("Saída", "dd/mm/aaaa")
        self.pessoas = f.campo("Pessoas", "2", largura=124, limite=2, permitido=so_numeros)
        f.botao("Consultar quartos livres", self.consultar)

        escolha = Cartao(topo, "Quartos disponíveis")
        escolha.pack(side="left", fill="both", expand=True)
        botao(escolha.acoes, "Confirmar reserva", self.reservar, "primario", largura=150).pack(side="right")
        self.disponiveis = Tabela(escolha, ("Quarto", "Categoria", "Cap.", "Diária", "Valor estimado"),
                                  (70, 110, 50, 100, 130), altura=5)
        self.disponiveis.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        lista = Cartao(self, "Todas as reservas")
        lista.pack(fill="both", expand=True, pady=(12, 0))
        botao(lista.acoes, "Cancelar reserva", self.cancelar, "perigo", largura=140).pack(side="right")
        self.tabela = Tabela(lista, ("Nº", "Hóspede", "Quarto", "Entrada", "Saída", "Pessoas",
                                     "Diárias", "Diária contratada", "Situação"),
                             (40, 150, 62, 95, 95, 70, 62, 130, 120), altura=6)
        self.tabela.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self._consultou = False

    def _ler_formulario(self):
        return ler_data(self.entrada.get()), ler_data(self.saida.get()), int(self.pessoas.get())

    # Botão 'Consultar quartos livres': lê as datas digitadas e pede ao Hotel quais quartos estão livres.
    def consultar(self):
        def acao():
            entrada, saida, pessoas = self._ler_formulario()
            quartos = self.hotel.quartos_disponiveis(entrada, saida, pessoas)
            noites = (saida - entrada).days
            self.disponiveis.preencher([(q.numero, (q.numero, q.categoria, q.capacidade,
                                                    formatar_moeda(q.diaria),
                                                    formatar_moeda(q.diaria * noites)), None)
                                        for q in quartos])
            self._consultou = True
            if not quartos:
                raise RegraNegocioErro("Nenhum quarto disponível para esse período e quantidade de pessoas.")
        self.executar(acao)

    # Botão 'Confirmar reserva': chama hotel.reservar(...). Se o quarto estiver ocupado nas datas, a regra lança o erro
    # e o executar() mostra 'já está reservado nesse período'.
    def reservar(self):
        numero = self.disponiveis.selecionado()
        if not self.hospede.get() or not numero or not self._consultou:
            messagebox.showinfo("Atenção", "Escolha o hóspede, consulte e selecione um quarto.")
            return
        hospede_id = int(self.hospede.get().split(" - ")[0])

        def acao():
            # Relê as datas: se mudaram, a regra de conflito valida de novo.
            entrada, saida, pessoas = self._ler_formulario()
            r = self.hotel.reservar(hospede_id, numero, entrada, saida, pessoas)
            self.disponiveis.preencher([])
            return r
        r = self.executar(acao)
        if r:
            self.app.avisar(f"Reserva nº {r.id} confirmada: {r.qtd_diarias} diária(s), "
                            f"{formatar_moeda(r.valor_hospedagem)}")

    def cancelar(self):
        rid = self.tabela.selecionado()
        if not rid:
            messagebox.showinfo("Atenção", "Selecione uma reserva.")
            return
        if messagebox.askyesno("Cancelar", f"Cancelar a reserva nº {rid}?"):
            def acao():
                self.hotel.reservas[int(rid)].cancelar()
                self.hotel.salvar()
            self.executar(acao, "Reserva cancelada. O quarto foi liberado.")

    def atualizar(self):
        self.hospede.configure(values=[f"{h.id} - {h.nome}" for h in self.hotel.hospedes.values()])
        self.tabela.preencher([(r.id, (r.id, r.hospede.nome, r.quarto.numero,
                                       formatar_data(r.entrada), formatar_data(r.saida),
                                       r.pessoas, r.qtd_diarias,
                                       formatar_moeda(r.diaria_contratada), r.status.value), r.status.name)
                               for r in sorted(self.hotel.reservas.values(), key=lambda r: r.entrada)])
