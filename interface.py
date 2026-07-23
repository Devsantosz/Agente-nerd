import customtkinter as ctk
import threading
from PIL import Image, ImageTk

from agent import conversar, gerar_titulo

from database import (
    criar_conversa,
    listar_conversas,
    salvar_mensagem,
    carregar_mensagens,
    atualizar_titulo,
    excluir_conversa
)


# ==========================
# PALETA ROXO / PRETO
# ==========================
COR_FUNDO          = "#150c22"   # fundo geral (preto arroxeado)
COR_SIDEBAR        = "#1b1030"   # fundo da sidebar
COR_CARD           = "#241a3d"   # cards / itens de lista / balão do agente
COR_CARD_HOVER     = "#2f2150"   # hover de itens de lista
COR_ROXO           = "#8b3ff5"   # roxo principal (botões, balão do usuário)
COR_ROXO_HOVER     = "#a869ff"   # roxo claro (hover)
COR_ROXO_SUAVE     = "#c9a6ff"   # detalhes suaves / texto de destaque
COR_TEXTO          = "#f1eafc"   # texto claro
COR_TEXTO_MUTED    = "#9d8ab8"   # texto secundário
COR_PERIGO         = "#e0335f"   # excluir
COR_PERIGO_HOVER   = "#ff5c85"   # excluir hover
COR_TRANSPARENTE   = "transparent"


