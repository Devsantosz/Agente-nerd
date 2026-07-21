import customtkinter as ctk
import threading
from PIL import Image

from agent import conversar, gerar_titulo

from database import (
    criar_conversa,
    listar_conversas,
    salvar_mensagem,
    carregar_mensagens,
    atualizar_titulo,
    excluir_conversa
)


class ChatInterface(ctk.CTk):

    def __init__(self):

        super().__init__()


        # ==========================
        # CONFIGURAÇÃO DA JANELA
        # ==========================

        self.title("Pretinho Nerd")

        self.geometry("1200x750")

        self.minsize(
            900,
            600
        )
        icone = ctk.CTkImage(
            light_image=Image.open("assets/logo.png"),
            dark_image=Image.open("assets/logo.png"),
            size=(64,64)
        )


        self.iconphoto(
            True,
            icone._light_image
        )


        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")


        self.conversa_atual = None

        self.primeira_mensagem = True


        # Controle sidebar

        self.sidebar_aberta = True
        self.sidebar_manual = False

        self.largura_min_sidebar = 1000



        self.bind(
            "<Configure>",
            self.verificar_tamanho
        )


        # ==========================
        # CONTAINER PRINCIPAL
        # ==========================


        self.container = ctk.CTkFrame(
            self
        )


        self.container.pack(
            fill="both",
            expand=True
        )



        # ==========================
        # SIDEBAR
        # ==========================


        self.sidebar = ctk.CTkFrame(
            self.container,
            width=280
        )


        self.sidebar.pack_propagate(
            False
        )


        self.sidebar.pack(
            side="left",
            fill="y"
        )



        titulo = ctk.CTkLabel(
            self.sidebar,
            text="💬 Conversas",
            font=(
                "Segoe UI",
                22,
                "bold"
            )
        )


        titulo.pack(
            pady=20
        )



        self.botao_nova = ctk.CTkButton(
            self.sidebar,
            text="+ Nova conversa",
            command=self.nova_conversa
        )


        self.botao_nova.pack(
            padx=20,
            pady=10,
            fill="x"
        )



        self.lista_conversas = ctk.CTkScrollableFrame(
            self.sidebar
        )


        self.lista_conversas.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )



        # ==========================
        # ÁREA DO CHAT
        # ==========================


        self.area_chat = ctk.CTkFrame(
            self.container
        )


        self.area_chat.pack(
            side="right",
            fill="both",
            expand=True
        )



        # HEADER


        self.header = ctk.CTkFrame(
            self.area_chat
        )


        self.header.pack(
            fill="x",
            pady=10
        )



        self.menu = ctk.CTkButton(
            self.header,
            text="☰",
            width=45,
            fg_color="transparent",
            hover_color="#333333",
            command=self.alternar_sidebar
        )


        self.menu.pack(
            side="left",
            padx=10
        )



        self.titulo = ctk.CTkLabel(
            self.header,
            text="🤖 Pretinho Nerd",
            font=(
                "Segoe UI",
                26,
                "bold"
            )
        )


        self.titulo.pack(
            side="left"
        )



        # ==========================
        # CHAT
        # ==========================


        self.chat = ctk.CTkScrollableFrame(
            self.area_chat
        )


        self.chat.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )



        # ==========================
        # INPUT
        # ==========================


        footer = ctk.CTkFrame(
            self.area_chat
        )


        footer.pack(
            fill="x",
            padx=20,
            pady=15
        )



        self.entrada = ctk.CTkTextbox(
            footer,
            height=60
        )


        self.entrada.pack(
            side="left",
            fill="x",
            expand=True
        )



        enviar = ctk.CTkButton(
            footer,
            text="Enviar",
            width=120,
            command=self.responder
        )


        enviar.pack(
            side="right",
            padx=10
        )



        self.entrada.bind(
            "<Return>",
            self.enter
        )



        self.atualizar_lista()

        self.nova_conversa()



    # ==========================
    # ENTER
    # ==========================


    def enter(self,event):

        self.responder()

        return "break"



    # ==========================
    # NOVA CONVERSA
    # ==========================


    def nova_conversa(self):


        self.conversa_atual = criar_conversa(
            "Nova conversa"
        )


        self.primeira_mensagem = True


        self.limpar_chat()


        self.atualizar_lista()



    # ==========================
    # LISTA
    # ==========================


    def atualizar_lista(self):


        for widget in self.lista_conversas.winfo_children():

            widget.destroy()



        for id_,titulo in listar_conversas():


            linha = ctk.CTkFrame(
                self.lista_conversas
            )


            linha.pack(
                fill="x",
                pady=5
            )



            abrir = ctk.CTkButton(
                linha,
                text=titulo,
                anchor="w",
                command=lambda id=id_: self.abrir_conversa(id)
            )


            abrir.pack(
                side="left",
                fill="x",
                expand=True
            )



            apagar = ctk.CTkButton(
                linha,
                text="🗑",
                width=40,
                fg_color="#8B0000",
                hover_color="#B22222",
                command=lambda id=id_: self.remover_conversa(id)
            )


            apagar.pack(
                side="right"
            )



    # ==========================
    # ABRIR CONVERSA
    # ==========================


    def abrir_conversa(self,id):


        self.conversa_atual = id

        self.primeira_mensagem = False


        self.limpar_chat()



        for remetente,texto in carregar_mensagens(id):


            self.criar_balao(
                texto,
                remetente == "usuario"
            )



    # ==========================
    # REMOVER
    # ==========================


    def remover_conversa(self,id):


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


    def criar_balao(
            self,
            texto,
            usuario=True):


        container = ctk.CTkFrame(
            self.chat,
            fg_color="transparent"
        )


        container.pack(
            fill="x",
            pady=5,
            padx=10
        )



        balao = ctk.CTkFrame(
            container,
            fg_color=(
                "#2563EB"
                if usuario
                else "#333333"
            ),
            corner_radius=15
        )


        balao.pack(
            anchor=(
                "w"
                if usuario
                else "e"
            )
        )



        label = ctk.CTkLabel(
            balao,
            text=texto,
            wraplength=600,
            justify="left"
        )


        label.pack(
            padx=15,
            pady=10
        )



    # ==========================
    # RESPONDER
    # ==========================


    def responder(self):


        pergunta = self.entrada.get(
            "1.0",
            "end"
        ).strip()



        if not pergunta:

            return



        self.entrada.delete(
            "1.0",
            "end"
        )



        self.criar_balao(
            pergunta,
            True
        )


        salvar_mensagem(
            self.conversa_atual,
            "usuario",
            pergunta
        )



        if self.primeira_mensagem:


            titulo = gerar_titulo(
                pergunta
            )


            atualizar_titulo(
                self.conversa_atual,
                titulo
            )


            self.primeira_mensagem = False


            self.atualizar_lista()



        def tarefa():


            resposta = conversar(
                pergunta
            )


            self.after(
                0,
                lambda:self.finalizar_resposta(resposta)
            )



        threading.Thread(
            target=tarefa,
            daemon=True
        ).start()



    def finalizar_resposta(self,resposta):


        self.criar_balao(
            resposta,
            False
        )


        salvar_mensagem(
            self.conversa_atual,
            "agente",
            resposta
        )



    # ==========================
    # SIDEBAR RESPONSIVA
    # ==========================


    def alternar_sidebar(self):


        if self.sidebar_aberta:


            self.sidebar.pack_forget()

            self.sidebar_aberta = False

            self.sidebar_manual = True



        else:


            self.sidebar.pack(
                side="left",
                fill="y"
            )


            self.sidebar_aberta = True

            self.sidebar_manual = False




    def verificar_tamanho(self,event):


        largura = self.winfo_width()



        if largura < self.largura_min_sidebar:


            if self.sidebar_aberta:


                self.sidebar.pack_forget()

                self.sidebar_aberta = False



        else:


            if (
                not self.sidebar_aberta
                and not self.sidebar_manual
            ):


                self.sidebar.pack(
                    side="left",
                    fill="y"
                )


                self.sidebar_aberta = True