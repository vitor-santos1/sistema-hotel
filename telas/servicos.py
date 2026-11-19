"""TELA SERVIÇOS (menu: Cadastros > Serviços).

ONDE ESTÁ O QUÊ
  Botão 'Cadastrar serviço' ... PaginaServicos.cadastrar -> Hotel.cadastrar_servico
  Botão 'Excluir' ............. PaginaServicos.excluir   -> Hotel.excluir_servico
"""

from __future__ import annotations

from modelos import LIMITES, formatar_moeda

from .componentes import Cartao, Formulario, Tabela, limpar
from .pagina import Pagina


class PaginaServicos(Pagina):
    """Tela do catálogo de serviços extras (frigobar, lavanderia...)."""

    titulo = "Serviços"
    subtitulo = "Catálogo de extras: frigobar, lavanderia, refeições"

    def __init__(self, master, app):
        super().__init__(master, app)
        form_card = Cartao(self, "Novo serviço")
        form_card.pack(side="left", fill="y", padx=(0, 12))
        f = Formulario(form_card)
        f.pack(padx=16, pady=(4, 16))
        self.descricao = f.campo("Descrição", "Água (frigobar)", limite=LIMITES["descricao"])
        self.preco = f.campo("Preço (R$)", "10,00")
        f.botao("Cadastrar serviço", self.cadastrar)

        lista = Cartao(self, "Catálogo")
        lista.pack(side="left", fill="both", expand=True)
        self.botao_excluir(lista, self.excluir)
        self.tabela = Tabela(lista, ("ID", "Descrição", "Preço"), (50, 300, 120))
        self.tabela.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def cadastrar(self):
        if self.executar(lambda: self.hotel.cadastrar_servico(self.descricao.get(), self.preco.get()),
                         "Serviço cadastrado."):
            limpar(self.descricao, self.preco)

    def excluir(self):
        self.excluir_selecionado(self.tabela, lambda k: f"'{self.hotel.servicos[int(k)].descricao}'",
                                 lambda k: self.hotel.excluir_servico(int(k)))

    def atualizar(self):
        self.tabela.preencher([(s.id, (s.id, s.descricao, formatar_moeda(s.preco)), None)
                               for s in self.hotel.servicos.values()])
