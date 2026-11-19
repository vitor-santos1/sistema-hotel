"""
TELAS: a interface do sistema (CustomTkinter).

As telas só recebem dados e mostram resultados. Toda regra fica em modelos/ e analise.py.
Para achar uma tela, procure pelo nome do item do menu:

  MENU                       ARQUIVO
  Operação > Painel ........ painel.py
  Operação > Reservas ...... reservas.py
  Operação > Hospedagem .... hospedagem.py
  Cadastros > Hóspedes ..... hospedes.py
  Cadastros > Quartos ...... quartos.py
  Cadastros > Serviços ..... servicos.py
  Relatórios > Análise ..... analise_dados.py

  OUTROS ARQUIVOS
  janela.py ............ a janela principal e o menu lateral (classe Aplicacao)
  pagina.py ............ a classe base de todas as telas (Pagina); tem o executar()
  componentes.py ....... tabela, cartão, formulário, botão, máscara de CPF...
  estilo.py ............ cores e fontes
  configuracao.py ...... onde ficam dados_hotel.json e a pasta fechamentos

COMO UMA TELA FUNCIONA
  botão da tela -> método da tela -> método do Hotel/Reserva (nas regras) -> grava no JSON
"""
