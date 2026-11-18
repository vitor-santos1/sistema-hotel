# Mapa das telas (`app.py`)

O `app.py` é o maior arquivo, mas é o mais **repetitivo**: todas as telas seguem o mesmo molde.
Entendendo uma, as outras são variações.

## O molde de toda tela
```
class PaginaXxx(Pagina):            # herda de Pagina (tem cabeçalho e o método executar)
    def __init__(self, master, app):
        super().__init__(master, app)   # monta o cabeçalho da Pagina
        ... cria os campos, botões e tabelas ...
    def botao_clicado(self):            # um método para cada botão
        self.executar(lambda: self.hotel.metodo_do_hotel(...), "mensagem de sucesso")
    def atualizar(self):                # recarrega os dados
        self.tabela.preencher([... dados vindos do self.hotel ...])
```
- **`self.hotel`** é o objeto `Hotel` (o mesmo para todas as telas). Toda regra está nele.
- **`self.executar(...)`** (`app.py`, linha 293) roda a ação. Se uma regra for violada, mostra a mensagem
  em vez de quebrar.
- **`atualizar()`** é chamado toda vez que a pessoa abre a tela.

## Cada tela e o que ela chama

| Tela (classe) | Linha | O que mostra | Métodos que ela chama |
|---|---|---|---|
| `PaginaPainel` | `app.py`, linha 313 | Números do dia, mapa de quartos, caixa | `Hotel.resumo`, `situacao_quarto`, `fechar_caixa` |
| `PaginaReservas` | `app.py`, linha 552 | Consulta de quartos livres e lista de reservas | `Hotel.quartos_disponiveis`, `reservar`, `Reserva.cancelar` |
| `PaginaHospedagem` | `app.py`, linha 652 | Check-in, consumos, conta e checkout | `Reserva.check_in`, `lancar_consumo`, `checkout`, `extrato` |
| `PaginaHospedes` | `app.py`, linha 426 | Cadastro e exclusão de hóspedes | `Hotel.cadastrar_hospede`, `excluir_hospede` |
| `PaginaQuartos` | `app.py`, linha 465 | Cadastro, diária e exclusão de quartos | `Hotel.cadastrar_quarto`, `excluir_quarto`, `Quarto.diaria` |
| `PaginaServicos` | `app.py`, linha 516 | Catálogo de extras | `Hotel.cadastrar_servico`, `excluir_servico` |
| `PaginaAnalise` | `app.py`, linha 816 | Indicadores e gráficos | `Analise.faturamento_total`, `taxa_ocupacao`, `faturamento_por_mes`... |

## Janela principal: `Aplicacao` (`app.py`, linha 931)
1. Cria o menu lateral a partir da lista `PAGINAS` (`app.py`, linha 935).
2. Cria **uma página de cada** e coloca todas no mesmo lugar, uma sobre a outra.
3. `mostrar(indice)` (`app.py`, linha 1015) traz a escolhida para a frente e chama o `atualizar()` dela.
4. No fim do arquivo, `if __name__ == "__main__":` carrega o `Hotel` do JSON e abre a janela.

## Componentes reaproveitados
| Classe | Linha | Para que serve |
|---|---|---|
| `Tabela` | `app.py`, linha 117 | Tabela com rolagem. `preencher(...)` coloca os dados e `selecionado()` diz a linha clicada |
| `Cartao` | `app.py`, linha 154 | Quadro com borda e título |
| `Indicador` | `app.py`, linha 171 | Cartão de número (herda de `Cartao`) |
| `Formulario` | `app.py`, linha 210 | Organiza rótulos e campos de texto |
| `Grafico` | `app.py`, linha 764 | Gráfico de barras desenhado no `Canvas` |
| `limitar_entrada` | `app.py`, linha 190 | Limite de caracteres e máscara (CPF, telefone) enquanto digita |

## O que dizer ao professor sobre o `app.py`
> "As telas só recebem dados e mostram resultados. Cada tela é uma classe que herda de `Pagina`, chama
> métodos do `Hotel` e atualiza a tabela. As regras e os cálculos não estão aqui: estão no `modelos.py`.
> Por isso, trocar o visual não mudou nenhuma regra."

Prova disso: o projeto tem **duas versões de telas** (`app.py` e `app_classico.py`) que usam exatamente as mesmas
classes do `modelos.py`.
