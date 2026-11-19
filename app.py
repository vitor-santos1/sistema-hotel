"""
TELAS do Sistema de Hotel (Tkinter).

As telas só recebem dados e mostram resultados. Toda regra e todo cálculo estão em modelos.py.
Cada tela é uma classe, e todas seguem o mesmo molde:
    __init__   monta os campos, botões e a tabela
    um método para cada botão (chama o Hotel)
    atualizar  recarrega a tabela com os dados do Hotel

Executar:  python app.py
"""

import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from modelos import CONFIRMADA, EM_HOSPEDAGEM, Hotel, RegraNegocioErro, reais

ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotel.json")


# ---------------------------------------------------------------------------
# Peças usadas por todas as telas
# ---------------------------------------------------------------------------

def campo(pai, rotulo, linha, largura=25):
    """Um rótulo com uma caixa de texto ao lado. Devolve a caixa de texto."""
    ttk.Label(pai, text=rotulo).grid(row=linha, column=0, sticky="w", padx=4, pady=3)
    entrada = ttk.Entry(pai, width=largura)
    entrada.grid(row=linha, column=1, sticky="w", padx=4, pady=3)
    return entrada


def tabela(pai, colunas, larguras, altura=6):
    """Uma tabela com os títulos das colunas. Devolve a tabela."""
    arvore = ttk.Treeview(pai, columns=colunas, show="headings", height=altura, selectmode="browse")
    for coluna, largura in zip(colunas, larguras):
        arvore.heading(coluna, text=coluna)
        arvore.column(coluna, width=largura)
    arvore.pack(fill="both", expand=True, pady=6)
    return arvore


def preencher(arvore, linhas):
    """Troca o conteúdo da tabela. linhas = lista de (chave, (valores...))."""
    arvore.delete(*arvore.get_children())
    for chave, valores in linhas:
        arvore.insert("", "end", iid=str(chave), values=valores)


def ler_data(texto):
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        raise RegraNegocioErro("Data inválida. Use o formato dd/mm/aaaa.")


def executar(acao):
    """A PONTE ENTRE A TELA E AS REGRAS: roda a ação. Se uma regra for violada
    (RegraNegocioErro), mostra a mensagem em vez de quebrar. Devolve True se deu certo."""
    try:
        acao()
        return True
    except RegraNegocioErro as erro:
        messagebox.showwarning("Não foi possível", str(erro))
    except ValueError:
        messagebox.showwarning("Dados inválidos", "Confira os campos preenchidos.")
    return False


def limpar(*campos):
    for c in campos:
        c.delete(0, "end")


# ---------------------------------------------------------------------------
# As telas (uma classe para cada aba)
# ---------------------------------------------------------------------------

class TelaHospedes(ttk.Frame):
    def __init__(self, pai, hotel):
        super().__init__(pai, padding=10)
        self.hotel = hotel
        formulario = ttk.LabelFrame(self, text="Novo hóspede", padding=8)
        formulario.pack(fill="x")
        self.nome = campo(formulario, "Nome:", 0, 35)
        self.documento = campo(formulario, "Documento:", 1)
        self.telefone = campo(formulario, "Telefone:", 2)
        ttk.Button(formulario, text="Cadastrar", command=self.cadastrar).grid(row=3, column=1, sticky="w", pady=6)
        self.lista = tabela(self, ("ID", "Nome", "Documento", "Telefone"), (50, 280, 150, 150))

    def cadastrar(self):
        if executar(lambda: self.hotel.cadastrar_hospede(self.nome.get(), self.documento.get(), self.telefone.get())):
            limpar(self.nome, self.documento, self.telefone)
            self.atualizar()

    def atualizar(self):
        preencher(self.lista, [(h.id, (h.id, h.nome, h.documento, h.telefone)) for h in self.hotel.hospedes.values()])


class TelaQuartos(ttk.Frame):
    def __init__(self, pai, hotel):
        super().__init__(pai, padding=10)
        self.hotel = hotel
        formulario = ttk.LabelFrame(self, text="Novo quarto", padding=8)
        formulario.pack(fill="x")
        self.numero = campo(formulario, "Número:", 0, 10)
        self.categoria = campo(formulario, "Categoria:", 1)
        self.capacidade = campo(formulario, "Capacidade (pessoas):", 2, 10)
        self.diaria = campo(formulario, "Diária (R$):", 3, 12)
        botoes = ttk.Frame(formulario)
        botoes.grid(row=4, column=1, sticky="w", pady=6)
        ttk.Button(botoes, text="Cadastrar", command=self.cadastrar).pack(side="left")
        ttk.Button(botoes, text="Alterar a diária do quarto selecionado", command=self.alterar_diaria).pack(side="left", padx=6)
        self.lista = tabela(self, ("Número", "Categoria", "Capacidade", "Diária"), (80, 200, 100, 120))

    def cadastrar(self):
        if executar(lambda: self.hotel.cadastrar_quarto(self.numero.get(), self.categoria.get(),
                                                        self.capacidade.get(), self.diaria.get())):
            limpar(self.numero, self.categoria, self.capacidade, self.diaria)
            self.atualizar()

    def alterar_diaria(self):
        numero = self.lista.selection()
        if not numero:
            messagebox.showinfo("Atenção", "Selecione um quarto na tabela e escreva a nova diária.")
            return
        # quarto.diaria = ... chama o setter, que valida o valor. Reservas já feitas mantêm o preço contratado.
        if executar(lambda: setattr(self.hotel.quartos[numero[0]], "diaria", self.diaria.get())):
            self.hotel.salvar()
            self.atualizar()

    def atualizar(self):
        preencher(self.lista, [(q.numero, (q.numero, q.categoria, q.capacidade, reais(q.diaria)))
                               for q in self.hotel.quartos.values()])


