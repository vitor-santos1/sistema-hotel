"""
Modelos (classes) do Sistema de Hotel.

Paradigma: Orientação a Objetos.
- Associação: Reserva referencia um Hospede e um Quarto.
- Composição: Reserva contém seus objetos Consumo (eles não existem sem ela).
- Cálculos dentro das classes: Consumo.subtotal, Reserva.qtd_diarias,
  Reserva.valor_hospedagem, Reserva.valor_consumos e Reserva.total.
- Hotel é a classe que gerencia tudo (cadastros, disponibilidade, arquivo JSON).
"""

from __future__ import annotations

# Imports: trazem ferramentas prontas do Python para este arquivo.
#   json = ler e gravar arquivos JSON      os = trabalhar com arquivos e pastas
#   date, datetime = datas e horas         Decimal = números exatos (para dinheiro)
#   Enum = lista fechada de valores
import json
import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

# Esta classe é um TIPO DE ERRO criado por nós. Quando uma regra do hotel é violada
# (ex.: quarto já reservado), o código faz  raise RegraNegocioErro("mensagem")  e a tela mostra a mensagem.
class RegraNegocioErro(Exception):
    """Erro lançado quando uma regra do hotel é violada."""


# Por que Decimal e não float? O float erra contas (0.1 + 0.2 = 0.30000000000000004).
# O Decimal faz conta exata, essencial para dinheiro.
# Esta função aceita '180', '180,50' ou 'R$ 1.234,56' e devolve um Decimal com 2 casas.
def dinheiro(valor) -> Decimal:
    """Converte texto/número para Decimal com 2 casas (nunca float para dinheiro)."""
    try:
        texto = str(valor).strip().replace("R$", "").replace(" ", "")
        if "," in texto:  # formato brasileiro: 1.234,56
            texto = texto.replace(".", "").replace(",", ".")
        d = Decimal(texto)
    except (InvalidOperation, ValueError):
        raise RegraNegocioErro(f"Valor monetário inválido: {valor!r}")
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def formatar_moeda(valor: Decimal) -> str:
    """Decimal('1234.5') -> 'R$ 1.234,50'"""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def ler_data(texto: str) -> date:
    """Lê uma data no formato dd/mm/aaaa."""
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        raise RegraNegocioErro(f"Data inválida: {texto!r} (use dd/mm/aaaa)")


def formatar_data(d: date) -> str:
    return d.strftime("%d/%m/%Y")


# ---------------------------------------------------------------------------
# Limites de tamanho e validações de texto (as telas usam os mesmos limites)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Classes do domínio
# ---------------------------------------------------------------------------

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


class Quarto:
    """Quarto físico do hotel, com capacidade e diária atual."""

    def __init__(self, numero: str, categoria: str, capacidade: int, diaria,
                 validar: bool = True):
        if not str(numero).strip():
            raise RegraNegocioErro("O número do quarto é obrigatório.")
        if int(capacidade) <= 0:
            raise RegraNegocioErro("A capacidade deve ser maior que zero.")
        if validar:
            numero = validar_tamanho(numero, "numero_quarto", "O número do quarto")
            categoria = validar_tamanho(categoria, "categoria", "A categoria") if str(categoria).strip() else "Standard"
            if int(capacidade) > LIMITES["capacidade"]:
                raise RegraNegocioErro(f"A capacidade máxima é {LIMITES['capacidade']} pessoas.")
        self.numero = str(numero).strip()
        self.categoria = categoria.strip() or "Standard"
        self.capacidade = int(capacidade)
        self.diaria = diaria  # usa o setter abaixo (validação)

    # ENCAPSULAMENTO: o valor de verdade fica em self._diaria (o _ avisa 'não mexa direto').
    # Quem usa a classe lê e escreve  quarto.diaria : o getter (@property) devolve o valor e o setter valida antes de guardar.
    @property
    def diaria(self) -> Decimal:
        return self._diaria

    # Setter: roda quando alguém escreve  quarto.diaria = 200.  Se o valor for inválido lança erro e NADA é guardado.
    @diaria.setter
    def diaria(self, valor):
        valor = dinheiro(valor)
        if valor <= 0:
            raise RegraNegocioErro("A diária deve ser maior que zero.")
        self._diaria = valor

    # Devolve True ou False. '0 < pessoas <= capacidade' é uma comparação encadeada: maior que 0 E menor ou igual à capacidade.
    def comporta(self, pessoas: int) -> bool:
        return 0 < pessoas <= self.capacidade

    def __str__(self):
        return f"Quarto {self.numero} - {self.categoria}"

    def para_dict(self):
        return {"numero": self.numero, "categoria": self.categoria,
                "capacidade": self.capacidade, "diaria": str(self.diaria)}


