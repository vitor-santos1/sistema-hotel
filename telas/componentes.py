"""PEÇAS REUTILIZÁVEIS DAS TELAS: todas as telas montam o visual com estas classes.

ONDE ESTÁ O QUÊ
  botao() ............... botão no padrão do sistema (primário, secundário ou perigo)
  Tabela ................ tabela com rolagem; preencher() coloca os dados, selecionado() diz a linha clicada
  Cartao ................ quadro com borda e título
  Indicador ............. cartão de número (HERDA de Cartao)
  Formulario ............ rótulos e campos de texto
  limitar_entrada() ..... limite de caracteres e máscara de CPF/telefone enquanto digita
  estilizar_tabelas() ... cores das tabelas (claro/escuro)
"""

from __future__ import annotations

from tkinter import ttk
import tkinter as tk

import customtkinter as ctk

from .estilo import ACENTO, ACENTO_HOVER, BORDA, COR_STATUS, LISTRA, REALCE, SUPERFICIE, TEXTO, TEXTO_SUAVE, VERMELHO, cor, fonte


def botao(master, texto, comando, tipo="primario", largura=None):
    """Botão no padrão do sistema: 'primario' (ação principal), 'secundario' ou 'perigo'."""
    estilos = {
        "primario": dict(fg_color=ACENTO, hover_color=ACENTO_HOVER, text_color="#ffffff", border_width=0),
        "secundario": dict(fg_color=SUPERFICIE, hover_color=REALCE, text_color=TEXTO,
                           border_width=1, border_color=BORDA),
        "perigo": dict(fg_color=SUPERFICIE, hover_color=("#fef3f2", "#3a2326"), text_color=VERMELHO,
                       border_width=1, border_color=("#f4b8b2", "#6b2b29")),
    }
    extra = {"width": largura} if largura else {}
    return ctk.CTkButton(master, text=texto, command=comando, height=32, corner_radius=6,
                         font=fonte(12), **estilos[tipo], **extra)


