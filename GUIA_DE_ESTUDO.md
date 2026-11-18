# Guia de estudo: Sistema de Hotel

Este guia é para os três integrantes estudarem o código e responderem às perguntas do professor.
Os números de linha valem para a versão atual do GitHub (conferidos). Abram o arquivo no VS Code e usem
**Ctrl+G** para ir direto à linha.

**Se vocês não são muito bons de Python, comecem pela pasta `estudo/`:**

| Arquivo | Para que serve |
|---|---|
| `estudo/1_PYTHON_DO_PROJETO.md` | As ~20 ideias de Python que aparecem no código, com trechos reais |
| `estudo/mini_hotel.py` | Mini-sistema de 90 linhas que roda no terminal. Entendam este antes do `modelos.py` |
| `estudo/2_PASSO_A_PASSO_DEBUG.md` | Como ver o código rodando, linha por linha, no VS Code |
| `estudo/3_MAPA_DO_APP.md` | O padrão das telas do `app.py`, para explicá-lo sem ler as 1.000 linhas |

O `modelos.py` e o `analise.py` também têm **comentários explicando cada trecho** (só comentários: o código é o mesmo).

**Ordem sugerida de estudo:**
0. `estudo/1_PYTHON_DO_PROJETO.md` e `estudo/mini_hotel.py` (cerca de 40 minutos).
1. Seção 1 (visão geral), cerca de 10 minutos.
2. Seção 2 (as classes do `modelos.py`), abrindo cada linha indicada. É a parte mais importante.
3. Seção 3 (o caminho de um clique), para entender como tela e classe conversam.
4. Seção 5 (perguntas): cada um responde em voz alta, sem olhar a resposta.

---

## 1. Visão geral em 1 minuto

O sistema é a recepção de um hotel pequeno: cadastrar hóspedes e quartos, reservar sem conflito de datas,
fazer check-in, lançar consumos, fechar a conta e fechar o caixa.

| Arquivo | O que tem | Precisa saber explicar? |
|---|---|---|
| `modelos.py` | **As classes do negócio**: regras, cálculos e gravação em JSON | **Sim, em detalhe** |
| `analise.py` | Classe `Analise`: lê o JSON e calcula indicadores | Sim, os principais métodos |
| `app.py` | As telas (CustomTkinter) | Só a ideia geral (seção 4) |
| `app_classico.py` | As mesmas telas sem bibliotecas extras (reserva) | Não |
| `tests/` | Testes automáticos das regras | Saber que existem e o que conferem |
| `dados_hotel.json` | Os dados salvos (criado ao usar o sistema) | Saber que é ali que tudo fica |

**A frase que resume a arquitetura:**
> As telas só recebem dados e mostram resultados. Toda regra e todo cálculo ficam nas classes do `modelos.py`.

---

## 2. As classes do `modelos.py`

### Como elas se relacionam

```
Hospede ──1──┐                 ┌──1── Quarto
             └──── Reserva ────┘
                      │ 0..*
                   Consumo ──1── Servico

Hotel: guarda todos os objetos acima e aplica as regras que envolvem várias reservas.
FechamentoCaixa: agrupa as reservas concluídas de um período.
```

### `Hospede` (linha 167)
- **Dados:** id, nome, documento, telefone.
- **Validações no construtor:** nome com 3 a 60 letras (`validar_nome`, linha 79), CPF com 11 dígitos
  ou RG com 7 a 9 (`limpar_documento`, linha 94), telefone com 10 ou 11 dígitos.
- Guarda o documento **só com números**. A versão com pontos e traço é calculada em `documento_formatado`.

### `Quarto` (linha 203)
- **Dados:** número, categoria, capacidade e diária.
- **`diaria` é uma `@property` (linha 225):** toda vez que alguém muda a diária, o *setter* valida o valor
  (não pode ser zero nem negativo). Esse é o exemplo de **encapsulamento** do projeto.
- `comporta(pessoas)` (linha 237): diz se o grupo cabe no quarto.

### `Servico` (linha 248) e `Consumo` (linha 271)
- `Servico` é o item do catálogo: descrição e preço atual.
- `Consumo` é o que o hóspede usou: qual serviço, quantidade e **preço unitário guardado no momento**.
- `Consumo.subtotal` (linha 287) = quantidade × preço unitário.

### `StatusReserva` (linha 295)
- Um `Enum` com as situações possíveis: Confirmada → Em hospedagem → Concluída, ou Cancelada.

