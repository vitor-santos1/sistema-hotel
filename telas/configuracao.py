"""CONFIGURAÇÃO: onde ficam os arquivos do sistema.

ONDE ESTÁ O QUÊ
  PASTA ............... a pasta do projeto
  ARQUIVO_DADOS ....... dados_hotel.json (onde o Hotel grava os dados)
  PASTA_FECHAMENTOS ... fechamentos/ (relatórios de caixa em .txt)
"""

from __future__ import annotations

import os


PASTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # a pasta do projeto (telas/ fica dentro dela)


ARQUIVO_DADOS = os.path.join(PASTA, "dados_hotel.json")


PASTA_FECHAMENTOS = os.path.join(PASTA, "fechamentos")
