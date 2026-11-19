# Guia de estudo: Sistema de Hotel

Este guia é para os três integrantes estudarem o código e responderem às perguntas do professor.

**Para achar onde está qualquer coisa, usem o [`MAPA_DO_CODIGO.md`](MAPA_DO_CODIGO.md)**: ele diz, para cada pergunta,
em qual arquivo e método está. Os arquivos e métodos citados neste guia são os da versão atual (conferidos).
No VS Code: **Ctrl+P** abre um arquivo pelo nome (digite `reserva`) e **Ctrl+Shift+O** vai até um método do arquivo aberto.

**Se vocês não são muito bons de Python, comecem pela pasta `estudo/`:**

| Arquivo | Para que serve |
|---|---|
| `estudo/1_PYTHON_DO_PROJETO.md` | As ~20 ideias de Python que aparecem no código, com trechos reais |
| `estudo/mini_hotel.py` | Mini-sistema de 90 linhas que roda no terminal. Entendam este antes da pasta `modelos/` |
| `estudo/2_PASSO_A_PASSO_DEBUG.md` | Como ver o código rodando, linha por linha, no VS Code |
| `estudo/3_MAPA_DO_APP.md` | O padrão das telas, para explicá-las sem ler arquivo por arquivo |

Os arquivos de `modelos/` e o `analise.py` também têm **comentários explicando cada trecho**.

**Ordem sugerida de estudo:**
0. `estudo/1_PYTHON_DO_PROJETO.md` e `estudo/mini_hotel.py` (cerca de 40 minutos).
1. Seção 1 (visão geral), cerca de 10 minutos.
2. Seção 2 (as classes da pasta `modelos/`), abrindo cada arquivo indicado. É a parte mais importante.
3. Seção 3 (o caminho de um clique), para entender como tela e classe conversam.
4. Seção 5 (perguntas): cada um responde em voz alta, sem olhar a resposta.

---

## 1. Visão geral em 1 minuto

O sistema é a recepção de um hotel pequeno: cadastrar hóspedes e quartos, reservar sem conflito de datas,
fazer check-in, lançar consumos, fechar a conta e fechar o caixa.

| Pasta ou arquivo | O que tem | Precisa saber explicar? |
|---|---|---|
| `modelos/` | **As classes do negócio**, uma por arquivo: regras, cálculos e gravação em JSON | **Sim, em detalhe** |
| `analise.py` | Classe `Analise`: lê o JSON e calcula indicadores | Sim, os principais métodos |
| `telas/` | As telas (CustomTkinter), uma por item do menu | Só a ideia geral (seção 4) |
| `app.py` | Abre o sistema | Sim, é curto |
| `app_classico.py` | As mesmas telas sem bibliotecas extras (reserva) | Não |
| `tests/` | Testes automáticos das regras | Saber que existem e o que conferem |
| `dados_hotel.json` | Os dados salvos (criado ao usar o sistema) | Saber que é ali que tudo fica |

**A frase que resume a arquitetura:**
> As telas só recebem dados e mostram resultados. Toda regra e todo cálculo ficam nas classes da pasta `modelos/`.

---

## 2. As classes da pasta `modelos/`

**A regra de ouro:** o arquivo tem o nome da classe. Cada arquivo começa com um texto "ONDE ESTÁ O QUÊ".

### Como elas se relacionam

```
Hospede ──1──┐                 ┌──1── Quarto
             └──── Reserva ────┘
                      │ 0..*
                   Consumo ──1── Servico

Hotel: guarda todos os objetos acima e aplica as regras que envolvem várias reservas.
FechamentoCaixa: agrupa as reservas concluídas de um período.
```

### `Hospede` (`modelos/hospede.py`)
- **Dados:** id, nome, documento, telefone.
- **Validações no construtor:** nome com 3 a 60 letras (`validar_nome`), CPF com 11 dígitos
  ou RG com 7 a 9 (`limpar_documento`), telefone com 10 ou 11 dígitos (`limpar_telefone`). Essas funções estão em `modelos/validacoes.py`.