class Servico:
    """Item do catálogo de extras (frigobar, lavanderia...)."""

    # Servico é o item do CATÁLOGO (ex.: Água, R$ 10,00). O preço pode mudar depois; por isso o Consumo guarda uma cópia do preço.
    def __init__(self, id: int, descricao: str, preco, validar: bool = True):
        if validar:
            descricao = validar_tamanho(descricao, "descricao", "A descrição do serviço", minimo=2)
        if not descricao.strip():
            raise RegraNegocioErro("A descrição do serviço é obrigatória.")
        preco = dinheiro(preco)
        if preco < 0:
            raise RegraNegocioErro("O preço não pode ser negativo.")
        self.id = id
        self.descricao = descricao.strip()
        self.preco = preco

    def __str__(self):
        return f"{self.descricao} - {formatar_moeda(self.preco)}"

    def para_dict(self):
        return {"id": self.id, "descricao": self.descricao, "preco": str(self.preco)}


class Consumo:
    """Consumo lançado em uma reserva. Guarda o preço contratado no momento."""

    # Consumo = quanto de um Servico foi usado numa reserva. Guarda uma REFERÊNCIA ao Servico (associação) e a quantidade.
    # preco_unitario=None significa 'se ninguém informar, use o preço atual do catálogo'.
    def __init__(self, servico: Servico, quantidade: int, preco_unitario=None):
        if int(quantidade) <= 0:
            raise RegraNegocioErro("A quantidade deve ser positiva.")
        self.servico = servico
        self.quantidade = int(quantidade)
        # Preço "congelado": se o catálogo mudar depois, a conta não muda.
        self.preco_unitario = dinheiro(servico.preco if preco_unitario is None
                                       else preco_unitario)

    # CÁLCULO dentro da classe: subtotal = quantidade x preço unitário. Usa-se assim: consumo.subtotal
    @property
    def subtotal(self) -> Decimal:
        return self.quantidade * self.preco_unitario

    def para_dict(self):
        return {"servico_id": self.servico.id, "quantidade": self.quantidade,
                "preco_unitario": str(self.preco_unitario)}


class StatusReserva(Enum):
    """Situações possíveis de uma reserva: Confirmada -> Em hospedagem -> Concluída (ou Cancelada)."""

    # Enum = lista FECHADA de valores. Em vez de textos soltos ('confirmada', 'Confirmada'...) que dariam erro de digitação,
    # usamos StatusReserva.CONFIRMADA. O texto bonito fica em .value ('Em hospedagem') e o nome em .name ('EM_HOSPEDAGEM').
    CONFIRMADA = "Confirmada"
    EM_HOSPEDAGEM = "Em hospedagem"
    CONCLUIDA = "Concluída"
    CANCELADA = "Cancelada"


