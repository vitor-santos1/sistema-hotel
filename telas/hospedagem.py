"""TELA HOSPEDAGEM (menu: Operação > Hospedagem): a estadia do hóspede.

ONDE ESTÁ O QUÊ
  Botão 'Fazer check-in' ...... PaginaHospedagem.check_in -> Reserva.check_in
  Botão 'Lançar' (consumo) .... PaginaHospedagem.lancar   -> Reserva.lancar_consumo
  Botão 'Confirmar checkout' .. PaginaHospedagem.checkout -> Reserva.checkout
  mostrar_conta() ............. mostra a conta (Reserva.extrato) e o total (Reserva.total)
"""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from modelos import StatusReserva, formatar_data, formatar_moeda

from .componentes import Cartao, Formulario, Tabela, botao, limpar, so_numeros
from .estilo import BORDA, FUNDO, TEXTO, TEXTO_SUAVE, fonte
from .pagina import Pagina


class PaginaHospedagem(Pagina):
    """Tela da estadia: check-in, lançamento de consumos, conta (Reserva.extrato) e checkout."""

    titulo = "Hospedagem"
    subtitulo = "Check-in, consumos e fechamento da conta"

    def __init__(self, master, app):
        super().__init__(master, app)
        esquerda = ctk.CTkFrame(self, fg_color="transparent")
        esquerda.pack(side="left", fill="y", padx=(0, 12))

        lista = Cartao(esquerda, "Reservas confirmadas e em hospedagem")
        lista.pack(fill="both", expand=True)
        botao(lista.acoes, "Fazer check-in", self.check_in, "primario", largura=120).pack(side="right")
        self.tabela = Tabela(lista, ("Nº", "Hóspede", "Quarto", "Período", "Situação"),
                             (40, 140, 66, 182, 125), altura=8)
        self.tabela.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self.tabela.tree.bind("<<TreeviewSelect>>", lambda e: self.mostrar_conta())

        consumo = Cartao(esquerda, "Lançar consumo")
        consumo.pack(fill="x", pady=(12, 0))
        linha = ctk.CTkFrame(consumo, fg_color="transparent")
        linha.pack(anchor="w", padx=16, pady=(0, 16))
        f_servico, f_qtd = Formulario(linha, 300), Formulario(linha, 90)
        f_servico.pack(side="left", padx=(0, 12))
        f_qtd.pack(side="left", padx=(0, 12))
        self.servico = f_servico.lista("Serviço")
        self.qtd = f_qtd.campo("Quantidade", "1", limite=3, permitido=so_numeros)
        botao(linha, "Lançar", self.lancar, "secundario", largura=90).pack(side="left", anchor="s")

        # Conta
        recibo = Cartao(self, "Conta da hospedagem")
        recibo.pack(side="left", fill="both", expand=True)
        self.extrato = ctk.CTkTextbox(recibo, font=ctk.CTkFont(family="Consolas", size=12),
                                      fg_color=FUNDO, text_color=TEXTO, corner_radius=6, border_width=1,
                                      border_color=BORDA, wrap="none")
        self.extrato.pack(fill="both", expand=True, padx=16, pady=(12, 0))
        rodape = ctk.CTkFrame(recibo, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=16)
        ctk.CTkLabel(rodape, text="TOTAL A PAGAR", font=fonte(10, True), text_color=TEXTO_SUAVE).pack(anchor="w")
        self.total = ctk.CTkLabel(rodape, text="R$ 0,00", font=fonte(26, True), text_color=TEXTO)
        self.total.pack(anchor="w")
        b = botao(rodape, "Confirmar checkout", self.checkout, "primario")
        b.configure(height=38, font=fonte(13, True))
        b.pack(fill="x", pady=(8, 0))

    def _reserva(self):
        rid = self.tabela.selecionado()
        if not rid:
            messagebox.showinfo("Atenção", "Selecione uma reserva na lista.")
            return None
        return self.hotel.reservas[int(rid)]

    def check_in(self):
        r = self._reserva()
        if r:
            self.executar(lambda: (r.check_in(), self.hotel.salvar()), f"Check-in da reserva nº {r.id} realizado.")

    def lancar(self):
        r = self._reserva()
        if not r:
            return
        if not self.servico.get():
            messagebox.showinfo("Atenção", "Escolha um serviço.")
            return
        servico = self.hotel.servicos[int(self.servico.get().split(" - ")[0])]
        if self.executar(lambda: (r.lancar_consumo(servico, int(self.qtd.get())), self.hotel.salvar()),
                         f"{servico.descricao} lançado na reserva nº {r.id}."):
            limpar(self.qtd)

    def checkout(self):
        r = self._reserva()
        if not r:
            return
        if r.status == StatusReserva.EM_HOSPEDAGEM and not messagebox.askyesno(
                "Checkout", f"Confirmar checkout com total de {formatar_moeda(r.total)}?"):
            return
        self.executar(lambda: (r.checkout(), self.hotel.salvar()),
                      f"Hospedagem concluída. Total pago: {formatar_moeda(r.total)}")

    def mostrar_conta(self):
        rid = self.tabela.selecionado()
        r = self.hotel.reservas[int(rid)] if rid else None
        self.extrato.configure(state="normal")
        self.extrato.delete("1.0", "end")
        self.extrato.insert("1.0", r.extrato() if r else "Selecione uma reserva para ver a conta.")
        self.extrato.configure(state="disabled")
        self.total.configure(text=formatar_moeda(r.total) if r else "R$ 0,00")

    def atualizar(self):
        selecionado = self.tabela.selecionado()
        ativas = sorted((r for r in self.hotel.reservas.values() if r.ativa), key=lambda r: r.entrada)
        self.tabela.preencher([(r.id, (r.id, r.hospede.nome, r.quarto.numero,
                                       f"{formatar_data(r.entrada)} a {formatar_data(r.saida)}",
                                       r.status.value), r.status.name) for r in ativas])
        self.servico.configure(values=[f"{s.id} - {s}" for s in self.hotel.servicos.values()])
        if selecionado and self.tabela.tree.exists(selecionado):
            self.tabela.tree.selection_set(selecionado)
        self.mostrar_conta()
