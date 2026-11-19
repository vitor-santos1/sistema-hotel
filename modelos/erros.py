"""ERRO DAS REGRAS DO HOTEL

Quando uma regra é violada (quarto já reservado, diária negativa, check-in numa reserva cancelada...),
o código faz  raise RegraNegocioErro("mensagem")  e a tela mostra a mensagem em vez de quebrar.

ONDE ESTÁ O QUÊ
  RegraNegocioErro ... o tipo de erro usado em todos os outros arquivos desta pasta.
"""

from __future__ import annotations


# Esta classe é um TIPO DE ERRO criado por nós. Quando uma regra do hotel é violada
# (ex.: quarto já reservado), o código faz  raise RegraNegocioErro("mensagem")  e a tela mostra a mensagem.
class RegraNegocioErro(Exception):
    """Erro lançado quando uma regra do hotel é violada."""