class Reserva:
    """Centro do sistema: liga Hospede + Quarto e reúne os Consumos."""

    # A Reserva é o CENTRO do sistema. Recebe os objetos Hospede e Quarto já prontos e guarda a referência a eles.
    # As 3 verificações abaixo impedem uma reserva inválida: saída antes da entrada, sem pessoas ou acima da capacidade.
    def __init__(self, id: int, hospede: Hospede, quarto: Quarto,
                 entrada: date, saida: date, pessoas: int,
                 diaria_contratada=None, status=StatusReserva.CONFIRMADA):
        if saida <= entrada:
            raise RegraNegocioErro("A data de saída deve ser posterior à entrada.")
        if int(pessoas) <= 0:
            raise RegraNegocioErro("A quantidade de pessoas deve ser positiva.")
        if not quarto.comporta(int(pessoas)):
            raise RegraNegocioErro(
                f"O quarto {quarto.numero} comporta no máximo {quarto.capacidade} pessoa(s).")
        self.id = id
        self.hospede = hospede              # associação
        self.quarto = quarto                # associação
        self.entrada = entrada
        self.saida = saida
        self.pessoas = int(pessoas)
        # PREÇO CONTRATADO: copia a diária do quarto NESTE momento. Se o hotel mudar o preço depois, esta reserva não muda.
        # 'A if condição else B' é um if em uma linha: usa o valor informado, ou a diária atual do quarto se não houver.
        self.diaria_contratada = dinheiro(quarto.diaria if diaria_contratada is None
                                          else diaria_contratada)
        self.status = status
        self.consumos: list[Consumo] = []   # composição

    # ---------------- cálculos ----------------
    # Subtrair duas datas dá um 'timedelta'; .days é o número de dias. Ex.: 22/11 - 19/11 = 3 diárias.
    @property
    def qtd_diarias(self) -> int:
        return (self.saida - self.entrada).days

    @property
    def valor_hospedagem(self) -> Decimal:
        return self.qtd_diarias * self.diaria_contratada

    # sum(... for c in self.consumos) soma o subtotal de cada consumo da lista. O Decimal('0.00') é o ponto de partida da soma.
    @property
    def valor_consumos(self) -> Decimal:
        return sum((c.subtotal for c in self.consumos), Decimal("0.00"))

    # TOTAL DA CONTA = hospedagem + consumos. Exemplo do roteiro: 540 + 60 = R$ 600,00.
    @property
    def total(self) -> Decimal:
        return self.valor_hospedagem + self.valor_consumos

    # ---------------- regras ----------------
    # 'in' confere se o valor está dentro da tupla. Só reservas Confirmadas ou Em hospedagem seguram o quarto.
    @property
    def ativa(self) -> bool:
        """Reservas canceladas ou concluídas não bloqueiam o quarto."""
        return self.status in (StatusReserva.CONFIRMADA, StatusReserva.EM_HOSPEDAGEM)

    # REGRA DE DATAS. Exemplo com uma reserva existente de 19/11 a 22/11:
    #   nova 20/11 a 23/11 -> CONFLITA     (20 < 22 e 23 > 19)
    #   nova 22/11 a 24/11 -> não conflita (22 < 22 é falso)
    #   nova 17/11 a 19/11 -> não conflita (19 > 19 é falso)
    def conflita_com(self, entrada: date, saida: date) -> bool:
        """Há conflito se: nova entrada < saída existente E nova saída > entrada existente.
        A saída é exclusiva: quem sai dia 22 libera o quarto para quem entra dia 22."""
        return self.ativa and entrada < self.saida and saida > self.entrada

    # Cada ação só é permitida numa certa situação (a reserva funciona como uma máquina de situações).
    # Aqui: check-in só se estiver Confirmada. Se não estiver, 'raise' interrompe o método e a tela mostra a mensagem.
    # Se estiver, muda o status para Em hospedagem.
    def check_in(self):
        if self.status != StatusReserva.CONFIRMADA:
            raise RegraNegocioErro("Check-in só é permitido em reserva confirmada.")
        self.status = StatusReserva.EM_HOSPEDAGEM

    # COMPOSIÇÃO: o Consumo é criado aqui dentro e guardado na lista self.consumos desta reserva.
    def lancar_consumo(self, servico: Servico, quantidade: int) -> Consumo:
        if self.status != StatusReserva.EM_HOSPEDAGEM:
            raise RegraNegocioErro("Consumos só podem ser lançados durante a hospedagem.")
        consumo = Consumo(servico, quantidade)
        self.consumos.append(consumo)
        return consumo

    def checkout(self) -> Decimal:
        if self.status != StatusReserva.EM_HOSPEDAGEM:
            raise RegraNegocioErro("Checkout só é permitido durante a hospedagem.")
        self.status = StatusReserva.CONCLUIDA
        return self.total

    def cancelar(self):
        if self.status != StatusReserva.CONFIRMADA:
            raise RegraNegocioErro("Somente reservas confirmadas podem ser canceladas.")
        self.status = StatusReserva.CANCELADA

    # Monta o texto da conta (o recibo que aparece na tela). Cada linha é uma f-string: f'...{valor}...' troca {valor} pelo conteúdo.
    def extrato(self) -> str:
        """Texto da conta para mostrar na tela de fechamento."""
        linhas = [
            f"Reserva nº {self.id}  -  {self.status.value}",
            f"Hóspede: {self.hospede}",
            f"{self.quarto}  |  {self.pessoas} pessoa(s)",
            f"Período: {formatar_data(self.entrada)} a {formatar_data(self.saida)}",
            "-" * 46,
            f"Hospedagem: {self.qtd_diarias} diária(s) x "
            f"{formatar_moeda(self.diaria_contratada)} = {formatar_moeda(self.valor_hospedagem)}",
        ]
        for c in self.consumos:
            linhas.append(f"{c.servico.descricao}: {c.quantidade} x "
                          f"{formatar_moeda(c.preco_unitario)} = {formatar_moeda(c.subtotal)}")
        linhas += ["-" * 46,
                   f"Consumos: {formatar_moeda(self.valor_consumos)}",
                   f"TOTAL:    {formatar_moeda(self.total)}"]
        return "\n".join(linhas)

    def para_dict(self):
        return {"id": self.id, "hospede_id": self.hospede.id,
                "quarto_numero": self.quarto.numero,
                "entrada": self.entrada.isoformat(), "saida": self.saida.isoformat(),
                "pessoas": self.pessoas, "diaria_contratada": str(self.diaria_contratada),
                "status": self.status.name,
                "consumos": [c.para_dict() for c in self.consumos]}


