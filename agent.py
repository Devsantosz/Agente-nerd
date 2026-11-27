from google import genai
from google.genai import types
from dotenv import load_dotenv
from pathlib import Path
import logging
import os
from openai import OpenAI

load_dotenv(Path(__file__).resolve().with_name(".env"))

API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()

if not API_KEY:
    raise ValueError(
        "A variável GEMINI_API_KEY não foi encontrada no arquivo .env"
    )

# =====================================================
# Cliente Gemini
# =====================================================

client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(
        timeout=90_000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)

# =====================================================
# Modelo
# =====================================================

MODEL = "gemini-3.6-flash"
OPENROUTER_MODEL = (os.getenv("OPENROUTER_MODEL") or "openrouter/free").strip()
OPENROUTER_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()
OPENROUTER_MODEL_LITE = (os.getenv("OPENROUTER_MODEL_LITE") or "nvidia/nemotron-3.5-lightning:free").strip()
OPENROUTER_MODEL_HIGH = (os.getenv("OPENROUTER_MODEL_HIGH") or "nvidia/nemotron-3-ultra-550b-a55b:free").strip()

MODOS_CHAT = {
    "lite": {
        "thinking_level": "low",
        "max_output_tokens": 1024,
        "history_limit": 8,
        "openrouter_model": OPENROUTER_MODEL_LITE,
        "instruction": "Responda de forma breve e rápida. Ensine o essencial, com um exemplo curto quando ajudar.",
    },
    "normal": {
        "thinking_level": "medium",
        "max_output_tokens": 2048,
        "history_limit": 20,
        "openrouter_model": OPENROUTER_MODEL,
        "instruction": "Responda com o nível habitual de detalhe, explicando o raciocínio pedagógico de forma clara.",
    },
    "high": {
        "thinking_level": "high",
        "max_output_tokens": 8192,
        "history_limit": 30,
        "openrouter_model": OPENROUTER_MODEL_HIGH,
        "instruction": "Dedique mais esforço a questões complexas. Confira cálculos e conclusões e apresente uma explicação pedagógica detalhada, sem expor raciocínio interno privado.",
    },
}

# =====================================================
# Prompt do sistema
# =====================================================

PROMPT = """
Você é o Pretinho Nerd, um assistente de inteligência artificial especializado em preparação para o ENEM.

Sua missão é ajudar estudantes a estudar de forma inteligente, organizada e eficiente para conquistar uma boa nota no ENEM.

PERSONALIDADE:
- Você é um professor particular paciente, inteligente e motivador.
- Sempre explique de forma simples e clara.
- Nunca faça o estudante se sentir incapaz.
- Incentive o aprendizado e a evolução.
- Responda sempre em português do Brasil.

ESPECIALIDADES:

Você domina todas as áreas cobradas no ENEM:

Linguagens, Códigos e suas Tecnologias:
- Português.
- Interpretação de texto.
- Gramática.
- Literatura brasileira.
- Figuras de linguagem.
- Redação ENEM.
- Inglês.
- Artes.
- Educação Física.

Ciências Humanas:
- História do Brasil.
- História Geral.
- Geografia.
- Filosofia.
- Sociologia.
- Atualidades.

Ciências da Natureza:
- Biologia.
- Química.
- Física.

Matemática:
- Matemática básica.
- Porcentagem.
- Regra de três.
- Funções.
- Geometria.
- Estatística.
- Probabilidade.
- Matemática financeira.
- Análise de gráficos.

REDAÇÃO ENEM:
- Ensine o modelo dissertativo-argumentativo.
- Ajude a criar introdução, desenvolvimento e conclusão.
- Explique a competência 1, 2, 3, 4 e 5.
- Corrija redações dando nota aproximada de 0 a 1000.
- Mostre como melhorar os argumentos.

MÉTODO DE ENSINO:

Quando explicar um assunto:
1. Apresente o conceito de forma simples.
2. Dê exemplos do cotidiano.
3. Mostre como o ENEM costuma cobrar.
4. Faça um resumo dos pontos principais.
5. Crie exercícios para treinar.
6. Corrija os exercícios explicando os erros.

QUESTÕES:
- Ao criar questões, siga o estilo do ENEM.
- Use textos, gráficos ou situações-problema quando necessário.
- Explique detalhadamente a resolução.
- Mostre estratégias para economizar tempo na prova.

PLANO DE ESTUDOS:
- Ajude o estudante a criar cronogramas.
- Organize matérias por prioridade.
- Sugira revisões usando técnicas como:
  - Revisão espaçada.
  - Resumos.
  - Mapas mentais.
  - Resolução de exercícios.

REGRAS:
- Nunca responda apenas com a resposta final de uma questão.
- Sempre ensine o raciocínio.
- Se o estudante demonstrar dificuldade, explique de outra forma.
- Use Markdown quando organizar conteúdos, listas ou códigos.
- Seja objetivo, mas completo.

Você é o Pretinho Nerd: o parceiro de estudos que ajuda o aluno a chegar preparado para o ENEM 2026.
"""

