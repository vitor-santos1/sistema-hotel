# Sistema de Hotel (versão simples)

Seminário de Paradigmas: **Orientação a Objetos**, em Python. Uma recepção de hotel: cadastrar hóspedes e quartos,
reservar sem conflito de datas, fazer check-in, lançar consumos e fechar a conta no checkout.

## Como executar
Só precisa do **Python 3** (o Tkinter já vem com ele). Não instala mais nada.

    python app.py            (ou dois cliques em executar.bat no Windows)
    python tests/teste_regras.py   (confere as regras)

Os dados ficam em `hotel.json`, criado na primeira execução. Apague esse arquivo para começar do zero.

## Onde está cada coisa (são só 2 arquivos)
| Arquivo | O que tem |
|---|---|
| `modelos.py` | **Todas as regras e cálculos.** As classes `Hospede`, `Quarto`, `Servico`, `Consumo`, `Reserva` e `Hotel` |
| `app.py` | **As telas** (uma classe para cada aba). Só mostram e chamam o `modelos.py` |
| `tests/teste_regras.py` | O roteiro da apresentação, conferido automaticamente |

### Dentro do `modelos.py`
| Classe | O que faz |
|---|---|
| `Hospede` | A pessoa (nome, documento, telefone) |
| `Quarto` | Número, categoria, capacidade e **diária** (o setter valida: encapsulamento) |
| `Consumo` | Um extra usado (água, lavanderia). `subtotal` = quantidade x preço. O catálogo é a constante `SERVICOS` |
| `Reserva` | **O centro:** liga hóspede e quarto, guarda os consumos, calcula o `total` e tem `conflita_com`, `check_in`, `lancar_consumo`, `checkout`, `cancelar` |
| `Hotel` | Guarda tudo, confere se o quarto está livre (`quarto_livre`), faz a `reservar` e grava (`salvar`) e lê (`carregar`) o JSON |

### Como uma tela funciona
`botão da tela  →  método da tela (app.py)  →  método do Hotel ou da Reserva (modelos.py)  →  salva no JSON`

Se uma regra for violada, o `modelos.py` lança `RegraNegocioErro` e a função `executar` do `app.py` mostra a mensagem.

## Orientação a objetos no projeto
- **Associação:** a `Reserva` guarda um `Hospede` e um `Quarto`.
- **Composição:** a `Reserva` guarda a lista de `Consumo`.
- **Cálculos dentro das classes:** `Consumo.subtotal`, `Reserva.qtd_diarias`, `valor_hospedagem`, `valor_consumos` e `total`.
- **Encapsulamento:** `Quarto.diaria` só muda pelo setter, que recusa valor zero ou negativo.
- **Herança:** as telas herdam de `ttk.Frame` e a janela herda de `tk.Tk` (classes do Tkinter).
- **`Decimal`** para dinheiro (o `float` erra contas) e **preço contratado** guardado na reserva.

### A regra de datas (`Reserva.conflita_com`)
Há conflito quando a nova entrada é **antes** da saída existente **e** a nova saída é **depois** da entrada existente.
A comparação usa `<` (e não `<=`), então quem sai dia 22 libera o quarto para quem entra dia 22.

## Roteiro da demonstração
1. **Hóspedes:** cadastrar "Maria Silva".
2. **Reservas:** Maria, 19/11/2026 a 22/11/2026, 2 pessoas → Consultar → quarto 101 → Reservar.
3. Consultar 20/11/2026 a 23/11/2026: o 101 **não aparece** (conflito).
4. **Hospedagem:** selecionar a reserva → Fazer check-in.
5. Lançar 4 x Água e 1 x Lavanderia. A conta mostra **R$ 600,00** (3 x 180 + 40 + 20).
6. Fazer checkout.