class ChatInterface(ctk.CTk):

    def __init__(self):
        super().__init__()

        # ==========================
        # CONFIGURAÇÃO DA JANELA
        # ==========================
        self.title("Pretinho Nerd")
        self.geometry("1200x750")
        self.minsize(350, 900)

        icone = ImageTk.PhotoImage(Image.open("assets/logo.png"))
        self.iconphoto(True, icone)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.configure(fg_color=COR_FUNDO)

        self.conversa_atual = None
        self.primeira_mensagem = True

        # Controle sidebar
        self.sidebar_aberta = True
        self.sidebar_manual = False
        self.largura_min_sidebar = 1000

        self.bind("<Configure>", self.verificar_tamanho)

        # ==========================
        # CONTAINER PRINCIPAL
        # ==========================
        self.container = ctk.CTkFrame(self, fg_color=COR_FUNDO)
        self.container.pack(fill="both", expand=True)

        # ==========================
        # SIDEBAR
        # ==========================
        self.sidebar = ctk.CTkFrame(
            self.container,
            width=280,
            fg_color=COR_SIDEBAR,
            corner_radius=0
        )
        self.sidebar.pack_propagate(False)
        self.sidebar.pack(side="left", fill="y")

        titulo = ctk.CTkLabel(
            self.sidebar,
            text="💬 Conversas",
            font=("Segoe UI", 22, "bold"),
            text_color=COR_TEXTO
        )
        titulo.pack(pady=20)

        self.botao_nova = ctk.CTkButton(
            self.sidebar,
            text="+ Nova conversa",
            command=self.nova_conversa,
            fg_color=COR_ROXO,
            hover_color=COR_ROXO_HOVER,
            text_color="white",
            corner_radius=14,
            font=("Segoe UI", 12, "bold"),
            height=38
        )
        self.botao_nova.pack(padx=20, pady=10, fill="x")

        self.lista_conversas = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color=COR_TRANSPARENTE
        )
        self.lista_conversas.pack(fill="both", expand=True, padx=10, pady=10)

        # ==========================
        # ÁREA DO CHAT
        # ==========================
        self.area_chat = ctk.CTkFrame(self.container, fg_color=COR_FUNDO)
        self.area_chat.pack(side="right", fill="both", expand=True)

        # HEADER
        self.header = ctk.CTkFrame(
            self.area_chat,
            fg_color=COR_SIDEBAR,
            corner_radius=16,
            height=64
        )
        self.header.pack(fill="x", padx=20, pady=(20, 10))

        self.menu = ctk.CTkButton(
            self.header,
            text="☰",
            width=45,
            fg_color=COR_TRANSPARENTE,
            hover_color=COR_CARD_HOVER,
            text_color=COR_TEXTO,
            corner_radius=10,
            command=self.alternar_sidebar
        )
        self.menu.pack(side="left", padx=10, pady=10)

        self.titulo = ctk.CTkLabel(
            self.header,
            text=" Pretinho Nerd",
            font=("Segoe UI", 24, "bold"),
            text_color=COR_TEXTO
        )
        self.titulo.pack(side="left", pady=10)

        # ==========================
        # CHAT
        # ==========================
        self.chat = ctk.CTkScrollableFrame(
            self.area_chat,
            fg_color=COR_FUNDO
        )
        self.chat.pack(fill="both", expand=True, padx=20, pady=10)

        # ==========================
        # INPUT
        # ==========================
        footer = ctk.CTkFrame(
            self.area_chat,
            fg_color=COR_SIDEBAR,
            corner_radius=16
        )
        footer.pack(fill="x", padx=20, pady=15)

        self.entrada = ctk.CTkTextbox(
            footer,
            height=40,
            fg_color=COR_CARD,
            text_color=COR_TEXTO,
            corner_radius=12,
            border_width=0,
            font=("Segoe UI", 12)
        )
        self.entrada.pack(side="left", fill="x", expand=True, padx=10, pady=10)

        enviar = ctk.CTkButton(
            footer,
            text="Enviar",
            width=120,
            height=40,
            fg_color=COR_ROXO,
            hover_color=COR_ROXO_HOVER,
            text_color="white",
            corner_radius=12,
            font=("Segoe UI", 12, "bold"),
            command=self.responder
        )
        enviar.pack(side="right", padx=10, pady=10)

        self.entrada.bind("<Return>", self.enter)

        self.atualizar_lista()
        self.nova_conversa()

    # ==========================
    # ENTER
    # ==========================
    def enter(self, event):
        self.responder()
        return "break"

    # ==========================
    # NOVA CONVERSA
    # ==========================
    def nova_conversa(self):
        self.conversa_atual = criar_conversa("Nova conversa")
        self.primeira_mensagem = True
        self.limpar_chat()
        self.atualizar_lista()

    # ==========================
    # LISTA
    # ==========================
    def atualizar_lista(self):
        for widget in self.lista_conversas.winfo_children():
            widget.destroy()

        for id_, titulo in listar_conversas():

            linha = ctk.CTkFrame(
                self.lista_conversas,
                fg_color=COR_CARD,
                corner_radius=12
            )
            linha.pack(fill="x", pady=5)

            abrir = ctk.CTkButton(
                linha,
                text=titulo,
                anchor="w",
                fg_color=COR_TRANSPARENTE,
                hover_color=COR_CARD_HOVER,
                text_color=COR_TEXTO,
                corner_radius=12,
                font=("Segoe UI", 12),
                command=lambda id=id_: self.abrir_conversa(id)
            )
            abrir.pack(side="left", fill="x", expand=True)

            apagar = ctk.CTkButton(
                linha,
                text="🗑",
                width=36,
                fg_color=COR_TRANSPARENTE,
                hover_color=COR_PERIGO_HOVER,
                text_color=COR_PERIGO,
                corner_radius=12,
                command=lambda id=id_: self.remover_conversa(id)
            )
            apagar.pack(side="right", padx=4, pady=4)

    # ==========================
    # ABRIR CONVERSA
    # ==========================
    def abrir_conversa(self, id):
        self.conversa_atual = id
        self.primeira_mensagem = False
        self.limpar_chat()

        for remetente, texto in carregar_mensagens(id):
            self.criar_balao(texto, remetente == "usuario")

    # ==========================
    # REMOVER
    # ==========================
    def remover_conversa(self, id):
        excluir_conversa(id)

        if self.conversa_atual == id:
            self.nova_conversa()

        self.atualizar_lista()

    # ==========================
    # LIMPAR
    # ==========================
    def limpar_chat(self):
        for widget in self.chat.winfo_children():
            widget.destroy()

    # ==========================
    # BALÃO
    # ==========================
    def criar_balao(self, texto, usuario=True):

        container = ctk.CTkFrame(self.chat, fg_color=COR_TRANSPARENTE)
        container.pack(fill="x", pady=5, padx=10)

        balao = ctk.CTkFrame(
            container,
            fg_color=COR_ROXO if usuario else COR_CARD,
            corner_radius=16
        )
        balao.pack(anchor="e" if usuario else "w")

        label = ctk.CTkLabel(
            balao,
            text=texto,
            wraplength=600,
            justify="left",
            text_color="white" if usuario else COR_TEXTO,
            font=("Segoe UI", 12)
        )
        label.pack(padx=15, pady=10)

    # ==========================
    # RESPONDER
    # ==========================
    def responder(self):

        pergunta = self.entrada.get("1.0", "end").strip()

        if not pergunta:
            return

        self.entrada.delete("1.0", "end")

        self.criar_balao(pergunta, True)

        salvar_mensagem(self.conversa_atual, "usuario", pergunta)

        if self.primeira_mensagem:
            titulo = gerar_titulo(pergunta)
            atualizar_titulo(self.conversa_atual, titulo)
            self.primeira_mensagem = False
            self.atualizar_lista()

        def tarefa():
            resposta = conversar(pergunta)
            self.after(0, lambda: self.finalizar_resposta(resposta))

        threading.Thread(target=tarefa, daemon=True).start()

    def finalizar_resposta(self, resposta):
        self.criar_balao(resposta, False)
        salvar_mensagem(self.conversa_atual, "agente", resposta)

    # ==========================
    # SIDEBAR RESPONSIVA
    # ==========================
    def alternar_sidebar(self):
        if self.sidebar_aberta:
            self.sidebar.pack_forget()
            self.sidebar_aberta = False
            self.sidebar_manual = True
        else:
            self.sidebar.pack(side="left", fill="y")
            self.sidebar_aberta = True
            self.sidebar_manual = False

    def verificar_tamanho(self, event):
        largura = self.winfo_width()

        if largura < self.largura_min_sidebar:
            if self.sidebar_aberta:
                self.sidebar.pack_forget()
                self.sidebar_aberta = False
        else:
            if not self.sidebar_aberta and not self.sidebar_manual:
                self.sidebar.pack(side="left", fill="y")
                self.sidebar_aberta = True