PROMPT_LITE = """
Você é o Pretinho Nerd, tutor de preparação para o ENEM. Responda em português do Brasil,
com linguagem simples, acolhedora e concisa. Ensine o raciocínio essencial, usando um
exemplo curto quando ajudar. Em questões, explique como chegar à resposta; em redações,
considere as competências do ENEM. Não invente dados quando não souber.
"""


def _prompt_do_modo(modo):
    return PROMPT_LITE if modo == "lite" else PROMPT

# =====================================================
# Histórico
# =====================================================

def _historico_normalizado(contexto, limite=20):
    turnos = []
    for remetente, mensagem in (contexto or [])[-limite:]:
        role = "model" if remetente in ("agente", "model") else "user"
        if turnos and turnos[-1][0] == role:
            turnos[-1] = (role, f"{turnos[-1][1]}\n{mensagem}")
        else:
            turnos.append((role, mensagem))
    return turnos


def _erro_temporario(error):
    code = (
        getattr(error, "code", None)
        or getattr(error, "status_code", None)
        or getattr(getattr(error, "response", None), "status_code", None)
    )
    try:
        return int(code) in (408, 429, 500, 502, 503, 504)
    except (TypeError, ValueError):
        status = str(code or getattr(error, "status", "")).upper()
        return status in {
            "RESOURCE_EXHAUSTED",
            "UNAVAILABLE",
            "DEADLINE_EXCEEDED",
            "INTERNAL",
        }


def _mensagens_openrouter(contexto, pergunta, parcial, modo):
    perfil = MODOS_CHAT[modo]
    mensagens = [{
        "role": "system",
        "content": f"{_prompt_do_modo(modo)}\n\nMODO DE RESPOSTA: {perfil['instruction']}",
    }]
    for role, texto in _historico_normalizado(contexto, perfil["history_limit"]):
        mensagens.append({
            "role": "assistant" if role == "model" else "user",
            "content": texto,
        })
    mensagens.append({"role": "user", "content": pergunta})
    if parcial:
        mensagens.extend([
            {"role": "assistant", "content": parcial},
            {
                "role": "user",
                "content": (
                    "Continue a resposta anterior do ponto em que parou. Não repita "
                    "o trecho já escrito; complete a frase se necessário e prossiga."
                ),
            },
        ])
    return mensagens


def responder_em_partes(pergunta, contexto=None, modo="normal"):
    """Transmite a resposta no perfil escolhido e usa OpenRouter como reserva."""
    modo = modo if modo in MODOS_CHAT else "normal"
    perfil = MODOS_CHAT[modo]
    turnos = _historico_normalizado(contexto, perfil["history_limit"])
    if turnos and turnos[-1][0] == "user":
        turnos[-1] = ("user", f"{turnos[-1][1]}\n{pergunta}")
    else:
        turnos.append(("user", pergunta))

    conteudos = [
        types.Content(role=role, parts=[types.Part(text=texto)])
        for role, texto in turnos
    ]
    resposta = ""
    try:
        stream = client.models.generate_content_stream(
            model=MODEL,
            contents=conteudos,
            config=types.GenerateContentConfig(
                system_instruction=f"{_prompt_do_modo(modo)}\n\nMODO DE RESPOSTA: {perfil['instruction']}",
                max_output_tokens=perfil["max_output_tokens"],
                thinking_config=types.ThinkingConfig(
                    thinking_level=perfil["thinking_level"],
                ),
            ),
        )
        for chunk in stream:
            trecho = chunk.text or ""
            if trecho:
                resposta += trecho
                yield {"type": "delta", "text": trecho, "provider": "Gemini"}
    except Exception as error:
        if not _erro_temporario(error):
            logging.getLogger(__name__).exception("Falha na resposta do Gemini")
            yield {"type": "error", "error": "O Gemini não conseguiu concluir a resposta."}
            yield {"type": "done", "text": resposta, "incomplete": True}
            return
        if not OPENROUTER_KEY:
            yield {
                "type": "error",
                "error": "Limite do Gemini atingido. Configure OPENROUTER_API_KEY para continuar com o modelo alternativo.",
            }
            yield {"type": "done", "text": resposta, "incomplete": True}
            return

        yield {"type": "status", "text": f"Gemini indisponível; continuando no modo {modo.title()}…"}
        try:
            openrouter = OpenAI(
                api_key=OPENROUTER_KEY,
                base_url="https://openrouter.ai/api/v1",
                timeout=90,
                max_retries=0,
            )
            stream = openrouter.chat.completions.create(
                model=perfil["openrouter_model"],
                messages=_mensagens_openrouter(contexto, pergunta, resposta, modo),
                max_tokens=perfil["max_output_tokens"],
                **({"reasoning_effort": "high"} if modo == "high" else {}),
                stream=True,
            )
            for evento in stream:
                trecho = evento.choices[0].delta.content or ""
                if trecho:
                    resposta += trecho
                    yield {"type": "delta", "text": trecho, "provider": "OpenRouter"}
        except Exception:
            logging.getLogger(__name__).exception("Falha na continuação pelo OpenRouter")
            yield {
                "type": "error",
                "error": "O modelo alternativo também falhou. O trecho já recebido foi preservado.",
            }
            yield {"type": "done", "text": resposta, "incomplete": True}
            return

    yield {"type": "done", "text": resposta, "incomplete": False}
