"""
SISTEMA DE HOTEL: ponto de entrada. Para abrir o sistema:  python app.py

COMO O PROJETO ESTÁ ORGANIZADO
  app.py ........... este arquivo: carrega os dados e abre a janela
  modelos/ ......... AS REGRAS E OS CÁLCULOS (uma classe por arquivo: reserva.py, quarto.py, hotel.py...)
  telas/ ........... AS TELAS (uma por item do menu: reservas.py, painel.py, hospedagem.py...)
  analise.py ....... a classe Analise (lê o JSON e calcula os indicadores)
  tests/ ........... testes automáticos das regras
  dados_hotel.json . os dados salvos (criado ao usar o sistema)

Cada pasta tem, no __init__.py, um mapa de "o que está em qual arquivo".
Versão reserva sem bibliotecas extras: python app_classico.py
"""

from modelos import Hotel
from telas.configuracao import ARQUIVO_DADOS
from telas.janela import Aplicacao

if __name__ == "__main__":
    # 1) Hotel.carregar lê o dados_hotel.json  2) cria a janela  3) mainloop() espera os cliques
    Aplicacao(Hotel.carregar(ARQUIVO_DADOS)).mainloop()