### `Reserva` (linha 306): o centro do sistema
- **Associação:** guarda referência ao `Hospede` e ao `Quarto` (linha 322).
- **Composição:** guarda a lista de `Consumo` (linha 332). O consumo não existe fora da reserva.
- **Preço contratado:** guarda a `diaria_contratada`. Se o hotel mudar a diária do quarto depois, a conta não muda.
- **Cálculos:**

| Método | Linha | Conta |
|---|---|---|
| `qtd_diarias` | 337 | dias entre a saída e a entrada |
| `valor_hospedagem` | 341 | diárias × diária contratada |
| `valor_consumos` | 346 | soma dos subtotais dos consumos |
| `total` | 351 | hospedagem + consumos |

- **Regras de situação:**

| Método | Linha | Regra |
|---|---|---|
| `check_in` | 373 | só se estiver Confirmada |
| `lancar_consumo` | 379 | só se estiver Em hospedagem |
| `checkout` | 386 | só se estiver Em hospedagem; vira Concluída |
| `cancelar` | 392 | só se estiver Confirmada |

- **`conflita_com` (linha 365):** a regra de datas, em uma linha:
  ```python
  return self.ativa and entrada < self.saida and saida > self.entrada
  ```
  Há conflito quando a nova entrada é **antes** da saída existente **e** a nova saída é **depois** da entrada existente.
  Como a comparação é `<` e não `<=`, quem sai no dia 22 libera o quarto para quem entra no dia 22.
  Reservas canceladas ou concluídas não bloqueiam (`self.ativa`, linha 357).

### `FechamentoCaixa` (linha 426)
- Reúne as hospedagens concluídas desde o fechamento anterior.
- Cálculos: `quantidade`, `valor_hospedagem`, `valor_consumos` e `total`.
- `relatorio` (linha 462) monta o texto em formato de cupom; `salvar_relatorio` (linha 483) grava em `.txt`.
- **Nada é apagado.** O fechamento só marca até onde o caixa foi contado.

### `Hotel` (linha 500): a classe que gerencia tudo
- Guarda dicionários com todos os hóspedes, quartos, serviços e reservas, e a lista de fechamentos.
- **Cadastros:** `cadastrar_hospede` (linha 520) e os equivalentes de quarto e serviço. Impedem documento ou número repetido.
- **Exclusões:** `excluir_hospede` (linha 552) e equivalentes. Não deixam excluir quem tem reserva ativa ou concluída.
- **Disponibilidade:** `quarto_livre` (linha 591) pergunta para cada reserva se ela `conflita_com` as datas.
  `quartos_disponiveis` (linha 596) filtra os quartos que comportam o grupo e estão livres.
- **`reservar` (linha 603):** confere se o quarto está livre, cria a `Reserva` e salva.
- **Caixa:** `reservas_caixa_aberto` (linha 618) e `fechar_caixa` (linha 632).
- **Painel:** `situacao_quarto` (linha 644) e `resumo` (linha 658).
- **JSON:** `salvar` (linha 674) transforma cada objeto em dicionário (`para_dict`) e grava o arquivo.
  `carregar` (linha 692) faz o caminho inverso e **recria os objetos** com as ligações entre eles.

### Funções auxiliares (topo do arquivo)
- `RegraNegocioErro` (linha 31): o erro lançado quando uma regra é violada. A tela mostra a mensagem dele.
- `dinheiro` (linha 38): transforma texto em `Decimal` com 2 casas.
- `LIMITES` (linha 74): o tamanho máximo de cada campo, usado pelas classes e pelas telas.
- `mascara_documento` (linha 111): formata `12345678900` como `123.456.789-00` enquanto a pessoa digita.

---

## 3. O caminho de um clique: "Confirmar reserva"

Este é o melhor exemplo para mostrar ao professor como tela e classe conversam.

1. **Tela** (`app.py`, linha 614, `PaginaReservas.reservar`): lê o hóspede, as datas e o quarto escolhidos.
2. Chama **`Hotel.reservar`** (`modelos.py`, linha 603).
3. O `Hotel` chama **`quarto_livre`** (linha 591), que pergunta a **cada reserva** se ela **`conflita_com`** as datas (linha 365).
4. Se estiver livre, cria **`Reserva(...)`** (linha 306). O construtor confere datas, pessoas e capacidade.
5. O `Hotel` guarda a reserva e chama **`salvar`** (linha 674), que grava o `dados_hotel.json`.
6. Se alguma regra falhar, sai um **`RegraNegocioErro`**. A tela o captura em **`Pagina.executar`**
   (`app.py`, linha 293) e mostra a mensagem, por exemplo "O quarto 101 já está reservado nesse período".

