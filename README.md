# Metabase Custom Dashboard IFrame

Este projeto demonstra como incorporar dados de uma pergunta do Metabase em um `iframe` dentro de um dashboard. Os scripts consultam a API do Metabase aplicando os filtros definidos no próprio dashboard.

## Estrutura de pastas

```
metabase_customizacoes/
├── api/
│   ├── config.py        # Configurações de URL e token da API
│   ├── metabase_api.py  # Funções para consulta à API do Metabase
│   └── filter_utils.js  # Captura de filtros do dashboard (uso em vários front-ends)
├── proxy_server/
│   ├── config.py        # Configurações do proxy (porta e caminhos)
│   └── proxy_server.py  # Servidor Flask que serve o HTML e faz proxy das chamadas
└── componentes/
    └── dashboard tabela/
        ├── dashboard-iframe.html  # HTML do iframe
        ├── dashboard-iframe.js    # Lógica para ler filtros e consultar a API
        └── dashboard-iframe.css   # Estilos do iframe
```

Há também um `requirements.txt` com as dependências Python.

## Configuração do ambiente (Fedora 41)

1. **Instalar dependências Python**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configurar o Nginx**

Inclua as seguintes rotas adicionais no arquivo `/etc/nginx/conf.d/metabase.conf` para encaminhar as requisições para o proxy (porta 3500):

```nginx
location /componentes/ {
    proxy_pass http://localhost:3500/componentes/;
}

location /proxy/ {
    proxy_pass http://localhost:3500/;
}

location /api/ {
    proxy_pass http://localhost:3500/api/;
}
```

Recarregue o Nginx:

```bash
sudo systemctl reload nginx
```

3. **Executar o proxy**

```bash
cd metabase_customizacoes/proxy_server
python proxy_server.py
```

O proxy servirá os arquivos HTML e encaminhará as consultas para a API do Metabase.

4. **Incorporar o iframe no dashboard**

Adicione ao dashboard do Metabase um bloco de iframe apontando para:

```html
<iframe src="https://metabasedashboards.ngrok.io/componentes/dashboard tabela/dashboard-iframe.html?question_id=51" width="100%" height="800"></iframe>
```

O JavaScript do iframe irá ler periodicamente os filtros do dashboard e atualizar a consulta, exibindo a tabela resultante e informações de depuração.
O script `filter_utils.js` localizado na pasta `api/` é responsável por detectar mudanças nos filtros e compartilhar os valores com os diversos front‑ends que venham a utilizá-lo.
