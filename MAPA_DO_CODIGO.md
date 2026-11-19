# Mapa do código: onde está cada coisa

Este mapa serve para responder **"em que parte do código está isso?"** sem consultar nada e **sem decorar número de linha**.

## A regra de ouro
> **O arquivo tem o nome da classe.** Check-in é da *Reserva*? Está em `modelos/reserva.py`.
> Cadastrar quarto é da tela de *Quartos*? Está em `telas/quartos.py`.

Basta pensar: **"de quem é isso?"** (de qual classe, ou de qual tela). O nome do arquivo responde.

---

## 1. As pastas do projeto
```
app.py ............ abre o sistema (carrega os dados e abre a janela)
modelos/ .......... AS REGRAS E OS CÁLCULOS   (uma classe por arquivo)
telas/ ............ AS TELAS                  (um arquivo por item do menu)
analise.py ........ a classe Analise (lê o JSON e calcula os indicadores)
tests/ ............ testes automáticos
dados_hotel.json .. os dados salvos
```
**Frase para dizer:** *"As regras ficam na pasta `modelos`, as telas na pasta `telas`. A tela só chama a regra."*

---

## 2. `modelos/`: uma classe por arquivo
| Arquivo | Classe | O que tem |
|---|---|---|
| `hospede.py` | `Hospede` | A pessoa. Valida nome, CPF/RG e telefone |
| `quarto.py` | `Quarto` | Número, categoria, capacidade e **diária** (encapsulamento) |
| `servico.py` | `Servico` | Item do catálogo (frigobar, lavanderia) |
| `consumo.py` | `Consumo` | Quanto de um serviço foi usado. Tem o **subtotal** |
| `reserva.py` | `Reserva` e `StatusReserva` | **O centro do sistema**: datas, conflito, check-in, checkout, total |
| `caixa.py` | `FechamentoCaixa` | O fechamento de caixa e o relatório |
| `hotel.py` | `Hotel` | Guarda tudo. Reservar, excluir, caixa, **salvar e carregar o JSON** |
| `erros.py` | `RegraNegocioErro` | O erro que as regras lançam |
| `formatos.py` | (funções) | Dinheiro (`Decimal`) e datas |
| `validacoes.py` | (funções) | Limites, validação de nome, CPF/RG, telefone e as máscaras |

Cada arquivo começa com um texto **"ONDE ESTÁ O QUÊ"** listando o que tem dentro.

---

## 3. "Em que parte do código está...?"  (pergunta → arquivo → método)

### Conceitos de orientação a objetos
| Se ele perguntar | Arquivo | Onde |
|---|---|---|
| **Associação** | `modelos/reserva.py` | `Reserva.__init__` (`self.hospede`, `self.quarto`) |
| **Composição** | `modelos/reserva.py` | `Reserva.__init__` (`self.consumos`) |
| **Encapsulamento** | `modelos/quarto.py` | `Quarto.diaria` (getter e setter) |
| **Herança** | `telas/pagina.py` | `Pagina` (as telas herdam dela); `Indicador` herda de `Cartao` em `telas/componentes.py` |
| **Cálculo dentro da classe** | `modelos/reserva.py` | `total`, `qtd_diarias`, `valor_hospedagem`, `valor_consumos` |
| **Subtotal do consumo** | `modelos/consumo.py` | `Consumo.subtotal` |
| **Lista fechada de situações** (`Enum`) | `modelos/reserva.py` | `StatusReserva` |
| **Erro das regras** | `modelos/erros.py` | `RegraNegocioErro` |

