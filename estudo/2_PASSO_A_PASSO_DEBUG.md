# Passo a passo: ver o código rodando (debug no VS Code)

Ler código ajuda; **vê-lo executar** ajuda muito mais. O VS Code permite parar o programa numa linha e
olhar o valor de cada variável. Isso não altera nenhum arquivo.

## Preparação (uma vez)
1. Abra a pasta do projeto no VS Code.
2. Confira o interpretador do `.venv` no canto inferior direito (algo como `.venv (3.13.x)`).
3. Apague o `dados_hotel.json` para começar limpo.

## Exercício 1: seguir uma reserva por dentro

**Colocar o ponto de parada**
1. Aperte **Ctrl+P**, digite `hotel` e Enter: abre o `modelos/hotel.py`. Depois aperte **Ctrl+Shift+O**, digite `reservar` e Enter.
2. Clique na margem **à esquerda do número da linha** `hospede = self.hospedes[hospede_id]` (a linha logo abaixo do `def`).
   Aparece uma **bolinha vermelha**: é o *breakpoint*.

**Rodar com debug**
3. Abra o `app.py` (o arquivo que abre o sistema) e aperte **F5**. Se aparecer uma lista, escolha **Python Debugger → Python File**.
4. O sistema abre. Cadastre uma hóspede (aba **Hóspedes**). Depois, em **Reservas**, escolha a hóspede,
   digite as datas `19/11/2026` e `22/11/2026`, `2` pessoas, clique em **Consultar quartos livres**,
   selecione o quarto 101 e clique em **Confirmar reserva**.
5. O VS Code **pula para a frente** e mostra a linha amarela: o programa **parou** no breakpoint.

**Andar linha por linha**
6. Na barra de controle do debug aparecem os botões. Os que importam:

| Tecla | Nome | O que faz |
|---|---|---|
| **F10** | Step Over | executa a linha e vai para a próxima |
| **F11** | Step Into | **entra** na função chamada na linha |
| **Shift+F11** | Step Out | termina a função atual e volta |
| **F5** | Continue | segue até o próximo breakpoint (ou até o fim) |

7. Aperte **F10** algumas vezes e olhe o painel **Variables** (à esquerda). Veja `hospede`, `quarto`, `entrada`, `saida`.
   Passe o mouse sobre `entrada` para ver a data.
8. Na linha `if not self.quarto_livre(quarto, entrada, saida):` aperte **F11** para **entrar** em `quarto_livre`.
   Entre também em `conflita_com` (**`modelos/reserva.py` (método `conflita_com`)**). Olhe os valores de `entrada`, `self.saida` e `saida`.
9. Aperte **Shift+F11** para sair e **F10** até a linha `r = Reserva(...)`. Aperte **F11** para entrar no **construtor**
   da `Reserva` e acompanhe as verificações (datas, pessoas, capacidade).
10. Aperte **F5** para terminar. A reserva aparece no sistema.

**O que observar:** os dados passam da tela para `Hotel.reservar`, depois para `quarto_livre`, depois para
`Reserva.conflita_com`. Essa é a mesma sequência do "caminho de um clique" do `GUIA_DE_ESTUDO.md`.

## Exercício 2: ver o conflito de datas acontecendo
1. Deixe o breakpoint do exercício 1 e faça **a mesma reserva de novo**, para o mesmo quarto e as mesmas datas.
2. Entre em `conflita_com` com **F11**. Repare em `entrada < self.saida and saida > self.entrada`: as duas
   partes são verdadeiras, então devolve `True`.
3. Siga com **F10**: o `RegraNegocioErro` é lançado e a tela mostra "já está reservado nesse período".
4. Agora tente `22/11/2026` a `24/11/2026`. Veja que `entrada < self.saida` fica **falso** (22 < 22) e a reserva é aceita.

## Exercício 3: ver o total da conta
1. Remova o breakpoint antigo (clique na bolinha) e coloque um em `def total(self) -> Decimal:` da classe `Reserva`
   (**`modelos/reserva.py` (método `total`)**).
2. Pelo sistema, faça check-in, lance consumos e abra a conta na aba **Hospedagem**.
3. Quando parar, abra o painel **Debug Console** (embaixo) e digite:
   ```
   self.valor_hospedagem
   self.valor_consumos
   len(self.consumos)
   ```
   O console responde com os valores na hora.

## Exercício 4 (sem tela): rodar o teste passo a passo
1. Abra `tests/teste_regras.py`, coloque um breakpoint na primeira linha que chama `hotel.reservar(`.
2. Abra o arquivo, aperte **F5** (Python File) e use **F10** e **F11**. Aqui não há janela do sistema: é só o código.

## Se algo não funcionar
- **O programa não para no breakpoint:** confira se a bolinha está vermelha cheia. Uma bolinha cinza significa que o
  VS Code não está em modo debug. Aperte **F5** (e não o botão ▶ simples).
- **A janela do sistema não aparece:** olhe a barra de tarefas, ela pode ter aberto atrás do VS Code.
- **Para terminar o debug:** aperte **Shift+F5** ou o quadrado vermelho.