class TelaServicos(ttk.Frame):
    def __init__(self, pai, hotel):
        super().__init__(pai, padding=10)
        self.hotel = hotel
        formulario = ttk.LabelFrame(self, text="Novo serviço", padding=8)
        formulario.pack(fill="x")
        self.descricao = campo(formulario, "Descrição:", 0, 35)
        self.preco = campo(formulario, "Preço (R$):", 1, 12)
        ttk.Button(formulario, text="Cadastrar", command=self.cadastrar).grid(row=2, column=1, sticky="w", pady=6)
        self.lista = tabela(self, ("ID", "Descrição", "Preço"), (50, 320, 120))

    def cadastrar(self):
        if executar(lambda: self.hotel.cadastrar_servico(self.descricao.get(), self.preco.get())):
            limpar(self.descricao, self.preco)
            self.atualizar()

    def atualizar(self):
        preencher(self.lista, [(s.id, (s.id, s.descricao, reais(s.preco))) for s in self.hotel.servicos.values()])


class TelaReservas(ttk.Frame):
    def __init__(self, pai, hotel):
        super().__init__(pai, padding=10)
        self.hotel = hotel
        formulario = ttk.LabelFrame(self, text="1. Consultar quartos livres", padding=8)
        formulario.pack(fill="x")
        ttk.Label(formulario, text="Hóspede:").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.hospede = ttk.Combobox(formulario, width=32, state="readonly")
        self.hospede.grid(row=0, column=1, sticky="w", padx=4, pady=3)
        self.entrada = campo(formulario, "Entrada (dd/mm/aaaa):", 1, 14)
        self.saida = campo(formulario, "Saída (dd/mm/aaaa):", 2, 14)
        self.pessoas = campo(formulario, "Pessoas:", 3, 6)
        ttk.Button(formulario, text="Consultar", command=self.consultar).grid(row=4, column=1, sticky="w", pady=6)

        ttk.Label(self, text="2. Escolha um quarto livre e reserve").pack(anchor="w", pady=(8, 0))
        self.livres = tabela(self, ("Quarto", "Categoria", "Capacidade", "Diária"), (80, 200, 100, 120), altura=3)
        ttk.Button(self, text="Reservar o quarto selecionado", command=self.reservar).pack(anchor="w")

        ttk.Label(self, text="Todas as reservas").pack(anchor="w", pady=(8, 0))
        self.lista = tabela(self, ("Nº", "Hóspede", "Quarto", "Entrada", "Saída", "Situação"),
                            (40, 200, 70, 100, 100, 120), altura=4)
        ttk.Button(self, text="Cancelar a reserva selecionada", command=self.cancelar).pack(anchor="w")

    def consultar(self):
        def acao():
            quartos = self.hotel.quartos_disponiveis(ler_data(self.entrada.get()), ler_data(self.saida.get()),
                                                     int(self.pessoas.get()))
            preencher(self.livres, [(q.numero, (q.numero, q.categoria, q.capacidade, reais(q.diaria))) for q in quartos])
            if not quartos:
                raise RegraNegocioErro("Nenhum quarto livre para esse período e esse número de pessoas.")
        executar(acao)

    def reservar(self):
        quarto = self.livres.selection()
        if not self.hospede.get() or not quarto:
            messagebox.showinfo("Atenção", "Escolha o hóspede, consulte e selecione um quarto livre.")
            return
        hospede_id = int(self.hospede.get().split(" - ")[0])   # o texto é "1 - Maria Silva"
        if executar(lambda: self.hotel.reservar(hospede_id, quarto[0], ler_data(self.entrada.get()),
                                                ler_data(self.saida.get()), int(self.pessoas.get()))):
            preencher(self.livres, [])
            self.atualizar()

    def cancelar(self):
        reserva = self.lista.selection()
        if reserva and executar(lambda: self.hotel.reservas[int(reserva[0])].cancelar()):
            self.hotel.salvar()
            self.atualizar()

    def atualizar(self):
        self.hospede["values"] = [f"{h.id} - {h.nome}" for h in self.hotel.hospedes.values()]
        preencher(self.lista, [(r.id, (r.id, r.hospede.nome, r.quarto.numero, f"{r.entrada:%d/%m/%Y}",
                                       f"{r.saida:%d/%m/%Y}", r.status)) for r in self.hotel.reservas.values()])


