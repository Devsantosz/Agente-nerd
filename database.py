from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    conversations = db.relationship(
        "Conversation",
        backref="owner",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Conversation(db.Model):
    __tablename__ = "conversas"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.Text, nullable=True)
    modo = db.Column(db.String(16), nullable=False, default="normal")
    data = db.Column(db.String(32), nullable=True)
    # Nullable para preservar conversas antigas e permitir vinculá-las à primeira conta local.
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    mensagens = db.relationship(
        "Message",
        backref="conversa",
        cascade="all, delete-orphan",
        order_by="Message.id",
    )


class Message(db.Model):
    __tablename__ = "mensagens"

    id = db.Column(db.Integer, primary_key=True)
    conversa_id = db.Column(
        db.Integer,
        db.ForeignKey("conversas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    remetente = db.Column(db.String(32), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    data = db.Column(db.String(32), nullable=True)


def iniciar_banco(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        _adicionar_colunas_conversa_se_necessario()


def _adicionar_colunas_conversa_se_necessario():
    tabelas = set(inspect(db.engine).get_table_names())
    if "conversas" not in tabelas:
        return
    colunas = {coluna["name"] for coluna in inspect(db.engine).get_columns("conversas")}
    with db.engine.begin() as conexao:
        if "user_id" not in colunas:
            conexao.execute(
                text("ALTER TABLE conversas ADD COLUMN user_id INTEGER REFERENCES users(id)")
            )
        if "modo" not in colunas:
            conexao.execute(
                text("ALTER TABLE conversas ADD COLUMN modo VARCHAR(16) NOT NULL DEFAULT 'normal'")
            )


def criar_usuario(email, password):
    user = User(email=email.strip().lower())
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    # No banco SQLite local, associa o histórico antigo à primeira conta criada.
    if db.engine.dialect.name == "sqlite":
        Conversation.query.filter_by(user_id=None).update(
            {Conversation.user_id: user.id}, synchronize_session=False
        )
    db.session.commit()
    return user


def buscar_usuario_por_email(email):
    return User.query.filter_by(email=email.strip().lower()).first()


def criar_conversa(user_id, titulo="Nova conversa", modo="normal"):
    conversa = Conversation(
        user_id=user_id,
        titulo=titulo,
        modo=modo,
        data=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )
    db.session.add(conversa)
    db.session.commit()
    return conversa.id


def obter_conversa(user_id, conversa_id):
    return Conversation.query.filter_by(id=conversa_id, user_id=user_id).first()


def listar_conversas(user_id):
    conversas = (
        Conversation.query.filter_by(user_id=user_id)
        .order_by(Conversation.id.desc())
        .all()
    )
    return [(conversa.id, conversa.titulo, conversa.modo) for conversa in conversas]


def atualizar_modo_conversa(user_id, conversa_id, modo):
    conversa = obter_conversa(user_id, conversa_id)
    if not conversa:
        return False
    conversa.modo = modo
    db.session.commit()
    return True


def salvar_mensagem(conversa_id, remetente, mensagem):
    registro = Message(
        conversa_id=conversa_id,
        remetente=remetente,
        mensagem=mensagem,
        data=datetime.now().strftime("%H:%M"),
    )
    db.session.add(registro)
    db.session.commit()


def carregar_mensagens(conversa_id):
    mensagens = Message.query.filter_by(conversa_id=conversa_id).order_by(Message.id).all()
    return [(mensagem.remetente, mensagem.mensagem) for mensagem in mensagens]


def atualizar_titulo(conversa_id, titulo):
    Conversation.query.filter_by(id=conversa_id).update({"titulo": titulo})
    db.session.commit()


def excluir_conversa(conversa_id):
    conversa = db.session.get(Conversation, conversa_id)
    if conversa:
        db.session.delete(conversa)
        db.session.commit()
