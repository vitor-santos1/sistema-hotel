"""APOIO: LIMITES E VALIDAÇÕES DE TEXTO

ONDE ESTÁ O QUÊ
  LIMITES ................ tamanho máximo de cada campo (as telas usam os mesmos números)
  validar_nome ........... 3 a 60 letras
  limpar_documento ....... CPF (11 dígitos) ou RG (7 a 9); guarda só os números
  mascara_documento ...... formata 123.456.789-00 enquanto a pessoa digita
  limpar_telefone ........ DDD + número (10 ou 11 dígitos), opcional
  mascara_telefone ....... formata (11) 99999-0000 enquanto a pessoa digita
  validar_tamanho ........ confere tamanho mínimo e máximo de um texto
"""

from __future__ import annotations

from .erros import RegraNegocioErro


# Dicionário (dict): guarda pares chave -> valor. Aqui, o tamanho máximo de cada campo.
# As classes e as telas consultam LIMITES['nome'], assim o número 60 fica escrito num lugar só.
LIMITES = {"nome": 60, "documento": 14, "telefone": 15,
           "numero_quarto": 6, "categoria": 20, "capacidade": 10, "descricao": 40}


# Padrão de todas as validações: se algo está errado, 'raise RegraNegocioErro'; se está certo, devolve o valor limpo.
def validar_nome(nome: str) -> str:
    """Nome com 3 a 60 caracteres, só letras (aceita espaço, apóstrofo, hífen e ponto)."""
    nome = " ".join(str(nome).split())  # tira espaços repetidos
    if not nome:
        raise RegraNegocioErro("O nome do hóspede é obrigatório.")
    if len(nome) < 3:
        raise RegraNegocioErro("O nome deve ter pelo menos 3 caracteres.")
    if len(nome) > LIMITES["nome"]:
        raise RegraNegocioErro(f"O nome deve ter no máximo {LIMITES['nome']} caracteres.")
    # all(...) é True só se TODOS os caracteres passam no teste (letra, espaço, apóstrofo, hífen ou ponto).
    if not all(c.isalpha() or c in " '-." for c in nome):
        raise RegraNegocioErro("O nome deve conter apenas letras.")
    return nome


def limpar_documento(documento: str) -> str:
    """CPF tem 11 dígitos; RG tem de 7 a 9 (pode terminar em X). Guarda só os caracteres úteis."""
    # Fica só com letras e números (tira pontos e traço): '123.456.789-00' vira '12345678900'.
    # [c for c in texto if ...] é uma 'lista em uma linha': percorre o texto e guarda só o que passa no teste.
    limpo = "".join(c for c in str(documento).upper() if c.isalnum())
    if not limpo:
        raise RegraNegocioErro("O documento do hóspede é obrigatório.")
    # Só números, ou números com um X no fim (alguns RGs terminam em X).
    so_numeros = limpo.isdigit() or (limpo[:-1].isdigit() and limpo.endswith("X"))
    if not so_numeros:
        raise RegraNegocioErro("O documento deve ter apenas números (o RG pode terminar em X).")
    # CPF tem 11 dígitos; RG tem de 7 a 9.
    if len(limpo) not in (7, 8, 9, 11):
        raise RegraNegocioErro("Documento inválido: o CPF tem 11 dígitos e o RG de 7 a 9.")
    return limpo


def mascara_documento(texto: str) -> str:
    """Formata enquanto digita: 12345678900 -> 123.456.789-00 (o RG pode terminar em X)."""
    # Máscara: monta 123.456.789-00 conforme a pessoa digita, colocando ponto e traço nos lugares certos.
    # corpo[:3] são os 3 primeiros caracteres, corpo[3:6] os 3 seguintes, e assim por diante (fatiamento).
    t = [c for c in str(texto).upper() if c.isalnum()]
    digitos = "".join(c for c in t if c.isdigit())[:11]
    corpo = digitos + ("X" if t and t[-1] == "X" and len(digitos) in (7, 8) else "")
    resultado = corpo[:3]
    if corpo[3:6]:
        resultado += "." + corpo[3:6]
    if corpo[6:9]:
        resultado += "." + corpo[6:9]
    if corpo[9:11]:
        resultado += "-" + corpo[9:11]
    return resultado


formatar_documento = mascara_documento  # mesma regra para digitar e para mostrar na tabela


def limpar_telefone(telefone: str) -> str:
    """Opcional. Se informado, precisa de DDD + número (10 ou 11 dígitos)."""
    digitos = "".join(c for c in str(telefone) if c.isdigit())
    if not digitos:
        return ""
    if len(digitos) not in (10, 11):
        raise RegraNegocioErro("Telefone inválido: informe o DDD e o número (10 ou 11 dígitos).")
    return digitos


def mascara_telefone(texto: str) -> str:
    """Formata enquanto digita: 11999990000 -> (11) 99999-0000  |  1133334444 -> (11) 3333-4444"""
    d = "".join(c for c in str(texto) if c.isdigit())[:11]
    if len(d) <= 2:
        return f"({d}" if d else ""
    corte = 6 if len(d) <= 10 else 7  # fixo: 4+4 dígitos; celular: 5+4
    return f"({d[:2]}) {d[2:corte]}" + (f"-{d[corte:]}" if d[corte:] else "")


formatar_telefone = mascara_telefone


def validar_tamanho(texto: str, campo: str, rotulo: str, minimo: int = 1) -> str:
    texto = " ".join(str(texto).split())
    if len(texto) < minimo:
        raise RegraNegocioErro(f"{rotulo} é obrigatório(a)." if minimo == 1
                               else f"{rotulo} deve ter pelo menos {minimo} caracteres.")
    if len(texto) > LIMITES[campo]:
        raise RegraNegocioErro(f"{rotulo} deve ter no máximo {LIMITES[campo]} caracteres.")
    return texto