class FechamentoCaixa:
    """Fechamento de caixa: reúne as hospedagens concluídas desde o fechamento anterior.

    O faturamento não é apagado. Ele fica registrado no fechamento, e o painel passa a
    contar do zero a partir dele. O histórico completo continua na Análise de dados.
    """

    LARGURA = 42  # caracteres por linha do relatório (formato de cupom)

    # O fechamento guarda: o número, quando foi feito e QUAIS reservas entraram nele.
    # list(reservas) faz uma cópia da lista, para mudanças futuras não afetarem o fechamento.
    def __init__(self, numero: int, data_hora: datetime, reservas: list[Reserva]):
        self.numero = numero
        self.data_hora = data_hora
        self.reservas = list(reservas)

    # ---------------- cálculos ----------------
    @property
    def quantidade(self) -> int:
        return len(self.reservas)

    @property
    def valor_hospedagem(self) -> Decimal:
        return sum((r.valor_hospedagem for r in self.reservas), Decimal("0.00"))

    @property
    def valor_consumos(self) -> Decimal:
        return sum((r.valor_consumos for r in self.reservas), Decimal("0.00"))

    # Mesma ideia da Reserva: o total do caixa é a soma das hospedagens com os consumos de todas as reservas fechadas.
    @property
    def total(self) -> Decimal:
        return self.valor_hospedagem + self.valor_consumos

    # ---------------- relatório ----------------
    # Monta o relatório no formato de cupom (42 colunas). ljust e center alinham o texto à esquerda e ao centro.
    def relatorio(self, nome_hotel: str = "Hotel") -> str:
        """Texto no formato de cupom, pronto para salvar em .txt ou imprimir."""
        L = self.LARGURA

        def linha(esquerda: str, direita: str) -> str:
            return esquerda[:L - len(direita) - 1].ljust(L - len(direita)) + direita

        texto = ["=" * L, nome_hotel.upper().center(L),
                 f"FECHAMENTO DE CAIXA Nº {self.numero:03d}".center(L),
                 self.data_hora.strftime("%d/%m/%Y %H:%M").center(L), "=" * L,
                 linha("Res. Hóspede", "Total"), "-" * L]
        for r in sorted(self.reservas, key=lambda r: r.id):
            texto.append(linha(f"{r.id:>4} {r.hospede.nome[:22]} ({r.quarto.numero})", formatar_moeda(r.total)))
        texto += ["-" * L,
                  linha("Hospedagens:", str(self.quantidade)),
                  linha("Diárias:", formatar_moeda(self.valor_hospedagem)),
                  linha("Consumos:", formatar_moeda(self.valor_consumos)),
                  linha("TOTAL:", formatar_moeda(self.total)),
                  "=" * L]
        return "\n".join(texto)

    def salvar_relatorio(self, pasta: str, nome_hotel: str = "Hotel") -> str:
        """Grava o relatório em <pasta>/caixa_001.txt e devolve o caminho do arquivo."""
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, f"caixa_{self.numero:03d}.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(self.relatorio(nome_hotel) + "\n")
        return caminho

    def para_dict(self):
        return {"numero": self.numero, "data_hora": self.data_hora.isoformat(),
                "reservas": [r.id for r in self.reservas]}


