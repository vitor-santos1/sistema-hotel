"""TELA ANÁLISE DE DADOS (menu: Relatórios > Análise de dados) e o gráfico de barras.

A tela só mostra o que a classe Analise (analise.py) calculou.

ONDE ESTÁ O QUÊ
  Botão 'Abrir JSON...' ..... PaginaAnalise.abrir_arquivo -> Analise.de_arquivo
  Botão 'Exportar CSV' ....... PaginaAnalise.exportar     -> Analise.exportar_csv
  atualizar() ................ preenche os indicadores, os gráficos e as tabelas
  Grafico .................... gráfico de barras desenhado no Canvas
"""

from __future__ import annotations

from tkinter import filedialog, messagebox
import os
import tkinter as tk

import customtkinter as ctk

from analise import Analise
from modelos import RegraNegocioErro, formatar_data, formatar_moeda

from .componentes import Cartao, Indicador, Tabela, botao
from .estilo import ACENTO, BORDA, SUPERFICIE, TEXTO, TEXTO_SUAVE, cor
from .pagina import Pagina


def abreviar(valor) -> str:
    """45210 -> '45,2 mil'"""
    v = float(valor)
    return f"{v / 1000:.1f}".replace(".", ",") + " mil" if v >= 1000 else f"{v:.0f}"


# Gráfico desenhado à mão no Canvas (uma área de desenho): retângulos para as barras e textos para os valores.
class Grafico(tk.Canvas):
    """Gráfico de barras desenhado direto no Canvas do Tkinter (sem bibliotecas extras)."""

    def __init__(self, master, altura=150):
        super().__init__(master, height=altura, highlightthickness=0, bd=0)
        self.itens, self.horizontal = [], False
        self.bind("<Configure>", lambda e: self.desenhar())

    def mostrar(self, itens, horizontal=False):
        """itens: lista de (rótulo, valor)"""
        self.itens, self.horizontal = itens, horizontal
        self.desenhar()

    def desenhar(self):
        self.configure(bg=cor(SUPERFICIE))
        self.delete("all")
        suave, forte, linha, barra = cor(TEXTO_SUAVE), cor(TEXTO), cor(BORDA), cor(ACENTO)
        largura, altura = self.winfo_width(), self.winfo_height()
        if largura < 50:
            return
        if not self.itens:
            self.create_text(largura / 2, altura / 2, text="Sem dados no período", fill=suave,
                             font=("Segoe UI", 10))
            return
        maior = max(float(v) for _, v in self.itens) or 1
        n = len(self.itens)
        letra = ("Segoe UI", 8)
        if not self.horizontal:                                  # colunas
            base, topo = altura - 22, 18
            self.create_line(0, base, largura, base, fill=linha)
            passo = largura / n
            for i, (rotulo, valor) in enumerate(self.itens):
                meio, meia = (i + 0.5) * passo, min(passo * 0.28, 28)  # barra de no máximo 56 px
                x0, x1 = meio - meia, meio + meia
                y0 = base - (base - topo) * float(valor) / maior
                self.create_rectangle(x0, y0, x1, base, fill=barra, outline="")
                self.create_text((x0 + x1) / 2, y0 - 8, text=abreviar(valor), fill=forte, font=letra)
                self.create_text((x0 + x1) / 2, altura - 10, text=rotulo, fill=suave, font=letra)
        else:                                                    # barras deitadas
            esquerda, direita = 40, 64
            self.create_line(esquerda, 0, esquerda, altura, fill=linha)
            passo = altura / n
            for i, (rotulo, valor) in enumerate(self.itens):
                meio, meia = (i + 0.5) * passo, min(passo * 0.28, 11)  # barra de no máximo 22 px
                y0, y1 = meio - meia, meio + meia
                x1 = esquerda + (largura - esquerda - direita) * float(valor) / maior
                self.create_rectangle(esquerda, y0, x1, y1, fill=barra, outline="")
                self.create_text(esquerda - 6, (y0 + y1) / 2, text=rotulo, fill=suave, font=letra, anchor="e")
                self.create_text(x1 + 6, (y0 + y1) / 2, text=abreviar(valor), fill=forte, font=letra, anchor="w")


