# Pretinho Nerd

Assistente de estudos para o ENEM com contas pessoais, chat e histórico de conversas. Cada conta acessa apenas as próprias conversas. Para sincronizar entre celular e computador, publique o site e conecte-o a um PostgreSQL persistente.

## Executar localmente

Requisitos: Python 3.12 ou superior e uma chave do Google Gemini. Para habilitar a continuação automática quando o Gemini atingir um limite temporário, configure também uma chave do OpenRouter.

1. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

2. Copie `.env.example` para `.env` e preencha `GEMINI_API_KEY`. Para ativar o provedor alternativo, preencha também `OPENROUTER_API_KEY`; os modelos reserva podem permanecer com os valores sugeridos no exemplo.
3. Inicie o site:

   ```bash
   python main.py
   ```

4. Acesse https://agente-nerd.vercel.app/ e crie sua conta com e-mail e senha de pelo menos 12 caracteres.

Sem `DATABASE_URL`, o projeto usa o `chat.db` local. As conversas antigas nesse SQLite são vinculadas à primeira conta criada localmente.

## Publicar na Vercel

A Vercel detecta a aplicação Flask pelo objeto `app` exposto por `main.py`. Configure estas variáveis em **Project Settings → Environment Variables** para Production e Preview:

- `DATABASE_URL`: URL externa do PostgreSQL, pois a Vercel está fora da rede privada do Render
- `SECRET_KEY`: segredo aleatório com pelo menos 32 caracteres
- `GEMINI_API_KEY`: chave do Google Gemini
- `OPENROUTER_API_KEY`: chave do OpenRouter; necessária para continuar a resposta quando o Gemini retornar erro temporário de limite ou disponibilidade
- `OPENROUTER_MODEL`: modelo reserva do modo Normal; `openrouter/free` seleciona automaticamente um modelo gratuito disponível
- `OPENROUTER_MODEL_LITE`: modelo reserva do modo Lite; padrão `nvidia/nemotron-3.5-lightning:free`
- `OPENROUTER_MODEL_HIGH`: modelo reserva do modo High; padrão `nvidia/nemotron-3-ultra-550b-a55b:free`

A Vercel fornece `VERCEL=1`; o app usa isso para habilitar cookies seguros e exigir o PostgreSQL. Depois de alterar as variáveis, faça um novo deploy.

O chat oferece três modos por conversa: **Lite** usa raciocínio baixo, resposta curta e menos histórico; **Normal** mantém o padrão equilibrado; **High** usa raciocínio alto, mais histórico e um limite maior de saída. A escolha fica salva na conversa e acompanha a conta entre dispositivos. O seletor controla o perfil do Gemini e também escolhe o respectivo modelo reserva do OpenRouter.

Se o Gemini falhar por limite ou indisponibilidade temporária, o OpenRouter recebe o histórico e o trecho já gerado para continuar. A continuação preserva o conteúdo visível, mas modelos diferentes não compartilham o estado interno de geração e podem repetir ou reformular uma frase. Os modelos gratuitos do OpenRouter têm limites próprios e disponibilidade variável; a troca automática não garante respostas ilimitadas.

## Sincronizar entre dispositivos

Celular e computador precisam acessar a mesma URL publicada, conectada ao mesmo PostgreSQL persistente. Em produção, não use o SQLite local para armazenar as conversas.

### Importar conversas antigas

Para copiar o histórico de `chat.db` para o PostgreSQL, mantenha uma cópia do arquivo, crie a conta no site publicado e configure localmente `DATABASE_URL`, `SECRET_KEY` e `GEMINI_API_KEY` apontando para o mesmo servidor. Depois rode:

```bash
python migrar_conversas.py seu-email@exemplo.com
```

O comando cancela a importação se a conta já tiver mensagens, para evitar duplicatas. Não publique nem compartilhe o arquivo `.env` ou `chat.db`.

## Segurança e recuperação da conta

As senhas são armazenadas como hash, o login tem limite de tentativas e as ações usam sessão segura e proteção CSRF. O e-mail é usado como identificador, mas ainda não há confirmação de endereço nem recuperação de senha por e-mail. A recuperação exige configurar um serviço de envio de mensagens.

## Estrutura

- `main.py`: entrada Flask detectada pela Vercel e inicialização local
- `web_app.py`: rotas do site, API, autenticação e sessões
- `database.py`: modelos e persistência em SQLite/PostgreSQL
- `agent.py`: integração com Gemini, transmissão das respostas e continuação opcional pelo OpenRouter
- `migrar_conversas.py`: importação manual do histórico local
- `templates/index.html`: página do chat e tela de conta
- `static/css/`: estilos
- `static/js/`: interações do chat
- `static/img/`: imagens usadas pela interface
- `.python-version`: versão Python selecionada para a implantação
- `.vercelignore`: exclui segredos, banco local e arquivos de desenvolvimento do pacote

Não coloque `.env`, `chat.db` ou outros segredos no repositório. Configure-os como variáveis de ambiente na plataforma de hospedagem.
