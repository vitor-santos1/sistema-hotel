"""JANELA PRINCIPAL: Aplicacao.

Monta o menu lateral, cria UMA página de cada tipo (lista PAGINAS) e mostra uma de cada vez.

ONDE ESTÁ O QUÊ
  PAGINAS ......... a lista do menu (seção, nome, classe da tela)
  mostrar() ....... troca de tela e chama atualizar() dela
  avisar() ........ mensagem na barra de status (rodapé)
  alternar_tema() . tema claro / escuro
"""

from __future__ import annotations

from datetime import date, datetime
import os
import tkinter as tk

import customtkinter as ctk

from modelos import Hotel

from .analise_dados import PaginaAnalise
from .componentes import estilizar_tabelas
from .estilo import ACENTO, BORDA, FUNDO, MENU, MENU_ATIVO, MENU_TEXTO, SUPERFICIE, TEXTO_SUAVE, VERDE, data_por_extenso, fonte
from .hospedagem import PaginaHospedagem
from .hospedes import PaginaHospedes
from .painel import PaginaPainel
from .quartos import PaginaQuartos
from .reservas import PaginaReservas
from .servicos import PaginaServicos


# A JANELA PRINCIPAL. Monta o menu lateral, cria UMA página de cada tipo (lista PAGINAS) e mostra uma de cada vez.
class Aplicacao(ctk.CTk):
    """Janela principal: monta o menu lateral, cria uma página de cada tipo e troca entre elas."""

    # (seção do menu, nome, classe da página)
    PAGINAS = [("Operação", "Painel", PaginaPainel),
               ("Operação", "Reservas", PaginaReservas),
               ("Operação", "Hospedagem", PaginaHospedagem),
               ("Cadastros", "Hóspedes", PaginaHospedes),
               ("Cadastros", "Quartos", PaginaQuartos),
               ("Cadastros", "Serviços", PaginaServicos),
               ("Relatórios", "Análise de dados", PaginaAnalise)]

    def __init__(self, hotel: Hotel):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        super().__init__(fg_color=FUNDO)
        self.hotel = hotel
        self.title(f"{hotel.nome} - Recepção")
        self.geometry("1280x780")
        self.minsize(1100, 680)
        self.after(0, self._maximizar)
        estilizar_tabelas()

        # ----- menu lateral -----
        menu = ctk.CTkFrame(self, fg_color=MENU, corner_radius=0, width=220)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)
        marca = ctk.CTkFrame(menu, fg_color="transparent")
        marca.pack(fill="x", padx=18, pady=(22, 18))
        iniciais = "".join(p[0] for p in hotel.nome.split()[:2]).upper() or "H"
        ctk.CTkLabel(marca, text=iniciais, width=34, height=34, corner_radius=6, fg_color=ACENTO,
                     text_color="#ffffff", font=fonte(13, True)).pack(side="left")
        nomes = ctk.CTkFrame(marca, fg_color="transparent")
        nomes.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(nomes, text=hotel.nome, font=fonte(13, True), text_color="#ffffff").pack(anchor="w")
        ctk.CTkLabel(nomes, text="Recepção", font=fonte(11), text_color="#8b96a5").pack(anchor="w")

        self.botoes = []
        secao_atual = None
        for i, (secao, texto, _) in enumerate(self.PAGINAS):
            if secao != secao_atual:
                ctk.CTkLabel(menu, text=secao.upper(), font=fonte(10, True), text_color="#7d8896").pack(
                    anchor="w", padx=22, pady=(14, 4))
                secao_atual = secao
            b = ctk.CTkButton(menu, text=texto, anchor="w", height=34, corner_radius=6,
                              font=fonte(13), fg_color="transparent", hover_color=MENU_ATIVO,
                              text_color=MENU_TEXTO, command=lambda i=i: self.mostrar(i))
            b.pack(fill="x", padx=12, pady=1)
            self.botoes.append(b)

        self.tema = ctk.CTkSwitch(menu, text="Tema escuro", text_color=MENU_TEXTO, font=fonte(12),
                                  command=self.alternar_tema, progress_color=ACENTO)
        self.tema.pack(side="bottom", anchor="w", padx=22, pady=18)

        # ----- barra de status (rodapé) -----
        status = ctk.CTkFrame(self, fg_color=SUPERFICIE, corner_radius=0, height=30)
        status.pack(side="bottom", fill="x")
        status.pack_propagate(False)
        ctk.CTkFrame(status, height=1, fg_color=BORDA).pack(side="top", fill="x")
        self.mensagem = ctk.CTkLabel(status, text="Pronto", font=fonte(11), text_color=TEXTO_SUAVE)
        self.mensagem.pack(side="left", padx=16)
        self.info = ctk.CTkLabel(status, text="", font=fonte(11), text_color=TEXTO_SUAVE)
        self.info.pack(side="right", padx=16)

        # ----- área das páginas -----
        area = ctk.CTkFrame(self, fg_color="transparent")
        area.pack(side="left", fill="both", expand=True, padx=24, pady=(20, 14))
        self.paginas = []
        for _, _, classe in self.PAGINAS:
            pagina = classe(area, self)
            pagina.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.paginas.append(pagina)

        self._aviso_id = None
        self.indice_atual = 0
        self.mostrar(0)

    def _maximizar(self):
        try:
            self.state("zoomed")  # abre maximizada no Windows
        except tk.TclError:
            pass  # em outros sistemas mantém o tamanho padrão

    # Troca de tela: marca o item do menu, pede à página para atualizar() seus dados e a traz para a frente (tkraise).
    def mostrar(self, indice):
        """Traz a página escolhida para a frente e atualiza seus dados."""
        for i, b in enumerate(self.botoes):
            ativo = i == indice
            b.configure(fg_color=MENU_ATIVO if ativo else "transparent",
                        text_color="#ffffff" if ativo else MENU_TEXTO,
                        font=fonte(13, ativo))
        self.indice_atual = indice
        self.mostrar_fonte(os.path.basename(self.hotel.arquivo) if self.hotel.arquivo else "dados em memória")
        pagina = self.paginas[indice]
        pagina.atualizar()
        pagina.tkraise()

    def mostrar_fonte(self, nome):
        self.info.configure(text=f"{nome}   ·   {data_por_extenso(date.today())}")

    def avisar(self, texto):
        """Mostra o resultado da última operação na barra de status."""
        hora = datetime.now().strftime("%H:%M")
        self.mensagem.configure(text=f"●  {texto}   ({hora})", text_color=VERDE)
        if self._aviso_id:
            self.after_cancel(self._aviso_id)
        self._aviso_id = self.after(8000, lambda: self.mensagem.configure(text="Pronto", text_color=TEXTO_SUAVE))

    def alternar_tema(self):
        ctk.set_appearance_mode("dark" if self.tema.get() else "light")
        estilizar_tabelas()
        self.paginas[self.indice_atual].atualizar()  # redesenha os gráficos com as cores do tema