- Guarda o documento **só com números**. A versão com pontos e traço é calculada em `documento_formatado`.

### `Quarto` (`modelos/quarto.py`)
- **Dados:** número, categoria, capacidade e diária.
- **`diaria` é uma `@property`:** toda vez que alguém muda a diária, o *setter* valida o valor
  (não pode ser zero nem negativo). Esse é o exemplo de **encapsulamento** do projeto.
- `comporta(pessoas)`: diz se o grupo cabe no quarto.

### `Servico` (`modelos/servico.py`) e `Consumo` (`modelos/consumo.py`)
- `Servico` é o item do catálogo: descrição e preço atual.
- `Consumo` é o que o hóspede usou: qual serviço, quantidade e **preço unitário guardado no momento**.
- `Consumo.subtotal` = quantidade × preço unitário.

### `StatusReserva` (`modelos/reserva.py`)
- Um `Enum` com as situações possíveis: Confirmada → Em hospedagem → Concluída, ou Cancelada.

### `Reserva` (`modelos/reserva.py`): o centro do sistema
- **Associação:** guarda referência ao `Hospede` e ao `Quarto` (em `Reserva.__init__`).
- **Composição:** guarda a lista de `Consumo` (em `Reserva.__init__`). O consumo não existe fora da reserva.
- **Preço contratado:** guarda a `diaria_contratada`. Se o hotel mudar a diária do quarto depois, a conta não muda.
- **Cálculos:**

| Método | Conta |
|---|---|
| `qtd_diarias` | dias entre a saída e a entrada |
| `valor_hospedagem` | diárias × diária contratada |
| `valor_consumos` | soma dos subtotais dos consumos |
| `total` | hospedagem + consumos |

- **Regras de situação:**

| Método | Regra |
|---|---|
| `check_in` | só se estiver Confirmada |
| `lancar_consumo` | só se estiver Em hospedagem |
| `checkout` | só se estiver Em hospedagem; vira Concluída |
| `cancelar` | só se estiver Confirmada |

- **`conflita_com`:** a regra de datas, em uma linha:
  ```python
  return self.ativa and entrada < self.saida and saida > self.entrada
  ```
  Há conflito quando a nova entrada é **antes** da saída existente **e** a nova saída é **depois** da entrada existente.
  Como a comparação é `<` e não `<=`, quem sai no dia 22 libera o quarto para quem entra no dia 22.
  Reservas canceladas ou concluídas não bloqueiam (`ativa`, no mesmo arquivo).

### `FechamentoCaixa` (`modelos/caixa.py`)
- Reúne as hospedagens concluídas desde o fechamento anterior.
- Cálculos: `quantidade`, `valor_hospedagem`, `valor_consumos` e `total`.
- `relatorio` monta o texto em formato de cupom; `salvar_relatorio` grava em `.txt`.
- **Nada é apagado.** O fechamento só marca até onde o caixa foi contado.

### `Hotel` (`modelos/hotel.py`): a classe que gerencia tudo
- Guarda dicionários com todos os hóspedes, quartos, serviços e reservas, e a lista de fechamentos.
- **Cadastros:** `cadastrar_hospede` e os equivalentes de quarto e serviço. Impedem documento ou número repetido.
- **Exclusões:** `excluir_hospede` e equivalentes. Não deixam excluir quem tem reserva ativa ou concluída.
- **Disponibilidade:** `quarto_livre` pergunta para cada reserva se ela `conflita_com` as datas.
  `quartos_disponiveis` filtra os quartos que comportam o grupo e estão livres.
- **`reservar`:** confere se o quarto está livre, cria a `Reserva` e salva.
- **Caixa:** `reservas_caixa_aberto` e `fechar_caixa`.
- **Painel:** `situacao_quarto` e `resumo`.
- **JSON:** `salvar` transforma cada objeto em dicionário (`para_dict`) e grava o arquivo.
  `carregar` faz o caminho inverso e **recria os objetos** com as ligações entre eles.

