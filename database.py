import sqlite3
from datetime import datetime


BANCO = "chat.db"


def conectar():

    return sqlite3.connect(BANCO)



# Criar tabelas

def iniciar_banco():

    conexao = conectar()
    cursor = conexao.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversas (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        titulo TEXT,

        data TEXT

    )
    """)



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mensagens (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        conversa_id INTEGER,

        remetente TEXT,

        mensagem TEXT,

        data TEXT,

        FOREIGN KEY(conversa_id)
        REFERENCES conversas(id)

    )
    """)


    conexao.commit()
    conexao.close()



# Criar conversa nova

def criar_conversa(titulo="Nova conversa"):

    conexao = conectar()

    cursor = conexao.cursor()


    cursor.execute(
        """
        INSERT INTO conversas(titulo,data)
        VALUES (?,?)
        """,
        (
            titulo,
            datetime.now().strftime("%d/%m/%Y %H:%M")
        )
    )


    id_conversa = cursor.lastrowid


    conexao.commit()
    conexao.close()


    return id_conversa



# Buscar conversas

def listar_conversas():

    conexao = conectar()

    cursor = conexao.cursor()


    cursor.execute(
        """
        SELECT id,titulo
        FROM conversas
        ORDER BY id DESC
        """
    )


    resultado = cursor.fetchall()


    conexao.close()


    return resultado



# Salvar mensagem

def salvar_mensagem(
        conversa_id,
        remetente,
        mensagem):


    conexao = conectar()

    cursor = conexao.cursor()


    cursor.execute(
        """
        INSERT INTO mensagens
        (
        conversa_id,
        remetente,
        mensagem,
        data
        )

        VALUES (?,?,?,?)
        """,
        (
            conversa_id,
            remetente,
            mensagem,
            datetime.now().strftime("%H:%M")
        )
    )


    conexao.commit()

    conexao.close()



# Carregar mensagens

def carregar_mensagens(conversa_id):

    conexao = conectar()

    cursor = conexao.cursor()


    cursor.execute(
        """
        SELECT remetente,mensagem
        FROM mensagens

        WHERE conversa_id=?

        ORDER BY id
        """,
        (conversa_id,)
    )


    mensagens = cursor.fetchall()


    conexao.close()


    return mensagens


def atualizar_titulo(conversa_id, titulo):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute(
        """
        UPDATE conversas
        SET titulo = ?
        WHERE id = ?
        """,
        (
            titulo,
            conversa_id
        )
    )

    conexao.commit()
    conexao.close()



def excluir_conversa(conversa_id):

    conexao = conectar()
    cursor = conexao.cursor()


    # Remove mensagens
    cursor.execute(
        """
        DELETE FROM mensagens
        WHERE conversa_id = ?
        """,
        (conversa_id,)
    )


    # Remove conversa
    cursor.execute(
        """
        DELETE FROM conversas
        WHERE id = ?
        """,
        (conversa_id,)
    )


    conexao.commit()
    conexao.close()