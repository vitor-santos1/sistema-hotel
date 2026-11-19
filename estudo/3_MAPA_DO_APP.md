# Mapa das telas (pasta `telas/`)

As telas ficam na pasta `telas/`, **um arquivo por item do menu**. Todas seguem o mesmo molde:
entendendo uma, as outras são variações.

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
- **`self.executar(...)`** (em `telas/pagina.py`) roda a ação. Se uma regra for violada, mostra a mensagem em vez de quebrar.
- **`atualizar()`** é chamado toda vez que a pessoa abre a tela.

## Cada tela, o arquivo e o que ela chama
| Item do menu | Arquivo | Classe | O que mostra | Métodos que ela chama |
|---|---|---|---|---|
| Painel | `telas/painel.py` | `PaginaPainel` | Números do dia, mapa de quartos, caixa | `Hotel.resumo`, `situacao_quarto`, `fechar_caixa` |
| Reservas | `telas/reservas.py` | `PaginaReservas` | Consulta de quartos livres e lista de reservas | `Hotel.quartos_disponiveis`, `reservar`, `Reserva.cancelar` |
| Hospedagem | `telas/hospedagem.py` | `PaginaHospedagem` | Check-in, consumos, conta e checkout | `Reserva.check_in`, `lancar_consumo`, `checkout`, `extrato` |
| Hóspedes | `telas/hospedes.py` | `PaginaHospedes` | Cadastro e exclusão de hóspedes | `Hotel.cadastrar_hospede`, `excluir_hospede` |
| Quartos | `telas/quartos.py` | `PaginaQuartos` | Cadastro, diária e exclusão de quartos | `Hotel.cadastrar_quarto`, `excluir_quarto`, `Quarto.diaria` |
| Serviços | `telas/servicos.py` | `PaginaServicos` | Catálogo de extras | `Hotel.cadastrar_servico`, `excluir_servico` |
| Análise de dados | `telas/analise_dados.py` | `PaginaAnalise` | Indicadores e gráficos | `Analise.faturamento_total`, `taxa_ocupacao`, `faturamento_por_mes`... |

## Janela principal: `Aplicacao` (`telas/janela.py`)
1. Cria o menu lateral a partir da lista `PAGINAS`.
2. Cria **uma página de cada** e coloca todas no mesmo lugar, uma sobre a outra.
3. `mostrar(indice)` traz a escolhida para a frente e chama o `atualizar()` dela.
4. No `app.py`, o bloco `if __name__ == "__main__":` carrega o `Hotel` do JSON e abre a janela.

## Peças reaproveitadas
| Classe | Arquivo | Para que serve |
|---|---|---|
| `Tabela` | `telas/componentes.py` | Tabela com rolagem. `preencher(...)` coloca os dados e `selecionado()` diz a linha clicada |
| `Cartao` | `telas/componentes.py` | Quadro com borda e título |
| `Indicador` | `telas/componentes.py` | Cartão de número (herda de `Cartao`) |
| `Formulario` | `telas/componentes.py` | Organiza rótulos e campos de texto |
| `limitar_entrada` | `telas/componentes.py` | Limite de caracteres e máscara (CPF, telefone) enquanto digita |
| `Grafico` | `telas/analise_dados.py` | Gráfico de barras desenhado no `Canvas` |

## O que dizer ao professor sobre as telas
> "As telas só recebem dados e mostram resultados. Cada tela é uma classe que herda de `Pagina`, chama
> métodos do `Hotel` e atualiza a tabela. As regras e os cálculos não estão aqui: estão na pasta `modelos/`.
> Por isso, trocar o visual não mudou nenhuma regra."

Prova disso: o projeto tem **duas versões de telas** (a pasta `telas/` e o `app_classico.py`) que usam exatamente as mesmas
classes de `modelos/`.