### Os arquivos de apoio (também em `modelos/`)
- `erros.py`, `RegraNegocioErro`: o erro lançado quando uma regra é violada. A tela mostra a mensagem dele.
- `formatos.py`, `dinheiro`: transforma texto em `Decimal` com 2 casas.
- `validacoes.py`, `LIMITES`: o tamanho máximo de cada campo, usado pelas classes e pelas telas.
- `validacoes.py`, `mascara_documento`: formata `12345678900` como `123.456.789-00` enquanto a pessoa digita.

---

## 3. O caminho de um clique: "Confirmar reserva"

Este é o melhor exemplo para mostrar ao professor como tela e classe conversam.

1. **Tela** (`telas/reservas.py`, `PaginaReservas.reservar`): lê o hóspede, as datas e o quarto escolhidos.
2. Chama **`Hotel.reservar`** (`modelos/hotel.py`).
3. O `Hotel` chama **`quarto_livre`** (mesmo arquivo), que pergunta a **cada reserva** se ela **`conflita_com`** as datas (`modelos/reserva.py`).
4. Se estiver livre, cria **`Reserva(...)`** (`modelos/reserva.py`). O construtor confere datas, pessoas e capacidade.
5. O `Hotel` guarda a reserva e chama **`salvar`** (`modelos/hotel.py`), que grava o `dados_hotel.json`.
6. Se alguma regra falhar, sai um **`RegraNegocioErro`**. A tela o captura em **`Pagina.executar`**
   (`telas/pagina.py`) e mostra a mensagem, por exemplo "O quarto 101 já está reservado nesse período".

O checkout segue o mesmo padrão: a tela (`telas/hospedagem.py`, `PaginaHospedagem.checkout`) chama `Reserva.checkout` (`modelos/reserva.py`).

---

## 4. As telas (pasta `telas/`) em poucas frases

- Cada tela é uma classe que **herda de `Pagina`** (`telas/pagina.py`). A `Pagina` monta o cabeçalho e tem o método
  `executar`, que roda uma ação e mostra o erro se uma regra for violada.
- Cada página tem um método `atualizar()`, que busca os dados no `Hotel` e preenche as tabelas.
- Componentes reutilizados em todas as telas (`telas/componentes.py`): `Cartao`, `Indicador` (herda de `Cartao`), `Formulario`
  e `Tabela`. O `Grafico` (`telas/analise_dados.py`) desenha as barras no `Canvas`.
- `limitar_entrada` (`telas/componentes.py`) impede digitar além do limite e aplica a máscara de CPF e telefone.
- A classe `Aplicacao` (`telas/janela.py`) monta o menu lateral e troca de página.
- Uma tela por item do menu: `painel.py`, `reservas.py`, `hospedagem.py`, `hospedes.py`, `quartos.py`, `servicos.py`, `analise_dados.py`.

---

## 5. Perguntas prováveis do professor

**Conceitos**

1. **Qual a diferença entre classe e objeto?**
   A classe é o molde (`Reserva`); o objeto é uma reserva específica criada a partir dela, como a da Maria no quarto 101.

2. **Onde está a associação?**
   `Reserva` guarda um `Hospede` e um `Quarto` (`modelos/reserva.py`, em `__init__`). Eles existem independentemente da reserva.

3. **E a composição?**
   `Reserva` guarda a lista de `Consumo` (`modelos/reserva.py`, em `__init__`). O consumo só existe dentro da reserva.

4. **Onde está o encapsulamento?**
   Em `Quarto.diaria` (`modelos/quarto.py`). A diária é guardada em `_diaria` e só muda pelo *setter*, que valida o valor.

5. **Tem herança?**
   Nas telas: cada página herda de `Pagina` (`telas/pagina.py`), e `Indicador` herda de `Cartao` (`telas/componentes.py`). Nas classes do negócio não precisamos:
   hóspede, quarto e reserva não são tipos uns dos outros. Criar herança só para ter herança seria artificial.

6. **Por que os cálculos ficam nas classes e não nas telas?**
   Porque a regra fica num lugar só. As duas versões das telas e os testes usam o mesmo cálculo.

**Regras**

