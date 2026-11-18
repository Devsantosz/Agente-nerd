# Pretinho Nerd

Assistente de estudos para o ENEM, agora como site responsivo. A aplicação oferece chat com IA, histórico de conversas salvo em SQLite e sugestões para começar a estudar.

## Requisitos

- Python 3.10 ou superior
- Uma chave de API do Google Gemini

## Como executar

1. Crie e ative um ambiente virtual, se desejar.
2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Crie um arquivo `.env` na raiz do projeto com sua chave:

   ```env
   GEMINI_API_KEY=sua_chave_aqui
   ```

4. Inicie o site:

   ```bash
   python main.py
   ```

5. Acesse http://127.0.0.1:5000 no navegador.

O banco `chat.db` é criado automaticamente na pasta do projeto e guarda conversas e mensagens.

## Estrutura

- `main.py`: ponto de entrada do site
- `web_app.py`: servidor Flask e rotas da API
- `templates/index.html`: página principal
- `static/`: estilos, interações e imagens
- `agent.py`: integração com Gemini e instruções de ensino
- `database.py`: persistência local em SQLite

## Publicação

Para publicar em um servidor, configure `GEMINI_API_KEY` como variável de ambiente e use um servidor WSGI, como Gunicorn, apontando para `web_app:app`. Não publique a chave no código ou no repositório.
