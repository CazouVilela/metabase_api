# Metabase Customizações

Sistema de customizações para Metabase que permite criar componentes interativos (tabelas, gráficos, dashboards) em iframes, capturando filtros do dashboard principal e executando queries otimizadas.

## 🚀 Características

- **Performance Nativa**: Execução de queries com a mesma performance do Metabase nativo
- **Cache Redis**: Cache inteligente com compressão gzip
- **Filtros Dinâmicos**: Captura automática de filtros do dashboard
- **Componentes Modulares**: Arquitetura preparada para múltiplos tipos de visualização
- **Recursos Compartilhados**: Código reutilizável entre componentes

## 📁 Estrutura do Projeto

```
metabase_customizacoes/
├── config/                          # Configurações
│   ├── .env                        # Variáveis de ambiente (criar do .env.example)
│   ├── .env.example                # Exemplo de configuração
│   └── settings.py                 # Configurações centralizadas
│
├── api/                            # Backend Flask
│   ├── server.py                   # Servidor principal
│   ├── routes/                     # Endpoints da API
│   │   ├── query_routes.py        # Rotas de query
│   │   ├── debug_routes.py        # Rotas de debug
│   │   └── static_routes.py       # Rotas de arquivos estáticos
│   ├── services/                   # Serviços de negócio
│   │   ├── query_service.py       # Execução de queries
│   │   ├── metabase_service.py    # Comunicação com Metabase
│   │   └── cache_service.py       # Gerenciamento de cache
│   └── utils/                      # Utilitários
│       ├── filters.py             # Processamento de filtros
│       └── query_parser.py        # Parser de queries SQL
│
├── componentes/                    # Frontend
│   ├── recursos_compartilhados/   # Código reutilizável
│   │   ├── js/                    # JavaScript compartilhado
│   │   │   ├── api-client.js     # Cliente API
│   │   │   ├── filter-manager.js # Gerenciamento de filtros
│   │   │   ├── data-processor.js # Processamento de dados
│   │   │   └── export-utils.js   # Utilitários de exportação
│   │   └── css/                   # Estilos compartilhados
│   │       └── base.css          # CSS base
│   │
│   └── tabela_virtual/            # Componente de tabela
│       ├── index.html
│       ├── css/
│       │   └── tabela.css
│       └── js/
│           ├── main.js
│           └── table-renderer.js
│
├── nginx/                         # Configurações Nginx
│   └── metabase.conf
│
├── scripts/                       # Scripts utilitários
│   ├── start.sh                  # Inicialização
│   └── test.sh                   # Testes
│
├── docs/                         # Documentação
├── logs/                         # Logs da aplicação
└── tests/                        # Testes automatizados
```

## 🔧 Instalação

### 1. Clone o repositório
```bash
cd ~
git clone <seu-repositorio>
cd metabase_customizacoes
```

### 2. Configure o ambiente
```bash
# Copie o arquivo de exemplo
cp config/.env.example config/.env

# Edite com suas configurações
nano config/.env
```

### 3. Instale as dependências
```bash
# Crie ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

### 4. Configure o Nginx
```bash
# Copie a configuração
sudo cp nginx/metabase.conf /etc/nginx/conf.d/

# Recarregue o Nginx
sudo nginx -s reload
```

### 5. Configure o Redis (opcional)
```bash
# Instale o Redis
sudo dnf install redis

# Inicie o serviço
sudo systemctl enable --now redis
```

## 🚀 Uso

### Iniciar o servidor
```bash
# Modo desenvolvimento
./scripts/start.sh

# Modo produção
./scripts/start.sh prod
```

### Criar um iframe no Metabase

1. No dashboard do Metabase, adicione um componente de texto
2. Use o seguinte código:

```html
<iframe 
  src="https://seu-dominio.com/metabase_customizacoes/componentes/tabela_virtual/?question_id=51"
  width="100%" 
  height="600"
  frameborder="0">
</iframe>
```

### Testar a instalação
```bash
./scripts/test.sh
```

## 📊 Componentes Disponíveis

### Tabela Virtual
- Renderização otimizada com virtualização
- Suporte para grandes volumes de dados (100k+ linhas)
- Exportação para CSV
- Formatação automática de números, datas e moedas

### Futuros Componentes
- Gráficos interativos
- KPIs dinâmicos
- Mapas de calor
- Dashboards customizados

## 🔌 API

### Endpoints principais

#### Executar Query
```
GET /api/query?question_id=51&filtro1=valor1&filtro2=valor2
```

#### Informações da Questão
```
GET /api/question/{id}/info
```

#### Debug de Filtros
```
GET /api/debug/filters
```

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```env
# Metabase
METABASE_URL=http://localhost:3000
METABASE_USERNAME=seu_email@example.com
METABASE_PASSWORD=sua_senha

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agencias
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_SCHEMA=road

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=true

# API
API_PORT=3500
CACHE_ENABLED=true
CACHE_TTL=300
```

## 🛠️ Desenvolvimento

### Adicionar novo componente

1. Crie a pasta em `componentes/`:
```bash
mkdir -p componentes/meu_componente/{js,css}
```

2. Crie os arquivos básicos:
- `index.html` - Estrutura HTML
- `js/main.js` - Lógica principal
- `css/styles.css` - Estilos específicos

3. Use os recursos compartilhados:
```javascript
// Em seu main.js
const filters = filterManager.captureFromParent();
const data = await apiClient.queryData(questionId, filters);
```

### Executar testes
```bash
# Testes unitários
pytest tests/

# Com cobertura
pytest --cov=api tests/
```

### Formatação de código
```bash
# Python
black api/

# Verificar estilo
flake8 api/
```

## 📝 Troubleshooting

### Erro de conexão com PostgreSQL
- Verifique as credenciais no `.env`
- Confirme que o PostgreSQL está rodando
- Teste a conexão: `psql -h localhost -U usuario -d banco`

### Cache não funciona
- Verifique se o Redis está rodando: `redis-cli ping`
- Confirme `REDIS_ENABLED=true` no `.env`

### Filtros não são capturados
- Verifique se o iframe está no mesmo domínio
- Confirme que os nomes dos filtros correspondem
- Use o endpoint `/api/debug/filters` para debug

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é proprietário e confidencial.

## 👥 Suporte

Para suporte, entre em contato com a equipe de desenvolvimento.
