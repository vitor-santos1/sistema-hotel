"""TELA HÓSPEDES (menu: Cadastros > Hóspedes).

ONDE ESTÁ O QUÊ
  Botão 'Cadastrar hóspede' ... PaginaHospedes.cadastrar -> Hotel.cadastrar_hospede
  Botão 'Excluir' ............. PaginaHospedes.excluir    -> Hotel.excluir_hospede
"""

from __future__ import annotations

from modelos import LIMITES, mascara_documento, mascara_telefone

from .componentes import Cartao, Formulario, Tabela, limpar
from .pagina import Pagina


class PaginaHospedes(Pagina):
    """Tela de cadastro e exclusão de hóspedes (usa Hotel.cadastrar_hospede e Hotel.excluir_hospede)."""

    titulo = "Hóspedes"
    subtitulo = "Pessoas responsáveis pelas reservas"

    def __init__(self, master, app):
        super().__init__(master, app)
        form_card = Cartao(self, "Novo hóspede")
        form_card.pack(side="left", fill="y", padx=(0, 12))
        f = Formulario(form_card)
        f.pack(padx=16, pady=(4, 16))
        self.nome = f.campo("Nome completo", "Maria Silva", limite=LIMITES["nome"])
        self.doc = f.campo("CPF ou RG", "000.000.000-00", limite=LIMITES["documento"],
                           formatador=mascara_documento)
        self.tel = f.campo("Telefone (opcional)", "(00) 00000-0000", limite=LIMITES["telefone"],
                           formatador=mascara_telefone)
        f.botao("Cadastrar hóspede", self.cadastrar)

        lista = Cartao(self, "Hóspedes cadastrados")
        lista.pack(side="left", fill="both", expand=True)
        self.botao_excluir(lista, self.excluir)
        self.tabela = Tabela(lista, ("ID", "Nome", "Documento", "Telefone"), (50, 230, 150, 140))
        self.tabela.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def cadastrar(self):
        if self.executar(lambda: self.hotel.cadastrar_hospede(self.nome.get(), self.doc.get(), self.tel.get()),
                         "Hóspede cadastrado."):
            limpar(self.nome, self.doc, self.tel)

    def excluir(self):
        self.excluir_selecionado(self.tabela, lambda k: self.hotel.hospedes[int(k)].nome,
                                 lambda k: self.hotel.excluir_hospede(int(k)))

    def atualizar(self):
        self.tabela.preencher([(h.id, (h.id, h.nome, h.documento_formatado, h.telefone_formatado), None)
                               for h in self.hotel.hospedes.values()])
