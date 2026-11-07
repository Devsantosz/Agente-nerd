from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "A variável GEMINI_API_KEY não foi encontrada no arquivo .env"
    )

# =====================================================
# Cliente Gemini
# =====================================================

client = genai.Client(api_key=API_KEY)

# =====================================================
# Modelo
# =====================================================

MODEL = "gemini-3.6-flash"

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

historico = [
    types.Content(
        role="user",
        parts=[
            types.Part(text=PROMPT)
        ]
    )
]

# =====================================================
# Conversa
# =====================================================

def conversar(pergunta: str):

    global historico

    try:

        historico.append(
            types.Content(
                role="user",
                parts=[
                    types.Part(text=pergunta)
                ]
            )
        )

        resposta = client.models.generate_content(
            model=MODEL,
            contents=historico
        )

        texto = resposta.text

        historico.append(
            types.Content(
                role="model",
                parts=[
                    types.Part(text=texto)
                ]
            )
        )

        return texto

    except Exception as erro:

        return f"""
Ocorreu um erro.

{erro}
"""
    

def gerar_titulo(mensagem):

    try:

        resposta = client.models.generate_content(
            model=MODEL,
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