# ---------------------------------------------------------------------------
# Classe gerenciadora
# ---------------------------------------------------------------------------

class Hotel:
    """Guarda todos os objetos e aplica as regras que envolvem várias reservas."""

    # O Hotel guarda tudo em DICIONÁRIOS: self.hospedes[3] devolve o hóspede de id 3; self.quartos['101'] devolve o quarto 101.
    # 'arquivo' é o caminho do JSON onde os dados são gravados. Sem arquivo (None), nada é gravado (útil nos testes).
    def __init__(self, nome: str = "Hotel", arquivo: str | None = None):
        self.nome = nome
        self.arquivo = arquivo
        self.hospedes: dict[int, Hospede] = {}
        self.quartos: dict[str, Quarto] = {}
        self.servicos: dict[int, Servico] = {}
        self.reservas: dict[int, Reserva] = {}
        self.fechamentos: list[FechamentoCaixa] = []

    # Descobre o próximo número livre: o maior id existente + 1 (ou 1 se ainda não houver nenhum).
    def _proximo_id(self, colecao: dict) -> int:
        return max(colecao.keys(), default=0) + 1

    # ---------------- cadastros ----------------
    # Padrão de TODOS os cadastros: 1) cria o objeto (o construtor valida)  2) confere duplicidade  3) guarda no dicionário  4) salva no JSON.
    def cadastrar_hospede(self, nome, documento, telefone="") -> Hospede:
        h = Hospede(self._proximo_id(self.hospedes), nome, documento, telefone)  # valida
        if any(outro.documento == h.documento for outro in self.hospedes.values()):
            raise RegraNegocioErro("Já existe hóspede com esse documento.")
        self.hospedes[h.id] = h
        self.salvar()
        return h

    def cadastrar_quarto(self, numero, categoria, capacidade, diaria) -> Quarto:
        q = Quarto(numero, categoria, capacidade, diaria)  # valida
        if q.numero in self.quartos:
            raise RegraNegocioErro("Já existe quarto com esse número.")
        self.quartos[q.numero] = q
        self.salvar()
        return q

    def cadastrar_servico(self, descricao, preco) -> Servico:
        s = Servico(self._proximo_id(self.servicos), descricao, preco)
        self.servicos[s.id] = s
        self.salvar()
        return s

    # ---------------- exclusões ----------------
    # Regra: não se exclui um cadastro que tem reserva ativa ou histórico de hospedagem,
    # senão a conta de uma reserva ficaria sem hóspede/quarto/serviço (integridade dos dados).
    # Reservas CANCELADAS não têm valor financeiro, então são apagadas junto.
    def _remover_canceladas(self, reservas: list[Reserva]):
        for r in reservas:
            del self.reservas[r.id]

    # Só exclui se o hóspede não tiver reservas ativas ou concluídas (senão a conta ficaria sem dono).
    # 'is' compara se é o MESMO objeto (não só igual). any(...) é True se pelo menos um item passa no teste.
    def excluir_hospede(self, hospede_id: int) -> Hospede:
        h = self.hospedes.get(hospede_id)
        if h is None:
            raise RegraNegocioErro("Hóspede não encontrado.")
        suas = [r for r in self.reservas.values() if r.hospede is h]
        if any(r.status != StatusReserva.CANCELADA for r in suas):
            raise RegraNegocioErro(f"{h.nome} possui reservas (ativas ou concluídas) e não pode ser excluído(a). "
                                   "Cancele as reservas confirmadas antes.")
        self._remover_canceladas(suas)
        del self.hospedes[hospede_id]
        self.salvar()
        return h

    def excluir_quarto(self, numero: str) -> Quarto:
        q = self.quartos.get(numero)
        if q is None:
            raise RegraNegocioErro("Quarto não encontrado.")
        suas = [r for r in self.reservas.values() if r.quarto is q]
        if any(r.status != StatusReserva.CANCELADA for r in suas):
            raise RegraNegocioErro(f"O quarto {q.numero} possui reservas (ativas ou concluídas) e não pode ser "
                                   "excluído. Cancele as reservas confirmadas antes.")
        self._remover_canceladas(suas)
        del self.quartos[numero]
        self.salvar()
        return q

    def excluir_servico(self, servico_id: int) -> Servico:
        s = self.servicos.get(servico_id)
        if s is None:
            raise RegraNegocioErro("Serviço não encontrado.")
        if any(c.servico is s for r in self.reservas.values() for c in r.consumos):
            raise RegraNegocioErro(f"'{s.descricao}' já foi lançado em hospedagens e não pode ser excluído.")
        del self.servicos[servico_id]
        self.salvar()
        return s

    # ---------------- disponibilidade e reservas ----------------
    # Pergunta a CADA reserva deste quarto se ela conflita com as datas. Se alguma conflita, o quarto não está livre.
    # 'not any(...)' lê-se: 'nenhuma conflita'.
    def quarto_livre(self, quarto: Quarto, entrada: date, saida: date) -> bool:
        return not any(r.quarto is quarto and r.conflita_com(entrada, saida)
                       for r in self.reservas.values())

    # Lista só os quartos que comportam o grupo E estão livres no período (uma lista em uma linha com filtro).
    def quartos_disponiveis(self, entrada: date, saida: date, pessoas: int) -> list[Quarto]:
        if saida <= entrada:
            raise RegraNegocioErro("A data de saída deve ser posterior à entrada.")
        return [q for q in self.quartos.values()
                if q.comporta(pessoas) and self.quarto_livre(q, entrada, saida)]

    # O caminho completo de uma reserva: acha o hóspede e o quarto, confere o conflito de datas, cria a Reserva, guarda e salva.
    def reservar(self, hospede_id: int, numero_quarto: str,
                 entrada: date, saida: date, pessoas: int) -> Reserva:
        hospede = self.hospedes[hospede_id]
        quarto = self.quartos[numero_quarto]
        if not self.quarto_livre(quarto, entrada, saida):
            raise RegraNegocioErro(
                f"O quarto {quarto.numero} já está reservado nesse período.")
        r = Reserva(self._proximo_id(self.reservas), hospede, quarto,
                    entrada, saida, pessoas)
        self.reservas[r.id] = r
        self.salvar()
        return r

    # ---------------- caixa ----------------
    # 'fechadas' é um conjunto (set) com os ids das reservas que já entraram em algum fechamento. O caixa aberto é o resto.
    def reservas_caixa_aberto(self) -> list[Reserva]:
        """Hospedagens concluídas que ainda não entraram em nenhum fechamento."""
        fechadas = {r.id for f in self.fechamentos for r in f.reservas}
        return [r for r in self.reservas.values()
                if r.status == StatusReserva.CONCLUIDA and r.id not in fechadas]

    def faturamento_caixa_aberto(self) -> Decimal:
        return sum((r.total for r in self.reservas_caixa_aberto()), Decimal("0.00"))

    @property
    def ultimo_fechamento(self) -> FechamentoCaixa | None:
        return self.fechamentos[-1] if self.fechamentos else None

    # Fecha o caixa: junta as reservas concluídas ainda não contadas num FechamentoCaixa. Não apaga nada, só registra.
    def fechar_caixa(self, agora: datetime | None = None) -> FechamentoCaixa:
        pendentes = self.reservas_caixa_aberto()
        if not pendentes:
            raise RegraNegocioErro("Não há hospedagens concluídas desde o último fechamento de caixa.")
        fechamento = FechamentoCaixa(len(self.fechamentos) + 1,
                                     agora or datetime.now().replace(microsecond=0), pendentes)
        self.fechamentos.append(fechamento)
        self.salvar()
        return fechamento

    # ---------------- painel ----------------
    # Usado no mapa de quartos do painel (Livre / Reservado / Ocupado).
    def situacao_quarto(self, quarto: Quarto, hoje: date | None = None) -> str:
        """'Ocupado' se há hóspede no quarto; 'Reservado' se há reserva para hoje; senão 'Livre'."""
        hoje = hoje or date.today()
        situacao = "Livre"
        for r in self.reservas.values():
            if r.quarto is not quarto:
                continue
            if r.status == StatusReserva.EM_HOSPEDAGEM:
                return "Ocupado"
            if r.status == StatusReserva.CONFIRMADA and r.entrada <= hoje < r.saida:
                situacao = "Reservado"
        return situacao

    # Junta os números do painel num dicionário. A tela só lê os resultados.
    def resumo(self, hoje: date | None = None) -> dict:
        hoje = hoje or date.today()
        ativas = [r for r in self.reservas.values() if r.ativa]
        ocupados = {r.quarto.numero for r in ativas if r.entrada <= hoje < r.saida}
        return {
            "em_hospedagem": [r for r in ativas if r.status == StatusReserva.EM_HOSPEDAGEM],
            "entradas_hoje": [r for r in ativas
                              if r.status == StatusReserva.CONFIRMADA and r.entrada == hoje],
            "saidas_hoje": [r for r in ativas
                            if r.status == StatusReserva.EM_HOSPEDAGEM and r.saida == hoje],
            "ocupacao": (len(ocupados) / len(self.quartos) * 100) if self.quartos else 0.0,
            "faturamento": self.faturamento_caixa_aberto(),  # desde o último fechamento de caixa
        }

    # ---------------- persistência (JSON) ----------------
    # SALVAR: transforma cada objeto em dicionário (para_dict) e grava tudo num arquivo JSON. É chamado a cada alteração.
    def salvar(self):
        if not self.arquivo:
            return
        dados = {
            "nome": self.nome,
            "hospedes": [h.para_dict() for h in self.hospedes.values()],
            "quartos": [q.para_dict() for q in self.quartos.values()],
            "servicos": [s.para_dict() for s in self.servicos.values()],
            "reservas": [r.para_dict() for r in self.reservas.values()],
            "fechamentos": [f.para_dict() for f in self.fechamentos],
        }
        with open(self.arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    # CARREGAR: faz o caminho inverso. Lê o JSON e recria os objetos NA ORDEM CERTA: primeiro hóspedes, quartos e serviços,
    # depois as reservas (que dependem deles) e por fim consumos e fechamentos.
    # 'cls' é a própria classe Hotel (por isso @classmethod: o método não precisa de um Hotel já criado).
    @classmethod
    def carregar(cls, arquivo: str) -> "Hotel":
        hotel = cls(arquivo=arquivo)
        if not os.path.exists(arquivo):
            hotel._dados_iniciais()
            return hotel
        with open(arquivo, encoding="utf-8") as f:
            dados = json.load(f)
        hotel.nome = dados.get("nome", "Hotel")
        for d in dados["hospedes"]:
            hotel.hospedes[d["id"]] = Hospede(d["id"], d["nome"], d["documento"], d["telefone"], validar=False)
        for d in dados["quartos"]:
            hotel.quartos[d["numero"]] = Quarto(d["numero"], d["categoria"],
                                                d["capacidade"], d["diaria"], validar=False)
        for d in dados["servicos"]:
            hotel.servicos[d["id"]] = Servico(d["id"], d["descricao"], d["preco"], validar=False)
        for d in dados["reservas"]:
            r = Reserva(d["id"], hotel.hospedes[d["hospede_id"]],
                        hotel.quartos[d["quarto_numero"]],
                        date.fromisoformat(d["entrada"]), date.fromisoformat(d["saida"]),
                        d["pessoas"], d["diaria_contratada"], StatusReserva[d["status"]])
            for c in d["consumos"]:
                r.consumos.append(Consumo(hotel.servicos[c["servico_id"]],
                                          c["quantidade"], c["preco_unitario"]))
            hotel.reservas[r.id] = r
        for d in dados.get("fechamentos", []):  # arquivos antigos não têm fechamentos
            hotel.fechamentos.append(FechamentoCaixa(
                d["numero"], datetime.fromisoformat(d["data_hora"]),
                [hotel.reservas[i] for i in d["reservas"] if i in hotel.reservas]))
        return hotel

    def _dados_iniciais(self):
        """Quartos e serviços de exemplo para a primeira execução."""
        self.nome = "Hotel Paradigmas"
        for numero, cat, cap, diaria in [("101", "Standard", 2, "180.00"),
                                         ("102", "Standard", 2, "180.00"),
                                         ("201", "Luxo", 3, "280.00"),
                                         ("301", "Família", 5, "350.00")]:
            self.quartos[numero] = Quarto(numero, cat, cap, diaria)
        for i, (desc, preco) in enumerate([("Água (frigobar)", "10.00"),
                                           ("Refrigerante (frigobar)", "8.00"),
                                           ("Lavanderia", "20.00"),
                                           ("Café da manhã no quarto", "35.00")], start=1):
            self.servicos[i] = Servico(i, desc, preco)
        self.salvar()
