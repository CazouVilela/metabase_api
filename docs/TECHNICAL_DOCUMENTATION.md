# Documentação Técnica Completa - Metabase Customizações v3.5

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Estrutura de Arquivos e Módulos](#3-estrutura-de-arquivos-e-módulos)
4. [API Backend (Flask)](#4-api-backend-flask)
5. [Frontend (Componentes)](#5-frontend-componentes)
6. [Fluxos de Dados](#6-fluxos-de-dados)
7. [Sistema de Filtros](#7-sistema-de-filtros)
8. [Sistema de Virtualização](#8-sistema-de-virtualização)
9. [Configuração e Deploy](#9-configuração-e-deploy)
10. [Otimizações e Performance](#10-otimizações-e-performance)
11. [Troubleshooting](#11-troubleshooting)
12. [Guia de Desenvolvimento](#12-guia-de-desenvolvimento)
13. [Comandos de Debug](#13-comandos-de-debug)
14. [Changelog](#14-changelog)

---

## 1. Visão Geral

### 1.1 Propósito
Sistema de customização para Metabase que permite criar componentes interativos (tabelas, gráficos) em iframes dentro de dashboards, capturando filtros aplicados e executando queries otimizadas diretamente no PostgreSQL.

### 1.2 Principais Características
- **Virtualização Real**: Apenas ~300 linhas HTML no DOM independente do volume total (v3.4)
- **Performance Extrema**: Suporta milhões de linhas sem problemas de memória
- **Cache Inteligente**: Redis com compressão gzip (temporariamente desabilitado em v3.4)
- **Filtros Dinâmicos**: Captura automática com detecção inteligente de mudanças
- **Parser de Datas Avançado**: Suporte completo para filtros relativos dinâmicos
- **Mapeamento Inteligente**: Sistema flexível de mapeamento de parâmetros
- **Filtros JSON**: Suporte a filtragem por conteúdo de campos JSONB
- **Economia de Memória**: 99.95% menos uso de memória para grandes volumes
- **Monitoramento Inteligente**: Detecção de mudanças sem loops falsos
- **Debug Avançado**: Comandos para diagnóstico em produção
- **Gráficos Interativos**: Componente de gráfico combinado com múltiplos eixos (v3.5)

### 1.3 Stack Tecnológico
- **Backend**: Flask 3.1.0 (Python 3.8+) + psycopg2
- **Frontend**: JavaScript ES6+ vanilla + Virtualização customizada
- **Gráficos**: Highcharts 11.x
- **Cache**: Redis 5.0+ (opcional)
- **Database**: PostgreSQL 12+
- **Proxy**: Nginx
- **Deploy**: Gunicorn + systemd
- **Dependências Python**: python-dateutil, Flask, psycopg2-binary, redis, python-dotenv

### 1.4 Capacidades de Volume (v3.5)
- **Tabela Virtual**: 653.285+ linhas sem problemas
- **Gráfico Combinado**: 600.000+ linhas agregadas em ~500ms
- **Memória constante**: ~300MB independente do número de linhas
- **Renderização instantânea**: < 0.1s para tabela, < 1s para gráfico
- **Scroll suave**: 60 FPS garantidos
- **Exportação**: Suporta milhões de linhas

---

## 2. Arquitetura do Sistema

### 2.1 Diagrama de Fluxo
```
[Dashboard Metabase]
        ↓ (filtros na URL)
[iframe Componente]
        ↓ (captura filtros via filterManager)
[JavaScript Frontend]
        ↓ (requisição AJAX com controle de concorrência)
[Nginx :8080]
        ↓ (proxy)
[Flask API :3500]
        ↓ (QueryParser processa filtros e mapeamentos)
        ↓ (extrai e modifica query)
[PostgreSQL :5432]
        ↓ (dados formato colunar)
[Redis :6379] (cache - opcional)
        ↓
[Componente Específico]
        ├─ Tabela: Virtualização Real
        └─ Gráfico: Agregação + Highcharts
```

### 2.2 Componentes Principais

#### Backend
- **API Flask**: Servidor principal que processa requisições
- **Query Service**: Executa queries com pool de conexões
- **Metabase Service**: Comunica com API do Metabase
- **Cache Service**: Gerencia cache Redis (desabilitado em v3.4)
- **Query Parser**: Processa template tags, filtros e mapeamentos

#### Frontend - Recursos Compartilhados
- **Filter Manager**: Captura e monitora filtros com detecção inteligente
- **API Client**: Comunicação com backend e validação de respostas
- **Data Processor**: Processa e formata dados
- **Export Utils**: Exportação de dados otimizada

#### Frontend - Componentes Específicos
- **Tabela Virtual**: Renderização com virtualização real (v3.4)
- **Gráfico Combinado**: Visualização multi-eixos com Highcharts (v3.5)

---

## 3. Estrutura de Arquivos e Módulos

### 3.1 Estrutura de Diretórios
```
metabase_customizacoes/
├── api/                          # Backend Flask
│   ├── routes/                   # Endpoints
│   ├── services/                 # Lógica de negócio
│   └── utils/                    # Utilitários
│       └── query_parser.py       # Parser de queries e filtros
├── componentes/                  # Frontend
│   ├── recursos_compartilhados/  # JS/CSS reutilizável
│   │   ├── js/
│   │   │   ├── api-client.js    # Cliente API com validação (v3.4)
│   │   │   ├── filter-manager.js # Gerenciador com detecção inteligente (v3.4)
│   │   │   ├── data-processor.js # Processador de dados
│   │   │   └── export-utils.js   # Utilitários de exportação
│   │   └── css/
│   │       └── base.css          # Estilos compartilhados
│   ├── tabela_virtual/           # Componente tabela
│   │   ├── index.html            # HTML principal
│   │   ├── js/
│   │   │   ├── main.js           # App principal com debug (v3.4)
│   │   │   ├── virtual-table.js  # Virtualização real (v3.4)
│   │   │   └── utils.js          # Utilitários locais
│   │   └── css/
│   │       └── tabela.css        # Estilos + virtualização
│   └── grafico_combo/            # Componente gráfico (v3.5)
│       ├── index.html            # HTML principal
│       ├── js/
│       │   ├── main_grafico_combo.js # App principal
│       │   ├── config.js         # Configurações
│       │   ├── data-transformer.js # Agregação otimizada
│       │   └── chart-builder.js  # Construtor Highcharts
│       ├── css/
│       │   └── grafico.css       # Estilos específicos
│       └── README.md             # Documentação do componente
├── config/                       # Configurações
├── nginx/                        # Config Nginx
├── scripts/                      # Scripts de gestão
└── docs/                         # Documentação
```

### 3.2 Arquivos Principais (v3.5)
- `api/server.py`: Servidor Flask principal
- `api/services/query_service.py`: Execução de queries
- `api/utils/query_parser.py`: Parser avançado de queries
- `componentes/recursos_compartilhados/js/filter-manager.js`: Monitor inteligente de filtros
- `componentes/recursos_compartilhados/js/api-client.js`: Cliente API com validação robusta
- `componentes/tabela_virtual/js/main.js`: App tabela com controle de concorrência
- `componentes/tabela_virtual/js/virtual-table.js`: Virtualização real para milhões de linhas
- `componentes/grafico_combo/js/main_grafico_combo.js`: App gráfico com performance otimizada
- `componentes/grafico_combo/js/data-transformer.js`: Agregação em lotes para grandes volumes
- `componentes/grafico_combo/js/chart-builder.js`: Construtor Highcharts com altura fixa
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
    - Pool de conexões otimizado
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

**Validação de Resposta** (v3.4):
- Verifica estrutura `data.cols` e `data.rows`
- Retorna erro claro se dados inválidos
- Log detalhado de problemas

**Resposta** (Formato Colunar):
```json
{
  "data": {
    "cols": [
      {"name": "date", "base_type": "type/Date", "display_name": "Data"},
      {"name": "spend", "base_type": "type/Decimal", "display_name": "Investimento"}
    ],
    "rows": [
      ["2024-01-01", 150.50],
      ["2024-01-02", 200.00]
    ]
  },
  "row_count": 653285,
  "running_time": 250,
  "from_cache": false
}
```

### 4.3 Query Service (`api/services/query_service.py`)

**Otimizações**:
- Formato colunar nativo mantido
- Pool de 20 conexões persistentes
- work_mem: 256MB
- Statement timeout: 300s
- Cache Redis com compressão

### 4.4 Query Parser (`api/utils/query_parser.py`)

**Funcionalidades**:
- Parser de datas dinâmicas completo
- Mapeamento inteligente de parâmetros
- Suporte a filtros JSON complexos
- Tratamento especial para conversões

---

## 5. Frontend (Componentes)

### 5.1 Recursos Compartilhados

#### Filter Manager (`filter-manager.js`) v3.4

**Melhorias**:
- ✅ Flag `isFirstCapture` evita detecção falsa inicial
- ✅ Comparação robusta de estados
- ✅ Logs detalhados de mudanças
- ✅ Delay configurável antes de iniciar monitoramento

```javascript
// Uso recomendado
filterManager.startMonitoring(callback, 2000); // 2 segundos delay
```

#### API Client (`api-client.js`) v3.4

**Melhorias**:
- ✅ Cache temporariamente desabilitado (problema com dados vazios)
- ✅ Validação rigorosa de respostas
- ✅ Limpeza automática de cache em erros
- ✅ Logs detalhados de dados recebidos

```javascript
// Validação implementada
if (!data || !data.data || !data.data.rows) {
  throw new Error('Resposta inválida da API');
}
```

### 5.2 Componente Tabela Virtual

#### Virtual Table (`virtual-table.js`) v3.4

**Virtualização Real Implementada**:

```javascript
// Configuração
visibleRows: 100      // Linhas visíveis
bufferRows: 100       // Buffer acima/abaixo
rowHeight: 30         // Altura de cada linha

// Resultado
Total: 653.285 linhas
DOM: ~300 linhas
Economia: 99.95%
```

**Características**:
- Renderização sob demanda durante scroll
- Throttle de 60 FPS
- Zero cache de HTML
- Suporte a milhões de linhas

#### App Principal (`main.js`) v3.4

**Melhorias**:
- ✅ Flag `isLoading` previne requisições simultâneas
- ✅ Delay de 3s antes de iniciar monitoramento
- ✅ Comandos de debug integrados
- ✅ Validação completa de dados

### 5.3 Componente Gráfico Combinado (v3.5)

#### Visão Geral
Componente de visualização que apresenta dados em formato de gráfico combinado com múltiplos eixos Y, baseado na biblioteca Highcharts.

#### Características Principais
- **3 Eixos Y independentes**: Impressões, Clicks e Investimento
- **Agregação por mês**: Reduz volume de dados automaticamente
- **Colunas empilhadas**: Impressões por conta
- **Linhas sobrepostas**: Clicks e Investimento totais
- **Exportação múltipla**: PNG, JPG, SVG, CSV
- **Performance otimizada**: Agregação em lotes para grandes volumes
- **Altura fixa**: Previne crescimento vertical infinito

#### Arquitetura (`grafico_combo/`)

**Controlador Principal** (`main_grafico_combo.js`):
```javascript
class ChartApp {
    - Integração com FilterManager
    - Carregamento de dados via API
    - Controle de estado e loading
    - Comandos de debug avançados
    - Debounce de 500ms para filtros
    - Medição de performance por etapa
}
```

**Transformador de Dados** (`data-transformer.js`):
```javascript
class DataTransformer {
    - Agregação mensal automática
    - Processamento em lotes (1000 linhas)
    - Logs de progresso durante agregação
    - Mapeamento de colunas flexível
    - Cálculo de estatísticas
    - Exportação CSV otimizada
}
```

**Construtor do Gráfico** (`chart-builder.js`):
```javascript
class ChartBuilder {
    - Configuração de 3 eixos Y
    - Altura fixa de 450px
    - Responsive design
    - Modo tela cheia
    - Exportação nativa
    - Animação desabilitada na renderização inicial
}
```

#### Fluxo de Dados

1. **Carregamento**: 41k+ linhas da API (~650ms)
2. **Agregação**: Reduz para ~24-36 pontos mensais (~500ms)
3. **Transformação**: Formato Highcharts (~50ms)
4. **Renderização**: Gráfico interativo (~100ms)

#### Performance

| Métrica | Valor |
|---------|-------|
| Dados de entrada | 600k+ linhas |
| Dados processados | ~36 pontos |
| Tempo total | < 1.5s |
| Tempo agregação | ~500ms |
| Memória | ~50-100MB |

#### Configuração (`config.js`)

```javascript
columnMapping: {
    date: 'date',
    account: 'account_name',
    impressions: 'impressions',
    clicks: 'clicks',
    spend: 'spend'
}
```

---

## 6. Fluxos de Dados

### 6.1 Fluxo de Carregamento - Tabela (v3.4)

```
1. Inicialização
   - Injeta estilos de virtualização
   - Configura serviços
   - Carrega dados iniciais
   - Aguarda 3s antes de monitorar filtros

2. Carregamento de Dados
   - Flag isLoading previne concorrência
   - Valida resposta rigorosamente
   - Detecta formato colunar

3. Renderização Virtual
   - Cria estrutura com espaçador virtual
   - Renderiza apenas linhas visíveis (~300)
   - Configura scroll handler otimizado

4. Interação
   - Scroll renderiza novas linhas sob demanda
   - Atualiza indicador de linhas visíveis
   - Mantém performance constante
```

### 6.2 Fluxo de Carregamento - Gráfico (v3.5)

```
1. Inicialização
   - Valida question_id da URL
   - Configura event listeners
   - Carrega dados iniciais
   - Aguarda 3s antes de monitorar

2. Carregamento de Dados
   - Flag isLoading previne concorrência
   - Mede tempo de cada etapa
   - Valida resposta da API

3. Transformação
   - Agregação em lotes (1000 linhas)
   - Logs de progresso (25%, 50%, 75%)
   - Reduz para pontos mensais

4. Renderização
   - Container com altura fixa (450px)
   - Animação desabilitada inicialmente
   - Reabilita animação após 100ms

5. Interação
   - Debounce de 500ms para mudanças de filtros
   - Modo tela cheia dinâmico
   - Exportação em múltiplos formatos
```

### 6.3 Fluxo de Detecção de Filtros (v3.4)

```
1. Monitoramento Inicial
   - Aguarda 3 segundos após carregar
   - Captura estado inicial sem notificar

2. Detecção de Mudanças
   - Compara JSON stringificado
   - Ignora primeira "mudança" (isFirstCapture)
   - Loga mudanças detalhadamente

3. Atualização
   - Verifica flag isLoading
   - Executa nova requisição se livre
   - Atualiza componente com novos dados
```

---

## 7. Sistema de Filtros

### 7.1 Parser Dinâmico de Datas

O sistema suporta filtros de data dinâmicos compatíveis com o Metabase. O parser (`api/utils/query_parser.py`) detecta e converte automaticamente filtros relativos em intervalos de data SQL.

#### 7.1.1 Sintaxe Suportada

**Formato básico**: `[direção][número][unidade][flag_inclusão]`
- **direção**: past, last, next, previous
- **número**: qualquer número inteiro
- **unidade**: days, weeks, months, quarters, years
- **flag_inclusão**: `~` (opcional) para incluir período atual

#### 7.1.2 Comportamento dos Filtros

**PASSADO (past/last)**:

| Filtro | Sem flag (~) | Com flag (~) |
|--------|--------------|--------------|
| past7days | Últimos 7 dias (excluindo hoje) | Últimos 7 dias incluindo hoje |
| past2weeks | 2 semanas completas anteriores (Dom-Sáb) | 2 semanas anteriores + semana atual |
| past3months | 3 meses completos anteriores | 3 meses anteriores + mês atual |

#### 7.1.3 Casos Especiais

- `thisday`: hoje (Metabase usa este em vez de "today")
- `yesterday`: ontem
- `tomorrow`: amanhã
- `thisweek/month/quarter/year`: período atual completo
- `alltime`: desde 2000-01-01 até hoje

### 7.2 Mapeamento de Parâmetros

O sistema suporta mapeamento automático de parâmetros do dashboard para campos SQL:

```python
FIELD_MAPPING = {
    'data': 'date',
    'conta': 'account_name',
    'campanha': 'campaign_name',
    'adset': 'adset_name',
    'ad_name': 'ad_name',
    'anuncio': 'ad_name',      # Sinônimo
    'plataforma': 'publisher_platform',
    'posicao': 'platform_position',
    'device': 'impression_device',
    'objective': 'objective',
    'optimization_goal': 'optimization_goal',
    'buying_type': 'buying_type',
    'action_type_filter': 'action_type',
    'conversoes_consideradas': 'conversoes_consideradas'
}
```

### 7.3 Filtro de Conversões por Action Type

O filtro `conversoes_consideradas` permite filtragem por conteúdo JSON:

```sql
[[AND EXISTS (
  SELECT 1 
  FROM jsonb_array_elements(conversions) AS elem
  WHERE elem->>'action_type' IN (
    SELECT action_type 
    FROM road.view_conversions_action_types_list
    WHERE {{conversoes_consideradas}}
  )
)]]
```

---

## 8. Sistema de Virtualização (v3.4)

### 8.1 Conceito

Em vez de renderizar todas as linhas no DOM, apenas ~300 linhas são mantidas a qualquer momento, independente do volume total de dados.

### 8.2 Implementação

```javascript
// Estrutura HTML
<div class="virtual-scroll-area">           // Container com scroll
  <div class="virtual-scroll-spacer">       // Espaçador com altura total
    <div class="virtual-content">           // Apenas linhas visíveis
      <table>
        <tr style="position: absolute; top: 0px">...</tr>
        <tr style="position: absolute; top: 30px">...</tr>
        // ... apenas ~300 linhas
      </table>
    </div>
  </div>
</div>
```

### 8.3 Benefícios

- **Memória constante**: ~300MB para qualquer volume
- **Performance constante**: Sempre rápido
- **Sem limites**: Suporta milhões de linhas

### 8.4 Configuração

```javascript
// Em virtual-table.js
this.visibleRows = 100;    // Quantas linhas visíveis
this.bufferRows = 100;     // Buffer para scroll suave
this.rowHeight = 30;       // Altura de cada linha em pixels
```

---

## 9. Configuração e Deploy

### 9.1 Variáveis de Ambiente (.env)

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

# Redis (opcional em v3.4)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=false  # Desabilitado temporariamente

# API
API_PORT=3500
API_TIMEOUT=300
CACHE_ENABLED=false  # Desabilitado em v3.4
CACHE_TTL=300

# Performance
MAX_POOL_SIZE=20
WORK_MEM=256MB
MAX_ROWS_WITHOUT_WARNING=250000

# Development
DEBUG=false
LOG_LEVEL=INFO
```

### 9.2 Instalação

```bash
cd ~/metabase_customizacoes
source venv/bin/activate
pip install -r requirements.txt
```

### 9.3 Scripts de Gestão

```bash
./scripts/start.sh   # Inicia servidor
./scripts/stop.sh    # Para servidor
./scripts/status.sh  # Verifica status
```

---

## 10. Otimizações e Performance

### 10.1 Backend
- Pool de 20 conexões persistentes
- work_mem: 256MB para queries grandes
- Statement timeout: 300s
- Formato colunar mantido

### 10.2 Frontend - Tabela (v3.4)
- **Virtualização real**: Apenas ~300 linhas no DOM
- **Throttle de scroll**: Máximo 60 FPS
- **Zero duplicação**: Dados não são copiados
- **Renderização sob demanda**: HTML gerado durante scroll

### 10.3 Frontend - Gráfico (v3.5)
- **Agregação em lotes**: Processa 1000 linhas por vez
- **Altura fixa**: Previne redimensionamento infinito
- **Animação otimizada**: Desabilitada na renderização inicial
- **Debounce de filtros**: 500ms para evitar múltiplas atualizações

### 10.4 Métricas de Performance

#### Tabela Virtual
| Volume | Memória Usada | Tempo Renderização | FPS Scroll |
|--------|---------------|-------------------|------------|
| 10k | ~50MB | < 0.1s | 60 |
| 100k | ~150MB | < 0.1s | 60 |
| 653k | ~300MB | < 0.1s | 60 |
| 1M+ | ~300MB | < 0.1s | 60 |

#### Gráfico Combinado
| Volume | Tempo API | Tempo Agregação | Tempo Total |
|--------|-----------|-----------------|-------------|
| 10k | ~200ms | ~50ms | < 0.5s |
| 100k | ~400ms | ~200ms | < 1s |
| 600k | ~650ms | ~500ms | < 1.5s |

---

## 11. Troubleshooting

### 11.1 Tabela Some Após Carregar (v3.4)

**Sintomas**: Dados aparecem e depois mostram "Nenhum dado encontrado"

**Solução**:
1. Execute no console:
```javascript
filterManager.stopMonitoring()
app.debugFilters()
app.loadDataNoFilters()
```

2. Se persistir, verifique:
- Cache está desabilitado no `.env`
- Logs do Flask para erros na query
- Network tab para respostas vazias

### 11.2 Erro de Memória

**Sintomas**: "Out of Memory" no navegador

**Verificações**:
1. Confirme que está usando a v3.4 com virtualização
2. Execute `app.getStats()` e verifique "Linhas no DOM"
3. Deve mostrar ~300, não 653k

### 11.3 Scroll Travando

**Solução**:
- Ajuste `bufferRows` para valor maior (150-200)
- Verifique se CSS de virtualização foi aplicado
- Confirme que `rowHeight` corresponde ao CSS real

### 11.4 Filtros Não Funcionam

**Debug**:
```javascript
app.debugFilters()  // Mostra estado atual
// Verifique se "changed: true" aparece quando muda filtros
```

### 11.5 Gráfico Crescendo Verticalmente (v3.5)

**Sintomas**: Gráfico aumenta de altura infinitamente

**Solução**:
```javascript
// Força altura fixa
chartApp.fixHeight()

// Para monitoramento temporariamente
chartApp.stopMonitoring()
```

### 11.6 Gráfico Demora para Carregar (v3.5)

**Diagnóstico**:
```javascript
// Recarrega com medição de tempo
chartApp.refresh()
// Observe: API time, Transform time, Chart time
```

**Se a agregação estiver lenta**:
- Considere limitar o período de dados
- Adicione filtro de data padrão (últimos 12 meses)

---

## 12. Guia de Desenvolvimento

### 12.1 Adicionar Novo Componente

1. Copie estrutura de `tabela_virtual` ou `grafico_combo`
2. Use recursos compartilhados
3. Implemente virtualização se necessário
4. Adicione comandos de debug
5. Documente no README específico

### 12.2 Modificar Virtualização

```javascript
// Ajustar número de linhas visíveis
this.visibleRows = 200;  // Mais linhas
this.bufferRows = 150;   // Mais buffer

// Mudar altura das linhas
this.rowHeight = 40;     // Linhas mais altas
```

### 12.3 Modificar Agregação do Gráfico

```javascript
// Em data-transformer.js
// Ajustar tamanho do lote
const batchSize = 5000;  // Lotes maiores

// Mudar agregação (ex: por semana)
const weekNumber = getWeekNumber(date);
const weekKey = `${year}-W${weekNumber}`;
```

### 12.4 Debug em Produção

```javascript
// Comandos úteis no console

// TABELA
app.getStats()           // Estatísticas completas
app.showMemoryStats()    // Uso de memória
app.debugFilters()       // Estado dos filtros
app.loadDataNoFilters()  // Carrega sem filtros

// GRÁFICO
chartApp.getStats()      // Estatísticas do gráfico
chartApp.refresh()       // Recarrega com timing
chartApp.fixHeight()     // Força altura fixa
chartApp.debugData()     // Debug detalhado

// AMBOS
filterManager.stopMonitoring()    // Para monitoramento
filterManager.currentFilters      // Filtros ativos
```

---

## 13. Comandos de Debug (v3.5)

### 13.1 Comandos da Tabela Virtual

```javascript
// Informações do sistema
app.getStats()          // Estatísticas completas
app.showMemoryStats()   // Detalhes de memória

// Debug de filtros
app.debugFilters()      // Estado atual dos filtros
filterManager.currentFilters  // Filtros ativos
filterManager.stopMonitoring() // Para monitoramento

// Controle manual
app.loadData("manual")  // Recarrega dados
app.loadDataNoFilters() // Carrega sem filtros
app.clearCaches()       // Limpa caches

// Exportação
app.exportData()        // Exporta CSV
```

### 13.2 Comandos do Gráfico Combinado

```javascript
// Informações do sistema
chartApp.getStats()     // Estatísticas do gráfico
chartApp.debugData()    // Debug detalhado dos dados

// Controle de filtros
chartApp.getFilters()   // Filtros ativos
chartApp.stopMonitoring()  // Para monitoramento
chartApp.startMonitoring() // Reinicia monitoramento

// Controle manual
chartApp.refresh()      // Recarrega com timing
chartApp.fixHeight()    // Força altura de 450px

// Exportação
chartApp.exportData()   // Exporta CSV dos dados agregados
```

### 13.3 Scripts de Diagnóstico

#### Performance do Gráfico
```javascript
// Diagnóstico completo de performance
console.clear();
chartApp.refresh();
// Observe os tempos de cada etapa no console
```

#### Monitoramento de Redimensionamento
```javascript
// Detecta mudanças de altura
const container = document.getElementById('chart-container');
const observer = new ResizeObserver(entries => {
    for (let entry of entries) {
        console.log('Altura mudou:', entry.contentRect.height);
    }
});
observer.observe(container);
```

### 13.4 Exemplo de Debug Completo

```javascript
// 1. Verificar estado geral
const stats = app.getStats ? app.getStats() : chartApp.getStats();
console.log(stats);

// 2. Se componente sumiu ou está com problema
filterManager.stopMonitoring();
if (app.debugFilters) app.debugFilters();

// 3. Recarregar manualmente
if (app.loadDataNoFilters) {
    app.loadDataNoFilters();
} else {
    chartApp.refresh();
}

// 4. Verificar memória (apenas tabela)
if (app.showMemoryStats) app.showMemoryStats();

// 5. Forçar correções (apenas gráfico)
if (chartApp.fixHeight) chartApp.fixHeight();
```

---

## 14. Changelog

### v3.5.0 (29/07/2025) 📊

#### 🎯 Novo Componente: Gráfico Combinado
- Visualização multi-eixos com Highcharts
- 3 eixos Y independentes (Impressões, Clicks, Investimento)
- Colunas empilhadas por conta + linhas totalizadoras
- Agregação automática por mês/ano
- Exportação em múltiplos formatos

#### ⚡ Otimizações de Performance
- ✅ Agregação em lotes (1000 linhas por vez)
- ✅ Logs de progresso durante processamento
- ✅ Parse otimizado de datas (substring)
- ✅ Desabilita animação na renderização inicial
- ✅ Debounce de 500ms para mudanças de filtros

#### 🐛 Correções Importantes
- ✅ **Corrigido**: Gráfico crescendo verticalmente infinitamente
- ✅ **Corrigido**: Performance lenta com grandes volumes
- ✅ **Corrigido**: Múltiplas renderizações desnecessárias
- ✅ **Corrigido**: Altura não respeitada no container

#### 🔧 Melhorias Técnicas
- Container com altura fixa de 450px
- CSS com overflow hidden
- Comando `fixHeight()` para correção manual
- Medição de tempo por etapa (API, Transform, Chart)
- Modo fullscreen com altura dinâmica

#### 📝 Novos Comandos de Debug
- `chartApp.refresh()`: Recarrega com timing detalhado
- `chartApp.fixHeight()`: Força altura de 450px
- `chartApp.debugData()`: Debug completo dos dados
- `chartApp.startMonitoring()`: Reinicia monitoramento

### v3.4.0 (29/07/2025) 🚀

#### 🎯 Virtualização Real
- Implementada renderização verdadeiramente virtual
- Apenas ~300 linhas no DOM para qualquer volume
- Economia de 99.95% de memória para grandes volumes
- Suporte testado para 653k+ linhas sem problemas

#### 🐛 Correções Críticas
- ✅ **Corrigido**: Tabela sumindo após carregar (cache corrompido)
- ✅ **Corrigido**: Loop infinito de detecção de filtros
- ✅ **Corrigido**: Erro "Out of Memory" com grandes volumes
- ✅ **Corrigido**: Múltiplas requisições simultâneas

#### 🔧 Melhorias Técnicas
- Cache temporariamente desabilitado (estava causando problemas)
- Flag `isFirstCapture` no filter-manager evita detecções falsas
- Flag `isLoading` previne requisições concorrentes
- Validação rigorosa de respostas da API
- Delay de 3s antes de iniciar monitoramento de filtros

#### 📝 Debug e Monitoramento
- Novos comandos de debug no console
- Método `debugFilters()` para diagnóstico
- Método `loadDataNoFilters()` para testes
- Logs detalhados de mudanças de filtros
- Indicador visual de linhas renderizadas

#### ⚡ Performance
- Renderização instantânea (< 0.1s) para qualquer volume
- Scroll suave garantido (60 FPS)
- Throttle agressivo no scroll handler
- Zero duplicação de dados na memória

### v3.3.0 (29/07/2025)

#### 🚀 Filtro de Conversões por Action Type
- Implementado filtro especial para campos JSON
- Suporte a múltipla seleção de action types
- Filtragem baseada em conteúdo de arrays JSONB
- Integração nativa com Field Filter do Metabase

### v3.2.0 (23/07/2025)

#### 🚀 Mapeamento Inteligente de Parâmetros
- Sistema de mapeamento flexível para nomes de filtros
- Busca em duas etapas: nome original → nome mapeado
- Suporte a sinônimos (ex: "anuncio" → "ad_name")

### v3.1.0 (23/07/2025)

#### 🚀 Parser de Datas Dinâmico
- Suporte completo para filtros relativos do Metabase
- Detecção automática de padrões (past/next + número + unidade)
- Cálculo correto de períodos completos
- Flag `~` para incluir período atual

### v3.0.0 (Janeiro 2025)

#### 🚀 Formato Colunar Nativo
- Suporte a 600.000+ linhas sem erro
- 3x menos uso de memória
- Compatível com formato Metabase nativo

#### 🔄 Monitoramento Automático de Filtros
- Detecção em tempo real de mudanças
- Atualização automática da tabela
- Zero configuração necessária

### v2.0.0

- Versão inicial com tabela virtual
- Suporte básico a filtros
- Cache Redis

---

## Sobre Esta Documentação

**Versão**: 3.5.0  
**Última Atualização**: 29 de Julho de 2025  
**Principais Mudanças**: Novo componente de gráfico combinado com otimizações de performance

### Manutenção

Para manter esta documentação atualizada:
1. Documente mudanças significativas no Changelog
2. Atualize exemplos de código quando modificar APIs
3. Adicione novos casos de troubleshooting
4. Mantenha comandos de debug atualizados
5. Registre métricas de performance reais

### Como Atualizar para v3.5

1. **Faça backup** dos arquivos atuais
2. **Adicione** a pasta `componentes/grafico_combo/` com todos os arquivos
3. **Atualize** os arquivos modificados:
   - `main_grafico_combo.js`
   - `data-transformer.js`
   - `chart-builder.js`
   - `grafico.css`
4. **Reinicie** o servidor Flask
5. **Limpe** o cache do navegador
6. **Teste** com grandes volumes de dados

### Estrutura de Componentes

O sistema agora suporta dois tipos de visualização:

1. **Tabela Virtual**: Para dados detalhados com scroll infinito
   - URL: `.../tabela_virtual/?question_id=XX`
   - Ideal para: Análise detalhada, exportação completa

2. **Gráfico Combinado**: Para visualização agregada e tendências
   - URL: `.../grafico_combo/?question_id=XX`
   - Ideal para: Dashboards executivos, análise de tendências

Ambos compartilham os mesmos recursos base e sistema de filtros, garantindo consistência e reusabilidade.

---

**Fim da Documentação Técnica v3.5**
