"""
Telas do Sistema de Hotel (CustomTkinter).

A interface só recebe dados e mostra resultados.
Todas as regras e cálculos ficam nas classes de modelos.py e analise.py.

Instalar uma vez:  pip install customtkinter
Executar:         python app.py
(Versão reserva sem bibliotecas extras: python app_classico.py)
"""

import os
import tkinter as tk
from datetime import date, datetime
from tkinter import ttk, messagebox, filedialog

import customtkinter as ctk

from analise import Analise
from modelos import (Hotel, RegraNegocioErro, StatusReserva, LIMITES,
                     mascara_documento, mascara_telefone,
                     ler_data, formatar_data, formatar_moeda)

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DADOS = os.path.join(PASTA, "dados_hotel.json")
PASTA_FECHAMENTOS = os.path.join(PASTA, "fechamentos")

# ---------------------------------------------------------------------------
# Paleta (cada par é: (tema claro, tema escuro)). Uma cor de destaque só;
# verde, amarelo e vermelho aparecem apenas para indicar situação.
# ---------------------------------------------------------------------------
FUNDO = ("#f3f4f6", "#16181d")
SUPERFICIE = ("#ffffff", "#1e2128")
BORDA = ("#dfe3e8", "#2e323b")
TEXTO = ("#1d2939", "#e4e7ec")
TEXTO_SUAVE = ("#667085", "#98a2b3")
REALCE = ("#f2f4f7", "#262a33")            # fundo ao passar o mouse
LISTRA = ("#f9fafb", "#1b1e24")            # linhas alternadas das tabelas
ACENTO = ("#1d5fa3", "#4a86c8")
ACENTO_HOVER = ("#174d85", "#3c74b3")
VERDE = ("#2f7d4f", "#5cbf86")
AMARELO = ("#b54708", "#f2a93b")
VERMELHO = ("#b42318", "#f47b72")
CINZA = ("#667085", "#98a2b3")
MENU = ("#1d2939", "#101318")
MENU_ATIVO = ("#2f3e52", "#232a35")
MENU_TEXTO = "#c9d1db"
COR_SITUACAO = {"Livre": VERDE, "Reservado": AMARELO, "Ocupado": VERMELHO}
COR_STATUS = {StatusReserva.CONFIRMADA: ACENTO, StatusReserva.EM_HOSPEDAGEM: VERDE,
              StatusReserva.CONCLUIDA: CINZA, StatusReserva.CANCELADA: VERMELHO}

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]


def fonte(tamanho=13, negrito=False):
    return ctk.CTkFont(family="Segoe UI", size=tamanho, weight="bold" if negrito else "normal")


def escuro() -> bool:
    return ctk.get_appearance_mode() == "Dark"


def cor(par) -> str:
    """Widgets do Tkinter puro (tabela, gráfico) não aceitam o par claro/escuro: escolhe um."""
    return par if isinstance(par, str) else par[1 if escuro() else 0]


def data_por_extenso(d: date) -> str:
    return f"{DIAS[d.weekday()]}, {d.day} de {MESES[d.month - 1]} de {d.year}"


# ---------------------------------------------------------------------------
# Componentes reutilizáveis
# ---------------------------------------------------------------------------

def botao(master, texto, comando, tipo="primario", largura=None):
    """Botão no padrão do sistema: 'primario' (ação principal), 'secundario' ou 'perigo'."""
    estilos = {
        "primario": dict(fg_color=ACENTO, hover_color=ACENTO_HOVER, text_color="#ffffff", border_width=0),
        "secundario": dict(fg_color=SUPERFICIE, hover_color=REALCE, text_color=TEXTO,
                           border_width=1, border_color=BORDA),
        "perigo": dict(fg_color=SUPERFICIE, hover_color=("#fef3f2", "#3a2326"), text_color=VERMELHO,
                       border_width=1, border_color=("#f4b8b2", "#6b2b29")),
    }
    extra = {"width": largura} if largura else {}
    return ctk.CTkButton(master, text=texto, command=comando, height=32, corner_radius=6,
                         font=fonte(12), **estilos[tipo], **extra)


