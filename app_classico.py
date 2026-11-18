"""
Telas do Sistema de Hotel (Tkinter + ttk).

A interface só recebe dados e mostra resultados.
Todas as regras e cálculos ficam nas classes de modelos.py.

Executar:  python app.py
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox

from modelos import (Hotel, RegraNegocioErro, StatusReserva, LIMITES,
                     mascara_documento, mascara_telefone,
                     ler_data, formatar_data, formatar_moeda)

ARQUIVO_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados_hotel.json")


# ---------------------------------------------------------------------------
# Componentes reutilizáveis
# ---------------------------------------------------------------------------

class Tabela(ttk.Frame):
    """Treeview com barra de rolagem."""

    def __init__(self, master, colunas, larguras=None, altura=10):
        super().__init__(master)
        self.tree = ttk.Treeview(self, columns=colunas, show="headings",
                                 height=altura, selectmode="browse")
        for i, col in enumerate(colunas):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=(larguras[i] if larguras else 120), anchor="w")
        barra = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=barra.set)
        self.tree.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    def preencher(self, linhas):
        """linhas: lista de (id, (valores...))"""
        self.tree.delete(*self.tree.get_children())
        for iid, valores in linhas:
            self.tree.insert("", "end", iid=str(iid), values=valores)

    def selecionado(self):
        sel = self.tree.selection()
        return sel[0] if sel else None


def limitar_entrada(entrada, maximo, permitido=None, formatador=None):
    """Impede digitar além do limite e caracteres não permitidos.
    Com 'formatador', também aplica a máscara enquanto a pessoa digita (CPF, telefone)."""
    def corrigir(_evento=None):
        atual = entrada.get()
        if formatador:
            novo = formatador(atual)
        else:
            novo = "".join(c for c in atual if permitido(c)) if permitido else atual
        novo = novo[:maximo]
        if novo != atual:
            entrada.delete(0, "end")
            entrada.insert(0, novo)
    entrada.bind("<KeyRelease>", corrigir, add="+")


def campo(master, rotulo, linha, largura=25, coluna=0, limite=None, permitido=None, formatador=None):
    ttk.Label(master, text=rotulo).grid(row=linha, column=coluna, sticky="w", padx=4, pady=3)
    entrada = ttk.Entry(master, width=largura)
    entrada.grid(row=linha, column=coluna + 1, sticky="w", padx=4, pady=3)
    if limite:
        limitar_entrada(entrada, limite, permitido, formatador)
    return entrada


class Aba(ttk.Frame):
    """Classe base das abas: guarda o hotel e trata erros de regra de negócio."""

    def __init__(self, master, hotel: Hotel):
        super().__init__(master, padding=10)
        self.hotel = hotel

    def atualizar(self):
        pass

    def botao_excluir(self, tabela, nome, excluir):
        """Botão 'Excluir': pede confirmação e chama o método de exclusão do Hotel (que aplica as regras)."""
        def clicar():
            chave = tabela.selecionado()
            if not chave:
                messagebox.showinfo("Atenção", "Selecione um item na tabela.")
                return
            if messagebox.askyesno("Excluir", f"Excluir {nome(chave)}? Essa ação não pode ser desfeita."):
                self.executar(lambda: excluir(chave), "Cadastro excluído.")
        ttk.Button(self, text="Excluir selecionado", command=clicar).pack(anchor="e", pady=(6, 0))

    def executar(self, acao, sucesso=None):
        """Executa uma operação e mostra o erro amigável se uma regra for violada."""
        try:
            resultado = acao()
        except RegraNegocioErro as e:
            messagebox.showwarning("Operação não permitida", str(e))
            return None
        except (ValueError, KeyError) as e:
            messagebox.showwarning("Dados inválidos", f"Verifique os campos informados.\n({e})")
            return None
        if sucesso:
            messagebox.showinfo("Sucesso", sucesso)
        self.atualizar()
        return resultado


# ---------------------------------------------------------------------------
# Abas
# ---------------------------------------------------------------------------

class AbaPainel(Aba):
    def __init__(self, master, hotel):
        super().__init__(master, hotel)
        self.cards = ttk.Frame(self)
        self.cards.pack(fill="x", pady=(0, 10))
        self.valores = {}
        for i, (chave, titulo) in enumerate([("hosp", "Em hospedagem"),
                                             ("entradas", "Entradas hoje"),
                                             ("saidas", "Saídas hoje"),
                                             ("ocupacao", "Ocupação hoje"),
                                             ("fat", "Faturamento (concluídas)")]):
            box = ttk.LabelFrame(self.cards, text=titulo, padding=10)
            box.grid(row=0, column=i, padx=5, sticky="nsew")
            self.cards.columnconfigure(i, weight=1)
            lbl = ttk.Label(box, text="-", font=("Segoe UI", 20, "bold"))
            lbl.pack()
            self.valores[chave] = lbl

        ttk.Label(self, text="Hospedagens em andamento", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.tabela = Tabela(self, ("Reserva", "Hóspede", "Quarto", "Entrada", "Saída", "Conta parcial"),
                             (70, 220, 120, 100, 100, 130))
        self.tabela.pack(fill="both", expand=True)

    def atualizar(self):
        r = self.hotel.resumo()
        self.valores["hosp"]["text"] = len(r["em_hospedagem"])
        self.valores["entradas"]["text"] = len(r["entradas_hoje"])
        self.valores["saidas"]["text"] = len(r["saidas_hoje"])
        self.valores["ocupacao"]["text"] = f"{r['ocupacao']:.0f}%"
        self.valores["fat"]["text"] = formatar_moeda(r["faturamento"])
        self.tabela.preencher([(res.id, (res.id, res.hospede.nome, res.quarto.numero,
                                         formatar_data(res.entrada), formatar_data(res.saida),
                                         formatar_moeda(res.total)))
                               for res in r["em_hospedagem"]])


class AbaHospedes(Aba):
    def __init__(self, master, hotel):
        super().__init__(master, hotel)
        form = ttk.LabelFrame(self, text="Novo hóspede", padding=8)
        form.pack(fill="x")
        self.nome = campo(form, "Nome:", 0, 35, limite=LIMITES["nome"])
        self.doc = campo(form, "Documento (CPF 11 dígitos / RG):", 1, limite=LIMITES["documento"],
                         formatador=mascara_documento)
        self.tel = campo(form, "Telefone (com DDD):", 2, limite=LIMITES["telefone"],
                         formatador=mascara_telefone)
        ttk.Button(form, text="Cadastrar", style="Accent.TButton", command=self.cadastrar).grid(row=3, column=1, sticky="w", padx=4, pady=6)

        self.tabela = Tabela(self, ("ID", "Nome", "Documento", "Telefone"), (50, 260, 160, 140))
        self.tabela.pack(fill="both", expand=True, pady=(10, 0))
        self.botao_excluir(self.tabela, lambda k: self.hotel.hospedes[int(k)].nome,
                           lambda k: self.hotel.excluir_hospede(int(k)))

    def cadastrar(self):
        h = self.executar(lambda: self.hotel.cadastrar_hospede(self.nome.get(), self.doc.get(), self.tel.get()),
                          "Hóspede cadastrado.")
        if h:
            for e in (self.nome, self.doc, self.tel):
                e.delete(0, "end")

    def atualizar(self):
        self.tabela.preencher([(h.id, (h.id, h.nome, h.documento_formatado, h.telefone_formatado))
                               for h in self.hotel.hospedes.values()])


class AbaQuartos(Aba):
    def __init__(self, master, hotel):
        super().__init__(master, hotel)
        form = ttk.LabelFrame(self, text="Novo quarto / alterar diária", padding=8)
        form.pack(fill="x")
        self.numero = campo(form, "Número:", 0, 10, limite=LIMITES["numero_quarto"])
        self.categoria = campo(form, "Categoria:", 1, limite=LIMITES["categoria"])
        self.capacidade = campo(form, "Capacidade (pessoas):", 2, 10, limite=2,
                                permitido=lambda c: c.isdigit())
        self.diaria = campo(form, "Diária (R$):", 3, 12)
        botoes = ttk.Frame(form)
        botoes.grid(row=4, column=1, sticky="w", pady=6)
        ttk.Button(botoes, text="Cadastrar", style="Accent.TButton", command=self.cadastrar).pack(side="left", padx=4)
        ttk.Button(botoes, text="Alterar diária do selecionado", command=self.alterar_diaria).pack(side="left")

        self.tabela = Tabela(self, ("Número", "Categoria", "Capacidade", "Diária atual"), (80, 180, 100, 120))
        self.tabela.pack(fill="both", expand=True, pady=(10, 0))
        self.botao_excluir(self.tabela, lambda k: f"o quarto {k}", lambda k: self.hotel.excluir_quarto(k))

    def cadastrar(self):
        self.executar(lambda: self.hotel.cadastrar_quarto(self.numero.get(), self.categoria.get(),
                                                          int(self.capacidade.get()), self.diaria.get()),
                      "Quarto cadastrado.")

    def alterar_diaria(self):
        numero = self.tabela.selecionado()
        if not numero:
            messagebox.showinfo("Atenção", "Selecione um quarto na tabela.")
            return

        def acao():
            self.hotel.quartos[numero].diaria = self.diaria.get()
            self.hotel.salvar()
        self.executar(acao, "Diária alterada. Reservas já feitas mantêm a diária contratada.")

    def atualizar(self):
        self.tabela.preencher([(q.numero, (q.numero, q.categoria, q.capacidade, formatar_moeda(q.diaria)))
                               for q in self.hotel.quartos.values()])


class AbaServicos(Aba):
    def __init__(self, master, hotel):
        super().__init__(master, hotel)
        form = ttk.LabelFrame(self, text="Novo serviço / extra", padding=8)
        form.pack(fill="x")
        self.descricao = campo(form, "Descrição:", 0, 35, limite=LIMITES["descricao"])
        self.preco = campo(form, "Preço (R$):", 1, 12)
        ttk.Button(form, text="Cadastrar", style="Accent.TButton", command=self.cadastrar).grid(row=2, column=1, sticky="w", padx=4, pady=6)

        self.tabela = Tabela(self, ("ID", "Descrição", "Preço"), (50, 300, 120))
        self.tabela.pack(fill="both", expand=True, pady=(10, 0))
        self.botao_excluir(self.tabela, lambda k: f"'{self.hotel.servicos[int(k)].descricao}'",
                           lambda k: self.hotel.excluir_servico(int(k)))

    def cadastrar(self):
        self.executar(lambda: self.hotel.cadastrar_servico(self.descricao.get(), self.preco.get()),
                      "Serviço cadastrado.")

    def atualizar(self):
        self.tabela.preencher([(s.id, (s.id, s.descricao, formatar_moeda(s.preco)))
                               for s in self.hotel.servicos.values()])


class AbaReservas(Aba):
    def __init__(self, master, hotel):
        super().__init__(master, hotel)
        topo = ttk.Frame(self)
        topo.pack(fill="x")

        form = ttk.LabelFrame(topo, text="1. Pesquisar disponibilidade", padding=8)
        form.pack(side="left", fill="y")
        ttk.Label(form, text="Hóspede:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.hospede = ttk.Combobox(form, width=32, state="readonly")
        self.hospede.grid(row=0, column=1, padx=4, pady=3)
        self.entrada = campo(form, "Entrada (dd/mm/aaaa):", 1, 14)
        self.saida = campo(form, "Saída (dd/mm/aaaa):", 2, 14)
        self.pessoas = campo(form, "Pessoas:", 3, 6)
        ttk.Button(form, text="Consultar quartos livres", style="Accent.TButton", command=self.consultar).grid(
            row=4, column=1, sticky="w", padx=4, pady=6)

        disp = ttk.LabelFrame(topo, text="2. Escolher quarto", padding=8)
        disp.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.disponiveis = Tabela(disp, ("Quarto", "Categoria", "Cap.", "Diária", "Valor estimado"),
                                  (60, 100, 50, 90, 120), altura=5)
        self.disponiveis.pack(fill="both", expand=True)
        ttk.Button(disp, text="Confirmar reserva", style="Accent.TButton", command=self.reservar).pack(anchor="e", pady=(6, 0))

        lista = ttk.LabelFrame(self, text="Reservas", padding=8)
        lista.pack(fill="both", expand=True, pady=(10, 0))
        self.tabela = Tabela(lista, ("Nº", "Hóspede", "Quarto", "Entrada", "Saída",
                                     "Pessoas", "Diárias", "Diária contratada", "Situação"),
                             (40, 180, 60, 90, 90, 60, 60, 120, 110))
        self.tabela.pack(fill="both", expand=True)
        ttk.Button(lista, text="Cancelar reserva selecionada", command=self.cancelar).pack(anchor="e", pady=(6, 0))
        self._periodo = None

    def _ler_formulario(self):
        entrada, saida = ler_data(self.entrada.get()), ler_data(self.saida.get())
        pessoas = int(self.pessoas.get())
        return entrada, saida, pessoas

    def consultar(self):
        def acao():
            entrada, saida, pessoas = self._ler_formulario()
            quartos = self.hotel.quartos_disponiveis(entrada, saida, pessoas)
            noites = (saida - entrada).days
            self.disponiveis.preencher([(q.numero, (q.numero, q.categoria, q.capacidade,
                                                    formatar_moeda(q.diaria),
                                                    formatar_moeda(q.diaria * noites)))
                                        for q in quartos])
            self._periodo = (entrada, saida, pessoas)
            if not quartos:
                raise RegraNegocioErro("Nenhum quarto disponível para esse período e quantidade de pessoas.")
        self.executar(acao)

    def reservar(self):
        numero = self.disponiveis.selecionado()
        if not self.hospede.get() or not numero or not self._periodo:
            messagebox.showinfo("Atenção", "Selecione o hóspede, consulte e escolha um quarto.")
            return
        hospede_id = int(self.hospede.get().split(" - ")[0])

        def acao():
            # Relê o formulário: se o usuário mudou as datas, a regra de conflito valida de novo.
            entrada, saida, pessoas = self._ler_formulario()
            r = self.hotel.reservar(hospede_id, numero, entrada, saida, pessoas)
            self.disponiveis.preencher([])
            return r
        r = self.executar(acao)
        if r:
            messagebox.showinfo("Reserva confirmada",
                                f"Reserva nº {r.id}: {r.qtd_diarias} diária(s), "
                                f"total da hospedagem {formatar_moeda(r.valor_hospedagem)}.")

    def cancelar(self):
        rid = self.tabela.selecionado()
        if not rid:
            messagebox.showinfo("Atenção", "Selecione uma reserva.")
            return
        if messagebox.askyesno("Cancelar", f"Cancelar a reserva nº {rid}?"):
            def acao():
                self.hotel.reservas[int(rid)].cancelar()
                self.hotel.salvar()
            self.executar(acao, "Reserva cancelada. O quarto foi liberado.")

    def atualizar(self):
        self.hospede["values"] = [f"{h.id} - {h.nome}" for h in self.hotel.hospedes.values()]
        self.tabela.preencher([(r.id, (r.id, r.hospede.nome, r.quarto.numero,
                                       formatar_data(r.entrada), formatar_data(r.saida),
                                       r.pessoas, r.qtd_diarias,
                                       formatar_moeda(r.diaria_contratada), r.status.value))
                               for r in sorted(self.hotel.reservas.values(), key=lambda r: r.entrada)])


class AbaHospedagem(Aba):
    def __init__(self, master, hotel):
        super().__init__(master, hotel)
        esquerda = ttk.Frame(self)
        esquerda.pack(side="left", fill="both", expand=True)

        ttk.Label(esquerda, text="Reservas confirmadas e em hospedagem",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.tabela = Tabela(esquerda, ("Nº", "Hóspede", "Quarto", "Período", "Situação"),
                             (40, 150, 55, 180, 115))
        self.tabela.pack(fill="both", expand=True)
        self.tabela.tree.bind("<<TreeviewSelect>>", lambda e: self.mostrar_extrato())
        ttk.Button(esquerda, text="Fazer check-in", style="Accent.TButton", command=self.check_in).pack(anchor="w", pady=6)

        consumo = ttk.LabelFrame(esquerda, text="Lançar consumo", padding=8)
        consumo.pack(fill="x")
        ttk.Label(consumo, text="Serviço:").grid(row=0, column=0, sticky="w", padx=4)
        self.servico = ttk.Combobox(consumo, width=32, state="readonly")
        self.servico.grid(row=0, column=1, padx=4, pady=3)
        self.qtd = campo(consumo, "Quantidade:", 1, 6)
        ttk.Button(consumo, text="Lançar", style="Accent.TButton", command=self.lancar).grid(row=2, column=1, sticky="w", padx=4, pady=6)

        direita = ttk.LabelFrame(self, text="Fechamento da conta", padding=8)
        direita.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.extrato = tk.Text(direita, width=56, height=22, font=("Consolas", 11), state="disabled",
                               relief="flat", padx=10, pady=10)
        self.extrato.pack(fill="both", expand=True)
        ttk.Button(direita, text="Confirmar checkout", style="Accent.TButton", command=self.checkout).pack(anchor="e", pady=(6, 0))

    def _reserva(self):
        rid = self.tabela.selecionado()
        if not rid:
            messagebox.showinfo("Atenção", "Selecione uma reserva.")
            return None
        return self.hotel.reservas[int(rid)]

    def check_in(self):
        r = self._reserva()
        if r:
            self.executar(lambda: (r.check_in(), self.hotel.salvar()), f"Check-in da reserva nº {r.id} realizado.")

    def lancar(self):
        r = self._reserva()
        if not r:
            return
        if not self.servico.get():
            messagebox.showinfo("Atenção", "Escolha um serviço.")
            return
        servico = self.hotel.servicos[int(self.servico.get().split(" - ")[0])]
        self.executar(lambda: (r.lancar_consumo(servico, int(self.qtd.get())), self.hotel.salvar()))
        self.qtd.delete(0, "end")

    def checkout(self):
        r = self._reserva()
        if not r:
            return
        if r.status == StatusReserva.EM_HOSPEDAGEM and not messagebox.askyesno(
                "Checkout", f"Confirmar checkout com total de {formatar_moeda(r.total)}?"):
            return
        self.executar(lambda: (r.checkout(), self.hotel.salvar()),
                      f"Hospedagem concluída. Total pago: {formatar_moeda(r.total)}")

    def mostrar_extrato(self):
        rid = self.tabela.selecionado()
        texto = self.hotel.reservas[int(rid)].extrato() if rid else ""
        self.extrato.configure(state="normal")
        self.extrato.delete("1.0", "end")
        self.extrato.insert("1.0", texto)
        self.extrato.configure(state="disabled")

    def atualizar(self):
        selecionado = self.tabela.selecionado()
        visiveis = [r for r in self.hotel.reservas.values() if r.ativa]
        self.tabela.preencher([(r.id, (r.id, r.hospede.nome, r.quarto.numero,
                                       f"{formatar_data(r.entrada)} a {formatar_data(r.saida)}",
                                       r.status.value))
                               for r in sorted(visiveis, key=lambda r: r.entrada)])
        self.servico["values"] = [f"{s.id} - {s}" for s in self.hotel.servicos.values()]
        if selecionado and self.tabela.tree.exists(selecionado):
            self.tabela.tree.selection_set(selecionado)
        self.mostrar_extrato()


# ---------------------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------------------

class Aplicacao(tk.Tk):
    def __init__(self, hotel: Hotel):
        super().__init__()
        self.hotel = hotel
        self.title(f"{hotel.nome} - Sistema de Recepção")
        self.geometry("1150x700")

        # Cabeçalho com o nome do hotel e o botão de tema
        topo = ttk.Frame(self, padding=(14, 10, 14, 0))
        topo.pack(fill="x")
        ttk.Label(topo, text=f"🏨  {hotel.nome}", font=("Segoe UI", 18, "bold")).pack(side="left")
        self.botao_tema = ttk.Button(topo, command=self.alternar_tema)
        self.botao_tema.pack(side="right")
        self.escuro = False
        self.aplicar_tema()

        abas = ttk.Notebook(self)
        abas.pack(fill="both", expand=True, padx=12, pady=12)
        self.abas = []
        for titulo, classe in [("Painel", AbaPainel), ("Hóspedes", AbaHospedes),
                               ("Quartos", AbaQuartos), ("Serviços", AbaServicos),
                               ("Reservas", AbaReservas), ("Hospedagem e Checkout", AbaHospedagem)]:
            aba = classe(abas, hotel)
            abas.add(aba, text=titulo)
            self.abas.append(aba)
            aba.atualizar()
        # Ao trocar de aba, recarrega os dados (ex.: hóspede novo aparece na tela de reservas)
        abas.bind("<<NotebookTabChanged>>",
                  lambda e: self.abas[abas.index(abas.select())].atualizar())

    def aplicar_tema(self):
        """Usa o tema moderno Sun Valley (pip install sv-ttk).
        Se a biblioteca não estiver instalada, usa o tema padrão 'clam'."""
        try:
            import sv_ttk
            sv_ttk.set_theme("dark" if self.escuro else "light")
        except ImportError:
            ttk.Style(self).theme_use("clam")
        self.botao_tema["text"] = "☀  Tema claro" if self.escuro else "🌙  Tema escuro"
        # O tk.Text (extrato) não é um widget ttk: as cores são definidas à mão
        fundo, texto = ("#1c1c1c", "#e6e6e6") if self.escuro else ("#ffffff", "#1a1a1a")
        for aba in getattr(self, "abas", []):
            if isinstance(aba, AbaHospedagem):
                aba.extrato.configure(bg=fundo, fg=texto, insertbackground=texto)

    def alternar_tema(self):
        self.escuro = not self.escuro
        self.aplicar_tema()


if __name__ == "__main__":
    Aplicacao(Hotel.carregar(ARQUIVO_DADOS)).mainloop()