def estilizar_tabelas():
    """O CustomTkinter não tem tabela; usamos ttk.Treeview com as cores da paleta."""
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure("Hotel.Treeview", background=cor(SUPERFICIE), fieldbackground=cor(SUPERFICIE),
                     foreground=cor(TEXTO), rowheight=30, borderwidth=0, font=("Segoe UI", 10))
    estilo.map("Hotel.Treeview", background=[("selected", cor(ACENTO))],
               foreground=[("selected", "#ffffff")])
    estilo.configure("Hotel.Treeview.Heading", background=cor(SUPERFICIE), foreground=cor(TEXTO_SUAVE),
                     relief="flat", borderwidth=0, font=("Segoe UI", 9, "bold"), padding=(6, 6))
    estilo.map("Hotel.Treeview.Heading", background=[("active", cor(SUPERFICIE))])
    estilo.layout("Hotel.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    for tabela in list(Tabela.todas):
        try:
            tabela.aplicar_cores()
        except tk.TclError:          # tabela de uma janela que já foi fechada
            Tabela.todas.remove(tabela)


# COMPONENTE reutilizável: uma tabela com rolagem. Todas as telas usam esta mesma classe.
# preencher(linhas) coloca os dados; selecionado() devolve a linha que o usuário clicou.
class Tabela(ctk.CTkFrame):
    """Tabela (Treeview) com linhas alternadas e cor da situação da reserva."""

    todas = []  # para recolorir todas ao trocar o tema

    def __init__(self, master, colunas, larguras, altura=8):
        super().__init__(master, fg_color="transparent")
        self.tree = ttk.Treeview(self, columns=colunas, show="headings", height=altura,
                                 selectmode="browse", style="Hotel.Treeview")
        for col, largura in zip(colunas, larguras):
            self.tree.heading(col, text=col.upper(), anchor="w")
            self.tree.column(col, width=largura, anchor="w")
        barra = ctk.CTkScrollbar(self, command=self.tree.yview, width=12)
        self.tree.configure(yscrollcommand=barra.set)
        self.tree.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        Tabela.todas.append(self)
        self.aplicar_cores()

    def aplicar_cores(self):
        self.tree.tag_configure("listra", background=cor(LISTRA))
        for situacao, par in COR_STATUS.items():
            self.tree.tag_configure(situacao.name, foreground=cor(par))

    def preencher(self, linhas):
        """linhas: lista de (id, (valores...), tag)"""
        self.tree.delete(*self.tree.get_children())
        for i, (iid, valores, tag) in enumerate(linhas):
            tags = tuple(t for t in (tag, "listra" if i % 2 else None) if t)
            self.tree.insert("", "end", iid=str(iid), values=valores, tags=tags)

    def selecionado(self):
        sel = self.tree.selection()
        return sel[0] if sel else None


# HERANÇA: (ctk.CTkFrame) significa que Cartao herda tudo de um quadro do customtkinter e acrescenta borda e título.
class Cartao(ctk.CTkFrame):
    """Painel com borda fina, título e uma área de ações à direita do título."""

    def __init__(self, master, titulo=None, **kwargs):
        super().__init__(master, fg_color=SUPERFICIE, corner_radius=8, border_width=1,
                         border_color=BORDA, **kwargs)
        self.acoes = None
        if titulo:
            topo = ctk.CTkFrame(self, fg_color="transparent")
            topo.pack(fill="x", padx=16, pady=(10, 8))
            ctk.CTkLabel(topo, text=titulo, font=fonte(13, True), text_color=TEXTO).pack(side="left")
            self.acoes = ctk.CTkFrame(topo, fg_color="transparent", width=1, height=1)
            self.acoes.pack(side="right")
            ctk.CTkFrame(self, height=1, fg_color=BORDA).pack(fill="x", padx=1)


# HERANÇA: Indicador é um Cartao com rótulo, número grande e detalhe. Aproveita tudo do Cartao.
class Indicador(Cartao):
    """Cartão de número: rótulo, valor em destaque e uma linha de detalhe."""

    def __init__(self, master, rotulo):
        super().__init__(master)
        ctk.CTkLabel(self, text=rotulo.upper(), font=fonte(10, True), text_color=TEXTO_SUAVE).pack(
            anchor="w", padx=16, pady=(12, 0))
        self.valor = ctk.CTkLabel(self, text="-", font=fonte(22, True), text_color=TEXTO)
        self.valor.pack(anchor="w", padx=16)
        self.detalhe = ctk.CTkLabel(self, text="", font=fonte(11), text_color=TEXTO_SUAVE)
        self.detalhe.pack(anchor="w", padx=16, pady=(0, 10))

    def mostrar(self, valor, detalhe=""):
        self.valor.configure(text=valor)
        self.detalhe.configure(text=detalhe)


# Faz o campo de texto parar de aceitar caracteres ao chegar no limite e aplicar a máscara (CPF, telefone).
# As funções de máscara e os limites vêm do modelos.py: a tela só as usa.
def limitar_entrada(entrada, maximo, permitido=None, formatador=None):
    """Impede digitar além do limite e caracteres não permitidos.
    Com 'formatador', também aplica a máscara enquanto a pessoa digita (CPF, telefone)."""
    def corrigir(_evento=None):
        atual = entrada.get()
        if formatador:
            novo = formatador(atual)
        else:
            novo = "".join(c for c in atual if permitido(c)) if permitido else atual
        novo = novo[:maximo]
        if novo != atual:
            entrada.delete(0, "end")
            entrada.insert(0, novo)
    entrada.bind("<KeyRelease>", corrigir, add="+")


def so_numeros(c):
    return c.isdigit()


class Formulario(ctk.CTkFrame):
    """Organiza os campos com o rótulo em cima de cada um."""

    def __init__(self, master, largura=300):
        super().__init__(master, fg_color="transparent")
        self.largura = largura

    def _rotulo(self, texto):
        ctk.CTkLabel(self, text=texto, font=fonte(12), text_color=TEXTO_SUAVE).pack(anchor="w", pady=(8, 2))

    def campo(self, rotulo, exemplo="", largura=None, limite=None, permitido=None, formatador=None):
        self._rotulo(rotulo)
        entrada = ctk.CTkEntry(self, width=largura or self.largura, height=32, corner_radius=6,
                               border_width=1, border_color=BORDA, fg_color=SUPERFICIE,
                               text_color=TEXTO, placeholder_text=exemplo, font=fonte(12))
        entrada.pack(anchor="w")
        if limite:
            limitar_entrada(entrada, limite, permitido, formatador)
        return entrada

    def lista(self, rotulo, largura=None):
        self._rotulo(rotulo)
        caixa = ctk.CTkComboBox(self, width=largura or self.largura, height=32, corner_radius=6,
                                border_width=1, border_color=BORDA, fg_color=SUPERFICIE,
                                button_color=BORDA, button_hover_color=REALCE, text_color=TEXTO,
                                values=[], state="readonly", font=fonte(12), dropdown_font=fonte(12))
        caixa.pack(anchor="w")
        return caixa

    def botao(self, texto, comando, tipo="primario"):
        b = botao(self, texto, comando, tipo, largura=self.largura)
        b.pack(anchor="w", pady=(14, 0))
        return b


def limpar(*entradas):
    for e in entradas:
        e.delete(0, "end")
