"""Importa conversas do chat.db local para o banco configurado em DATABASE_URL."""

import argparse
import sqlite3
from pathlib import Path

from database import Conversation, Message, User, db
from web_app import app


def migrar(email):
    origem = Path(__file__).resolve().with_name("chat.db")
    if not origem.exists():
        raise SystemExit("chat.db não foi encontrado nesta pasta.")

    with app.app_context():
        if db.engine.dialect.name == "sqlite":
            raise SystemExit("Configure DATABASE_URL com seu PostgreSQL antes de migrar.")

        usuario = User.query.filter_by(email=email.strip().lower()).first()
        if not usuario:
            raise SystemExit("Crie sua conta no site antes de importar as conversas.")

        conversas_existentes = Conversation.query.filter_by(user_id=usuario.id).all()
        if any(conversa.mensagens for conversa in conversas_existentes):
            raise SystemExit("A conta já tem conversas. A importação foi cancelada para evitar duplicatas.")
        for conversa in conversas_existentes:
            db.session.delete(conversa)
        db.session.flush()

        with sqlite3.connect(origem) as banco_local:
            tabelas = {
                linha[0]
                for linha in banco_local.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if not {"conversas", "mensagens"}.issubset(tabelas):
                raise SystemExit("O chat.db não tem o formato de conversas esperado.")

            colunas_conversa = {
                linha[1]
                for linha in banco_local.execute("PRAGMA table_info(conversas)")
            }
            if "user_id" in colunas_conversa:
                conta_local = banco_local.execute(
                    "SELECT id FROM users WHERE email = ?",
                    (usuario.email,),
                ).fetchone()
                if not conta_local:
                    raise SystemExit("A conta local correspondente não foi encontrada no chat.db.")
                linhas = banco_local.execute(
                    "SELECT id, titulo, data FROM conversas WHERE user_id = ? ORDER BY id",
                    (conta_local[0],),
                ).fetchall()
            else:
                linhas = banco_local.execute(
                    "SELECT id, titulo, data FROM conversas ORDER BY id"
                ).fetchall()

            total_mensagens = 0
            for conversa_id, titulo, data in linhas:
                nova = Conversation(user_id=usuario.id, titulo=titulo, data=data)
                db.session.add(nova)
                db.session.flush()
                mensagens = banco_local.execute(
                    "SELECT remetente, mensagem, data FROM mensagens "
                    "WHERE conversa_id = ? ORDER BY id",
                    (conversa_id,),
                ).fetchall()
                for remetente, mensagem, data_mensagem in mensagens:
                    db.session.add(Message(
                        conversa_id=nova.id,
                        remetente=remetente,
                        mensagem=mensagem,
                        data=data_mensagem,
                    ))
                total_mensagens += len(mensagens)

        db.session.commit()
        print(f"{len(linhas)} conversas e {total_mensagens} mensagens importadas para {usuario.email}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email", help="e-mail da conta já criada no site")
    migrar(parser.parse_args().email)
