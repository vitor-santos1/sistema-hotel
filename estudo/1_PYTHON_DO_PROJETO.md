# Python que aparece neste projeto

Este guia é para quem **não é muito bom de Python**. Ele explica, com trechos reais do nosso código, as
cerca de 20 ideias que aparecem nos arquivos. Quem entende estas ideias consegue ler o projeto inteiro.

Como usar: leia uma seção, abra o arquivo na linha indicada (**Ctrl+G** no VS Code) e veja o trecho de verdade.
Antes de começar, rode o mini-sistema, que usa várias destas ideias em pequeno:

```bash
.venv\Scripts\python estudo\mini_hotel.py
```

---

## 1. Comentários
Tudo depois de `#` é só explicação para quem lê. O Python ignora.
```python
# Preço "congelado": se o catálogo mudar depois, a conta não muda.
```
Um texto entre três aspas logo depois de `class` ou `def` (`"""..."""`) é a *docstring*: a descrição da classe ou função.

## 2. Variáveis e tipos
Uma variável guarda um valor: `nome = "Maria"`, `dias = 3`, `ativo = True`, `telefone = None` (None = "nada").
Tipos que aparecem: texto (`str`), inteiro (`int`), `True`/`False` (`bool`), lista, dicionário e `Decimal`.

## 3. Funções: `def` e `return`
Uma função é um bloco de código com nome, que recebe valores e devolve um resultado.
```python
def formatar_data(d: date) -> str:
    return d.strftime("%d/%m/%Y")
```
- `def` cria a função; `d` é o valor que ela recebe; `return` devolve o resultado.
- `: date` e `-> str` são **dicas de tipo**: avisam o que entra e o que sai. Ajudam quem lê, não mudam nada na execução.
- Usar a função: `formatar_data(hoje)`.
- Onde aparece: `modelos.py`, linha 38.

## 4. Classes e objetos
- **Classe** é o molde: `Reserva`. **Objeto** é uma unidade feita com o molde: a reserva da Maria.
- `__init__` é o **construtor**: roda quando o objeto é criado.
- `self` é o próprio objeto. `self.nome = nome` guarda o dado dentro dele.
```python
class Hospede:
    def __init__(self, id, nome, documento, telefone=""):
        self.id = id
        self.nome = nome
```
Criar um objeto: `maria = Hospede(1, "Maria Silva", "12345678900")`.
- Onde aparece: `modelos.py`, linha 167 e, o mais importante, `modelos.py`, linha 306.

## 5. Atributos e métodos
- **Atributo** é um dado do objeto: `reserva.entrada`.
- **Método** é uma função do objeto: `reserva.check_in()`. Repare nos parênteses.
- Dentro da classe, o método usa `self` para acessar os dados do próprio objeto.

## 6. `@property`: método que se usa como dado
```python
@property
def total(self) -> Decimal:
    return self.valor_hospedagem + self.valor_consumos
```
Por causa do `@property`, escrevemos `reserva.total` (sem parênteses) e o Python calcula na hora.
- Onde aparece: `modelos.py`, linha 351.
- Com `@diaria.setter` ele também controla a **escrita**: `modelos.py`, linha 230 valida antes de guardar. Isso é **encapsulamento**.

## 7. `if` e `raise` (regras e erros)
```python
def check_in(self):
    if self.status != StatusReserva.CONFIRMADA:
        raise RegraNegocioErro("Check-in só é permitido em reserva confirmada.")
    self.status = StatusReserva.EM_HOSPEDAGEM
```
- `if` testa uma condição. `!=` quer dizer "diferente de". `==` é "igual a".
- `raise` **lança um erro** e interrompe o método. A linha seguinte não roda.
- Se o `if` não for verdadeiro, o código segue e muda o status.
- Onde aparece: `modelos.py`, linha 373.

## 8. `try` / `except` (capturar erros)
```python
try:
    hotel = Hotel.carregar(caminho)
except (ValueError, KeyError, TypeError, AttributeError):
    raise RegraNegocioErro("Esse arquivo não tem o formato de dados do hotel ...")
```
O Python **tenta** o bloco do `try`. Se acontecer um dos erros listados no `except`, o programa não quebra: roda o bloco do `except`.
- Onde aparece: `analise.py`, linha 40 e, nas telas, `app.py`, linha 293, que captura o `RegraNegocioErro` e mostra a mensagem.

## 9. Listas e `for`
```python
for c in self.consumos:
    linhas.append(f"{c.servico.descricao}: {c.quantidade} x ...")
```
- Lista: `[1, 2, 3]`. `append` acrescenta um item no fim.
- `for c in lista:` repete o bloco uma vez para cada item (`c` é o item da vez).
- Onde aparece: `modelos.py`, linha 398.

