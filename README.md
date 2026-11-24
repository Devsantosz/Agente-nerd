# Pretinho Nerd

Assistente de estudos para o ENEM com contas pessoais, chat e histórico de conversas. Cada conta acessa apenas as próprias conversas. Para sincronizar entre celular e computador, publique o site e conecte-o a um PostgreSQL persistente.

## Executar localmente

Requisitos: Python 3.12 ou superior e uma chave do Google Gemini.

1. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

2. Copie `.env.example` para `.env` e preencha `GEMINI_API_KEY`.
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

A Vercel fornece `VERCEL=1`; o app usa isso para habilitar cookies seguros e exigir o PostgreSQL. Depois de alterar as variáveis, faça um novo deploy.

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
- `agent.py`: integração com Gemini e modelo reserva
- `migrar_conversas.py`: importação manual do histórico local
- `templates/index.html`: página do chat e tela de conta
- `static/css/`: estilos
- `static/js/`: interações do chat
- `static/img/`: imagens usadas pela interface
- `.python-version`: versão Python selecionada para a implantação
- `.vercelignore`: exclui segredos, banco local e arquivos de desenvolvimento do pacote

Não coloque `.env`, `chat.db` ou outros segredos no repositório. Configure-os como variáveis de ambiente na plataforma de hospedagem.
