from google import genai
from google.genai import types
from dotenv import load_dotenv
from pathlib import Path
import logging
import os
import time

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
FALLBACK_MODEL = "gemini-3.5-flash-lite"


def _gerar_conteudo(contents, config=None):
    """Repete falhas temporárias e tenta um modelo reserva."""
    modelos = [MODEL]
    if FALLBACK_MODEL != MODEL:
        modelos.append(FALLBACK_MODEL)

    ultimo_erro = None
    for indice, modelo in enumerate(modelos):
        tentativas = 2 if indice == 0 else 1
        for tentativa in range(tentativas):
            try:
                return client.models.generate_content(
                    model=modelo,
                    contents=contents,
                    config=config,
                )
            except Exception as erro:
                ultimo_erro = erro
                if getattr(erro, "code", None) not in (429, 500, 502, 503, 504):
                    raise
                if tentativa + 1 < tentativas:
                    time.sleep(1.5)

    raise ultimo_erro

# =====================================================
# Prompt do sistema
# =====================================================

PROMPT = """
Você é o Pretinho Nerd, um assistente de inteligência artificial especializado em preparação para o ENEM 2026.

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

# =====================================================
# Histórico
# =====================================================

# =====================================================
# Conversa
# =====================================================

def conversar(pergunta: str, contexto=None):
    """Gera uma resposta usando somente o histórico da conversa atual."""

    try:
        turnos = []
        for remetente, mensagem in (contexto or [])[-20:]:
            role = "model" if remetente in ("agente", "model") else "user"
            if turnos and turnos[-1][0] == role:
                turnos[-1] = (role, f"{turnos[-1][1]}\n{mensagem}")
            else:
                turnos.append((role, mensagem))

        if turnos and turnos[-1][0] == "user":
            turnos[-1] = ("user", f"{turnos[-1][1]}\n{pergunta}")
        else:
            turnos.append(("user", pergunta))

        conteudos = [
            types.Content(role=role, parts=[types.Part(text=mensagem)])
            for role, mensagem in turnos
        ]

        resposta = _gerar_conteudo(
            contents=conteudos,
            config=types.GenerateContentConfig(
                system_instruction=PROMPT,
                max_output_tokens=2048,
            ),
        )

        return resposta.text or "Não consegui preparar uma resposta agora. Tente novamente."

    except Exception as erro:
        logging.getLogger(__name__).exception("Falha na chamada generate_content do Gemini")
        detalhe = f"{type(erro).__name__}: {erro}"
        if API_KEY:
            detalhe = detalhe.replace(API_KEY, "[chave ocultada]")
        raise RuntimeError(f"Falha ao consultar o Gemini — {detalhe[:350]}") from erro
    

def gerar_titulo(mensagem):

    try:

        resposta = _gerar_conteudo(
            contents=f"""
            Crie um título curto para uma conversa.

            Regras:
            - máximo 5 palavras
            - não use aspas
            - seja objetivo

            Mensagem:
            {mensagem}
            """
        )


        titulo = resposta.text.strip()

        return titulo


    except Exception:

        return mensagem[:30]
