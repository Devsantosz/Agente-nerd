import os
import re
import secrets
import json
from datetime import timedelta
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, stream_with_context
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from database import (
    User,
    atualizar_titulo,
    atualizar_modo_conversa,
    buscar_usuario_por_email,
    carregar_mensagens,
    criar_conversa,
    criar_usuario,
    db,
    excluir_conversa,
    iniciar_banco,
    listar_conversas,
    obter_conversa,
    salvar_mensagem,
)


load_dotenv(Path(__file__).resolve().with_name(".env"))

app = Flask(__name__)
is_vercel = os.getenv("VERCEL") == "1"
production = is_vercel or os.getenv("RENDER") == "true" or os.getenv("APP_ENV") == "production"
secret_key = os.getenv("SECRET_KEY")
if production and (not secret_key or len(secret_key) < 32):
    raise RuntimeError("Configure SECRET_KEY com pelo menos 32 caracteres no servidor.")

database_url = os.getenv("DATABASE_URL")
if is_vercel and not database_url:
    raise RuntimeError("Configure DATABASE_URL para conectar o site da Vercel ao PostgreSQL.")
if not database_url:
    sqlite_path = Path(__file__).resolve().with_name("chat.db").as_posix()
    database_url = f"sqlite:///{sqlite_path}"
elif database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config.update(
    SECRET_KEY=secret_key or secrets.token_hex(32),
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=production or os.getenv("COOKIE_SECURE") == "true",
    SESSION_COOKIE_SAMESITE="Lax",
    REMEMBER_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_SECURE=production or os.getenv("COOKIE_SECURE") == "true",
    REMEMBER_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)
iniciar_banco(app)

csrf = CSRFProtect(app)
login_manager = LoginManager(app)
limiter = Limiter(get_remote_address, app=app, storage_uri="memory://", default_limits=[])


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Entre na sua conta para continuar.", "authenticated": False}), 401


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/auth/me")
def auth_status():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False})
    return jsonify({"authenticated": True, "email": current_user.email})


@app.post("/api/auth/register")
@limiter.limit("5 per minute")
def register():
    data = request.get_json(silent=True) or {}
    raw_email = data.get("email")
    raw_password = data.get("password")
    email = raw_email.strip().lower() if isinstance(raw_email, str) else ""
    password = raw_password if isinstance(raw_password, str) else ""
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return jsonify({"error": "Informe um e-mail válido."}), 400
    if len(password) < 12:
        return jsonify({"error": "A senha precisa ter pelo menos 12 caracteres."}), 400
    if buscar_usuario_por_email(email):
        return jsonify({"error": "Este e-mail já tem uma conta. Entre nela."}), 409

    user = criar_usuario(email, password)
    login_user(user, remember=True, duration=timedelta(days=30))
    from flask import session

    session.permanent = True
    return jsonify({"authenticated": True, "email": user.email}), 201


@app.post("/api/auth/login")
@limiter.limit("5 per minute")
def login():
    data = request.get_json(silent=True) or {}
    raw_email = data.get("email")
    raw_password = data.get("password")
    email = raw_email.strip().lower() if isinstance(raw_email, str) else ""
    password = raw_password if isinstance(raw_password, str) else ""
    user = buscar_usuario_por_email(email)
    if not user or not user.check_password(password):
        return jsonify({"error": "E-mail ou senha incorretos."}), 401

    login_user(user, remember=True, duration=timedelta(days=30))
    from flask import session

    session.permanent = True
    return jsonify({"authenticated": True, "email": user.email})


@app.post("/api/auth/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@app.get("/api/conversations")
@login_required
def conversations():
    return jsonify([
        {"id": id_, "title": title, "mode": mode}
        for id_, title, mode in listar_conversas(current_user.id)
    ])


@app.post("/api/conversations")
@login_required
def new_conversation():
    conversation_id = criar_conversa(current_user.id)
    return jsonify({"id": conversation_id, "title": "Nova conversa", "mode": "normal"}), 201


@app.post("/api/conversations/<int:conversation_id>/mode")
@login_required
def set_conversation_mode(conversation_id):
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")
    if not isinstance(mode, str) or mode not in {"lite", "normal", "high"}:
        return jsonify({"error": "Escolha Lite, Normal ou High."}), 400
    if not atualizar_modo_conversa(current_user.id, conversation_id, mode):
        return jsonify({"error": "Conversa não encontrada."}), 404
    return jsonify({"mode": mode})


@app.get("/api/conversations/<int:conversation_id>/messages")
@login_required
def messages(conversation_id):
    conversation = obter_conversa(current_user.id, conversation_id)
    if not conversation:
        return jsonify({"error": "Conversa não encontrada."}), 404
    return jsonify({
        "mode": conversation.modo or "normal",
        "messages": [
            {"sender": sender, "text": text}
            for sender, text in carregar_mensagens(conversation_id)
        ],
    })


@app.post("/api/conversations/<int:conversation_id>/messages")
@login_required
def send_message(conversation_id):
    conversation = obter_conversa(current_user.id, conversation_id)
    if not conversation:
        return jsonify({"error": "Conversa não encontrada."}), 404

    data = request.get_json(silent=True) or {}
    question = (data.get("message") or "").strip()
    if not question:
        return jsonify({"error": "Escreva uma mensagem antes de enviar."}), 400
    if len(question) > 12000:
        return jsonify({"error": "A mensagem deve ter até 12.000 caracteres."}), 400

    mode = data.get("mode", conversation.modo or "normal")
    if not isinstance(mode, str) or mode not in {"lite", "normal", "high"}:
        return jsonify({"error": "Escolha Lite, Normal ou High."}), 400
    if mode != conversation.modo:
        conversation.modo = mode
        db.session.commit()

    history = carregar_mensagens(conversation_id)
    salvar_mensagem(conversation_id, "usuario", question)
    def eventos():
        from agent import responder_em_partes

        resposta_completa = ""
        titulo = None
        for evento in responder_em_partes(question, history, mode):
            if evento["type"] == "delta":
                resposta_completa += evento["text"]
            elif evento["type"] == "done":
                resposta_completa = evento.get("text", resposta_completa)
                if resposta_completa:
                    salvar_mensagem(conversation_id, "agente", resposta_completa)
                if not history:
                    titulo = " ".join(question.split()[:5]) or "Nova conversa"
                    atualizar_titulo(conversation_id, titulo)
                evento["title"] = titulo
            yield f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(eventos()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


@app.delete("/api/conversations/<int:conversation_id>")
@login_required
def delete_conversation(conversation_id):
    if not obter_conversa(current_user.id, conversation_id):
        return jsonify({"error": "Conversa não encontrada."}), 404
    excluir_conversa(conversation_id)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=not production)