7. **Como o sistema impede duas reservas no mesmo quarto?**
   `conflita_com` (`modelos/reserva.py`): há conflito se a nova entrada é antes da saída existente e a nova saída é depois
   da entrada existente.

8. **Por que dá para reservar com entrada no mesmo dia da saída de outro hóspede?**
   Porque a comparação usa `<`: a data de saída não conta como noite ocupada.

9. **Por que guardar a diária na reserva se ela já está no quarto?**
   Para preservar o preço contratado. Se o hotel aumentar a diária amanhã, quem já reservou paga o combinado.

10. **Por que usar `Decimal` e não `float` para dinheiro?**
    O `float` tem erro de arredondamento (por exemplo, `0.1 + 0.2` dá `0.30000000000000004`). O `Decimal` faz conta exata.

11. **Como impedir check-in de uma reserva cancelada?**
    `check_in` (`modelos/reserva.py`) confere a situação e lança `RegraNegocioErro` se não estiver Confirmada.

12. **O que acontece se eu tentar excluir um hóspede que tem reserva?**
    `excluir_hospede` (`modelos/hotel.py`) bloqueia, para a conta não ficar sem dono. Reservas canceladas são apagadas junto.

**Dados e extras**

13. **Onde os dados ficam salvos?**
    No `dados_hotel.json`. `Hotel.salvar` grava e `Hotel.carregar` lê e recria os objetos (`modelos/hotel.py`).

14. **O fechamento de caixa apaga o faturamento?**
    Não. Ele registra quais reservas foram contadas e o painel começa do zero. O histórico continua na Análise de dados.

15. **Como a Análise de dados calcula a ocupação?**
    `taxa_ocupacao` (`analise.py`): diárias vendidas ÷ (quartos × dias do período) × 100.

---

## 6. Divisão da apresentação

| Integrante | Parte | Arquivos para dominar |
|---|---|---|
| 1 | Problema, classes e relações; cadastros e validações | `modelos/hospede.py`, `modelos/quarto.py` (a `@property`), `modelos/servico.py`, `modelos/consumo.py`, `modelos/validacoes.py`, `Hotel.excluir_hospede` |
| 2 | Reserva, diárias e conflito de datas | `modelos/reserva.py` inteiro, `conflita_com`, `Hotel.quarto_livre` e `Hotel.reservar` (`modelos/hotel.py`), caminho do clique (seção 3) |
| 3 | Check-in, consumos, checkout, caixa e análise | `check_in`, `lancar_consumo` e `checkout` (`modelos/reserva.py`), `modelos/caixa.py`, `Hotel.salvar` e `Hotel.carregar`, `analise.py` |

A divisão organiza a fala, mas **todos precisam entender o código inteiro**: o professor pode perguntar qualquer parte a qualquer um.

---

## 7. Glossário rápido

| Termo | Onde aparece | Explicação curta |
|---|---|---|
| `@property` | `Reserva.total`, `Quarto.diaria` | Método que se usa como atributo: `r.total`, sem parênteses |
| *setter* | `Quarto.diaria` | Código que roda quando alguém atribui um valor, usado para validar |
| `Enum` | `StatusReserva` | Lista fechada de valores possíveis |
| `Decimal` | `dinheiro()` | Número exato para dinheiro |
| `dict` | `Hotel.hospedes` | Dicionário: acha o objeto pela chave (id ou número do quarto) |
| JSON | `dados_hotel.json` | Arquivo de texto com os dados organizados em listas e dicionários |
| Exceção | `RegraNegocioErro` | Erro lançado de propósito quando uma regra é violada |
| `self` | todos os métodos | O próprio objeto que está executando o método |

---

## 8. Roteiro final antes da apresentação

1. Atualizar o projeto (`git pull`) e rodar os testes:
   `.venv\Scripts\python tests\teste_regras.py` e `.venv\Scripts\python tests\teste_analise.py`.
2. Apagar o `dados_hotel.json` e a pasta `fechamentos` para começar limpo.
3. Ensaiar o roteiro da demonstração do README, de ponta a ponta, cronometrando.
4. Cada integrante responde as 15 perguntas da seção 5 em voz alta, sem ler.
