# Pretinho Nerd

Assistente de estudos para o ENEM com contas pessoais, chat e histórico de conversas. Cada conta acessa apenas as próprias conversas. Para sincronizar entre celular e computador, publique o site e conecte-o a um PostgreSQL persistente.

## Executar localmente

Requisitos: Python 3.10 ou superior e uma chave do Google Gemini.

1. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

2. Copie `.env.example` para `.env` e preencha `GEMINI_API_KEY`.
3. Inicie o site:

   ```bash
   python main.py
   ```

4. Acesse http://127.0.0.1:5000 e crie sua conta com e-mail e senha de pelo menos 12 caracteres.

Sem `DATABASE_URL`, o projeto usa o arquivo local `chat.db`. As conversas antigas nesse SQLite são vinculadas à primeira conta criada localmente.

## Sincronizar entre dispositivos

Celular e computador precisam acessar a mesma URL publicada do site, conectada ao mesmo banco PostgreSQL. Configure no serviço de hospedagem:

- `DATABASE_URL`: URL do PostgreSQL persistente
- `SECRET_KEY`: segredo longo e aleatório, mantido igual nas reinicializações
- `GEMINI_API_KEY`: chave do Google Gemini
- `APP_ENV=production`: ativa o modo de produção e exige `SECRET_KEY`

Use HTTPS. Em produção, os cookies de sessão são marcados como seguros automaticamente. A plataforma de hospedagem precisa manter o PostgreSQL após reinicializações; não use o `chat.db` local como armazenamento de produção.

### Importar conversas antigas

Para copiar o histórico de `chat.db` para o PostgreSQL, mantenha uma cópia do arquivo, crie a conta no site publicado e configure localmente `DATABASE_URL`, `SECRET_KEY` e `GEMINI_API_KEY` apontando para o mesmo servidor. Depois rode:

```bash
python migrar_conversas.py seu-email@exemplo.com
```

O comando cancela a importação se a conta já tiver mensagens, para evitar duplicatas. Não publique nem compartilhe o arquivo `.env` ou `chat.db`.

## Segurança e recuperação da conta

As senhas são armazenadas como hash, o login tem limite de tentativas e as ações usam sessão segura e proteção CSRF. O e-mail é usado como identificador, mas ainda não há confirmação de endereço nem recuperação de senha por e-mail. A recuperação exige configurar um serviço de envio de mensagens.

## Estrutura

- `main.py`: inicializa o servidor Flask
- `web_app.py`: site, API, autenticação e sessões
- `database.py`: contas, conversas e mensagens em SQLite ou PostgreSQL
- `templates/index.html`: chat e tela de entrada/criação de conta
- `static/`: estilos, interações e imagens
- `migrar_conversas.py`: importação manual do histórico SQLite para PostgreSQL
- `agent.py`: integração com Gemini e modelo reserva

Não coloque `.env` ou segredos no repositório. Em produção, configure-os nas variáveis de ambiente da plataforma.
