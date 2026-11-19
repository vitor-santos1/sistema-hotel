"""CLASSE Hospede: a pessoa responsável pela reserva.

DADOS: id, nome, documento, telefone

ONDE ESTÁ O QUÊ
  __init__ .............. cria o hóspede e valida nome, documento e telefone
  documento_formatado ... CPF/RG com pontos e traço (propriedade)
  telefone_formatado .... telefone com parênteses e traço (propriedade)
  __str__ ............... como o hóspede aparece escrito
  para_dict ............. transforma em dicionário, para gravar no JSON
"""

from __future__ import annotations

from .validacoes import formatar_documento, formatar_telefone, limpar_documento, limpar_telefone, validar_nome


class Hospede:
    """Hóspede responsável pela reserva."""

    # __init__ é o CONSTRUTOR: roda quando criamos um objeto, ex.: Hospede(1, 'Maria', '12345678900').
    # 'self' é o próprio objeto que está sendo criado; self.nome = ... guarda o dado dentro dele.
    # validar=True confere os dados. validar=False é usado só ao carregar o arquivo (não derruba o programa com dados antigos).
    def __init__(self, id: int, nome: str, documento: str, telefone: str = "",
                 validar: bool = True):
        self.id = id
        if validar:
            self.nome = validar_nome(nome)
            self.documento = limpar_documento(documento)
            self.telefone = limpar_telefone(telefone)
        else:  # dados antigos do arquivo: carrega como estão, sem derrubar o programa
            self.nome, self.documento, self.telefone = nome.strip(), documento.strip(), telefone.strip()

    # @property faz o método ser usado como se fosse um dado: hospede.documento_formatado (sem parênteses).
    @property
    def documento_formatado(self) -> str:
        return formatar_documento(self.documento)

    @property
    def telefone_formatado(self) -> str:
        return formatar_telefone(self.telefone)

    # __str__ define como o objeto aparece quando vira texto: print(hospede) ou f"{hospede}".
    def __str__(self):
        return f"{self.nome} ({self.documento_formatado})"

    # para_dict transforma o objeto num dicionário simples, que dá para gravar no arquivo JSON.
    # O caminho de volta (JSON -> objetos) está em Hotel.carregar.
    def para_dict(self):
        return {"id": self.id, "nome": self.nome,
                "documento": self.documento, "telefone": self.telefone}
