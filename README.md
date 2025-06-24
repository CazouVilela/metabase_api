# Metabase Customizações com Proxy Flask

Este repositório contém uma aplicação Flask usada como proxy para renderização de componentes customizados do Metabase, como iframes interativos que recebem filtros do dashboard pai.

## Estrutura do Projeto

```
metabase_customizacoes/
├── api/
│   ├── __init__.py
│   ├── config.py               # Configurações como URL e credenciais do Metabase
│   └── metabase_api.py         # Funções para consultar a API do Metabase
│
├── proxy_server/
│   ├── __init__.py
│   ├── config.py               # Define portas e caminho de arquivos estáticos
│   └── proxy_server.py         # Servidor Flask com endpoints de proxy
│
├── componentes/
│   └── dashboard_tabela/       # Frontend HTML, CSS e JS para renderizar a tabela no iframe
│       ├── dashboard-iframe.html
│       ├── dashboard-iframe.css
│       └── dashboard-iframe.js
│
├── README.md
└── requirements.txt            # Dependências da aplicação (ex: Flask, requests)
```

## Executando localmente

1. Crie um ambiente virtual e ative:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure as credenciais do Metabase no arquivo `api/config.py`.

4. Execute o servidor Flask:

```bash
python proxy_server/proxy_server.py
```

## Endpoints disponíveis

- `/componentes/<arquivo>`: Serve arquivos HTML/JS/CSS do frontend.
- `/query?question_id=<id>&filtro1=...`: Faz a consulta autenticada ao Metabase com os filtros fornecidos.

### Servindo utilidades JavaScript

O endpoint `/api_js/<arquivo>` disponibiliza scripts utilitários armazenados no diretório `api`. Ele é útil para expor funções comuns compartilhadas pelos componentes. Exemplos de arquivos servidos são `filter_config.js` e `filter_utils.js`.

## Finalidade

Essa estrutura permite a criação de componentes visuais reutilizáveis no Metabase que suportam filtros dinâmicos, utilizando uma camada intermediária para comunicação com a API do Metabase.

