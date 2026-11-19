"""CLASSE BASE DE TODAS AS TELAS: Pagina.

Toda tela (PaginaReservas, PaginaHospedes...) HERDA desta classe: por isso todas têm o mesmo cabeçalho
e o método executar().

ONDE ESTÁ O QUÊ
  executar() ............ A PONTE ENTRE TELA E REGRAS: roda a ação e, se uma regra for violada
                          (RegraNegocioErro), mostra a mensagem em vez de quebrar
  excluir_selecionado() . pede confirmação e chama o método de exclusão do Hotel
  botao_excluir() ....... botão 'Excluir' no cabeçalho do cartão da lista
"""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from modelos import RegraNegocioErro

from .componentes import botao
from .estilo import TEXTO, TEXTO_SUAVE, fonte


# CLASSE BASE de todas as telas. Monta o cabeçalho e guarda o 'hotel'. Cada tela (PaginaReservas, PaginaHospedes...)
# herda daqui, por isso todas têm o método executar() e a mesma aparência.
class Pagina(ctk.CTkFrame):
    """Classe base das páginas: cabeçalho, acesso ao hotel e tratamento de erros."""

    titulo = ""
    subtitulo = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.hotel = app.hotel
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", pady=(0, 14))
        textos = ctk.CTkFrame(cabecalho, fg_color="transparent")
        textos.pack(side="left")
        ctk.CTkLabel(textos, text=self.titulo, font=fonte(20, True), text_color=TEXTO).pack(anchor="w")
        ctk.CTkLabel(textos, text=self.subtitulo, font=fonte(12), text_color=TEXTO_SUAVE).pack(anchor="w")
        self.acoes = ctk.CTkFrame(cabecalho, fg_color="transparent", width=1, height=1)  # botões da página
        self.acoes.pack(side="right", anchor="s")

    def atualizar(self):
        pass

    def botao_excluir(self, cartao, comando, texto="Excluir"):
        """Botão de exclusão no cabeçalho do cartão da lista."""
        botao(cartao.acoes, texto, comando, "perigo", largura=90).pack(side="right")

    def excluir_selecionado(self, tabela, nome, excluir):
        """Pede confirmação e chama o método de exclusão do Hotel (que aplica as regras)."""
        chave = tabela.selecionado()
        if not chave:
            messagebox.showinfo("Atenção", "Selecione um item na tabela.")
            return
        if messagebox.askyesno("Excluir", f"Excluir {nome(chave)}? Essa ação não pode ser desfeita."):
            self.executar(lambda: excluir(chave), "Cadastro excluído.")

    # PONTE ENTRE TELA E REGRAS: roda a ação pedida (ex.: reservar). Se uma regra for violada, o modelos.py lança
    # RegraNegocioErro e o 'except' abaixo mostra a mensagem. Se deu certo, avisa e atualiza a tela.
    def executar(self, acao, sucesso=None):
        """Executa uma operação; se uma regra for violada, mostra o motivo."""
        try:
            resultado = acao()
        except RegraNegocioErro as e:
            messagebox.showwarning("Operação não permitida", str(e))
            return None
        except (ValueError, KeyError) as e:
            messagebox.showwarning("Dados inválidos", f"Verifique os campos informados.\n({e})")
            return None
        except OSError as e:
            messagebox.showwarning("Arquivo", f"Não foi possível ler ou gravar o arquivo.\n({e})")
            return None
        if sucesso:
            self.app.avisar(sucesso)
        self.atualizar()
        return resultado
