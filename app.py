"""
Telas do Sistema de Hotel com visual moderno (CustomTkinter).

A interface só recebe dados e mostra resultados.
Todas as regras e cálculos ficam nas classes de modelos.py.

Instalar uma vez:  pip install customtkinter
Executar:         python app.py
(Versão reserva sem bibliotecas extras: python app_classico.py)
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import customtkinter as ctk

from analise import Analise
from modelos import (Hotel, RegraNegocioErro, StatusReserva, LIMITES,
                     mascara_documento, mascara_telefone,
                     ler_data, formatar_data, formatar_moeda)

ARQUIVO_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados_hotel.json")

# ---------------------------------------------------------------------------
# Cores (cada par é: (tema claro, tema escuro))
# ---------------------------------------------------------------------------
FUNDO = ("#eef1f6", "#141821")
CARTAO = ("#ffffff", "#1f2430")
MENU = ("#1e2a44", "#0f131b")
TEXTO_SUAVE = ("#6b7280", "#9ca3af")
AZUL = "#3b82f6"
VERDE = "#22a06b"
AMARELO = "#e5a50a"
VERMELHO = "#e5484d"
COR_SITUACAO = {"Livre": VERDE, "Reservado": AMARELO, "Ocupado": VERMELHO}


def fonte(tamanho=14, negrito=False):
    return ctk.CTkFont(family="Segoe UI", size=tamanho, weight="bold" if negrito else "normal")


# ---------------------------------------------------------------------------
# Componentes reutilizáveis
# ---------------------------------------------------------------------------

def estilizar_tabelas(escuro: bool):
    """O CustomTkinter não tem tabela; usamos ttk.Treeview com cores combinando."""
    fundo, texto, cabecalho = (("#1f2430", "#e5e7eb", "#2a3040") if escuro
                               else ("#ffffff", "#1f2937", "#f3f4f6"))
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure("Hotel.Treeview", background=fundo, fieldbackground=fundo, foreground=texto,
                     rowheight=32, borderwidth=0, font=("Segoe UI", 11))
    estilo.map("Hotel.Treeview", background=[("selected", AZUL)], foreground=[("selected", "white")])
    estilo.configure("Hotel.Treeview.Heading", background=cabecalho, foreground=texto,
                     relief="flat", font=("Segoe UI", 11, "bold"), padding=6)
    estilo.map("Hotel.Treeview.Heading", background=[("active", cabecalho)])
    estilo.layout("Hotel.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])


class Tabela(ctk.CTkFrame):
    """Tabela (Treeview) com barra de rolagem moderna."""

    def __init__(self, master, colunas, larguras, altura=8):
        super().__init__(master, fg_color="transparent")
        self.tree = ttk.Treeview(self, columns=colunas, show="headings", height=altura,
                                 selectmode="browse", style="Hotel.Treeview")
        for col, largura in zip(colunas, larguras):
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, width=largura, anchor="w")
        for situacao in StatusReserva:  # cor do texto conforme a situação da reserva
            cor = {StatusReserva.CONFIRMADA: AZUL, StatusReserva.EM_HOSPEDAGEM: VERDE,
                   StatusReserva.CONCLUIDA: "#8b8b8b", StatusReserva.CANCELADA: VERMELHO}[situacao]
            self.tree.tag_configure(situacao.name, foreground=cor)
        barra = ctk.CTkScrollbar(self, command=self.tree.yview)
        self.tree.configure(yscrollcommand=barra.set)
        self.tree.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    def preencher(self, linhas):
        """linhas: lista de (id, (valores...), tag)"""
        self.tree.delete(*self.tree.get_children())
        for iid, valores, tag in linhas:
            self.tree.insert("", "end", iid=str(iid), values=valores, tags=(tag,) if tag else ())

    def selecionado(self):
        sel = self.tree.selection()
        return sel[0] if sel else None


class Cartao(ctk.CTkFrame):
    """Caixa branca com cantos arredondados e título opcional."""

    def __init__(self, master, titulo=None, **kwargs):
        super().__init__(master, fg_color=CARTAO, corner_radius=14, **kwargs)
        if titulo:
            ctk.CTkLabel(self, text=titulo, font=fonte(15, True)).pack(anchor="w", padx=18, pady=(14, 6))


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


def so_numeros(c):
    return c.isdigit()


class Formulario(ctk.CTkFrame):
    """Organiza rótulos e campos em linhas."""

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.linha = 0

    def campo(self, rotulo, exemplo="", largura=240, limite=None, permitido=None, formatador=None):
        ctk.CTkLabel(self, text=rotulo, font=fonte(13), text_color=TEXTO_SUAVE).grid(
            row=self.linha, column=0, sticky="w", pady=6, padx=(0, 12))
        entrada = ctk.CTkEntry(self, width=largura, height=36, placeholder_text=exemplo)
        entrada.grid(row=self.linha, column=1, sticky="w", pady=6)
        if limite:
            limitar_entrada(entrada, limite, permitido, formatador)
        self.linha += 1
        return entrada

    def lista(self, rotulo, largura=240):
        ctk.CTkLabel(self, text=rotulo, font=fonte(13), text_color=TEXTO_SUAVE).grid(
            row=self.linha, column=0, sticky="w", pady=6, padx=(0, 12))
        caixa = ctk.CTkComboBox(self, width=largura, height=36, values=[], state="readonly")
        caixa.grid(row=self.linha, column=1, sticky="w", pady=6)
        self.linha += 1
        return caixa

    def botao(self, texto, comando, cor=AZUL):
        b = ctk.CTkButton(self, text=texto, command=comando, height=38, fg_color=cor,
                          font=fonte(13, True), corner_radius=10)
        b.grid(row=self.linha, column=1, sticky="w", pady=(10, 4))
        self.linha += 1
        return b


def limpar(*entradas):
    for e in entradas:
        e.delete(0, "end")


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------

class Pagina(ctk.CTkFrame):
    """Classe base das páginas: título, acesso ao hotel e tratamento de erros."""

    titulo = ""
    subtitulo = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.hotel = app.hotel
        ctk.CTkLabel(self, text=self.titulo, font=fonte(26, True)).pack(anchor="w")
        ctk.CTkLabel(self, text=self.subtitulo, font=fonte(13), text_color=TEXTO_SUAVE).pack(
            anchor="w", pady=(0, 14))

    def atualizar(self):
        pass

    def botao_excluir(self, master, comando, texto="Excluir selecionado"):
        ctk.CTkButton(master, text=texto, command=comando, height=36, fg_color=VERMELHO,
                      hover_color="#c2393d", font=fonte(13, True),
                      corner_radius=10).pack(anchor="e", padx=18, pady=(0, 16))

    def excluir_selecionado(self, tabela, nome, excluir):
        """Pede confirmação e chama o método de exclusão do Hotel (que aplica as regras)."""
        chave = tabela.selecionado()
        if not chave:
            messagebox.showinfo("Atenção", "Selecione um item na tabela.")
            return
        if messagebox.askyesno("Excluir", f"Excluir {nome(chave)}? Essa ação não pode ser desfeita."):
            self.executar(lambda: excluir(chave), "Cadastro excluído.")

    def executar(self, acao, sucesso=None):
        """Executa uma operação; se uma regra for violada, mostra o motivo."""
        try:
            resultado = acao()
        except RegraNegocioErro as e:
            messagebox.showwarning("Operação não permitida", str(e))
            return None
        except (ValueError, KeyError) as e:
            messagebox.showwarning("Dados inválidos", f"Verifique os campos informados.\n({e})")
            return None
        except OSError as e:
            messagebox.showwarning("Arquivo", f"Não foi possível ler ou gravar o arquivo.\n({e})")
            return None
        if sucesso:
            self.app.avisar(sucesso)
        self.atualizar()
        return resultado


class PaginaPainel(Pagina):
    titulo = "Painel"
    subtitulo = "Visão geral do hotel hoje"

    def __init__(self, master, app):
        super().__init__(master, app)
        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x")
        self.numeros = {}
        for i, (chave, rotulo, cor) in enumerate([("hosp", "Em hospedagem", VERDE),
                                                  ("entradas", "Entradas hoje", AZUL),
                                                  ("saidas", "Saídas hoje", AMARELO),
                                                  ("ocupacao", "Ocupação", "#8b5cf6"),
                                                  ("fat", "Faturamento", "#0ea5e9")]):
            card = Cartao(linha)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            linha.columnconfigure(i, weight=1)
            ctk.CTkFrame(card, height=5, fg_color=cor, corner_radius=3).pack(fill="x", padx=18, pady=(14, 0))
            ctk.CTkLabel(card, text=rotulo, font=fonte(13), text_color=TEXTO_SUAVE).pack(anchor="w", padx=18, pady=(8, 0))
            valor = ctk.CTkLabel(card, text="-", font=fonte(26, True))
            valor.pack(anchor="w", padx=18, pady=(0, 14))
            self.numeros[chave] = valor

        self.mapa = Cartao(self, "Mapa de quartos")
        self.mapa.pack(fill="x", pady=14)
        self.grade = ctk.CTkFrame(self.mapa, fg_color="transparent")
        self.grade.pack(fill="x", padx=18, pady=(0, 16))

        lista = Cartao(self, "Hospedagens em andamento")
        lista.pack(fill="both", expand=True)
        self.tabela = Tabela(lista, ("Reserva", "Hóspede", "Quarto", "Entrada", "Saída", "Conta parcial"),
                             (80, 240, 90, 110, 110, 140), altura=5)
        self.tabela.pack(fill="both", expand=True, padx=18, pady=(0, 16))

    def atualizar(self):
        r = self.hotel.resumo()
        self.numeros["hosp"].configure(text=str(len(r["em_hospedagem"])))
        self.numeros["entradas"].configure(text=str(len(r["entradas_hoje"])))
        self.numeros["saidas"].configure(text=str(len(r["saidas_hoje"])))
        self.numeros["ocupacao"].configure(text=f"{r['ocupacao']:.0f}%")
        self.numeros["fat"].configure(text=formatar_moeda(r["faturamento"]))

        # Um cartãozinho por quarto, colorido conforme a situação
        for w in self.grade.winfo_children():
            w.destroy()
        for i, quarto in enumerate(self.hotel.quartos.values()):
            situacao = self.hotel.situacao_quarto(quarto)
            cor = COR_SITUACAO[situacao]
            q = ctk.CTkFrame(self.grade, fg_color=cor, corner_radius=12, width=150, height=92)
            q.grid(row=i // 6, column=i % 6, padx=(0, 10), pady=4)
            q.grid_propagate(False)
            ctk.CTkLabel(q, text=quarto.numero, font=fonte(22, True), text_color="white").place(x=14, y=8)
            ctk.CTkLabel(q, text=quarto.categoria, font=fonte(12), text_color="white").place(x=14, y=40)
            ctk.CTkLabel(q, text=situacao.upper(), font=fonte(11, True), text_color="white").place(x=14, y=62)

        self.tabela.preencher([(res.id, (res.id, res.hospede.nome, res.quarto.numero,
                                         formatar_data(res.entrada), formatar_data(res.saida),
                                         formatar_moeda(res.total)), None)
                               for res in r["em_hospedagem"]])


class PaginaHospedes(Pagina):
    titulo = "Hóspedes"
    subtitulo = "Cadastro das pessoas responsáveis pelas reservas"

    def __init__(self, master, app):
        super().__init__(master, app)
        form_card = Cartao(self, "Novo hóspede")
        form_card.pack(side="left", fill="y", padx=(0, 14))
        f = Formulario(form_card)
        f.pack(padx=18, pady=(0, 18))
        self.nome = f.campo("Nome", "Maria Silva", limite=LIMITES["nome"])
        self.doc = f.campo("Documento", "CPF (11 dígitos) ou RG", limite=LIMITES["documento"],
                           formatador=mascara_documento)
        self.tel = f.campo("Telefone", "(11) 99999-0000", limite=LIMITES["telefone"],
                           formatador=mascara_telefone)
        f.botao("Cadastrar hóspede", self.cadastrar)

        lista = Cartao(self, "Hóspedes cadastrados")
        lista.pack(side="left", fill="both", expand=True)
        self.tabela = Tabela(lista, ("ID", "Nome", "Documento", "Telefone"), (50, 230, 150, 140))
        self.tabela.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        self.botao_excluir(lista, self.excluir)

    def cadastrar(self):
        if self.executar(lambda: self.hotel.cadastrar_hospede(self.nome.get(), self.doc.get(), self.tel.get()),
                         "Hóspede cadastrado!"):
            limpar(self.nome, self.doc, self.tel)

    def excluir(self):
        self.excluir_selecionado(self.tabela, lambda k: self.hotel.hospedes[int(k)].nome,
                                 lambda k: self.hotel.excluir_hospede(int(k)))

    def atualizar(self):
        self.tabela.preencher([(h.id, (h.id, h.nome, h.documento_formatado, h.telefone_formatado), None)
                               for h in self.hotel.hospedes.values()])


class PaginaQuartos(Pagina):
    titulo = "Quartos"
    subtitulo = "Capacidade e diária de cada quarto"

    def __init__(self, master, app):
        super().__init__(master, app)
        form_card = Cartao(self, "Novo quarto")
        form_card.pack(side="left", fill="y", padx=(0, 14))
        f = Formulario(form_card)
        f.pack(padx=18, pady=(0, 18))
        self.numero = f.campo("Número", "101", limite=LIMITES["numero_quarto"])
        self.categoria = f.campo("Categoria", "Standard, Luxo...", limite=LIMITES["categoria"])
        self.capacidade = f.campo("Capacidade", "nº de pessoas", limite=2, permitido=so_numeros)
        self.diaria = f.campo("Diária (R$)", "180,00")
        f.botao("Cadastrar quarto", self.cadastrar)
        f.botao("Alterar diária do selecionado", self.alterar_diaria, cor="#6b7280")

        lista = Cartao(self, "Quartos do hotel")
        lista.pack(side="left", fill="both", expand=True)
        self.tabela = Tabela(lista, ("Número", "Categoria", "Capacidade", "Diária atual"), (90, 180, 110, 130))
        self.tabela.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        self.botao_excluir(lista, self.excluir)

    def cadastrar(self):
        if self.executar(lambda: self.hotel.cadastrar_quarto(self.numero.get(), self.categoria.get(),
                                                             int(self.capacidade.get()), self.diaria.get()),
                         "Quarto cadastrado!"):
            limpar(self.numero, self.categoria, self.capacidade, self.diaria)

    def excluir(self):
        self.excluir_selecionado(self.tabela, lambda k: f"o quarto {k}",
                                 lambda k: self.hotel.excluir_quarto(k))

    def alterar_diaria(self):
        numero = self.tabela.selecionado()
        if not numero:
            messagebox.showinfo("Atenção", "Selecione um quarto na tabela e informe a nova diária.")
            return

        def acao():
            self.hotel.quartos[numero].diaria = self.diaria.get()  # setter valida o valor
            self.hotel.salvar()
        self.executar(acao, "Diária alterada! Reservas já feitas mantêm a diária contratada.")

    def atualizar(self):
        self.tabela.preencher([(q.numero, (q.numero, q.categoria, q.capacidade, formatar_moeda(q.diaria)), None)
                               for q in self.hotel.quartos.values()])


class PaginaServicos(Pagina):
    titulo = "Serviços"
    subtitulo = "Catálogo de extras: frigobar, lavanderia, refeições..."

    def __init__(self, master, app):
        super().__init__(master, app)
        form_card = Cartao(self, "Novo serviço")
        form_card.pack(side="left", fill="y", padx=(0, 14))
        f = Formulario(form_card)
        f.pack(padx=18, pady=(0, 18))
        self.descricao = f.campo("Descrição", "Água (frigobar)", limite=LIMITES["descricao"])
        self.preco = f.campo("Preço (R$)", "10,00")
        f.botao("Cadastrar serviço", self.cadastrar)

        lista = Cartao(self, "Catálogo")
        lista.pack(side="left", fill="both", expand=True)
        self.tabela = Tabela(lista, ("ID", "Descrição", "Preço"), (50, 300, 120))
        self.tabela.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        self.botao_excluir(lista, self.excluir)

    def cadastrar(self):
        if self.executar(lambda: self.hotel.cadastrar_servico(self.descricao.get(), self.preco.get()),
                         "Serviço cadastrado!"):
            limpar(self.descricao, self.preco)

    def excluir(self):
        self.excluir_selecionado(self.tabela, lambda k: f"'{self.hotel.servicos[int(k)].descricao}'",
                                 lambda k: self.hotel.excluir_servico(int(k)))

    def atualizar(self):
        self.tabela.preencher([(s.id, (s.id, s.descricao, formatar_moeda(s.preco)), None)
                               for s in self.hotel.servicos.values()])


class PaginaReservas(Pagina):
    titulo = "Reservas"
    subtitulo = "Consulte a disponibilidade e reserve um quarto"

    def __init__(self, master, app):
        super().__init__(master, app)
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x")

        busca = Cartao(topo, "1. Pesquisar")
        busca.pack(side="left", fill="y", padx=(0, 14))
        f = Formulario(busca)
        f.pack(padx=18, pady=(0, 18))
        self.hospede = f.lista("Hóspede")
        self.entrada = f.campo("Entrada", "dd/mm/aaaa")
        self.saida = f.campo("Saída", "dd/mm/aaaa")
        self.pessoas = f.campo("Pessoas", "2")
        f.botao("Consultar quartos livres", self.consultar)

        escolha = Cartao(topo, "2. Escolher o quarto")
        escolha.pack(side="left", fill="both", expand=True)
        self.disponiveis = Tabela(escolha, ("Quarto", "Categoria", "Cap.", "Diária", "Valor estimado"),
                                  (70, 110, 50, 100, 130), altura=5)
        self.disponiveis.pack(fill="both", expand=True, padx=18)
        ctk.CTkButton(escolha, text="Confirmar reserva", command=self.reservar, height=38, fg_color=VERDE,
                      font=fonte(13, True), corner_radius=10).pack(anchor="e", padx=18, pady=14)

        lista = Cartao(self, "Todas as reservas")
        lista.pack(fill="both", expand=True, pady=(14, 0))
        self.tabela = Tabela(lista, ("Nº", "Hóspede", "Quarto", "Entrada", "Saída", "Pessoas",
                                     "Diárias", "Diária contratada", "Situação"),
                             (40, 150, 62, 95, 95, 70, 62, 130, 120), altura=6)
        self.tabela.pack(fill="both", expand=True, padx=18)
        ctk.CTkButton(lista, text="Cancelar reserva selecionada", command=self.cancelar, height=36,
                      fg_color=VERMELHO, hover_color="#c2393d", font=fonte(13, True),
                      corner_radius=10).pack(anchor="e", padx=18, pady=14)
        self._consultou = False

    def _ler_formulario(self):
        return ler_data(self.entrada.get()), ler_data(self.saida.get()), int(self.pessoas.get())

    def consultar(self):
        def acao():
            entrada, saida, pessoas = self._ler_formulario()
            quartos = self.hotel.quartos_disponiveis(entrada, saida, pessoas)
            noites = (saida - entrada).days
            self.disponiveis.preencher([(q.numero, (q.numero, q.categoria, q.capacidade,
                                                    formatar_moeda(q.diaria),
                                                    formatar_moeda(q.diaria * noites)), None)
                                        for q in quartos])
            self._consultou = True
            if not quartos:
                raise RegraNegocioErro("Nenhum quarto disponível para esse período e quantidade de pessoas.")
        self.executar(acao)

    def reservar(self):
        numero = self.disponiveis.selecionado()
        if not self.hospede.get() or not numero or not self._consultou:
            messagebox.showinfo("Atenção", "Escolha o hóspede, consulte e selecione um quarto.")
            return
        hospede_id = int(self.hospede.get().split(" - ")[0])

        def acao():
            # Relê as datas: se mudaram, a regra de conflito valida de novo.
            entrada, saida, pessoas = self._ler_formulario()
            r = self.hotel.reservar(hospede_id, numero, entrada, saida, pessoas)
            self.disponiveis.preencher([])
            return r
        r = self.executar(acao)
        if r:
            self.app.avisar(f"Reserva nº {r.id} confirmada: {r.qtd_diarias} diária(s), "
                            f"{formatar_moeda(r.valor_hospedagem)}")

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
        self.hospede.configure(values=[f"{h.id} - {h.nome}" for h in self.hotel.hospedes.values()])
        self.tabela.preencher([(r.id, (r.id, r.hospede.nome, r.quarto.numero,
                                       formatar_data(r.entrada), formatar_data(r.saida),
                                       r.pessoas, r.qtd_diarias,
                                       formatar_moeda(r.diaria_contratada), r.status.value), r.status.name)
                               for r in sorted(self.hotel.reservas.values(), key=lambda r: r.entrada)])


class PaginaHospedagem(Pagina):
    titulo = "Hospedagem e Checkout"
    subtitulo = "Check-in, consumos e fechamento da conta"

    def __init__(self, master, app):
        super().__init__(master, app)
        esquerda = ctk.CTkFrame(self, fg_color="transparent")
        esquerda.pack(side="left", fill="y", padx=(0, 14))

        lista = Cartao(esquerda, "Reservas confirmadas e em hospedagem")
        lista.pack(fill="both", expand=True)
        self.tabela = Tabela(lista, ("Nº", "Hóspede", "Quarto", "Período", "Situação"),
                             (40, 130, 66, 182, 125), altura=6)
        self.tabela.pack(fill="both", expand=True, padx=18)
        self.tabela.tree.bind("<<TreeviewSelect>>", lambda e: self.mostrar_conta())
        ctk.CTkButton(lista, text="Fazer check-in", command=self.check_in, height=38, fg_color=AZUL,
                      font=fonte(13, True), corner_radius=10).pack(anchor="w", padx=18, pady=14)

        consumo = Cartao(esquerda, "Lançar consumo")
        consumo.pack(fill="x", pady=(14, 0))
        f = Formulario(consumo)
        f.pack(anchor="w", padx=18, pady=(0, 16))
        self.servico = f.lista("Serviço", largura=280)
        self.qtd = f.campo("Quantidade", "1", largura=100)
        f.botao("Lançar consumo", self.lancar)

        # Recibo
        recibo = Cartao(self, "Conta da hospedagem")
        recibo.pack(side="left", fill="both", expand=True)
        self.extrato = ctk.CTkTextbox(recibo, font=ctk.CTkFont(family="Consolas", size=12),
                                      fg_color=FUNDO, corner_radius=10, wrap="none")
        self.extrato.pack(fill="both", expand=True, padx=18)
        rodape = ctk.CTkFrame(recibo, fg_color="transparent")
        rodape.pack(fill="x", padx=18, pady=14)
        ctk.CTkLabel(rodape, text="TOTAL", font=fonte(13), text_color=TEXTO_SUAVE).pack(anchor="w")
        self.total = ctk.CTkLabel(rodape, text="R$ 0,00", font=fonte(30, True), text_color=VERDE)
        self.total.pack(anchor="w")
        ctk.CTkButton(rodape, text="Confirmar checkout", command=self.checkout, height=42, fg_color=VERDE,
                      font=fonte(14, True), corner_radius=10).pack(fill="x", pady=(8, 0))

    def _reserva(self):
        rid = self.tabela.selecionado()
        if not rid:
            messagebox.showinfo("Atenção", "Selecione uma reserva na lista.")
            return None
        return self.hotel.reservas[int(rid)]

    def check_in(self):
        r = self._reserva()
        if r:
            self.executar(lambda: (r.check_in(), self.hotel.salvar()), f"Check-in da reserva nº {r.id} realizado!")

    def lancar(self):
        r = self._reserva()
        if not r:
            return
        if not self.servico.get():
            messagebox.showinfo("Atenção", "Escolha um serviço.")
            return
        servico = self.hotel.servicos[int(self.servico.get().split(" - ")[0])]
        if self.executar(lambda: (r.lancar_consumo(servico, int(self.qtd.get())), self.hotel.salvar()),
                         f"{servico.descricao} lançado na reserva nº {r.id}"):
            limpar(self.qtd)

    def checkout(self):
        r = self._reserva()
        if not r:
            return
        if r.status == StatusReserva.EM_HOSPEDAGEM and not messagebox.askyesno(
                "Checkout", f"Confirmar checkout com total de {formatar_moeda(r.total)}?"):
            return
        self.executar(lambda: (r.checkout(), self.hotel.salvar()),
                      f"Hospedagem concluída! Total pago: {formatar_moeda(r.total)}")

    def mostrar_conta(self):
        rid = self.tabela.selecionado()
        r = self.hotel.reservas[int(rid)] if rid else None
        self.extrato.configure(state="normal")
        self.extrato.delete("1.0", "end")
        self.extrato.insert("1.0", r.extrato() if r else "Selecione uma reserva para ver a conta.")
        self.extrato.configure(state="disabled")
        self.total.configure(text=formatar_moeda(r.total) if r else "R$ 0,00")

    def atualizar(self):
        selecionado = self.tabela.selecionado()
        ativas = sorted((r for r in self.hotel.reservas.values() if r.ativa), key=lambda r: r.entrada)
        self.tabela.preencher([(r.id, (r.id, r.hospede.nome, r.quarto.numero,
                                       f"{formatar_data(r.entrada)} a {formatar_data(r.saida)}",
                                       r.status.value), r.status.name) for r in ativas])
        self.servico.configure(values=[f"{s.id} - {s}" for s in self.hotel.servicos.values()])
        if selecionado and self.tabela.tree.exists(selecionado):
            self.tabela.tree.selection_set(selecionado)
        self.mostrar_conta()


# ---------------------------------------------------------------------------
# Análise de dados
# ---------------------------------------------------------------------------

def abreviar(valor) -> str:
    """45210 -> '45,2 mil'"""
    v = float(valor)
    return f"{v / 1000:.1f}".replace(".", ",") + " mil" if v >= 1000 else f"{v:.0f}"


class Grafico(tk.Canvas):
    """Gráfico de barras desenhado direto no Canvas do Tkinter (sem bibliotecas extras)."""

    def __init__(self, master, altura=150):
        super().__init__(master, height=altura, highlightthickness=0, bd=0)
        self.itens, self.horizontal = [], False
        self.bind("<Configure>", lambda e: self.desenhar())

    def mostrar(self, itens, horizontal=False):
        """itens: lista de (rótulo, valor)"""
        self.itens, self.horizontal = itens, horizontal
        self.desenhar()

    def desenhar(self):
        escuro = ctk.get_appearance_mode() == "Dark"
        fundo = CARTAO[1] if escuro else CARTAO[0]
        suave, forte = ("#9ca3af", "#e5e7eb") if escuro else ("#6b7280", "#1f2937")
        self.configure(bg=fundo)
        self.delete("all")
        largura, altura = self.winfo_width(), self.winfo_height()
        if largura < 50:
            return
        if not self.itens:
            self.create_text(largura / 2, altura / 2, text="Sem dados", fill=suave)
            return
        maior = max(float(v) for _, v in self.itens) or 1
        n = len(self.itens)
        letra = ("Segoe UI", 8)
        if not self.horizontal:                                  # barras em pé
            base, topo = altura - 22, 18
            passo = largura / n
            for i, (rotulo, valor) in enumerate(self.itens):
                x0, x1 = i * passo + passo * 0.18, (i + 1) * passo - passo * 0.18
                y0 = base - (base - topo) * float(valor) / maior
                self.create_rectangle(x0, y0, x1, base, fill=AZUL, outline="")
                self.create_text((x0 + x1) / 2, y0 - 8, text=abreviar(valor), fill=forte, font=letra)
                self.create_text((x0 + x1) / 2, altura - 10, text=rotulo, fill=suave, font=letra)
        else:                                                    # barras deitadas
            esquerda, direita = 40, 64
            passo = altura / n
            for i, (rotulo, valor) in enumerate(self.itens):
                y0, y1 = i * passo + passo * 0.18, (i + 1) * passo - passo * 0.18
                x1 = esquerda + (largura - esquerda - direita) * float(valor) / maior
                self.create_rectangle(esquerda, y0, x1, y1, fill="#8b5cf6", outline="")
                self.create_text(esquerda - 6, (y0 + y1) / 2, text=rotulo, fill=forte, font=letra, anchor="e")
                self.create_text(x1 + 6, (y0 + y1) / 2, text=abreviar(valor), fill=forte, font=letra, anchor="w")


class PaginaAnalise(Pagina):
    titulo = "Análise de dados"
    subtitulo = "Indicadores calculados lendo o arquivo JSON do hotel"
    EXEMPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados_exemplo.json")

    def __init__(self, master, app):
        super().__init__(master, app)
        self.fonte = "hotel"        # "hotel", "exemplo" ou o caminho de um arquivo escolhido
        self.analise = None

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", pady=(0, 10))
        for texto, comando, cor in [("Dados do hotel", self.usar_hotel, AZUL),
                                    ("Dados de exemplo (2026)", self.usar_exemplo, "#8b5cf6"),
                                    ("Abrir arquivo JSON…", self.abrir_arquivo, "#6b7280"),
                                    ("Exportar CSV (Excel)", self.exportar, VERDE)]:
            ctk.CTkButton(barra, text=texto, command=comando, height=34, fg_color=cor,
                          font=fonte(13, True), corner_radius=10).pack(side="left", padx=(0, 8))
        self.origem = ctk.CTkLabel(barra, text="", font=fonte(12), text_color=TEXTO_SUAVE)
        self.origem.pack(side="right")

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x")
        self.numeros = {}
        for i, (chave, rotulo, cor) in enumerate([("fat", "Faturamento", "#0ea5e9"),
                                                  ("hosp", "Hospedagens concluídas", VERDE),
                                                  ("ticket", "Ticket médio", AZUL),
                                                  ("ocup", "Taxa de ocupação", "#8b5cf6"),
                                                  ("cancel", "Cancelamentos", VERMELHO)]):
            card = Cartao(linha)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            linha.columnconfigure(i, weight=1)
            ctk.CTkFrame(card, height=4, fg_color=cor, corner_radius=2).pack(fill="x", padx=14, pady=(10, 0))
            ctk.CTkLabel(card, text=rotulo, font=fonte(12), text_color=TEXTO_SUAVE).pack(anchor="w", padx=14, pady=(6, 0))
            valor = ctk.CTkLabel(card, text="-", font=fonte(20, True))
            valor.pack(anchor="w", padx=14, pady=(0, 10))
            self.numeros[chave] = valor

        graficos = ctk.CTkFrame(self, fg_color="transparent")
        graficos.pack(fill="x", pady=12)
        graficos.columnconfigure(0, weight=3, uniform="g")
        graficos.columnconfigure(1, weight=2, uniform="g")
        c1 = Cartao(graficos, "Faturamento por mês")
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.grafico_mes = Grafico(c1, 150)
        self.grafico_mes.pack(fill="x", padx=14, pady=(0, 12))
        c2 = Cartao(graficos, "Faturamento por quarto")
        c2.grid(row=0, column=1, sticky="nsew")
        self.grafico_quarto = Grafico(c2, 150)
        self.grafico_quarto.pack(fill="x", padx=14, pady=(0, 12))

        tabelas = ctk.CTkFrame(self, fg_color="transparent")
        tabelas.pack(fill="both", expand=True)
        tabelas.columnconfigure(0, weight=1, uniform="t")
        tabelas.columnconfigure(1, weight=1, uniform="t")
        t1 = Cartao(tabelas, "Serviços mais consumidos")
        t1.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.tabela_servicos = Tabela(t1, ("Serviço", "Qtd", "Valor"), (210, 60, 110), altura=4)
        self.tabela_servicos.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        t2 = Cartao(tabelas, "Hóspedes que mais gastaram")
        t2.grid(row=0, column=1, sticky="nsew")
        self.tabela_hospedes = Tabela(t2, ("Hóspede", "Hospedagens", "Total gasto"), (175, 120, 110), altura=4)
        self.tabela_hospedes.pack(fill="both", expand=True, padx=14, pady=(0, 12))

    # ----- escolha da fonte dos dados -----
    def usar_hotel(self):
        self.fonte = "hotel"
        self.atualizar()

    def usar_exemplo(self):
        self.fonte = "exemplo"
        self.atualizar()

    def abrir_arquivo(self):
        caminho = filedialog.askopenfilename(title="Escolha um arquivo de dados do hotel",
                                             filetypes=[("Arquivos JSON", "*.json"), ("Todos", "*.*")])
        if caminho:
            self.fonte = caminho
            self.atualizar()

    def exportar(self):
        caminho = filedialog.asksaveasfilename(title="Exportar hospedagens concluídas",
                                               defaultextension=".csv", initialfile="faturamento.csv",
                                               filetypes=[("CSV (abre no Excel)", "*.csv")])
        if caminho:
            n = self.executar(lambda: self.analise.exportar_csv(caminho))
            if n is not None:
                self.app.avisar(f"{n} hospedagens exportadas")

    def _carregar(self) -> Analise:
        if self.fonte == "hotel":
            return Analise(self.hotel, "Dados do hotel (ao vivo)")
        return Analise.de_arquivo(self.EXEMPLO if self.fonte == "exemplo" else self.fonte)

    def atualizar(self):
        try:
            self.analise = self._carregar()
        except RegraNegocioErro as e:
            messagebox.showwarning("Não foi possível abrir", str(e))
            self.fonte = "hotel"
            self.analise = self._carregar()
        a = self.analise
        self.origem.configure(text=f"Fonte: {a.origem}")
        self.numeros["fat"].configure(text=formatar_moeda(a.faturamento_total()))
        self.numeros["hosp"].configure(text=str(len(a.concluidas)))
        self.numeros["ticket"].configure(text=formatar_moeda(a.ticket_medio()))
        self.numeros["ocup"].configure(text=f"{a.taxa_ocupacao():.0f}%")
        self.numeros["cancel"].configure(text=f"{a.taxa_cancelamento():.0f}%")
        self.grafico_mes.mostrar(a.faturamento_por_mes())
        self.grafico_quarto.mostrar(a.faturamento_por_quarto(), horizontal=True)
        self.tabela_servicos.preencher([(i, (nome, qtd, formatar_moeda(valor)), None)
                                        for i, (nome, qtd, valor) in enumerate(a.consumo_por_servico())])
        self.tabela_hospedes.preencher([(i, (nome, n, formatar_moeda(total)), None)
                                        for i, (nome, n, total) in enumerate(a.ranking_hospedes(8))])


# ---------------------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------------------

class Aplicacao(ctk.CTk):
    PAGINAS = [("◧  Painel", PaginaPainel), ("👤  Hóspedes", PaginaHospedes),
               ("🛏  Quartos", PaginaQuartos), ("🧺  Serviços", PaginaServicos),
               ("📅  Reservas", PaginaReservas), ("🧾  Hospedagem", PaginaHospedagem),
               ("📊  Análise de dados", PaginaAnalise)]

    def __init__(self, hotel: Hotel):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        super().__init__(fg_color=FUNDO)
        self.hotel = hotel
        self.title(f"{hotel.nome} - Sistema de Recepção")
        self.geometry("1280x780")
        self.minsize(1000, 640)
        self.after(0, self._maximizar)
        estilizar_tabelas(escuro=False)

        # ----- menu lateral -----
        menu = ctk.CTkFrame(self, fg_color=MENU, corner_radius=0, width=230)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)
        ctk.CTkLabel(menu, text="🏨", font=fonte(40)).pack(pady=(28, 0))
        ctk.CTkLabel(menu, text=hotel.nome, font=fonte(18, True), text_color="white").pack()
        ctk.CTkLabel(menu, text="Recepção", font=fonte(12), text_color="#9aa7c0").pack(pady=(0, 24))

        self.botoes = []
        for i, (texto, _) in enumerate(self.PAGINAS):
            b = ctk.CTkButton(menu, text=texto, anchor="w", height=44, corner_radius=10,
                              font=fonte(14), fg_color="transparent", hover_color="#2d3b5c",
                              text_color="white", command=lambda i=i: self.mostrar(i))
            b.pack(fill="x", padx=14, pady=3)
            self.botoes.append(b)

        self.tema = ctk.CTkSwitch(menu, text="Modo escuro", text_color="white",
                                  command=self.alternar_tema, font=fonte(13))
        self.tema.pack(side="bottom", pady=24)

        # ----- área das páginas -----
        area = ctk.CTkFrame(self, fg_color="transparent")
        area.pack(side="left", fill="both", expand=True, padx=28, pady=(24, 8))
        self.paginas = []
        for _, classe in self.PAGINAS:
            pagina = classe(area, self)
            pagina.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.paginas.append(pagina)

        # ----- barra de aviso (mensagens de sucesso) -----
        self.aviso = ctk.CTkLabel(self, text="", height=38, corner_radius=10, fg_color=VERDE,
                                  text_color="white", font=fonte(13, True))
        self._aviso_id = None
        self.mostrar(0)

    def _maximizar(self):
        try:
            self.state("zoomed")  # abre maximizada no Windows
        except tk.TclError:
            pass  # em outros sistemas mantém o tamanho padrão

    def mostrar(self, indice):
        """Traz a página escolhida para a frente e atualiza seus dados."""
        for i, b in enumerate(self.botoes):
            b.configure(fg_color=AZUL if i == indice else "transparent")
        self.indice_atual = indice
        pagina = self.paginas[indice]
        pagina.atualizar()
        pagina.tkraise()

    def avisar(self, texto):
        """Mostra uma mensagem verde no canto superior por 3 segundos."""
        self.aviso.configure(text=f"  ✔  {texto}  ")
        self.aviso.place(relx=0.985, rely=0.03, anchor="ne")
        self.aviso.lift()
        if self._aviso_id:
            self.after_cancel(self._aviso_id)
        self._aviso_id = self.after(3000, self.aviso.place_forget)

    def alternar_tema(self):
        escuro = bool(self.tema.get())
        ctk.set_appearance_mode("dark" if escuro else "light")
        estilizar_tabelas(escuro)
        self.paginas[self.indice_atual].atualizar()  # redesenha os gráficos com as cores do tema


if __name__ == "__main__":
    Aplicacao(Hotel.carregar(ARQUIVO_DADOS)).mainloop()
