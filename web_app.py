from flask import Flask, jsonify, render_template, request

from database import (
    atualizar_titulo,
    carregar_mensagens,
    criar_conversa,
    excluir_conversa,
    iniciar_banco,
    listar_conversas,
    salvar_mensagem,
)

app = Flask(__name__)
iniciar_banco()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/conversations")
def conversations():
    return jsonify([{"id": id_, "title": title} for id_, title in listar_conversas()])


@app.post("/api/conversations")
def new_conversation():
    conversation_id = criar_conversa()
    return jsonify({"id": conversation_id, "title": "Nova conversa"}), 201


@app.get("/api/conversations/<int:conversation_id>/messages")
def messages(conversation_id):
    existing_ids = {id_ for id_, _ in listar_conversas()}
    if conversation_id not in existing_ids:
        return jsonify({"error": "Conversa não encontrada."}), 404
    return jsonify([
        {"sender": sender, "text": text}
        for sender, text in carregar_mensagens(conversation_id)
    ])


@app.post("/api/conversations/<int:conversation_id>/messages")
def send_message(conversation_id):
    existing_ids = {id_ for id_, _ in listar_conversas()}
    if conversation_id not in existing_ids:
        return jsonify({"error": "Conversa não encontrada."}), 404

    data = request.get_json(silent=True) or {}
    question = (data.get("message") or "").strip()
    if not question:
        return jsonify({"error": "Escreva uma mensagem antes de enviar."}), 400
    if len(question) > 12000:
        return jsonify({"error": "A mensagem deve ter até 12.000 caracteres."}), 400

    history = carregar_mensagens(conversation_id)
    salvar_mensagem(conversation_id, "usuario", question)
    try:
        from agent import conversar, gerar_titulo

        answer = conversar(question, history)
    except (RuntimeError, ValueError) as error:
        app.logger.error("Falha do assistente: %s", error)
        return jsonify({"error": str(error)}), 503
    except Exception:
        app.logger.exception("Falha ao responder mensagem")
        return jsonify({"error": "Não foi possível responder agora. Tente novamente."}), 503

    salvar_mensagem(conversation_id, "agente", answer)
    title = None
    if not history:
        try:
            title = gerar_titulo(question)
            atualizar_titulo(conversation_id, title)
        except Exception:
            title = question[:30]
            atualizar_titulo(conversation_id, title)
    return jsonify({"sender": "agente", "text": answer, "title": title})


@app.delete("/api/conversations/<int:conversation_id>")
def delete_conversation(conversation_id):
    existing_ids = {id_ for id_, _ in listar_conversas()}
    if conversation_id not in existing_ids:
        return jsonify({"error": "Conversa não encontrada."}), 404
    excluir_conversa(conversation_id)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
