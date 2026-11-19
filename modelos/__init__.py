"""
MODELOS: as classes do Sistema de Hotel (Orientação a Objetos).

Cada classe fica no SEU arquivo. Para achar algo, pense em "de quem é isso?":

  ARQUIVO          O QUE TEM
  hospede.py ..... classe Hospede        (a pessoa que se hospeda)
  quarto.py ...... classe Quarto         (capacidade e diária; encapsulamento da diária)
  servico.py ..... classe Servico        (item do catálogo: frigobar, lavanderia...)
  consumo.py ..... classe Consumo        (quanto de um serviço foi usado; subtotal)
  reserva.py ..... StatusReserva e classe Reserva  (o CENTRO: datas, conflito, check-in, checkout, total)
  caixa.py ....... classe FechamentoCaixa (fechar o caixa e o relatório)
  hotel.py ....... classe Hotel          (guarda tudo; reservar; excluir; salvar e carregar o JSON)
  erros.py ....... RegraNegocioErro      (o erro das regras)
  formatos.py .... dinheiro e datas      (Decimal, 'R$ 1.234,50', dd/mm/aaaa)
  validacoes.py .. limites e validações  (nome, CPF/RG, telefone e as máscaras)

RELAÇÕES
  - Associação: Reserva guarda um Hospede e um Quarto.
  - Composição: Reserva guarda a lista de Consumo (e cada Consumo aponta para um Servico).
  - Cálculos dentro das classes: Consumo.subtotal, Reserva.qtd_diarias, valor_hospedagem,
    valor_consumos e total, FechamentoCaixa.total.
  - Hotel é a classe que gerencia tudo (cadastros, disponibilidade, caixa, arquivo JSON).

Este arquivo só reúne os nomes, para o resto do projeto continuar escrevendo:
    from modelos import Hotel, Reserva, RegraNegocioErro
"""

from .caixa import FechamentoCaixa
from .consumo import Consumo
from .erros import RegraNegocioErro
from .formatos import dinheiro, formatar_data, formatar_moeda, ler_data
from .hospede import Hospede
from .hotel import Hotel
from .quarto import Quarto
from .reserva import Reserva, StatusReserva
from .servico import Servico
from .validacoes import (LIMITES, formatar_documento, formatar_telefone, limpar_documento, limpar_telefone,
                         mascara_documento, mascara_telefone, validar_nome, validar_tamanho)

__all__ = ["FechamentoCaixa", "Consumo", "RegraNegocioErro", "dinheiro", "formatar_data", "formatar_moeda",
           "ler_data", "Hospede", "Hotel", "Quarto", "Reserva", "StatusReserva", "Servico", "LIMITES",
           "formatar_documento", "formatar_telefone", "limpar_documento", "limpar_telefone",
           "mascara_documento", "mascara_telefone", "validar_nome", "validar_tamanho"]
