"""TELA PAINEL (menu: Operação > Painel).

ONDE ESTÁ O QUÊ
  Botão 'Fechar caixa' ..... PaginaPainel.fechar_caixa -> Hotel.fechar_caixa
  atualizar() .............. números do dia e mapa de quartos (Hotel.resumo e Hotel.situacao_quarto)
  JanelaRelatorio .......... a janela que mostra o relatório do caixa fechado
"""

from __future__ import annotations

from tkinter import messagebox
import os

import customtkinter as ctk

from modelos import formatar_data, formatar_moeda

from .componentes import Cartao, Indicador, Tabela, botao
from .configuracao import PASTA, PASTA_FECHAMENTOS
from .estilo import BORDA, COR_SITUACAO, FUNDO, SUPERFICIE, TEXTO, TEXTO_SUAVE, fonte
from .pagina import Pagina


# Cada tela segue o mesmo molde: 1) __init__ monta o visual  2) métodos dos botões chamam o Hotel  3) atualizar() recarrega os dados.
class PaginaPainel(Pagina):
    """Tela inicial: números do dia, mapa de quartos, hospedagens em andamento e fechamento de caixa."""

    titulo = "Painel"
    subtitulo = "Situação do hotel hoje"

    def __init__(self, master, app):
        super().__init__(master, app)
        botao(self.acoes, "Fechar caixa", self.fechar_caixa, "secundario", largura=120).pack(side="right")

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x")
        self.indicadores = {}
        for i, (chave, rotulo) in enumerate([("hosp", "Em hospedagem"), ("entradas", "Chegadas hoje"),
                                             ("saidas", "Saídas hoje"), ("ocupacao", "Ocupação"),
                                             ("caixa", "Caixa aberto")]):
            card = Indicador(linha, rotulo)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            linha.columnconfigure(i, weight=1, uniform="ind")
            self.indicadores[chave] = card

        self.mapa = Cartao(self, "Quartos")
        self.mapa.pack(fill="x", pady=12)
        legenda = self.mapa.acoes
        for situacao, par in COR_SITUACAO.items():
            ctk.CTkLabel(legenda, text=f"●  {situacao}", font=fonte(11), text_color=par).pack(side="left", padx=(12, 0))
        self.grade = ctk.CTkFrame(self.mapa, fg_color="transparent", height=1)
        self.grade.pack(fill="x", padx=16, pady=12)

        lista = Cartao(self, "Hospedagens em andamento")
        lista.pack(fill="both", expand=True)
        self.tabela = Tabela(lista, ("Reserva", "Hóspede", "Quarto", "Entrada", "Saída", "Conta parcial"),
                             (80, 240, 90, 110, 110, 140), altura=5)
        self.tabela.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    # O botão 'Fechar caixa': pede confirmação e chama hotel.fechar_caixa(). O cálculo todo está em modelos.py.
    def fechar_caixa(self):
        pendentes = self.hotel.reservas_caixa_aberto()
        if not pendentes:
            messagebox.showinfo("Fechar caixa", "Não há hospedagens concluídas desde o último fechamento.")
            return
        total = formatar_moeda(self.hotel.faturamento_caixa_aberto())
        if not messagebox.askyesno("Fechar caixa",
                                   f"Fechar o caixa com {len(pendentes)} hospedagem(ns), total de {total}?\n\n"
                                   "O valor do painel volta a zero. Nada é apagado: o histórico "
                                   "continua na Análise de dados."):
            return
        fechamento = self.executar(self.hotel.fechar_caixa)
        if fechamento:
            caminho = self.executar(lambda: fechamento.salvar_relatorio(PASTA_FECHAMENTOS, self.hotel.nome))
            self.app.avisar(f"Caixa nº {fechamento.numero} fechado: {formatar_moeda(fechamento.total)}")
            JanelaRelatorio(self.app, fechamento.relatorio(self.hotel.nome), caminho)

    def atualizar(self):
        r = self.hotel.resumo()
        total_quartos = len(self.hotel.quartos)
        ocupados = round(r["ocupacao"] * total_quartos / 100)
        ult = self.hotel.ultimo_fechamento
        self.indicadores["hosp"].mostrar(str(len(r["em_hospedagem"])), "reservas com check-in")
        self.indicadores["entradas"].mostrar(str(len(r["entradas_hoje"])), "aguardando check-in")
        self.indicadores["saidas"].mostrar(str(len(r["saidas_hoje"])), "checkouts previstos")
        self.indicadores["ocupacao"].mostrar(f"{r['ocupacao']:.0f}%", f"{ocupados} de {total_quartos} quartos")
        self.indicadores["caixa"].mostrar(
            formatar_moeda(r["faturamento"]),
            f"desde {ult.data_hora.strftime('%d/%m %H:%M')} (nº {ult.numero})" if ult else "nenhum fechamento ainda")

        # Um bloco por quarto, com a situação indicada por um ponto colorido
        for w in self.grade.winfo_children():
            w.destroy()
        for i, quarto in enumerate(self.hotel.quartos.values()):
            situacao = self.hotel.situacao_quarto(quarto)
            q = ctk.CTkFrame(self.grade, fg_color=SUPERFICIE, corner_radius=6, border_width=1,
                             border_color=BORDA, width=138, height=76)
            q.grid(row=i // 7, column=i % 7, padx=(0, 10), pady=4)
            q.pack_propagate(False)
            ctk.CTkLabel(q, text=quarto.numero, font=fonte(15, True), text_color=TEXTO,
                         height=22).pack(anchor="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(q, text=quarto.categoria, font=fonte(11), text_color=TEXTO_SUAVE,
                         height=16).pack(anchor="w", padx=12)
            ctk.CTkLabel(q, text=f"●  {situacao}", font=fonte(11), text_color=COR_SITUACAO[situacao],
                         height=18).pack(anchor="w", padx=12, pady=(2, 0))

        self.tabela.preencher([(res.id, (res.id, res.hospede.nome, res.quarto.numero,
                                         formatar_data(res.entrada), formatar_data(res.saida),
                                         formatar_moeda(res.total)), None)
                               for res in r["em_hospedagem"]])


class JanelaRelatorio(ctk.CTkToplevel):
    """Mostra o relatório do fechamento de caixa no formato de cupom."""

    def __init__(self, app, texto, caminho):
        super().__init__(app, fg_color=SUPERFICIE)
        self.title("Fechamento de caixa")
        self.resizable(False, False)
        caixa = ctk.CTkTextbox(self, width=420, height=330, font=ctk.CTkFont(family="Consolas", size=12),
                               fg_color=FUNDO, text_color=TEXTO, corner_radius=6, border_width=1,
                               border_color=BORDA, wrap="none")
        caixa.pack(padx=16, pady=(16, 8))
        caixa.insert("1.0", texto)
        caixa.configure(state="disabled")
        if caminho:
            ctk.CTkLabel(self, text=f"Salvo em: {os.path.relpath(caminho, PASTA)}", font=fonte(11),
                         text_color=TEXTO_SUAVE).pack(anchor="w", padx=16)
        botao(self, "Fechar", self.destroy, "primario", largura=100).pack(anchor="e", padx=16, pady=(8, 16))
        self.transient(app)
        self.update_idletasks()
        x = app.winfo_rootx() + (app.winfo_width() - self.winfo_reqwidth()) // 2
        y = app.winfo_rooty() + (app.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.after(150, self.lift)
