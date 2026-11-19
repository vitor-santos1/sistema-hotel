"""TELA QUARTOS (menu: Cadastros > Quartos).

ONDE ESTÁ O QUÊ
  Botão 'Cadastrar quarto' ............. PaginaQuartos.cadastrar     -> Hotel.cadastrar_quarto
  Botão 'Alterar diária do selecionado'  PaginaQuartos.alterar_diaria -> Quarto.diaria (setter, valida o valor)
  Botão 'Excluir' ...................... PaginaQuartos.excluir       -> Hotel.excluir_quarto
"""

from __future__ import annotations

from tkinter import messagebox

from modelos import LIMITES, formatar_moeda

from .componentes import Cartao, Formulario, Tabela, limpar, so_numeros
from .pagina import Pagina


class PaginaQuartos(Pagina):
    """Tela de cadastro de quartos, alteração da diária e exclusão (usa os métodos de quarto do Hotel)."""

    titulo = "Quartos"
    subtitulo = "Capacidade e diária de cada quarto"

    def __init__(self, master, app):
        super().__init__(master, app)
        form_card = Cartao(self, "Novo quarto")
        form_card.pack(side="left", fill="y", padx=(0, 12))
        f = Formulario(form_card)
        f.pack(padx=16, pady=(4, 16))
        self.numero = f.campo("Número", "101", limite=LIMITES["numero_quarto"])
        self.categoria = f.campo("Categoria", "Standard, Luxo...", limite=LIMITES["categoria"])
        self.capacidade = f.campo("Capacidade (pessoas)", "2", limite=2, permitido=so_numeros)
        self.diaria = f.campo("Diária (R$)", "180,00")
        f.botao("Cadastrar quarto", self.cadastrar)
        f.botao("Alterar diária do selecionado", self.alterar_diaria, "secundario")

        lista = Cartao(self, "Quartos do hotel")
        lista.pack(side="left", fill="both", expand=True)
        self.botao_excluir(lista, self.excluir)
        self.tabela = Tabela(lista, ("Número", "Categoria", "Capacidade", "Diária atual"), (90, 180, 110, 130))
        self.tabela.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def cadastrar(self):
        if self.executar(lambda: self.hotel.cadastrar_quarto(self.numero.get(), self.categoria.get(),
                                                             int(self.capacidade.get()), self.diaria.get()),
                         "Quarto cadastrado."):
            limpar(self.numero, self.categoria, self.capacidade, self.diaria)

    def excluir(self):
        self.excluir_selecionado(self.tabela, lambda k: f"o quarto {k}",
                                 lambda k: self.hotel.excluir_quarto(k))

    def alterar_diaria(self):
        numero = self.tabela.selecionado()
        if not numero:
            messagebox.showinfo("Atenção", "Selecione um quarto na tabela e informe a nova diária.")
            return

        def acao():
            self.hotel.quartos[numero].diaria = self.diaria.get()  # setter valida o valor
            self.hotel.salvar()
        self.executar(acao, "Diária alterada. Reservas já feitas mantêm a diária contratada.")

    def atualizar(self):
        self.tabela.preencher([(q.numero, (q.numero, q.categoria, q.capacidade, formatar_moeda(q.diaria)), None)
                               for q in self.hotel.quartos.values()])
