"""ESTILO: cores, fontes e textos de data. Nenhuma regra do hotel aqui.

ONDE ESTÁ O QUÊ
  FUNDO, SUPERFICIE, ACENTO... a paleta (cada cor é um par: tema claro, tema escuro)
  COR_SITUACAO ............... cores de Livre / Reservado / Ocupado
  COR_STATUS ................. cor de cada situação da reserva na tabela
  fonte(), escuro(), cor() ... apoio ao visual e ao tema escuro
  data_por_extenso() ......... 'quarta-feira, 18 de novembro de 2026'
"""

from __future__ import annotations

from datetime import date

import customtkinter as ctk

from modelos import StatusReserva


FUNDO = ("#f3f4f6", "#16181d")


SUPERFICIE = ("#ffffff", "#1e2128")


BORDA = ("#dfe3e8", "#2e323b")


TEXTO = ("#1d2939", "#e4e7ec")


TEXTO_SUAVE = ("#667085", "#98a2b3")


REALCE = ("#f2f4f7", "#262a33")            # fundo ao passar o mouse


LISTRA = ("#f9fafb", "#1b1e24")            # linhas alternadas das tabelas


ACENTO = ("#1d5fa3", "#4a86c8")


ACENTO_HOVER = ("#174d85", "#3c74b3")


VERDE = ("#2f7d4f", "#5cbf86")


AMARELO = ("#b54708", "#f2a93b")


VERMELHO = ("#b42318", "#f47b72")


CINZA = ("#667085", "#98a2b3")


MENU = ("#1d2939", "#101318")


MENU_ATIVO = ("#2f3e52", "#232a35")


MENU_TEXTO = "#c9d1db"


COR_SITUACAO = {"Livre": VERDE, "Reservado": AMARELO, "Ocupado": VERMELHO}


COR_STATUS = {StatusReserva.CONFIRMADA: ACENTO, StatusReserva.EM_HOSPEDAGEM: VERDE,
              StatusReserva.CONCLUIDA: CINZA, StatusReserva.CANCELADA: VERMELHO}


DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]


def fonte(tamanho=13, negrito=False):
    return ctk.CTkFont(family="Segoe UI", size=tamanho, weight="bold" if negrito else "normal")


# Funções pequenas de apoio ao visual (tema claro/escuro). Não têm regra do hotel.
def escuro() -> bool:
    return ctk.get_appearance_mode() == "Dark"


def cor(par) -> str:
    """Widgets do Tkinter puro (tabela, gráfico) não aceitam o par claro/escuro: escolhe um."""
    return par if isinstance(par, str) else par[1 if escuro() else 0]


def data_por_extenso(d: date) -> str:
    return f"{DIAS[d.weekday()]}, {d.day} de {MESES[d.month - 1]} de {d.year}"