class TelaHospedagem(ttk.Frame):
    """A estadia: check-in, consumos, conta e checkout."""

    def __init__(self, pai, hotel):
        super().__init__(pai, padding=10)
        self.hotel = hotel
        ttk.Label(self, text="Reservas confirmadas e em hospedagem").pack(anchor="w")
        self.lista = tabela(self, ("Nº", "Hóspede", "Quarto", "Situação"), (40, 250, 80, 130), altura=4)
        self.lista.bind("<<TreeviewSelect>>", lambda evento: self.mostrar_conta())
        ttk.Button(self, text="Fazer check-in", command=self.check_in).pack(anchor="w")

        consumo = ttk.LabelFrame(self, text="Lançar consumo", padding=8)
        consumo.pack(fill="x", pady=6)
        ttk.Label(consumo, text="Serviço:").grid(row=0, column=0, sticky="w", padx=4)
        self.servico = ttk.Combobox(consumo, width=32, state="readonly")
        self.servico.grid(row=0, column=1, padx=4)
        self.quantidade = campo(consumo, "Quantidade:", 1, 6)
        ttk.Button(consumo, text="Lançar", command=self.lancar).grid(row=2, column=1, sticky="w", pady=4)

        self.conta = tk.Text(self, height=9, width=60, state="disabled")
        self.conta.pack(fill="x")
        ttk.Button(self, text="Fazer checkout", command=self.checkout).pack(anchor="w", pady=6)

    def reserva_selecionada(self):
        selecionada = self.lista.selection()
        if not selecionada:
            messagebox.showinfo("Atenção", "Selecione uma reserva na tabela.")
            return None
        return self.hotel.reservas[int(selecionada[0])]

    def check_in(self):
        reserva = self.reserva_selecionada()
        if reserva and executar(reserva.check_in):
            self.hotel.salvar()
            self.atualizar()

    def lancar(self):
        reserva = self.reserva_selecionada()
        if not reserva or not self.servico.get():
            return
        servico = self.hotel.servicos[int(self.servico.get().split(" - ")[0])]
        if executar(lambda: reserva.lancar_consumo(servico, int(self.quantidade.get()))):
            self.hotel.salvar()
            limpar(self.quantidade)
            self.mostrar_conta()

    def checkout(self):
        reserva = self.reserva_selecionada()
        if reserva and executar(reserva.checkout):
            self.hotel.salvar()
            self.atualizar()

    def mostrar_conta(self):
        selecionada = self.lista.selection()
        texto = self.hotel.reservas[int(selecionada[0])].extrato() if selecionada else ""
        self.conta.configure(state="normal")
        self.conta.delete("1.0", "end")
        self.conta.insert("1.0", texto)
        self.conta.configure(state="disabled")

    def atualizar(self):
        ativas = [r for r in self.hotel.reservas.values() if r.status in (CONFIRMADA, EM_HOSPEDAGEM)]
        preencher(self.lista, [(r.id, (r.id, r.hospede.nome, r.quarto.numero, r.status)) for r in ativas])
        self.servico["values"] = [f"{s.id} - {s}" for s in self.hotel.servicos.values()]
        self.mostrar_conta()


# ---------------------------------------------------------------------------
# A janela principal
# ---------------------------------------------------------------------------

class Aplicacao(tk.Tk):
    def __init__(self, hotel):
        super().__init__()
        self.title("Hotel - Recepção")
        self.geometry("900x650")
        abas = ttk.Notebook(self)
        abas.pack(fill="both", expand=True, padx=8, pady=8)
        self.telas = []
        for titulo, classe in [("Hóspedes", TelaHospedes), ("Quartos", TelaQuartos), ("Serviços", TelaServicos),
                               ("Reservas", TelaReservas), ("Hospedagem", TelaHospedagem)]:
            tela = classe(abas, hotel)
            abas.add(tela, text=titulo)
            self.telas.append(tela)
        # Ao trocar de aba, a tela recarrega os dados
        abas.bind("<<NotebookTabChanged>>", lambda evento: self.telas[abas.index("current")].atualizar())
        self.telas[0].atualizar()


if __name__ == "__main__":
    # 1) Hotel.carregar lê o arquivo   2) cria a janela   3) mainloop() espera os cliques
    Aplicacao(Hotel.carregar(ARQUIVO)).mainloop()
