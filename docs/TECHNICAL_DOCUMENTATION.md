# Documentação Técnica Completa - Metabase Customizações

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Estrutura de Arquivos e Módulos](#3-estrutura-de-arquivos-e-módulos)
4. [API Backend (Flask)](#4-api-backend-flask)
5. [Frontend (Componentes)](#5-frontend-componentes)
6. [Fluxos de Dados](#6-fluxos-de-dados)
7. [Configuração e Deploy](#7-configuração-e-deploy)
8. [Otimizações e Performance](#8-otimizações-e-performance)
9. [Troubleshooting](#9-troubleshooting)
10. [Guia de Desenvolvimento](#10-guia-de-desenvolvimento)

---

## 1. Visão Geral

### 1.1 Propósito
Sistema de customização para Metabase que permite criar componentes interativos (tabelas, gráficos) em iframes dentro de dashboards, capturando filtros aplicados e executando queries otimizadas diretamente no PostgreSQL.

### 1.2 Principais Características
- **Performance Nativa**: Execução direta no PostgreSQL sem overhead do Metabase
- **Cache Inteligente**: Redis com compressão gzip e TTL configurável
- **Filtros Dinâmicos**: Captura automática com suporte a múltiplos valores e caracteres especiais
- **Virtualização**: Renderização eficiente de grandes volumes de dados (100k+ linhas)
- **Modular**: Arquitetura de componentes reutilizáveis

### 1.3 Stack Tecnológico
- **Backend**: Flask 3.1.0 (Python 3.8+) + psycopg2
- **Frontend**: JavaScript ES6+ vanilla + ClusterizeJS
- **Cache**: Redis 5.0+
- **Database**: PostgreSQL 12+
- **Proxy**: Nginx
- **Deploy**: Gunicorn + systemd

---

## 2. Arquitetura do Sistema

### 2.1 Diagrama de Fluxo
```
[Dashboard Metabase]
        ↓ (filtros na URL)
[iframe Componente]
        ↓ (captura filtros)
[JavaScript Frontend]
        ↓ (requisição AJAX)
[Nginx :8080]
        ↓ (proxy)
[Flask API :3500]
        ↓ (extrai query)
[PostgreSQL :5432]
        ↓ (dados)
[Redis :6379] (cache)
```

### 2.2 Componentes Principais

#### Backend
- **API Flask**: Servidor principal que processa requisições
- **Query Service**: Executa queries com pool de conexões
- **Metabase Service**: Comunica com API do Metabase
- **Cache Service**: Gerencia cache Redis
- **Filter Processor**: Processa e normaliza filtros
- **Query Parser**: Manipula SQL e template tags

#### Frontend
- **Filter Manager**: Captura e monitora filtros
- **API Client**: Comunicação com backend
- **Data Processor**: Processa e formata dados
- **Table Renderer**: Renderiza tabelas com virtualização
- **Export Utils**: Exportação de dados

---

## 3. Estrutura de Arquivos e Módulos

### 3.1 Estrutura de Diretórios
```
metabase_customizacoes/
├── api/                          # Backend Flask
│   ├── routes/                   # Endpoints
│   ├── services/                 # Lógica de negócio
│   └── utils/                    # Utilitários
├── componentes/                  # Frontend
│   ├── recursos_compartilhados/  # JS/CSS reutilizável
│   └── tabela_virtual/          # Componente tabela
├── config/                       # Configurações
├── nginx/                        # Config Nginx
├── scripts/                      # Scripts de gestão
└── docs/                         # Documentação
```

### 3.2 Arquivos Principais
- `api/server.py`: Servidor Flask principal
- `api/services/query_service.py`: Execução de queries
- `componentes/tabela_virtual/js/main.js`: App principal frontend
- `config/settings.py`: Configurações centralizadas
- `.env`: Variáveis de ambiente

---

## 4. API Backend (Flask)

### 4.1 Servidor Principal (`api/server.py`)

```python
def create_app():
    """Cria aplicação Flask com CORS e blueprints"""
    - Configura CORS para todos os origins
    - Registra blueprints: query_routes, debug_routes, static_routes
    - Configura logging rotativo
    - Retorna app configurado
```

**Porta**: 3500  
**Modo Debug**: Configurável via DEBUG env var

### 4.2 Rotas de Query (`api/routes/query_routes.py`)

#### `GET/POST /api/query`
**Propósito**: Executa query com filtros aplicados

**Parâmetros**:
- `question_id` (int): ID da pergunta no Metabase
- `[filtros]`: Qualquer filtro dinâmico

**Resposta**:
```json
{
  "data": {
    "cols": [...],  // Metadados das colunas
    "rows": [...]   // Dados em arrays
  },
  "row_count": 1000,
  "running_time": 250,
  "from_cache": false
}
```

**Fluxo interno**:
1. FilterProcessor captura filtros
2. QueryService.execute_query()
3. Retorna Response comprimida com gzip

#### `GET /api/question/{id}/info`
**Propósito**: Obtém metadados da questão  
**Resposta**: JSON com dataset_query, nome, etc

### 4.3 Rotas de Debug (`api/routes/debug_routes.py`)

#### `GET /api/debug/filters`
**Propósito**: Debug de filtros capturados  
**Resposta**: Filtros processados, multi-valores, caracteres especiais

#### `GET /api/debug/cache/stats`
**Propósito**: Estatísticas do cache Redis  
**Resposta**: Keys, memória, hits/misses

### 4.4 Query Service (`api/services/query_service.py`)

```python
class QueryService:
    def __init__(self):
        - Cria pool de 20 conexões PostgreSQL
        - Inicializa cache service
        - Configura prepared statements
    
    def execute_query(question_id: int, filters: Dict) -> Response:
        """Fluxo principal de execução"""
        1. Gera cache_key = SHA256(question_id + filters)
        2. Verifica cache Redis
        3. Se cache miss:
           - Extrai query SQL via MetabaseService
           - Aplica filtros via QueryParser
           - Executa via _execute_native_query()
           - Salva no cache
        4. Retorna Response formato Metabase
    
    def _execute_native_query(query_sql: str) -> Tuple[cols, rows, time]:
        """Execução otimizada"""
        - SET search_path TO road, public
        - SET work_mem = '256MB'
        - Cursor padrão (não dict)
        - Processa tipos: Decimal→float, date→ISO
        - Retorna formato colunar
```

**Otimizações**:
- Pool de conexões persistente
- work_mem aumentado para queries grandes
- Cursor padrão para melhor performance
- Processamento de tipos inline

### 4.5 Metabase Service (`api/services/metabase_service.py`)

```python
class MetabaseService:
    def get_session_token() -> str:
        """Autentica e reutiliza token"""
        
    def get_question_query(question_id: int) -> Dict:
        """Extrai SQL e template tags"""
        Retorna: {
            'query': 'SELECT ...',
            'template_tags': ['conta', 'campanha'],
            'question_name': 'Análise',
            'database_id': 2
        }
```

**Cache interno**: Queries extraídas são cacheadas em memória

### 4.6 Filter Processor (`api/utils/filters.py`)

```python
class FilterProcessor:
    MULTI_VALUE_PARAMS = [
        'campanha', 'conta', 'adset', 'ad_name',
        'plataforma', 'posicao', 'device', ...
    ]
    
    NORMALIZATION_MAP = {
        'posição': 'posicao',
        'anúncio': 'anuncio',
        'objetivo': 'objective'
    }
    
    def capture_from_request(request) -> Dict:
        """Captura filtros com suporte a múltiplos valores"""
        - Detecta parâmetros repetidos
        - Normaliza nomes
        - Decodifica caracteres especiais
        
    def format_for_metabase(filters) -> List[Dict]:
        """Converte para formato API Metabase"""
        - String única: {"value": ["valor"]}
        - Array: {"value": ["v1", "v2", "v3"]}
        - Data range: {"value": "2024-01-01~2024-01-31"}
```

### 4.7 Query Parser (`api/utils/query_parser.py`)

```python
class QueryParser:
    FIELD_MAPPING = {
        'data': 'date',
        'conta': 'account_name',
        'campanha': 'campaign_name',
        ...
    }
    
    def apply_filters(query: str, filters: Dict) -> str:
        """Substitui template tags do Metabase"""
        - Padrão: [[AND {{nome}}]]
        - Substitui por: AND campo = 'valor'
        - Arrays: AND campo IN ('v1', 'v2')
        - Remove tags não utilizadas
        
    def clean_problematic_fields(query: str) -> str:
        """Remove campos JSONB que causam erro"""
        - conversions_json → conversions
        - Remove aliases problemáticos
```

**SQL Injection Prevention**: Escape com aspas duplas

### 4.8 Cache Service (`api/services/cache_service.py`)

```python
class CacheService:
    def __init__(self):
        - Conecta Redis localhost:6379
        - Fallback se não disponível
        
    def get(key: str) -> Optional[Dict]:
        """Descomprime e deserializa"""
        
    def set(key: str, value: Dict):
        """Comprime com gzip e salva"""
        - TTL padrão: 300s
        - Compressão ~70%
```

---

## 5. Frontend (Componentes)

### 5.1 Recursos Compartilhados

#### API Client (`recursos_compartilhados/js/api-client.js`)

```javascript
class MetabaseAPIClient {
    constructor() {
        - baseUrl auto-detectada
        - timeout: 5 minutos
        - cache local Map()
    }
    
    async queryData(questionId, filters) {
        - Verifica cache local
        - GET /api/query
        - Adiciona ao cache
        - Retorna dados
    }
    
    buildUrl(endpoint, params) {
        - Suporta arrays: param=A&param=B
        - URLSearchParams
    }
}
```

#### Filter Manager (`recursos_compartilhados/js/filter-manager.js`)

```javascript
class FilterManager {
    captureFromParent() {
        - Detecta se está em iframe
        - Captura window.parent.location.href
        - Parse manual da query string
        - Retorna filtros normalizados
    }
    
    decodeParameter(str) {
        - Substitui + por espaço
        - decodeURIComponent (não unquote_plus!)
        - Dupla decodificação se necessário
    }
    
    startMonitoring(interval = 1000) {
        - Verifica mudanças periodicamente
        - Intervalo adaptativo (1s → 5s)
        - Notifica observers
    }
}
```

#### Data Processor (`recursos_compartilhados/js/data-processor.js`)

```javascript
class DataProcessor {
    processNativeResponse(nativeData) {
        - Converte formato colunar → objetos
        - cols + rows → [{col1: val1, ...}]
    }
    
    formatters = {
        'number': Intl.NumberFormat('pt-BR'),
        'currency': 'BRL',
        'percent': value/100 + '%',
        'date': toLocaleDateString('pt-BR')
    }
}
```

### 5.2 Componente Tabela Virtual

#### Estrutura HTML (`tabela_virtual/index.html`)
```html
<body>
    <div id="app">
        <div id="update-indicator"></div>
        <div id="debug-container"></div>
        <div id="table-container"></div>
    </div>
    
    <!-- ClusterizeJS para virtualização -->
    <script src="clusterize.min.js"></script>
    <!-- Scripts do componente -->
    <script src="js/utils.js"></script>
    <script src="js/filtros.js"></script>
    <script src="js/data-loader.js"></script>
    <script src="js/virtual-table.js"></script>
    <script src="js/main.js"></script>
</body>
```

#### App Principal (`tabela_virtual/js/main.js`)

```javascript
class App {
    async init() {
        - questionId da URL ou padrão 51
        - Cria VirtualTable
        - setupListeners() para atalhos
        - loadData('inicialização')
        - startMonitoring()
    }
    
    async loadData(motivo) {
        - Captura filtros do parent
        - Verifica se mudaram
        - Mostra loading
        - dataLoader.loadWithRetry()
        - virtualTable.render(dados)
        - Monitora memória se >10k linhas
    }
    
    setupListeners() {
        - Ctrl+R: Recarregar
        - Ctrl+E: Exportar CSV
        - visibilitychange: Recarrega ao voltar
    }
}
```

#### Virtual Table (`tabela_virtual/js/virtual-table.js`)

```javascript
class VirtualTable {
    render(data) {
        - Se >1000 linhas: ClusterizeJS
        - Se <1000: tabela normal
        - Mostra total formatado
        - Badge "Virtualização Ativa"
    }
    
    renderWithClusterize() {
        - rows_in_block: 50
        - blocks_in_cluster: 4
        - Header sticky
        - Scroll virtual
    }
    
    exportToCsv() {
        - Gera CSV com headers
        - Escapa vírgulas/aspas
        - Download via blob
    }
}
```

#### Data Loader (`tabela_virtual/js/data-loader.js`)

```javascript
class DataLoader {
    async loadData(questionId, filtros) {
        - SEMPRE usa /api/query (Native)
        - Headers: Accept-Encoding: gzip
        - processNativeResponse()
        - Retorna array de objetos
    }
    
    loadWithRetry(questionId, filtros, maxRetries = 3) {
        - Tentativas com backoff
        - 1s, 2s, 3s entre tentativas
    }
}
```

---

## 6. Fluxos de Dados

### 6.1 Fluxo Completo de Requisição

```
1. Dashboard Metabase
   URL: ?conta=EMPRESA&campanha=Camp1&campanha=Camp2
   
2. iframe (componente)
   - filterManager.captureFromParent()
   - Parse manual, decodificação dupla
   - Normalização: posição→posicao
   
3. Frontend → Backend
   GET /api/query?question_id=51&conta=EMPRESA&campanha=Camp1&campanha=Camp2
   
4. Backend Processing
   - FilterProcessor.capture_from_request()
   - Detecta múltiplos valores: campanha = ["Camp1", "Camp2"]
   - Cache key: SHA256("51:{filters}")
   
5. Cache Check
   - Redis GET metabase:query:{key}
   - Se hit: descomprime gzip, retorna
   
6. Query Execution (se cache miss)
   - MetabaseService: extrai SQL template
   - QueryParser: substitui [[AND {{conta}}]]
   - PostgreSQL: executa com work_mem=256MB
   - Processa tipos: Decimal→float
   
7. Response
   - Formato colunar Metabase
   - Compressão gzip
   - Headers: Content-Encoding: gzip
   - Salva no cache
   
8. Frontend Rendering
   - Converte colunar→objetos
   - Se >1000 linhas: ClusterizeJS
   - Formatação por tipo
   - Update indicator
```

### 6.2 Fluxo de Monitoramento de Filtros

```
1. startMonitoring(1000ms)
2. Loop:
   - captureFromParent()
   - hasChanged()?
   - Se sim: notifyObservers()
   - Se não: aumenta intervalo (+500ms até 5s)
3. Observer dispara loadData()
```

### 6.3 Fluxo de Cache

```
1. Request → Cache Key (SHA256)
2. Redis GET
3. Se existe e TTL válido:
   - Descomprime gzip
   - Parse JSON
   - Retorna imediato
4. Se não:
   - Executa query
   - JSON.stringify
   - Comprime gzip (~70% redução)
   - Redis SETEX com TTL 300s
```

---

## 7. Configuração e Deploy

### 7.1 Variáveis de Ambiente (.env)

```env
# Metabase
METABASE_URL=http://localhost:3000
METABASE_USERNAME=seu_email@example.com
METABASE_PASSWORD=sua_senha

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agencias
DB_USER=cazouvilela
DB_PASSWORD=sua_senha
DB_SCHEMA=road

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=true

# API
API_PORT=3500
API_TIMEOUT=300
CACHE_ENABLED=true
CACHE_TTL=300

# Performance
MAX_POOL_SIZE=20
WORK_MEM=256MB
MAX_ROWS_WITHOUT_WARNING=10000

# Development
DEBUG=false
LOG_LEVEL=INFO
```

### 7.2 Nginx Configuration

```nginx
server {
    listen 8080;
    client_max_body_size 900M;
    
    # API Flask
    location /metabase_customizacoes/api/ {
        proxy_pass http://127.0.0.1:3500/api/;
        proxy_read_timeout 300;
        add_header Access-Control-Allow-Origin "*";
    }
    
    # Componentes Frontend
    location /metabase_customizacoes/componentes/ {
        alias /home/cazouvilela/metabase_customizacoes/componentes/;
        add_header X-Frame-Options "SAMEORIGIN";
    }
    
    # Metabase (catch-all)
    location / {
        proxy_pass http://localhost:3000;
        gzip on;
        gzip_types application/json;
    }
}
```

### 7.3 Scripts de Gestão

#### start.sh
```bash
#!/bin/bash
- Verifica .env
- Cria/ativa venv
- pip install -r requirements.txt
- Testa PostgreSQL e Metabase
- Inicia servidor (dev ou gunicorn)
```

#### test.sh
```bash
#!/bin/bash
- Testa imports Python
- Verifica endpoints
- Lista componentes frontend
- Sugere pytest para testes unitários
```

### 7.4 Deploy em Produção

```bash
# Instalar dependências sistema
sudo dnf install python3 python3-pip redis nginx postgresql

# Clonar e configurar
cd /home/usuario
git clone [repo]
cd metabase_customizacoes
cp .env.example .env
# Editar .env

# Instalar Python deps
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar Nginx
sudo cp nginx/metabase.conf /etc/nginx/conf.d/
sudo nginx -s reload

# Iniciar com systemd
sudo systemctl start metabase-api
```

---

## 8. Otimizações e Performance

### 8.1 Backend

#### Pool de Conexões
- 20 conexões persistentes
- Reuso automático
- Health check antes de usar
- Fallback para nova conexão

#### Query Optimization
```sql
SET search_path TO road, public;
SET work_mem = '256MB';
SET random_page_cost = 1.1;
```

#### Cache Strategy
- Redis com gzip (~70% compressão)
- TTL 5 minutos
- Cache key: SHA256(question_id + filters)
- Skip cache para queries muito rápidas

### 8.2 Frontend

#### Virtualização
- ClusterizeJS para >1000 linhas
- Renderiza apenas visível
- Blocks de 50 linhas
- Mantém performance com 100k+ linhas

#### Otimizações de Rede
- Cache local em Map()
- Debounce de requisições
- Compressão gzip
- Timeout de 5 minutos

### 8.3 Caracteres Especiais

#### Problema Original
- `+` virava espaço
- Dupla codificação
- Flask decodifica errado

#### Solução
- Parse manual da query string
- `unquote()` em vez de `unquote_plus()`
- Decodificação controlada
- Suporta: `+ & % # | @ ! $ ^ ( ) [ ] { }`

### 8.4 Múltiplos Valores

#### Detecção
```javascript
// URL: ?camp=A&camp=B&camp=C
if (params[key]) {
    if (Array.isArray(params[key])) {
        params[key].push(value);
    } else {
        params[key] = [params[key], value];
    }
}
```

#### Formato Metabase
```json
{
    "type": "string/=",
    "target": ["dimension", ["template-tag", "campanha"]],
    "value": ["A", "B", "C"]  // Array
}
```

---

## 9. Troubleshooting

### 9.1 Problemas Comuns

#### "0 linhas retornadas"
1. Verificar filtros no `/api/debug/filters`
2. Comparar valores com banco
3. Testar decodificação de caracteres
4. Verificar logs do PostgreSQL

#### "Menos linhas que dashboard"
1. Verificar múltiplos valores
2. Debug com `?debug=true`
3. Comparar query executada

#### "Performance lenta"
1. Verificar índices no PostgreSQL
2. Cache Redis ativo?
3. Queries com EXPLAIN ANALYZE
4. Aumentar work_mem se necessário

#### "Erro de serialização JSON"
1. Campos JSONB problemáticos
2. Usar clean_problematic_fields()
3. Verificar tipos Decimal

### 9.2 Comandos Úteis

```javascript
// Console do navegador
app.getStats()              // Estatísticas
filterManager.currentFilters // Filtros ativos
dataLoader.clearCache()     // Limpa cache local

// API Debug
GET /api/debug/filters      // Filtros capturados
GET /api/debug/cache/stats  // Status Redis
POST /api/debug/cache/clear // Limpa cache
```

### 9.3 Logs

```bash
# API Flask
tail -f logs/api.log

# Nginx
tail -f /var/log/nginx/error.log

# PostgreSQL
tail -f /var/lib/pgsql/data/log/postgresql-*.log

# Redis
redis-cli MONITOR
```

---

## 10. Guia de Desenvolvimento

### 10.1 Adicionar Novo Componente

1. **Criar estrutura**:
```bash
mkdir -p componentes/meu_grafico/{js,css}
touch componentes/meu_grafico/index.html
```

2. **HTML base**:
```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="../recursos_compartilhados/css/base.css">
    <link rel="stylesheet" href="css/styles.css">
</head>
<body>
    <div id="app"></div>
    
    <script src="../recursos_compartilhados/js/api-client.js"></script>
    <script src="../recursos_compartilhados/js/filter-manager.js"></script>
    <script src="js/main.js"></script>
</body>
</html>
```

3. **JavaScript principal**:
```javascript
class MeuGrafico {
    async init() {
        const questionId = new URLSearchParams(window.location.search).get('question_id');
        const filters = filterManager.captureFromParent();
        const data = await apiClient.queryData(questionId, filters);
        this.render(data);
    }
}
```

### 10.2 Adicionar Novo Filtro

1. **Backend** (`api/utils/filters.py`):
```python
# Se aceita múltiplos valores
MULTI_VALUE_PARAMS.append('novo_filtro')

# Normalização se necessário
NORMALIZATION_MAP['novo'] = 'novo_filtro'
```

2. **Query Parser** (`api/utils/query_parser.py`):
```python
FIELD_MAPPING['novo_filtro'] = 'database_column_name'
```

3. **Frontend** (`filter-manager.js`):
```javascript
multiValueParams.push('novo_filtro');
```

### 10.3 Adicionar Novo Endpoint

1. **Criar rota** (`api/routes/custom_routes.py`):
```python
from flask import Blueprint

bp = Blueprint('custom', __name__)

@bp.route('/custom/action', methods=['POST'])
def custom_action():
    # Implementação
    return jsonify({'status': 'ok'})
```

2. **Registrar** (`api/server.py`):
```python
from api.routes import custom_routes
app.register_blueprint(custom_routes.bp, url_prefix='/api')
```

### 10.4 Testes

```python
# tests/test_filters.py
def test_multiple_values():
    filters = FilterProcessor()
    result = filters.capture_from_request(mock_request)
    assert result['campanha'] == ['A', 'B', 'C']

# tests/test_query_parser.py
def test_template_substitution():
    parser = QueryParser()
    sql = "SELECT * WHERE 1=1 [[AND {{conta}}]]"
    result = parser.apply_filters(sql, {'conta': 'EMPRESA'})
    assert "AND account_name = 'EMPRESA'" in result
```

### 10.5 Melhores Práticas

1. **Performance**:
   - Use cache para queries pesadas
   - Implemente paginação se >50k linhas
   - Monitore pool de conexões

2. **Segurança**:
   - Sempre escape valores SQL
   - Valide question_id como integer
   - Use HTTPS em produção

3. **Manutenibilidade**:
   - Documente mudanças
   - Mantenha logs detalhados
   - Use type hints no Python

4. **UX**:
   - Mostre loading states
   - Feedback de erros claro
   - Atalhos de teclado

---

## Anexo A: Template Tags do Metabase

### Formato Padrão
```sql
-- Filtro opcional
[[AND {{nome_filtro}}]]

-- Filtro obrigatório
{{nome_filtro}}

-- Com valor padrão
[[AND {{nome_filtro:default_value}}]]
```

### Tipos de Template Tags
- **Text**: Valor simples ou múltiplo
- **Number**: Valores numéricos
- **Date**: Single date ou range
- **Field Filter**: Mapeia para coluna específica

### Exemplo de Query Completa
```sql
WITH base_data AS (
  SELECT * 
  FROM road.view_metaads_insights_alldata
  WHERE 1=1
  [[AND {{data}}]]
  [[AND {{conta}}]]
  [[AND {{campanha}}]]
)
SELECT 
  date,
  account_name,
  campaign_name,
  SUM(spend) as total_spend,
  SUM(clicks) as total_clicks,
  CASE 
    WHEN SUM(impressions) = 0 THEN 0
    ELSE ROUND((SUM(clicks)::NUMERIC / SUM(impressions) * 100), 2)
  END AS ctr_percent
FROM base_data
GROUP BY date, account_name, campaign_name
ORDER BY date DESC
```

---

## Anexo B: Formato de Response Metabase

### Response Completa
```json
{
  "data": {
    "cols": [
      {
        "name": "date",
        "base_type": "type/Date",
        "display_name": "Data",
        "fingerprint": null
      },
      {
        "name": "spend",
        "base_type": "type/Decimal",
        "display_name": "Investimento",
        "fingerprint": {
          "type": {
            "type/Number": {
              "min": 0.0,
              "max": 10000.0,
              "avg": 500.0
            }
          }
        }
      }
    ],
    "rows": [
      ["2024-01-01", 150.50],
      ["2024-01-02", 200.00]
    ],
    "rows_truncated": 2,
    "results_metadata": {
      "columns": [...],
      "checksum": "abc123"
    }
  },
  "database_id": 2,
  "started_at": "2024-01-15T10:30:00.000Z",
  "json_query": {
    "database": 2,
    "type": "native",
    "native": {
      "query": "SELECT ...",
      "template-tags": {...}
    }
  },
  "average_execution_time": 145,
  "status": "completed",
  "context": "question",
  "row_count": 2,
  "running_time": 145
}
```

### Tipos de Base Type
- `type/Text`: Strings
- `type/Integer`: Inteiros
- `type/BigInteger`: Inteiros grandes
- `type/Float`: Decimais
- `type/Decimal`: Valores monetários
- `type/Date`: Apenas data
- `type/DateTime`: Data e hora
- `type/DateTimeWithTZ`: Com timezone
- `type/Boolean`: true/false
- `type/JSON`: Objetos JSON
- `type/Category`: Valores categóricos
- `type/URL`: Links
- `type/Email`: Endereços de email

---

## Sobre Esta Documentação

Esta documentação fornece uma visão completa do sistema Metabase Customizações, permitindo compreender e modificar qualquer parte sem necessidade dos arquivos de código fonte.

**Versão**: 2.0.0  
**Última Atualização**: Janeiro 2025  
**Mantido por**: Equipe de Desenvolvimento

### Como Usar Esta Documentação

1. **Para desenvolvimento**: Use o índice para encontrar a seção relevante
2. **Para troubleshooting**: Vá direto para seção 9
3. **Para adicionar features**: Siga os guias na seção 10
4. **Para deploy**: Seção 7 tem todos os passos

### Convenções

- `código inline`: Nomes de arquivos, funções, variáveis
- **Negrito**: Conceitos importantes
- *Itálico*: Observações e notas
- `→`: Indica fluxo ou transformação

### Contribuindo

Para manter esta documentação atualizada:
1. Documente mudanças significativas
2. Atualize exemplos de código
3. Adicione novos troubleshooting descobertos
4. Mantenha o índice sincronizado

---

**Fim da Documentação Técnica**