O checkout segue o mesmo padrão: a tela (`app.py`, linha 722) chama `Reserva.checkout` (`modelos.py`, linha 386).

---

## 4. As telas (`app.py`) em poucas frases

- Cada tela é uma classe que **herda de `Pagina`** (linha 256). A `Pagina` monta o cabeçalho e tem o método
  `executar` (linha 293), que roda uma ação e mostra o erro se uma regra for violada.
- Cada página tem um método `atualizar()`, que busca os dados no `Hotel` e preenche as tabelas.
- Componentes reutilizados em todas as telas: `Cartao`, `Indicador` (herda de `Cartao`, linha 171), `Formulario`,
  `Tabela` e `Grafico` (linha 764, desenha as barras no `Canvas`).
- `limitar_entrada` (linha 190) impede digitar além do limite e aplica a máscara de CPF e telefone.
- A classe `Aplicacao` monta o menu lateral e troca de página.

---

## 5. Perguntas prováveis do professor

**Conceitos**

1. **Qual a diferença entre classe e objeto?**
   A classe é o molde (`Reserva`); o objeto é uma reserva específica criada a partir dela, como a da Maria no quarto 101.

2. **Onde está a associação?**
   `Reserva` guarda um `Hospede` e um `Quarto` (`modelos.py`, linha 322). Eles existem independentemente da reserva.

3. **E a composição?**
   `Reserva` guarda a lista de `Consumo` (linha 332). O consumo só existe dentro da reserva.

4. **Onde está o encapsulamento?**
   Em `Quarto.diaria` (linha 225). A diária é guardada em `_diaria` e só muda pelo *setter*, que valida o valor.

5. **Tem herança?**
   Nas telas: cada página herda de `Pagina`, e `Indicador` herda de `Cartao`. Nas classes do negócio não precisamos:
   hóspede, quarto e reserva não são tipos uns dos outros. Criar herança só para ter herança seria artificial.

6. **Por que os cálculos ficam nas classes e não nas telas?**
   Porque a regra fica num lugar só. As duas versões das telas e os testes usam o mesmo cálculo.

**Regras**

7. **Como o sistema impede duas reservas no mesmo quarto?**
   `conflita_com` (linha 365): há conflito se a nova entrada é antes da saída existente e a nova saída é depois
   da entrada existente.

8. **Por que dá para reservar com entrada no mesmo dia da saída de outro hóspede?**
   Porque a comparação usa `<`: a data de saída não conta como noite ocupada.

9. **Por que guardar a diária na reserva se ela já está no quarto?**
   Para preservar o preço contratado. Se o hotel aumentar a diária amanhã, quem já reservou paga o combinado.

10. **Por que usar `Decimal` e não `float` para dinheiro?**
    O `float` tem erro de arredondamento (por exemplo, `0.1 + 0.2` dá `0.30000000000000004`). O `Decimal` faz conta exata.

11. **Como impedir check-in de uma reserva cancelada?**
    `check_in` (linha 373) confere a situação e lança `RegraNegocioErro` se não estiver Confirmada.

12. **O que acontece se eu tentar excluir um hóspede que tem reserva?**
    `excluir_hospede` (linha 552) bloqueia, para a conta não ficar sem dono. Reservas canceladas são apagadas junto.

**Dados e extras**

13. **Onde os dados ficam salvos?**
    No `dados_hotel.json`. `Hotel.salvar` (linha 674) grava e `Hotel.carregar` (linha 692) lê e recria os objetos.

14. **O fechamento de caixa apaga o faturamento?**
    Não. Ele registra quais reservas foram contadas e o painel começa do zero. O histórico continua na Análise de dados.

15. **Como a Análise de dados calcula a ocupação?**
    `taxa_ocupacao` (`analise.py`, linha 96): diárias vendidas ÷ (quartos × dias do período) × 100.

---

## 6. Divisão da apresentação

| Integrante | Parte | Arquivos e linhas para dominar |
|---|---|---|
| 1 | Problema, classes e relações; cadastros e validações | `Hospede` (167), `Quarto` (203) com a `@property` (225), `Servico` e `Consumo` (248 a 290), validações (79 a 129), exclusões (552) |
| 2 | Reserva, diárias e conflito de datas | `Reserva` (306 a 413), `conflita_com` (365), `Hotel.quarto_livre` e `reservar` (591 a 615), caminho do clique (seção 3) |
| 3 | Check-in, consumos, checkout, caixa e análise | `check_in`, `lancar_consumo`, `checkout` (373 a 392), `FechamentoCaixa` (426), `salvar` e `carregar` (674, 692), `analise.py` |

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