# Mostra o que a classe Analise (analise.py) calculou. A tela só pega os resultados e desenha cartões, gráficos e tabelas.
class PaginaAnalise(Pagina):
    """Tela de Análise de dados: mostra os indicadores calculados pela classe Analise (analise.py)."""

    titulo = "Análise de dados"
    subtitulo = "Indicadores calculados a partir do arquivo JSON"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.fonte = "hotel"        # "hotel" ou o caminho de um arquivo JSON escolhido
        self.analise = None

        botao(self.acoes, "Exportar CSV", self.exportar, "secundario", largura=110).pack(side="right")
        botao(self.acoes, "Abrir JSON…", self.abrir_arquivo, "secundario", largura=110).pack(side="right", padx=(0, 8))
        # só aparece quando outro arquivo está aberto
        self.botao_voltar = botao(self.acoes, "Voltar aos dados do hotel", self.usar_hotel, "secundario", largura=190)

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x")
        self.indicadores = {}
        for i, (chave, rotulo) in enumerate([("fat", "Faturamento"), ("hosp", "Hospedagens"),
                                             ("ticket", "Ticket médio"), ("ocup", "Taxa de ocupação"),
                                             ("cancel", "Cancelamentos")]):
            card = Indicador(linha, rotulo)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            linha.columnconfigure(i, weight=1, uniform="ind")
            self.indicadores[chave] = card

        graficos = ctk.CTkFrame(self, fg_color="transparent")
        graficos.pack(fill="x", pady=12)
        graficos.columnconfigure(0, weight=3, uniform="g")
        graficos.columnconfigure(1, weight=2, uniform="g")
        c1 = Cartao(graficos, "Faturamento por mês")
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.grafico_mes = Grafico(c1, 150)
        self.grafico_mes.pack(fill="x", padx=16, pady=12)
        c2 = Cartao(graficos, "Faturamento por quarto")
        c2.grid(row=0, column=1, sticky="nsew")
        self.grafico_quarto = Grafico(c2, 150)
        self.grafico_quarto.pack(fill="x", padx=16, pady=12)

        tabelas = ctk.CTkFrame(self, fg_color="transparent")
        tabelas.pack(fill="both", expand=True)
        tabelas.columnconfigure(0, weight=1, uniform="t")
        tabelas.columnconfigure(1, weight=1, uniform="t")
        tabelas.rowconfigure(0, weight=1)
        t1 = Cartao(tabelas, "Serviços mais consumidos")
        t1.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.tabela_servicos = Tabela(t1, ("Serviço", "Qtd", "Valor"), (210, 60, 110), altura=4)
        self.tabela_servicos.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        t2 = Cartao(tabelas, "Hóspedes que mais gastaram")
        t2.grid(row=0, column=1, sticky="nsew")
        self.tabela_hospedes = Tabela(t2, ("Hóspede", "Hospedagens", "Total gasto"), (175, 120, 110), altura=4)
        self.tabela_hospedes.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    # ----- escolha da fonte dos dados -----
    def _trocar_fonte(self, fonte_dados):
        self.fonte = fonte_dados
        self.atualizar()

    def usar_hotel(self):
        self._trocar_fonte("hotel")

    def abrir_arquivo(self):
        caminho = filedialog.askopenfilename(title="Escolha um arquivo de dados do hotel",
                                             filetypes=[("Arquivos JSON", "*.json"), ("Todos", "*.*")])
        if caminho:
            self._trocar_fonte(caminho)

    def exportar(self):
        caminho = filedialog.asksaveasfilename(title="Exportar hospedagens concluídas",
                                               defaultextension=".csv", initialfile="faturamento.csv",
                                               filetypes=[("CSV (abre no Excel)", "*.csv")])
        if caminho:
            n = self.executar(lambda: self.analise.exportar_csv(caminho))
            if n is not None:
                self.app.avisar(f"{n} hospedagens exportadas para {os.path.basename(caminho)}.")

    def _carregar(self) -> Analise:
        if self.fonte == "hotel":
            return Analise(self.hotel, "Dados do hotel")
        return Analise.de_arquivo(self.fonte)

    def atualizar(self):
        try:
            self.analise = self._carregar()
        except RegraNegocioErro as e:
            messagebox.showwarning("Não foi possível abrir", str(e))
            self.fonte = "hotel"
            self.analise = self._carregar()
        if self.fonte == "hotel":
            self.botao_voltar.pack_forget()
        else:
            self.botao_voltar.pack(side="right", padx=(0, 8))
        a = self.analise
        self.app.mostrar_fonte(a.origem)
        periodo = a.periodo()
        texto_periodo = f"{formatar_data(periodo[0])} a {formatar_data(periodo[1])}" if periodo else "sem hospedagens"
        self.indicadores["fat"].mostrar(formatar_moeda(a.faturamento_total()), texto_periodo)
        self.indicadores["hosp"].mostrar(str(len(a.concluidas)), f"{a.duracao_media():.1f} diárias em média")
        self.indicadores["ticket"].mostrar(formatar_moeda(a.ticket_medio()), "por hospedagem concluída")
        self.indicadores["ocup"].mostrar(f"{a.taxa_ocupacao():.0f}%", "diárias vendidas no período")
        self.indicadores["cancel"].mostrar(f"{a.taxa_cancelamento():.0f}%", f"de {a.total_reservas} reservas")
        self.grafico_mes.mostrar(a.faturamento_por_mes())
        self.grafico_quarto.mostrar(a.faturamento_por_quarto(), horizontal=True)
        self.tabela_servicos.preencher([(i, (nome, qtd, formatar_moeda(valor)), None)
                                        for i, (nome, qtd, valor) in enumerate(a.consumo_por_servico())])
        self.tabela_hospedes.preencher([(i, (nome, n, formatar_moeda(total)), None)
                                        for i, (nome, n, total) in enumerate(a.ranking_hospedes(8))])