def estilizar_tabelas():
    """O CustomTkinter não tem tabela; usamos ttk.Treeview com as cores da paleta."""
    estilo = ttk.Style()
    estilo.theme_use("clam")
    estilo.configure("Hotel.Treeview", background=cor(SUPERFICIE), fieldbackground=cor(SUPERFICIE),
                     foreground=cor(TEXTO), rowheight=30, borderwidth=0, font=("Segoe UI", 10))
    estilo.map("Hotel.Treeview", background=[("selected", cor(ACENTO))],
               foreground=[("selected", "#ffffff")])
    estilo.configure("Hotel.Treeview.Heading", background=cor(SUPERFICIE), foreground=cor(TEXTO_SUAVE),
                     relief="flat", borderwidth=0, font=("Segoe UI", 9, "bold"), padding=(6, 6))
    estilo.map("Hotel.Treeview.Heading", background=[("active", cor(SUPERFICIE))])
    estilo.layout("Hotel.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    for tabela in list(Tabela.todas):
        try:
            tabela.aplicar_cores()
        except tk.TclError:          # tabela de uma janela que já foi fechada
            Tabela.todas.remove(tabela)


class Tabela(ctk.CTkFrame):
    """Tabela (Treeview) com linhas alternadas e cor da situação da reserva."""

    todas = []  # para recolorir todas ao trocar o tema

    def __init__(self, master, colunas, larguras, altura=8):
        super().__init__(master, fg_color="transparent")
        self.tree = ttk.Treeview(self, columns=colunas, show="headings", height=altura,
                                 selectmode="browse", style="Hotel.Treeview")
        for col, largura in zip(colunas, larguras):
            self.tree.heading(col, text=col.upper(), anchor="w")
            self.tree.column(col, width=largura, anchor="w")
        barra = ctk.CTkScrollbar(self, command=self.tree.yview, width=12)
        self.tree.configure(yscrollcommand=barra.set)
        self.tree.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        Tabela.todas.append(self)
        self.aplicar_cores()

    def aplicar_cores(self):
        self.tree.tag_configure("listra", background=cor(LISTRA))
        for situacao, par in COR_STATUS.items():
            self.tree.tag_configure(situacao.name, foreground=cor(par))

    def preencher(self, linhas):
        """linhas: lista de (id, (valores...), tag)"""
        self.tree.delete(*self.tree.get_children())
        for i, (iid, valores, tag) in enumerate(linhas):
            tags = tuple(t for t in (tag, "listra" if i % 2 else None) if t)
            self.tree.insert("", "end", iid=str(iid), values=valores, tags=tags)

    def selecionado(self):
        sel = self.tree.selection()
        return sel[0] if sel else None


class Cartao(ctk.CTkFrame):
    """Painel com borda fina, título e uma área de ações à direita do título."""

    def __init__(self, master, titulo=None, **kwargs):
        super().__init__(master, fg_color=SUPERFICIE, corner_radius=8, border_width=1,
                         border_color=BORDA, **kwargs)
        self.acoes = None
        if titulo:
            topo = ctk.CTkFrame(self, fg_color="transparent")
            topo.pack(fill="x", padx=16, pady=(10, 8))
            ctk.CTkLabel(topo, text=titulo, font=fonte(13, True), text_color=TEXTO).pack(side="left")
            self.acoes = ctk.CTkFrame(topo, fg_color="transparent", width=1, height=1)
            self.acoes.pack(side="right")
            ctk.CTkFrame(self, height=1, fg_color=BORDA).pack(fill="x", padx=1)


class Indicador(Cartao):
    """Cartão de número: rótulo, valor em destaque e uma linha de detalhe."""

    def __init__(self, master, rotulo):
        super().__init__(master)
        ctk.CTkLabel(self, text=rotulo.upper(), font=fonte(10, True), text_color=TEXTO_SUAVE).pack(
            anchor="w", padx=16, pady=(12, 0))
        self.valor = ctk.CTkLabel(self, text="-", font=fonte(22, True), text_color=TEXTO)
        self.valor.pack(anchor="w", padx=16)
        self.detalhe = ctk.CTkLabel(self, text="", font=fonte(11), text_color=TEXTO_SUAVE)
        self.detalhe.pack(anchor="w", padx=16, pady=(0, 10))

    def mostrar(self, valor, detalhe=""):
        self.valor.configure(text=valor)
        self.detalhe.configure(text=detalhe)


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
    """Organiza os campos com o rótulo em cima de cada um."""

    def __init__(self, master, largura=300):
        super().__init__(master, fg_color="transparent")
        self.largura = largura

    def _rotulo(self, texto):
        ctk.CTkLabel(self, text=texto, font=fonte(12), text_color=TEXTO_SUAVE).pack(anchor="w", pady=(8, 2))

    def campo(self, rotulo, exemplo="", largura=None, limite=None, permitido=None, formatador=None):
        self._rotulo(rotulo)
        entrada = ctk.CTkEntry(self, width=largura or self.largura, height=32, corner_radius=6,
                               border_width=1, border_color=BORDA, fg_color=SUPERFICIE,
                               text_color=TEXTO, placeholder_text=exemplo, font=fonte(12))
        entrada.pack(anchor="w")
        if limite:
            limitar_entrada(entrada, limite, permitido, formatador)
        return entrada

    def lista(self, rotulo, largura=None):
        self._rotulo(rotulo)
        caixa = ctk.CTkComboBox(self, width=largura or self.largura, height=32, corner_radius=6,
                                border_width=1, border_color=BORDA, fg_color=SUPERFICIE,
                                button_color=BORDA, button_hover_color=REALCE, text_color=TEXTO,
                                values=[], state="readonly", font=fonte(12), dropdown_font=fonte(12))
        caixa.pack(anchor="w")
        return caixa

    def botao(self, texto, comando, tipo="primario"):
        b = botao(self, texto, comando, tipo, largura=self.largura)
        b.pack(anchor="w", pady=(14, 0))
        return b


def limpar(*entradas):
    for e in entradas:
        e.delete(0, "end")


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------

class Pagina(ctk.CTkFrame):
    """Classe base das páginas: cabeçalho, acesso ao hotel e tratamento de erros."""

    titulo = ""
    subtitulo = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.hotel = app.hotel
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", pady=(0, 14))
        textos = ctk.CTkFrame(cabecalho, fg_color="transparent")
        textos.pack(side="left")
        ctk.CTkLabel(textos, text=self.titulo, font=fonte(20, True), text_color=TEXTO).pack(anchor="w")
        ctk.CTkLabel(textos, text=self.subtitulo, font=fonte(12), text_color=TEXTO_SUAVE).pack(anchor="w")
        self.acoes = ctk.CTkFrame(cabecalho, fg_color="transparent", width=1, height=1)  # botões da página
        self.acoes.pack(side="right", anchor="s")

    def atualizar(self):
        pass

    def botao_excluir(self, cartao, comando, texto="Excluir"):
        """Botão de exclusão no cabeçalho do cartão da lista."""
        botao(cartao.acoes, texto, comando, "perigo", largura=90).pack(side="right")

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
    """Tela inicial: números do dia, mapa de quartos, hospedagens em andamento e fechamento de caixa."""

    titulo = "Painel"
    subtitulo = "Situação do hotel hoje"

    def __init__(self, master, app):
        super().__init__(master, app)
        botao(self.acoes, "Fechar caixa", self.fechar_caixa, "secundario", largura=120).pack(side="right")

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x")
        self.indicadores = {}
        for i, (chave, rotulo) in enumerate([("hosp", "Em hospedagem"), ("entradas", "Chegadas hoje"),
                                             ("saidas", "Saídas hoje"), ("ocupacao", "Ocupação"),
                                             ("caixa", "Caixa aberto")]):
            card = Indicador(linha, rotulo)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            linha.columnconfigure(i, weight=1, uniform="ind")
            self.indicadores[chave] = card

        self.mapa = Cartao(self, "Quartos")
        self.mapa.pack(fill="x", pady=12)
        legenda = self.mapa.acoes
        for situacao, par in COR_SITUACAO.items():
            ctk.CTkLabel(legenda, text=f"●  {situacao}", font=fonte(11), text_color=par).pack(side="left", padx=(12, 0))
        self.grade = ctk.CTkFrame(self.mapa, fg_color="transparent", height=1)
        self.grade.pack(fill="x", padx=16, pady=12)

        lista = Cartao(self, "Hospedagens em andamento")
        lista.pack(fill="both", expand=True)
        self.tabela = Tabela(lista, ("Reserva", "Hóspede", "Quarto", "Entrada", "Saída", "Conta parcial"),
                             (80, 240, 90, 110, 110, 140), altura=5)
        self.tabela.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def fechar_caixa(self):
        pendentes = self.hotel.reservas_caixa_aberto()
        if not pendentes:
            messagebox.showinfo("Fechar caixa", "Não há hospedagens concluídas desde o último fechamento.")
            return
        total = formatar_moeda(self.hotel.faturamento_caixa_aberto())
        if not messagebox.askyesno("Fechar caixa",
                                   f"Fechar o caixa com {len(pendentes)} hospedagem(ns), total de {total}?\n\n"
                                   "O valor do painel volta a zero. Nada é apagado: o histórico "
                                   "continua na Análise de dados."):
            return
        fechamento = self.executar(self.hotel.fechar_caixa)
        if fechamento:
            caminho = self.executar(lambda: fechamento.salvar_relatorio(PASTA_FECHAMENTOS, self.hotel.nome))
            self.app.avisar(f"Caixa nº {fechamento.numero} fechado: {formatar_moeda(fechamento.total)}")
            JanelaRelatorio(self.app, fechamento.relatorio(self.hotel.nome), caminho)

    def atualizar(self):
        r = self.hotel.resumo()
        total_quartos = len(self.hotel.quartos)
        ocupados = round(r["ocupacao"] * total_quartos / 100)
        ult = self.hotel.ultimo_fechamento
        self.indicadores["hosp"].mostrar(str(len(r["em_hospedagem"])), "reservas com check-in")
        self.indicadores["entradas"].mostrar(str(len(r["entradas_hoje"])), "aguardando check-in")
        self.indicadores["saidas"].mostrar(str(len(r["saidas_hoje"])), "checkouts previstos")
        self.indicadores["ocupacao"].mostrar(f"{r['ocupacao']:.0f}%", f"{ocupados} de {total_quartos} quartos")
        self.indicadores["caixa"].mostrar(
            formatar_moeda(r["faturamento"]),
            f"desde {ult.data_hora.strftime('%d/%m %H:%M')} (nº {ult.numero})" if ult else "nenhum fechamento ainda")

        # Um bloco por quarto, com a situação indicada por um ponto colorido
        for w in self.grade.winfo_children():
            w.destroy()
        for i, quarto in enumerate(self.hotel.quartos.values()):
            situacao = self.hotel.situacao_quarto(quarto)
            q = ctk.CTkFrame(self.grade, fg_color=SUPERFICIE, corner_radius=6, border_width=1,
                             border_color=BORDA, width=138, height=76)
            q.grid(row=i // 7, column=i % 7, padx=(0, 10), pady=4)
            q.pack_propagate(False)
            ctk.CTkLabel(q, text=quarto.numero, font=fonte(15, True), text_color=TEXTO,
                         height=22).pack(anchor="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(q, text=quarto.categoria, font=fonte(11), text_color=TEXTO_SUAVE,
                         height=16).pack(anchor="w", padx=12)
            ctk.CTkLabel(q, text=f"●  {situacao}", font=fonte(11), text_color=COR_SITUACAO[situacao],
                         height=18).pack(anchor="w", padx=12, pady=(2, 0))

        self.tabela.preencher([(res.id, (res.id, res.hospede.nome, res.quarto.numero,
                                         formatar_data(res.entrada), formatar_data(res.saida),
                                         formatar_moeda(res.total)), None)
                               for res in r["em_hospedagem"]])


class JanelaRelatorio(ctk.CTkToplevel):
    """Mostra o relatório do fechamento de caixa no formato de cupom."""

    def __init__(self, app, texto, caminho):
        super().__init__(app, fg_color=SUPERFICIE)
        self.title("Fechamento de caixa")
        self.resizable(False, False)
        caixa = ctk.CTkTextbox(self, width=420, height=330, font=ctk.CTkFont(family="Consolas", size=12),
                               fg_color=FUNDO, text_color=TEXTO, corner_radius=6, border_width=1,
                               border_color=BORDA, wrap="none")
        caixa.pack(padx=16, pady=(16, 8))
        caixa.insert("1.0", texto)
        caixa.configure(state="disabled")
        if caminho:
            ctk.CTkLabel(self, text=f"Salvo em: {os.path.relpath(caminho, PASTA)}", font=fonte(11),
                         text_color=TEXTO_SUAVE).pack(anchor="w", padx=16)
        botao(self, "Fechar", self.destroy, "primario", largura=100).pack(anchor="e", padx=16, pady=(8, 16))
        self.transient(app)
        self.update_idletasks()
        x = app.winfo_rootx() + (app.winfo_width() - self.winfo_reqwidth()) // 2
        y = app.winfo_rooty() + (app.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.after(150, self.lift)


class PaginaHospedes(Pagina):
    """Tela de cadastro e exclusão de hóspedes (usa Hotel.cadastrar_hospede e Hotel.excluir_hospede)."""

    titulo = "Hóspedes"
    subtitulo = "Pessoas responsáveis pelas reservas"

    def __init__(self, master, app):
        super().__init__(master, app)
        form_card = Cartao(self, "Novo hóspede")
        form_card.pack(side="left", fill="y", padx=(0, 12))
        f = Formulario(form_card)
        f.pack(padx=16, pady=(4, 16))
        self.nome = f.campo("Nome completo", "Maria Silva", limite=LIMITES["nome"])
        self.doc = f.campo("CPF ou RG", "000.000.000-00", limite=LIMITES["documento"],
                           formatador=mascara_documento)
        self.tel = f.campo("Telefone (opcional)", "(00) 00000-0000", limite=LIMITES["telefone"],
                           formatador=mascara_telefone)
        f.botao("Cadastrar hóspede", self.cadastrar)

        lista = Cartao(self, "Hóspedes cadastrados")
        lista.pack(side="left", fill="both", expand=True)
        self.botao_excluir(lista, self.excluir)
        self.tabela = Tabela(lista, ("ID", "Nome", "Documento", "Telefone"), (50, 230, 150, 140))
        self.tabela.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def cadastrar(self):
        if self.executar(lambda: self.hotel.cadastrar_hospede(self.nome.get(), self.doc.get(), self.tel.get()),
                         "Hóspede cadastrado."):
            limpar(self.nome, self.doc, self.tel)

    def excluir(self):
        self.excluir_selecionado(self.tabela, lambda k: self.hotel.hospedes[int(k)].nome,
                                 lambda k: self.hotel.excluir_hospede(int(k)))

    def atualizar(self):
        self.tabela.preencher([(h.id, (h.id, h.nome, h.documento_formatado, h.telefone_formatado), None)
                               for h in self.hotel.hospedes.values()])


class PaginaQuartos(Pagina):
    """Tela de cadastro de quartos, alteração da diária e exclusão (usa os métodos de quarto do Hotel)."""

    titulo = "Quartos"
    subtitulo = "Capacidade e diária de cada quarto"

    def __init__(self, master, app):
        super().__init__(master, app)
        form_card = Cartao(self, "Novo quarto")
        form_card.pack(side="left", fill="y", padx=(0, 12))
        f = Formulario(form_card)
        f.pack(padx=16, pady=(4, 16))
        self.numero = f.campo("Número", "101", limite=LIMITES["numero_quarto"])
        self.categoria = f.campo("Categoria", "Standard, Luxo...", limite=LIMITES["categoria"])
        self.capacidade = f.campo("Capacidade (pessoas)", "2", limite=2, permitido=so_numeros)
        self.diaria = f.campo("Diária (R$)", "180,00")
        f.botao("Cadastrar quarto", self.cadastrar)
        f.botao("Alterar diária do selecionado", self.alterar_diaria, "secundario")

        lista = Cartao(self, "Quartos do hotel")
        lista.pack(side="left", fill="both", expand=True)
        self.botao_excluir(lista, self.excluir)
        self.tabela = Tabela(lista, ("Número", "Categoria", "Capacidade", "Diária atual"), (90, 180, 110, 130))
        self.tabela.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def cadastrar(self):
        if self.executar(lambda: self.hotel.cadastrar_quarto(self.numero.get(), self.categoria.get(),
                                                             int(self.capacidade.get()), self.diaria.get()),
                         "Quarto cadastrado."):
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
        self.executar(acao, "Diária alterada. Reservas já feitas mantêm a diária contratada.")

    def atualizar(self):
        self.tabela.preencher([(q.numero, (q.numero, q.categoria, q.capacidade, formatar_moeda(q.diaria)), None)
                               for q in self.hotel.quartos.values()])


class PaginaServicos(Pagina):
    """Tela do catálogo de serviços extras (frigobar, lavanderia...)."""

    titulo = "Serviços"
    subtitulo = "Catálogo de extras: frigobar, lavanderia, refeições"

    def __init__(self, master, app):
        super().__init__(master, app)
        form_card = Cartao(self, "Novo serviço")
        form_card.pack(side="left", fill="y", padx=(0, 12))
        f = Formulario(form_card)
        f.pack(padx=16, pady=(4, 16))
        self.descricao = f.campo("Descrição", "Água (frigobar)", limite=LIMITES["descricao"])
        self.preco = f.campo("Preço (R$)", "10,00")
        f.botao("Cadastrar serviço", self.cadastrar)

        lista = Cartao(self, "Catálogo")
        lista.pack(side="left", fill="both", expand=True)
        self.botao_excluir(lista, self.excluir)
        self.tabela = Tabela(lista, ("ID", "Descrição", "Preço"), (50, 300, 120))
        self.tabela.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def cadastrar(self):
        if self.executar(lambda: self.hotel.cadastrar_servico(self.descricao.get(), self.preco.get()),
                         "Serviço cadastrado."):
            limpar(self.descricao, self.preco)

    def excluir(self):
        self.excluir_selecionado(self.tabela, lambda k: f"'{self.hotel.servicos[int(k)].descricao}'",
                                 lambda k: self.hotel.excluir_servico(int(k)))

    def atualizar(self):
        self.tabela.preencher([(s.id, (s.id, s.descricao, formatar_moeda(s.preco)), None)
                               for s in self.hotel.servicos.values()])


class PaginaReservas(Pagina):
    """Tela de reservas: consulta quartos livres (Hotel.quartos_disponiveis), reserva e cancela."""

    titulo = "Reservas"
    subtitulo = "Consulte a disponibilidade e reserve um quarto"

    def __init__(self, master, app):
        super().__init__(master, app)
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x")

        busca = Cartao(topo, "Pesquisar disponibilidade")
        busca.pack(side="left", fill="y", padx=(0, 12))
        f = Formulario(busca, largura=260)
        f.pack(padx=16, pady=(0, 16))
        self.hospede = f.lista("Hóspede")
        datas = ctk.CTkFrame(f, fg_color="transparent")
        datas.pack(anchor="w")
        f_entrada, f_saida = Formulario(datas, 124), Formulario(datas, 124)
        f_entrada.pack(side="left", padx=(0, 12))
        f_saida.pack(side="left")
        self.entrada = f_entrada.campo("Entrada", "dd/mm/aaaa")
        self.saida = f_saida.campo("Saída", "dd/mm/aaaa")
        self.pessoas = f.campo("Pessoas", "2", largura=124, limite=2, permitido=so_numeros)
        f.botao("Consultar quartos livres", self.consultar)

        escolha = Cartao(topo, "Quartos disponíveis")
        escolha.pack(side="left", fill="both", expand=True)
        botao(escolha.acoes, "Confirmar reserva", self.reservar, "primario", largura=150).pack(side="right")
        self.disponiveis = Tabela(escolha, ("Quarto", "Categoria", "Cap.", "Diária", "Valor estimado"),
                                  (70, 110, 50, 100, 130), altura=5)
        self.disponiveis.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        lista = Cartao(self, "Todas as reservas")
        lista.pack(fill="both", expand=True, pady=(12, 0))
        botao(lista.acoes, "Cancelar reserva", self.cancelar, "perigo", largura=140).pack(side="right")
        self.tabela = Tabela(lista, ("Nº", "Hóspede", "Quarto", "Entrada", "Saída", "Pessoas",
                                     "Diárias", "Diária contratada", "Situação"),
                             (40, 150, 62, 95, 95, 70, 62, 130, 120), altura=6)
        self.tabela.pack(fill="both", expand=True, padx=12, pady=(4, 12))
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
    """Tela da estadia: check-in, lançamento de consumos, conta (Reserva.extrato) e checkout."""

    titulo = "Hospedagem"
    subtitulo = "Check-in, consumos e fechamento da conta"

    def __init__(self, master, app):
        super().__init__(master, app)
        esquerda = ctk.CTkFrame(self, fg_color="transparent")
        esquerda.pack(side="left", fill="y", padx=(0, 12))

        lista = Cartao(esquerda, "Reservas confirmadas e em hospedagem")
        lista.pack(fill="both", expand=True)
        botao(lista.acoes, "Fazer check-in", self.check_in, "primario", largura=120).pack(side="right")
        self.tabela = Tabela(lista, ("Nº", "Hóspede", "Quarto", "Período", "Situação"),
                             (40, 140, 66, 182, 125), altura=8)
        self.tabela.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self.tabela.tree.bind("<<TreeviewSelect>>", lambda e: self.mostrar_conta())

        consumo = Cartao(esquerda, "Lançar consumo")
        consumo.pack(fill="x", pady=(12, 0))
        linha = ctk.CTkFrame(consumo, fg_color="transparent")
        linha.pack(anchor="w", padx=16, pady=(0, 16))
        f_servico, f_qtd = Formulario(linha, 300), Formulario(linha, 90)
        f_servico.pack(side="left", padx=(0, 12))
        f_qtd.pack(side="left", padx=(0, 12))
        self.servico = f_servico.lista("Serviço")
        self.qtd = f_qtd.campo("Quantidade", "1", limite=3, permitido=so_numeros)
        botao(linha, "Lançar", self.lancar, "secundario", largura=90).pack(side="left", anchor="s")

        # Conta
        recibo = Cartao(self, "Conta da hospedagem")
        recibo.pack(side="left", fill="both", expand=True)
        self.extrato = ctk.CTkTextbox(recibo, font=ctk.CTkFont(family="Consolas", size=12),
                                      fg_color=FUNDO, text_color=TEXTO, corner_radius=6, border_width=1,
                                      border_color=BORDA, wrap="none")
        self.extrato.pack(fill="both", expand=True, padx=16, pady=(12, 0))
        rodape = ctk.CTkFrame(recibo, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=16)
        ctk.CTkLabel(rodape, text="TOTAL A PAGAR", font=fonte(10, True), text_color=TEXTO_SUAVE).pack(anchor="w")
        self.total = ctk.CTkLabel(rodape, text="R$ 0,00", font=fonte(26, True), text_color=TEXTO)
        self.total.pack(anchor="w")
        b = botao(rodape, "Confirmar checkout", self.checkout, "primario")
        b.configure(height=38, font=fonte(13, True))
        b.pack(fill="x", pady=(8, 0))

    def _reserva(self):
        rid = self.tabela.selecionado()
        if not rid:
            messagebox.showinfo("Atenção", "Selecione uma reserva na lista.")
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
        if self.executar(lambda: (r.lancar_consumo(servico, int(self.qtd.get())), self.hotel.salvar()),
                         f"{servico.descricao} lançado na reserva nº {r.id}."):
            limpar(self.qtd)

    def checkout(self):
        r = self._reserva()
        if not r:
            return
        if r.status == StatusReserva.EM_HOSPEDAGEM and not messagebox.askyesno(
                "Checkout", f"Confirmar checkout com total de {formatar_moeda(r.total)}?"):
            return
        self.executar(lambda: (r.checkout(), self.hotel.salvar()),
                      f"Hospedagem concluída. Total pago: {formatar_moeda(r.total)}")

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
        self.configure(bg=cor(SUPERFICIE))
        self.delete("all")
        suave, forte, linha, barra = cor(TEXTO_SUAVE), cor(TEXTO), cor(BORDA), cor(ACENTO)
        largura, altura = self.winfo_width(), self.winfo_height()
        if largura < 50:
            return
        if not self.itens:
            self.create_text(largura / 2, altura / 2, text="Sem dados no período", fill=suave,
                             font=("Segoe UI", 10))
            return
        maior = max(float(v) for _, v in self.itens) or 1
        n = len(self.itens)
        letra = ("Segoe UI", 8)
        if not self.horizontal:                                  # colunas
            base, topo = altura - 22, 18
            self.create_line(0, base, largura, base, fill=linha)
            passo = largura / n
            for i, (rotulo, valor) in enumerate(self.itens):
                meio, meia = (i + 0.5) * passo, min(passo * 0.28, 28)  # barra de no máximo 56 px
                x0, x1 = meio - meia, meio + meia
                y0 = base - (base - topo) * float(valor) / maior
                self.create_rectangle(x0, y0, x1, base, fill=barra, outline="")
                self.create_text((x0 + x1) / 2, y0 - 8, text=abreviar(valor), fill=forte, font=letra)
                self.create_text((x0 + x1) / 2, altura - 10, text=rotulo, fill=suave, font=letra)
        else:                                                    # barras deitadas
            esquerda, direita = 40, 64
            self.create_line(esquerda, 0, esquerda, altura, fill=linha)
            passo = altura / n
            for i, (rotulo, valor) in enumerate(self.itens):
                meio, meia = (i + 0.5) * passo, min(passo * 0.28, 11)  # barra de no máximo 22 px
                y0, y1 = meio - meia, meio + meia
                x1 = esquerda + (largura - esquerda - direita) * float(valor) / maior
                self.create_rectangle(esquerda, y0, x1, y1, fill=barra, outline="")
                self.create_text(esquerda - 6, (y0 + y1) / 2, text=rotulo, fill=suave, font=letra, anchor="e")
                self.create_text(x1 + 6, (y0 + y1) / 2, text=abreviar(valor), fill=forte, font=letra, anchor="w")


class PaginaAnalise(Pagina):
    """Tela de Análise de dados: mostra os indicadores calculados pela classe Analise (analise.py)."""

    titulo = "Análise de dados"
    subtitulo = "Indicadores calculados a partir do arquivo JSON"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.fonte = "hotel"        # "hotel" ou o caminho de um arquivo JSON escolhido
        self.analise = None

        botao(self.acoes, "Exportar CSV", self.exportar, "secundario", largura=110).pack(side="right")
        botao(self.acoes, "Abrir JSON…", self.abrir_arquivo, "secundario", largura=110).pack(side="right", padx=(0, 8))
        # só aparece quando outro arquivo está aberto
        self.botao_voltar = botao(self.acoes, "Voltar aos dados do hotel", self.usar_hotel, "secundario", largura=190)

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x")
        self.indicadores = {}
        for i, (chave, rotulo) in enumerate([("fat", "Faturamento"), ("hosp", "Hospedagens"),
                                             ("ticket", "Ticket médio"), ("ocup", "Taxa de ocupação"),
                                             ("cancel", "Cancelamentos")]):
            card = Indicador(linha, rotulo)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            linha.columnconfigure(i, weight=1, uniform="ind")
            self.indicadores[chave] = card

        graficos = ctk.CTkFrame(self, fg_color="transparent")
        graficos.pack(fill="x", pady=12)
        graficos.columnconfigure(0, weight=3, uniform="g")
        graficos.columnconfigure(1, weight=2, uniform="g")
        c1 = Cartao(graficos, "Faturamento por mês")
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.grafico_mes = Grafico(c1, 150)
        self.grafico_mes.pack(fill="x", padx=16, pady=12)
        c2 = Cartao(graficos, "Faturamento por quarto")
        c2.grid(row=0, column=1, sticky="nsew")
        self.grafico_quarto = Grafico(c2, 150)
        self.grafico_quarto.pack(fill="x", padx=16, pady=12)

        tabelas = ctk.CTkFrame(self, fg_color="transparent")
        tabelas.pack(fill="both", expand=True)
        tabelas.columnconfigure(0, weight=1, uniform="t")
        tabelas.columnconfigure(1, weight=1, uniform="t")
        tabelas.rowconfigure(0, weight=1)
        t1 = Cartao(tabelas, "Serviços mais consumidos")
        t1.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.tabela_servicos = Tabela(t1, ("Serviço", "Qtd", "Valor"), (210, 60, 110), altura=4)
        self.tabela_servicos.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        t2 = Cartao(tabelas, "Hóspedes que mais gastaram")
        t2.grid(row=0, column=1, sticky="nsew")
        self.tabela_hospedes = Tabela(t2, ("Hóspede", "Hospedagens", "Total gasto"), (175, 120, 110), altura=4)
        self.tabela_hospedes.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    # ----- escolha da fonte dos dados -----
    def _trocar_fonte(self, fonte_dados):
        self.fonte = fonte_dados
        self.atualizar()

    def usar_hotel(self):
        self._trocar_fonte("hotel")

    def abrir_arquivo(self):
        caminho = filedialog.askopenfilename(title="Escolha um arquivo de dados do hotel",
                                             filetypes=[("Arquivos JSON", "*.json"), ("Todos", "*.*")])
        if caminho:
            self._trocar_fonte(caminho)

    def exportar(self):
        caminho = filedialog.asksaveasfilename(title="Exportar hospedagens concluídas",
                                               defaultextension=".csv", initialfile="faturamento.csv",
                                               filetypes=[("CSV (abre no Excel)", "*.csv")])
        if caminho:
            n = self.executar(lambda: self.analise.exportar_csv(caminho))
            if n is not None:
                self.app.avisar(f"{n} hospedagens exportadas para {os.path.basename(caminho)}.")

    def _carregar(self) -> Analise:
        if self.fonte == "hotel":
            return Analise(self.hotel, "Dados do hotel")
        return Analise.de_arquivo(self.fonte)

    def atualizar(self):
        try:
            self.analise = self._carregar()
        except RegraNegocioErro as e:
            messagebox.showwarning("Não foi possível abrir", str(e))
            self.fonte = "hotel"
            self.analise = self._carregar()
        if self.fonte == "hotel":
            self.botao_voltar.pack_forget()
        else:
            self.botao_voltar.pack(side="right", padx=(0, 8))
        a = self.analise
        self.app.mostrar_fonte(a.origem)
        periodo = a.periodo()
        texto_periodo = f"{formatar_data(periodo[0])} a {formatar_data(periodo[1])}" if periodo else "sem hospedagens"
        self.indicadores["fat"].mostrar(formatar_moeda(a.faturamento_total()), texto_periodo)
        self.indicadores["hosp"].mostrar(str(len(a.concluidas)), f"{a.duracao_media():.1f} diárias em média")
        self.indicadores["ticket"].mostrar(formatar_moeda(a.ticket_medio()), "por hospedagem concluída")
        self.indicadores["ocup"].mostrar(f"{a.taxa_ocupacao():.0f}%", "diárias vendidas no período")
        self.indicadores["cancel"].mostrar(f"{a.taxa_cancelamento():.0f}%", f"de {a.total_reservas} reservas")
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
    """Janela principal: monta o menu lateral, cria uma página de cada tipo e troca entre elas."""

    # (seção do menu, nome, classe da página)
    PAGINAS = [("Operação", "Painel", PaginaPainel),
               ("Operação", "Reservas", PaginaReservas),
               ("Operação", "Hospedagem", PaginaHospedagem),
               ("Cadastros", "Hóspedes", PaginaHospedes),
               ("Cadastros", "Quartos", PaginaQuartos),
               ("Cadastros", "Serviços", PaginaServicos),
               ("Relatórios", "Análise de dados", PaginaAnalise)]

    def __init__(self, hotel: Hotel):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        super().__init__(fg_color=FUNDO)
        self.hotel = hotel
        self.title(f"{hotel.nome} - Recepção")
        self.geometry("1280x780")
        self.minsize(1100, 680)
        self.after(0, self._maximizar)
        estilizar_tabelas()

        # ----- menu lateral -----
        menu = ctk.CTkFrame(self, fg_color=MENU, corner_radius=0, width=220)
        menu.pack(side="left", fill="y")
        menu.pack_propagate(False)
        marca = ctk.CTkFrame(menu, fg_color="transparent")
        marca.pack(fill="x", padx=18, pady=(22, 18))
        iniciais = "".join(p[0] for p in hotel.nome.split()[:2]).upper() or "H"
        ctk.CTkLabel(marca, text=iniciais, width=34, height=34, corner_radius=6, fg_color=ACENTO,
                     text_color="#ffffff", font=fonte(13, True)).pack(side="left")
        nomes = ctk.CTkFrame(marca, fg_color="transparent")
        nomes.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(nomes, text=hotel.nome, font=fonte(13, True), text_color="#ffffff").pack(anchor="w")
        ctk.CTkLabel(nomes, text="Recepção", font=fonte(11), text_color="#8b96a5").pack(anchor="w")

        self.botoes = []
        secao_atual = None
        for i, (secao, texto, _) in enumerate(self.PAGINAS):
            if secao != secao_atual:
                ctk.CTkLabel(menu, text=secao.upper(), font=fonte(10, True), text_color="#7d8896").pack(
                    anchor="w", padx=22, pady=(14, 4))
                secao_atual = secao
            b = ctk.CTkButton(menu, text=texto, anchor="w", height=34, corner_radius=6,
                              font=fonte(13), fg_color="transparent", hover_color=MENU_ATIVO,
                              text_color=MENU_TEXTO, command=lambda i=i: self.mostrar(i))
            b.pack(fill="x", padx=12, pady=1)
            self.botoes.append(b)

        self.tema = ctk.CTkSwitch(menu, text="Tema escuro", text_color=MENU_TEXTO, font=fonte(12),
                                  command=self.alternar_tema, progress_color=ACENTO)
        self.tema.pack(side="bottom", anchor="w", padx=22, pady=18)

        # ----- barra de status (rodapé) -----
        status = ctk.CTkFrame(self, fg_color=SUPERFICIE, corner_radius=0, height=30)
        status.pack(side="bottom", fill="x")
        status.pack_propagate(False)
        ctk.CTkFrame(status, height=1, fg_color=BORDA).pack(side="top", fill="x")
        self.mensagem = ctk.CTkLabel(status, text="Pronto", font=fonte(11), text_color=TEXTO_SUAVE)
        self.mensagem.pack(side="left", padx=16)
        self.info = ctk.CTkLabel(status, text="", font=fonte(11), text_color=TEXTO_SUAVE)
        self.info.pack(side="right", padx=16)

        # ----- área das páginas -----
        area = ctk.CTkFrame(self, fg_color="transparent")
        area.pack(side="left", fill="both", expand=True, padx=24, pady=(20, 14))
        self.paginas = []
        for _, _, classe in self.PAGINAS:
            pagina = classe(area, self)
            pagina.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.paginas.append(pagina)

        self._aviso_id = None
        self.indice_atual = 0
        self.mostrar(0)

    def _maximizar(self):
        try:
            self.state("zoomed")  # abre maximizada no Windows
        except tk.TclError:
            pass  # em outros sistemas mantém o tamanho padrão

    def mostrar(self, indice):
        """Traz a página escolhida para a frente e atualiza seus dados."""
        for i, b in enumerate(self.botoes):
            ativo = i == indice
            b.configure(fg_color=MENU_ATIVO if ativo else "transparent",
                        text_color="#ffffff" if ativo else MENU_TEXTO,
                        font=fonte(13, ativo))
        self.indice_atual = indice
        self.mostrar_fonte(os.path.basename(self.hotel.arquivo) if self.hotel.arquivo else "dados em memória")
        pagina = self.paginas[indice]
        pagina.atualizar()
        pagina.tkraise()

    def mostrar_fonte(self, nome):
        self.info.configure(text=f"{nome}   ·   {data_por_extenso(date.today())}")

    def avisar(self, texto):
        """Mostra o resultado da última operação na barra de status."""
        hora = datetime.now().strftime("%H:%M")
        self.mensagem.configure(text=f"●  {texto}   ({hora})", text_color=VERDE)
        if self._aviso_id:
            self.after_cancel(self._aviso_id)
        self._aviso_id = self.after(8000, lambda: self.mensagem.configure(text="Pronto", text_color=TEXTO_SUAVE))

    def alternar_tema(self):
        ctk.set_appearance_mode("dark" if self.tema.get() else "light")
        estilizar_tabelas()
        self.paginas[self.indice_atual].atualizar()  # redesenha os gráficos com as cores do tema


if __name__ == "__main__":
    Aplicacao(Hotel.carregar(ARQUIVO_DADOS)).mainloop()