### Regras do hotel
| Se ele perguntar | Arquivo | Onde |
|---|---|---|
| **Conflito de datas** | `modelos/reserva.py` | `Reserva.conflita_com` |
| **O quarto está livre?** | `modelos/hotel.py` | `Hotel.quarto_livre` |
| **Quartos disponíveis** | `modelos/hotel.py` | `Hotel.quartos_disponiveis` |
| **Fazer uma reserva** | `modelos/hotel.py` | `Hotel.reservar` |
| **Check-in** | `modelos/reserva.py` | `Reserva.check_in` |
| **Lançar consumo** | `modelos/reserva.py` | `Reserva.lancar_consumo` |
| **Checkout** | `modelos/reserva.py` | `Reserva.checkout` |
| **Cancelar reserva** | `modelos/reserva.py` | `Reserva.cancelar` |
| **Preço contratado** | `modelos/reserva.py` | `Reserva.__init__` (`diaria_contratada`) |
| **Texto da conta** | `modelos/reserva.py` | `Reserva.extrato` |
| **Diária não pode ser negativa** | `modelos/quarto.py` | `Quarto.diaria` (setter) |
| **Quarto comporta o grupo?** | `modelos/quarto.py` | `Quarto.comporta` |
| **Fechar o caixa** | `modelos/hotel.py` e `modelos/caixa.py` | `Hotel.fechar_caixa` e a classe `FechamentoCaixa` |
| **Excluir cadastros** | `modelos/hotel.py` | `Hotel.excluir_hospede`, `excluir_quarto`, `excluir_servico` |
| **Números e mapa do Painel** | `modelos/hotel.py` | `Hotel.resumo` e `Hotel.situacao_quarto` |

### Validações e dinheiro
| Se ele perguntar | Arquivo | Onde |
|---|---|---|
| **Validar o nome** | `modelos/validacoes.py` | `validar_nome` |
| **Validar CPF/RG** | `modelos/validacoes.py` | `limpar_documento` |
| **Validar telefone** | `modelos/validacoes.py` | `limpar_telefone` |
| **Máscara de CPF/telefone ao digitar** | `modelos/validacoes.py` e `telas/componentes.py` | `mascara_documento`, `mascara_telefone` e `limitar_entrada` |
| **Limite de caracteres** | `modelos/validacoes.py` | `LIMITES` |
| **Dinheiro com `Decimal`** | `modelos/formatos.py` | `dinheiro` |

### Dados (JSON)
| Se ele perguntar | Arquivo | Onde |
|---|---|---|
| **Gravar os dados** | `modelos/hotel.py` | `Hotel.salvar` |
| **Ler os dados** | `modelos/hotel.py` | `Hotel.carregar` |
| **Dados da primeira vez (4 quartos, 4 serviços)** | `modelos/hotel.py` | `Hotel._dados_iniciais` |
| **Onde fica o arquivo de dados** | `telas/configuracao.py` | `ARQUIVO_DADOS` |
| **Cada classe vira dicionário** | cada arquivo de `modelos/` | `para_dict` |

### Análise de dados (`analise.py`)
| Se ele perguntar | Onde |
|---|---|
| **Ler o arquivo JSON** | `Analise.de_arquivo` |
| **Faturamento / ticket médio** | `Analise.faturamento_total`, `Analise.ticket_medio` |
| **Taxa de ocupação** | `Analise.taxa_ocupacao` |
| **Faturamento por mês / por quarto** | `Analise.faturamento_por_mes`, `Analise.faturamento_por_quarto` |
| **Ranking de hóspedes** | `Analise.ranking_hospedes` |
| **Exportar para o Excel** | `Analise.exportar_csv` |

### Telas
| Se ele perguntar | Arquivo | Onde |
|---|---|---|
| **Onde o programa começa** | `app.py` | o bloco `if __name__ == "__main__"` |
| **Como a mensagem de erro aparece na tela** | `telas/pagina.py` | `Pagina.executar` |
| **O menu lateral** | `telas/janela.py` | `Aplicacao` (a lista `PAGINAS`) |
| **A tabela / o gráfico** | `telas/componentes.py` / `telas/analise_dados.py` | `Tabela` / `Grafico` |

---