## 10. Lista em uma linha (*list comprehension*)
```python
return [q for q in self.quartos.values()
        if q.comporta(pessoas) and self.quarto_livre(q, entrada, saida)]
```
Lê-se: "uma lista com cada `q` dos quartos, **se** ele comporta o grupo e está livre". É um `for` com filtro escrito numa linha.
- Onde aparece: `modelos.py`, linha 596.

## 11. Dicionários
Guardam pares **chave → valor**. A gente acha o valor pela chave.
```python
self.hospedes: dict[int, Hospede] = {}     # cria vazio
self.hospedes[h.id] = h                    # guarda: chave = id, valor = o hóspede
hotel.hospedes[3]                          # busca o hóspede de id 3
```
Outros usos: `.values()` (só os valores), `.items()` (pares chave e valor), `.get(chave)` (busca sem dar erro se não existir).
- Onde aparece: `modelos.py`, linha 505 e `modelos.py`, linha 74.

## 12. *f-strings*: texto com valores dentro
```python
raise RegraNegocioErro(f"O quarto {quarto.numero} já está reservado nesse período.")
```
O `f` antes das aspas faz o `{...}` ser trocado pelo valor. Resultado: "O quarto 101 já está reservado nesse período."

## 13. Funções prontas que aparecem muito
| Função | O que faz | Exemplo no projeto |
|---|---|---|
| `len(x)` | quantos itens | `len(self.reservas)` |
| `sum(...)` | soma | `sum(c.subtotal for c in self.consumos)` |
| `any(...)` | `True` se **pelo menos um** passa no teste | `modelos.py`, linha 591 |
| `all(...)` | `True` se **todos** passam | `modelos.py`, linha 79 |
| `sorted(...)` | ordena | `analise.py`, linha 127 |
| `min(...)`, `max(...)` | menor e maior | `analise.py`, linha 87 |

## 14. `lambda`: função de uma linha
```python
sorted(soma.items(), key=lambda item: item[1], reverse=True)
```
`lambda item: item[1]` é uma função sem nome que recebe `item` e devolve o segundo elemento (`item[1]`). Aqui serve para ordenar
os quartos pelo valor, do maior para o menor.

## 15. `import`
```python
from datetime import date, datetime
from decimal import Decimal
```
Traz ferramentas prontas. `from modelos import Hotel` traz a classe `Hotel` do nosso arquivo `modelos.py`. É assim que
as telas usam as classes.

## 16. `Enum`: lista fechada de valores
```python
class StatusReserva(Enum):
    CONFIRMADA = "Confirmada"
    EM_HOSPEDAGEM = "Em hospedagem"
```
Em vez de textos soltos que poderiam ser digitados errado, usamos `StatusReserva.CONFIRMADA`.
`.value` é o texto bonito; `.name` é o nome (`"CONFIRMADA"`). Onde aparece: `modelos.py`, linha 295.

## 17. `Decimal`: dinheiro sem erro
Com `float`: `0.1 + 0.2` dá `0.30000000000000004`. Com `Decimal` a conta é exata.
A função `dinheiro()` converte qualquer valor digitado para `Decimal` com 2 casas.

## 18. Arquivos e JSON: `with open`
```python
with open(self.arquivo, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)
```
- `open(arquivo, "w")` abre para **escrever** (`"r"` seria ler).
- `with` fecha o arquivo sozinho no fim, mesmo se der erro.
- `json.dump` grava o dicionário em formato JSON; `json.load` faz o caminho contrário.
- Onde aparece: `modelos.py`, linha 674 (grava) e `modelos.py`, linha 692 (lê).

## 19. `@classmethod` e `cls`
Um método de classe não precisa de um objeto já criado. `Hotel.carregar("dados.json")` **cria** um Hotel a partir do arquivo.
Dentro dele, `cls` é a própria classe `Hotel`.

## 20. `if __name__ == "__main__":`
Esse bloco só roda quando o arquivo é executado direto (`python app.py`), e não quando outro arquivo o importa.
É o ponto de entrada do programa. Onde aparece: no fim do `app.py`, linha 1047.

---

## Como ler um método que você não conhece
1. Leia o **nome** e a **docstring** (a descrição entre três aspas).
2. Olhe o que ele **recebe** (parênteses) e o que **devolve** (`return`).
3. Procure os `if` e `raise`: são as **regras** (o que é proibido).
4. Siga as chamadas: se aparece `self.outro_metodo()`, vá até ele.
5. Em dúvida, ponha um `print(variavel)` no meio ou use o debug do VS Code
   (veja `estudo/2_PASSO_A_PASSO_DEBUG.md`).