## 4. `telas/`: um arquivo por item do menu
| Item do menu | Arquivo | Classe |
|---|---|---|
| Operação > Painel | `painel.py` | `PaginaPainel` |
| Operação > Reservas | `reservas.py` | `PaginaReservas` |
| Operação > Hospedagem | `hospedagem.py` | `PaginaHospedagem` |
| Cadastros > Hóspedes | `hospedes.py` | `PaginaHospedes` |
| Cadastros > Quartos | `quartos.py` | `PaginaQuartos` |
| Cadastros > Serviços | `servicos.py` | `PaginaServicos` |
| Relatórios > Análise de dados | `analise_dados.py` | `PaginaAnalise` |

Outros: `janela.py` (a janela e o menu), `pagina.py` (a base de todas as telas), `componentes.py` (tabela, cartão, formulário, botão), `estilo.py` (cores), `configuracao.py` (onde ficam os arquivos).

---

## 5. "Qual botão chama o quê?"  (botão → método da tela → regra)
| Tela | Botão | Método da tela | A regra que ele chama |
|---|---|---|---|
| **Hóspedes** | Cadastrar hóspede | `cadastrar` | `Hotel.cadastrar_hospede` |
| | Excluir | `excluir` | `Hotel.excluir_hospede` |
| **Quartos** | Cadastrar quarto | `cadastrar` | `Hotel.cadastrar_quarto` |
| | Alterar diária do selecionado | `alterar_diaria` | `Quarto.diaria` (setter) |
| | Excluir | `excluir` | `Hotel.excluir_quarto` |
| **Serviços** | Cadastrar serviço | `cadastrar` | `Hotel.cadastrar_servico` |
| | Excluir | `excluir` | `Hotel.excluir_servico` |
| **Reservas** | Consultar quartos livres | `consultar` | `Hotel.quartos_disponiveis` |
| | **Confirmar reserva** | `reservar` | `Hotel.reservar` |
| | Cancelar reserva | `cancelar` | `Reserva.cancelar` |
| **Hospedagem** | Fazer check-in | `check_in` | `Reserva.check_in` |
| | Lançar | `lancar` | `Reserva.lancar_consumo` |
| | **Confirmar checkout** | `checkout` | `Reserva.checkout` |
| | (a conta na tela) | `mostrar_conta` | `Reserva.extrato` |
| **Painel** | **Fechar caixa** | `fechar_caixa` | `Hotel.fechar_caixa` |
| **Análise de dados** | Abrir JSON… | `abrir_arquivo` | `Analise.de_arquivo` |
| | Exportar CSV | `exportar` | `Analise.exportar_csv` |

---

## 6. Como uma ação percorre o código
```
Clique em "Confirmar reserva"
   │
   ▼
telas/reservas.py ........ PaginaReservas.reservar   (lê o que foi digitado)
   │
   ▼
modelos/hotel.py ......... Hotel.reservar            (confere se o quarto está livre)
   │        └──► Hotel.quarto_livre ──► Reserva.conflita_com   (regra das datas)
   ▼
modelos/reserva.py ....... Reserva(...)              (cria a reserva; recusa dados inválidos)
   │
   ▼
modelos/hotel.py ......... Hotel.salvar              (grava no dados_hotel.json)

Se alguma regra falhar → RegraNegocioErro → telas/pagina.py (Pagina.executar) mostra a mensagem.
```
**Todo botão segue o mesmo caminho:** tela → regra → JSON.

---

## 7. Se esquecer onde está
| Atalho (VS Code) | O que faz |
|---|---|
| **Ctrl+P** | Abre um arquivo pelo nome. Digite `reserva` e Enter |
| **Ctrl+Shift+O** | Lista as classes e métodos do arquivo aberto |
| **Ctrl+Shift+F** | Procura um texto em todos os arquivos (o nome de um botão, uma mensagem de erro) |

Como os arquivos têm o nome da classe, **Ctrl+P + o nome da classe** leva ao lugar certo em 3 segundos.
