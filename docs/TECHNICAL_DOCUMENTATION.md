# Documentação Técnica Completa - Metabase Customizações v3.2

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Estrutura de Arquivos e Módulos](#3-estrutura-de-arquivos-e-módulos)
4. [API Backend (Flask)](#4-api-backend-flask)
5. [Frontend (Componentes)](#5-frontend-componentes)
6. [Fluxos de Dados](#6-fluxos-de-dados)
7. [Sistema de Filtros](#7-sistema-de-filtros)
8. [Configuração e Deploy](#8-configuração-e-deploy)
9. [Otimizações e Performance](#9-otimizações-e-performance)
10. [Troubleshooting](#10-troubleshooting)
11. [Guia de Desenvolvimento](#11-guia-de-desenvolvimento)
12. [Changelog](#12-changelog)

---

## 1. Visão Geral

### 1.1 Propósito
Sistema de customização para Metabase que permite criar componentes interativos (tabelas, gráficos) em iframes dentro de dashboards, capturando filtros aplicados e executando queries otimizadas diretamente no PostgreSQL.

### 1.2 Principais Características
- **Performance Nativa**: Execução direta no PostgreSQL sem overhead do Metabase
- **Cache Inteligente**: Redis com compressão gzip e TTL configurável
- **Filtros Dinâmicos**: Captura automática com suporte a múltiplos valores e caracteres especiais
- **Parser de Datas Avançado**: Suporte completo para filtros relativos dinâmicos (v3.1)
- **Mapeamento Inteligente**: Sistema flexível de mapeamento de parâmetros (v3.2)
- **Virtualização**: Renderização eficiente de grandes volumes de dados (600k+ linhas)
- **Formato Colunar**: Otimização de memória usando formato nativo do Metabase
- **Monitoramento Automático**: Detecção e atualização em tempo real de mudanças de filtros
- **Modular**: Arquitetura de componentes reutilizáveis

### 1.3 Stack Tecnológico
- **Backend**: Flask 3.1.0 (Python 3.8+) + psycopg2
- **Frontend**: JavaScript ES6+ vanilla + ClusterizeJS
- **Cache**: Redis 5.0+
- **Database**: PostgreSQL 12+
- **Proxy**: Nginx
- **Deploy**: Gunicorn + systemd
- **Dependências Python**: python-dateutil (para cálculos de data)

### 1.4 Capacidades de Volume
- **< 250.000 linhas**: Renderização normal instantânea
- **250.000 - 600.000 linhas**: Formato colunar otimizado
- **600.000+ linhas**: Suportado com formato colunar nativo
- **Exportação CSV**: Qualquer volume (processamento em chunks)

---

## 2. Arquitetura do Sistema

### 2.1 Diagrama de Fluxo
```
[Dashboard Metabase]
        ↓ (filtros na URL)
[iframe Componente]
        ↓ (captura filtros via filterManager)
[JavaScript Frontend]
        ↓ (requisição AJAX)
[Nginx :8080]
        ↓ (proxy)
[Flask API :3500]
        ↓ (QueryParser processa filtros e mapeamentos)
        ↓ (extrai e modifica query)
[PostgreSQL :5432]
        ↓ (dados formato colunar)
[Redis :6379] (cache)
        ↓
[Frontend Renderização]
        ↓ (formato colunar ou objetos)
[ClusterizeJS] (virtualização)
```

### 2.2 Componentes Principais

#### Backend
- **API Flask**: Servidor principal que processa requisições
- **Query Service**: Executa queries com pool de conexões
- **Metabase Service**: Comunica com API do Metabase
- **Cache Service**: Gerencia cache Redis
- **Query Parser**: Processa template tags, filtros de data dinâmicos e mapeamentos (v3.2)

#### Frontend
- **Filter Manager**: Captura e monitora filtros automaticamente
- **API Client**: Comunicação com backend (recursos compartilhados)
- **Data Processor**: Processa e formata dados
- **Virtual Table**: Renderiza tabelas com virtualização e formato colunar
- **Export Utils**: Exportação de dados otimizada

---

## 3. Estrutura de Arquivos e Módulos

### 3.1 Estrutura de Diretórios
```
metabase_customizacoes/
├── api/                          # Backend Flask
│   ├── routes/                   # Endpoints
│   ├── services/                 # Lógica de negócio
│   └── utils/                    # Utilitários
│       └── query_parser.py       # Parser de queries, filtros e mapeamentos (v3.2)
├── componentes/                  # Frontend
│   ├── recursos_compartilhados/  # JS/CSS reutilizável
│   │   ├── js/
│   │   │   ├── api-client.js    # Cliente API unificado
│   │   │   ├── filter-manager.js # Gerenciador de filtros
│   │   │   ├── data-processor.js # Processador de dados
│   │   │   └── export-utils.js   # Utilitários de exportação
│   │   └── css/
│   │       └── base.css          # Estilos compartilhados
│   └── tabela_virtual/           # Componente tabela
│       ├── index.html            # HTML principal
│       ├── js/
│       │   ├── main.js           # App principal
│       │   ├── virtual-table.js  # Tabela com formato colunar
│       │   └── utils.js          # Utilitários locais
│       └── css/
│           └── tabela.css        # Estilos específicos
├── config/                       # Configurações
├── nginx/                        # Config Nginx
├── scripts/                      # Scripts de gestão
└── docs/                         # Documentação
```

### 3.2 Arquivos Principais
- `api/server.py`: Servidor Flask principal
- `api/services/query_service.py`: Execução de queries
- `api/utils/query_parser.py`: Parser avançado de queries, filtros e mapeamentos (v3.2)
- `componentes/recursos_compartilhados/js/filter-manager.js`: Monitor automático de filtros
- `componentes/tabela_virtual/js/main.js`: App com formato colunar
- `componentes/tabela_virtual/js/virtual-table.js`: Renderização otimizada
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
- `[filtros]`: Qualquer filtro dinâmico, incluindo filtros de data relativos e nomes mapeados

**Exemplo de filtros de data suportados** (v3.1):
- `data=past7days`: últimos 7 dias (sem incluir hoje)
- `data=past7days~`: últimos 7 dias incluindo hoje
- `data=past8weeks`: 8 semanas completas anteriores
- `data=past8weeks~`: 8 semanas anteriores + semana atual
- `data=next30days`: próximos 30 dias (começando amanhã)
- `data=next30days~`: próximos 30 dias incluindo hoje
- `data=thisday`: hoje (Metabase usa "thisday" em vez de "today")
- `data=2024-01-01~2024-12-31`: intervalo específico

**Exemplo de mapeamentos suportados** (v3.2):
- `anuncio=MeuAd123`: mapeado para `ad_name='MeuAd123'`
- `conta=Empresa`: mapeado para `account_name='Empresa'`

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

**Otimizações para grandes volumes**:
- Mantém formato colunar do PostgreSQL
- Pool de conexões persistente (20 conexões)
- work_mem aumentado para 256MB
- Cache Redis com compressão gzip

### 4.4 Query Parser (`api/utils/query_parser.py`)

**Mapeamento Inteligente de Parâmetros (v3.2)**:

O `QueryParser` agora implementa busca inteligente de template tags:

```python
def apply_filters(self, query: str, filters: Dict[str, Any]) -> str:
    """
    Substitui template tags pelos valores dos filtros
    
    v3.2: Implementa busca em duas etapas:
    1. Tenta encontrar [[AND {{parametro}}]]
    2. Se não encontrar e houver mapeamento, tenta [[AND {{campo_mapeado}}]]
    """
```

**Características**:
- Zero configuração adicional necessária
- Compatibilidade retroativa garantida
- Logs informativos quando usa mapeamento
- Suporte a sinônimos e múltiplas línguas

---

## 5. Frontend (Componentes)

### 5.1 Recursos Compartilhados

#### Filter Manager (`recursos_compartilhados/js/filter-manager.js`)

**Funcionalidades principais**:
- ✅ Detecção automática de mudanças de filtros
- ✅ Suporte a múltiplos valores
- ✅ Normalização de parâmetros
- ✅ Decodificação de caracteres especiais
- ✅ Monitoramento automático com intervalo configurável

```javascript
// Exemplo de uso
filterManager.startMonitoring(1000); // Verifica a cada segundo
filterManager.onChange((filters) => {
    console.log('Filtros mudaram:', filters);
});
```

#### API Client (`recursos_compartilhados/js/api-client.js`)

```javascript
// Exemplo de uso
const apiClient = new MetabaseAPIClient();
const data = await apiClient.queryData(questionId, {
    conta: 'EMPRESA XYZ',
    data: 'past7days~',
    anuncio: 'MeuAnuncio123'  // v3.2: mapeado automaticamente
});
```

### 5.2 Componente Tabela Virtual

#### App Principal (`tabela_virtual/js/main.js`)

**Principais funcionalidades**:
- Usa recursos compartilhados
- Monitoramento automático de filtros
- Suporte a formato colunar nativo
- Exportação CSV otimizada

---

## 6. Fluxos de Dados

### 6.1 Fluxo com Monitoramento Automático e Mapeamento

```
1. Dashboard Metabase
   - Usuário seleciona filtro "anúncio" = "MeuAd123"
   - URL atualiza: ?anuncio=MeuAd123
   
2. FilterManager (monitoramento ativo)
   - Verifica URL a cada 1 segundo
   - Detecta mudança automaticamente
   - Notifica observers
   
3. App.loadData() é chamado
   - Captura filtros atuais
   - Envia para API: anuncio=MeuAd123
   
4. QueryParser processa (v3.2)
   - Busca [[AND {{anuncio}}]] na query (não encontra)
   - Consulta mapeamento: anuncio → ad_name
   - Busca [[AND {{ad_name}}]] na query (encontra!)
   - Substitui template tag: AND ad_name = 'MeuAd123'
   
5. Backend executa query
   - Mantém formato colunar
   - Retorna dados filtrados
   
6. Frontend renderiza
   - Usa formato colunar se disponível
   - 3x menos memória
```

---

## 7. Sistema de Filtros

### 7.1 Parser Dinâmico de Datas (v3.1)

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
| past1quarters | Trimestre anterior completo | Trimestre anterior + trimestre atual |
| past2years | 2 anos completos anteriores | 2 anos anteriores + ano atual |

**FUTURO (next)**:

| Filtro | Sem flag (~) | Com flag (~) |
|--------|--------------|--------------|
| next7days | Próximos 7 dias (começa amanhã) | Hoje + próximos 7 dias |
| next2weeks | 2 semanas começando no próximo domingo | Semana atual + próximas 2 semanas |
| next3months | 3 meses começando no próximo mês | Mês atual + próximos 3 meses |

#### 7.1.3 Casos Especiais

- `thisday`: hoje (Metabase usa este em vez de "today")
- `yesterday`: ontem
- `tomorrow`: amanhã
- `thisweek/month/quarter/year`: período atual completo
- `lastweek/month/quarter/year`: período anterior completo
- `nextweek/month/quarter/year`: próximo período completo
- `alltime`: desde 2000-01-01 até hoje

#### 7.1.4 Exemplos Práticos

Considerando hoje = 23/07/2025 (Quarta):

```
past1days     → 2025-07-22 (apenas ontem)
past1days~    → 2025-07-22 até 2025-07-23 (ontem + hoje)
past7days     → 2025-07-16 até 2025-07-22 (7 dias sem hoje)
past7days~    → 2025-07-17 até 2025-07-23 (7 dias com hoje)

past8weeks    → 2025-05-25 (Dom) até 2025-07-19 (Sáb) - 8 semanas completas
past8weeks~   → 2025-05-25 (Dom) até 2025-07-26 (Sáb) - 8 semanas + atual

next1days     → 2025-07-24 (apenas amanhã)
next1days~    → 2025-07-23 até 2025-07-24 (hoje + amanhã)
next7days     → 2025-07-24 até 2025-07-30 (7 dias começando amanhã)
next7days~    → 2025-07-23 até 2025-07-29 (hoje + próximos 7 dias)
```

### 7.2 Implementação Técnica

O parser usa regex para detectar padrões dinâmicos:

```python
pattern = r'^(past|last|next|previous)(\d+)(day|days|week|weeks|month|months|quarter|quarters|year|years)$'
```

Principais características:
- Usa `datetime` e `timedelta` para dias
- Usa `relativedelta` para meses/anos (mais preciso)
- Semanas começam no domingo (padrão Metabase)
- Trimestres seguem calendário fiscal (Q1=Jan-Mar)

### 7.3 Mapeamento de Parâmetros (v3.2)

O sistema suporta mapeamento automático de parâmetros do dashboard para campos SQL, permitindo flexibilidade nos nomes dos filtros.

#### 7.3.1 Configuração de Mapeamento

O mapeamento é definido em `api/utils/query_parser.py`:

```python
FIELD_MAPPING = {
    'data': 'date',
    'conta': 'account_name',
    'campanha': 'campaign_name',
    'adset': 'adset_name',
    'ad_name': 'ad_name',
    'anuncio': 'ad_name',      # Sinônimo para ad_name
    'plataforma': 'publisher_platform',
    'posicao': 'platform_position',
    'device': 'impression_device',
    'objective': 'objective',
    'optimization_goal': 'optimization_goal',
    'buying_type': 'buying_type',
    'action_type_filter': 'action_type'
}
```

#### 7.3.2 Funcionamento do Mapeamento Inteligente (v3.2)

O parser agora tenta encontrar template tags de duas formas:

1. **Busca direta**: Procura `[[AND {{nome_parametro}}]]`
2. **Busca mapeada**: Se não encontrar, procura `[[AND {{campo_sql_mapeado}}]]`

**Exemplo prático**:
- Dashboard envia: `anuncio=MeuAnuncio123`
- Parser procura: `[[AND {{anuncio}}]]` (não encontra)
- Parser então procura: `[[AND {{ad_name}}]]` (encontra!)
- Aplica filtro: `AND ad_name = 'MeuAnuncio123'`

#### 7.3.3 Casos de Uso

1. **Múltiplos dashboards com nomenclaturas diferentes**:
   - Dashboard A usa filtro "anuncio"
   - Dashboard B usa filtro "ad_name"
   - Ambos funcionam com a mesma query SQL

2. **Migração gradual**:
   - Permite renomear filtros no dashboard sem quebrar queries existentes
   - Suporta período de transição com ambos os nomes

3. **Localização**:
   - Dashboards em português podem usar "anuncio"
   - Dashboards em inglês podem usar "ad_name"

---

## 8. Configuração e Deploy

### 8.1 Variáveis de Ambiente (.env)

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
MAX_ROWS_WITHOUT_WARNING=250000

# Development
DEBUG=false
LOG_LEVEL=INFO
```

### 8.2 Instalação de Dependências

```bash
cd ~/metabase_customizacoes
source venv/bin/activate
pip install -r requirements.txt
pip install python-dateutil  # Necessário para parser de datas v3.1
```

### 8.3 Scripts de Gestão

#### start.sh
```bash
#!/bin/bash
- Verifica .env
- Cria/ativa venv
- pip install -r requirements.txt
- Testa PostgreSQL, Redis e Metabase
- Inicia servidor (dev ou gunicorn)
```

#### stop.sh
```bash
#!/bin/bash
- Para servidor Flask/Gunicorn
- Limpa processos órfãos
```

---

## 9. Otimizações e Performance

### 9.1 Backend

#### Pool de Conexões
- 20 conexões persistentes
- Reuso automático
- Health check antes de usar

#### Query Optimization
```sql
SET search_path TO road, public;
SET work_mem = '256MB';
SET random_page_cost = 1.1;
```

#### Cache Redis
- Compressão gzip (~96% de redução)
- TTL configurável (padrão 5 minutos)
- Chave baseada em hash SHA256

### 9.2 Frontend

#### Formato Colunar
**Economia de memória**:
- Formato objeto: ~1.2GB para 600k linhas
- Formato colunar: ~400MB (3x menos!)

#### Virtualização
- ClusterizeJS com geração progressiva
- HTML criado sob demanda
- Apenas elementos visíveis renderizados

---

## 10. Troubleshooting

### 10.1 Problemas Comuns

#### "Filtro do dashboard não é aplicado no iframe" (v3.2)

**Sintomas**:
- Log mostra: `⚠️ Tag não encontrada na query: nome_do_filtro`
- Dados não são filtrados no iframe, mas funcionam no dashboard nativo

**Causas possíveis**:
1. Nome do filtro no dashboard não corresponde ao template tag na query
2. Falta mapeamento para o nome usado

**Solução v3.2**:
1. Verificar o nome exato do template tag na query SQL
2. Adicionar mapeamento em `FIELD_MAPPING` se necessário:
   ```python
   'nome_usado_no_dashboard': 'nome_do_campo_sql'
   ```
3. Reiniciar o servidor Flask

**Exemplo de debug**:
```
# Log antes do fix:
⚠️ Tag não encontrada na query: anuncio

# Log após adicionar mapeamento:
🔄 Usando mapeamento: anuncio → ad_name
✅ Substituído: anuncio -> ad_name = 'MeuAnuncio123'...
```

#### "Filtro de data retorna 0 linhas"
**Causas possíveis**:
1. Template tag mal configurado no Metabase
2. Formato de data não reconhecido

**Solução**:
- Verificar se o template tag está como `[[AND {{data}}]]`
- Verificar logs do parser para ver datas calculadas
- Testar com filtros simples primeiro (today, yesterday)

#### "Diferença de linhas entre Metabase e iframe"
**Causa**: Cálculo diferente de períodos

**Solução v3.1**:
- O parser agora calcula períodos idênticos ao Metabase
- Semanas começam no domingo
- Flag `~` inclui período atual completo

#### "Erro 500 com filtros de data"
**Causa**: Parser não reconheceu formato

**Logs úteis**:
```
📅 Filtro dinâmico detectado: past 8 weeks
📊 Datas calculadas: 2025-05-25 (Dom) até 2025-07-19 (Sáb)
→ 8 semanas completas (56 dias)
```

### 10.2 Comandos de Debug

```javascript
// Console do navegador

// Ver filtros atuais
filterManager.currentFilters

// Ver estatísticas
app.getStats()

// Testar parser de data manualmente
// No servidor Flask, verificar logs ao aplicar filtros
```

---

## 11. Guia de Desenvolvimento

### 11.1 Adicionar Suporte a Novo Filtro de Data

1. **Verificar se já é suportado**:
   - O parser suporta qualquer combinação de número + unidade
   - Ex: past365days, next52weeks funcionam automaticamente

2. **Adicionar caso especial** (se necessário):
   ```python
   # Em query_parser.py, adicionar em special_cases
   'myfiltername': lambda: (start_date, end_date)
   ```

3. **Testar**:
   ```bash
   # Aplicar filtro no dashboard
   # Verificar logs do servidor para datas calculadas
   ```

### 11.2 Adicionar Suporte a Novo Nome de Filtro (v3.2)

Se um filtro do dashboard não está sendo aplicado:

1. **Identificar o problema**:
   ```
   # No log do Flask:
   ⚠️ Tag não encontrada na query: novo_filtro
   ```

2. **Verificar o template tag na query SQL**:
   ```sql
   [[AND {{nome_campo_sql}}]]
   ```

3. **Adicionar mapeamento**:
   ```python
   # Em api/utils/query_parser.py
   FIELD_MAPPING = {
       # ... outros mapeamentos ...
       'novo_filtro': 'nome_campo_sql',  # Adicionar esta linha
   }
   ```

4. **Testar**:
   - Reiniciar servidor
   - Aplicar filtro no dashboard
   - Verificar log: `🔄 Usando mapeamento: novo_filtro → nome_campo_sql`

### 11.3 Melhores Práticas

1. **Performance**:
   - Sempre preferir formato colunar para > 100k linhas
   - Usar cache Redis para queries pesadas
   - Aplicar filtros para reduzir volume

2. **Filtros de Data**:
   - Sempre testar com e sem flag `~`
   - Verificar logs para confirmar datas
   - Considerar timezone (servidor usa hora local)

3. **Mapeamentos** (v3.2):
   - Mantenha nomes descritivos
   - Documente sinônimos
   - Considere retrocompatibilidade

4. **Debug**:
   - Ativar DEBUG=true no .env para logs detalhados
   - Usar ferramentas do navegador para monitorar memória
   - Verificar Network tab para ver tamanho das respostas

### 11.4 Melhores Práticas para Mapeamentos (v3.2)

1. **Mantenha nomes descritivos**:
   ```python
   'conta': 'account_name',        # ✅ Claro e intuitivo
   'c': 'account_name',            # ❌ Muito abreviado
   ```

2. **Documente sinônimos**:
   ```python
   'ad_name': 'ad_name',          # Nome original em inglês
   'anuncio': 'ad_name',          # Sinônimo em português
   'advertisement': 'ad_name',     # Variação em inglês
   ```

3. **Considere retrocompatibilidade**:
   - Sempre mantenha mapeamentos antigos
   - Adicione novos sem remover existentes
   - Teste com dashboards existentes

---

## 12. Changelog

### v3.2.0 (23/07/2025)

#### 🚀 Mapeamento Inteligente de Parâmetros
- Sistema de mapeamento flexível para nomes de filtros
- Busca em duas etapas: nome original → nome mapeado
- Suporte a sinônimos (ex: "anuncio" → "ad_name")
- Permite múltiplos dashboards com nomenclaturas diferentes

#### 🐛 Correções
- ✅ Corrigido filtro "anuncio" não sendo aplicado no iframe
- ✅ Melhorado sistema de detecção de template tags
- ✅ Adicionados logs para debug de mapeamentos

#### 📝 Melhorias
- Logs mostram quando mapeamento é utilizado
- Documentação de troubleshooting atualizada
- Exemplos práticos de uso de mapeamentos

#### 🔧 Mudanças Técnicas
- Modificado `QueryParser.apply_filters()` para busca inteligente
- Adicionado suporte a sinônimos em `FIELD_MAPPING`
- Melhorada detecção de template tags na query

### v3.1.0 (23/07/2025)

#### 🚀 Parser de Datas Dinâmico
- Suporte completo para filtros relativos do Metabase
- Detecção automática de padrões (past/next + número + unidade)
- Cálculo correto de períodos completos
- Flag `~` para incluir período atual
- Compatibilidade total com comportamento do Metabase

#### 🐛 Correções
- ✅ Corrigido erro 500 com filtros relativos (past7weeks)
- ✅ Corrigido cálculo de semanas (domingo a sábado)
- ✅ Corrigido diferença de contagem de linhas
- ✅ Corrigido suporte para "thisday" (Metabase usa em vez de "today")
- ✅ Corrigido comportamento de filtros futuros com flag

#### 📝 Melhorias
- Logs detalhados mostrando datas calculadas e dias da semana
- Mensagens específicas por tipo de período
- Documentação completa do sistema de filtros

### v3.0.0 (Janeiro 2025)

#### 🚀 Formato Colunar Nativo
- Suporte a 600.000+ linhas sem erro
- 3x menos uso de memória
- Compatível com formato Metabase nativo

#### 🔄 Monitoramento Automático de Filtros
- Detecção em tempo real de mudanças
- Atualização automática da tabela
- Zero configuração necessária

#### 📦 Recursos Compartilhados
- Código unificado entre componentes
- Manutenção centralizada
- Redução de duplicação

### v2.0.0

- Versão inicial com tabela virtual
- Suporte básico a filtros
- Cache Redis

---

## Resumo das Mudanças v3.2

**Problema Resolvido**: Filtros do dashboard com nomes diferentes dos template tags SQL não eram aplicados.

**Solução Implementada**: Sistema de mapeamento inteligente que tenta encontrar template tags tanto com o nome original do parâmetro quanto com o nome mapeado.

**Impacto**: 
- Zero breaking changes
- Suporte a múltiplas nomenclaturas
- Facilita internacionalização
- Melhora flexibilidade do sistema

**Arquivos Modificados**:
- `api/utils/query_parser.py`: Adicionado mapeamento e lógica de busca inteligente
- `docs/TECHNICAL_DOCUMENTATION.md`: Documentação atualizada

---

## Sobre Esta Documentação

**Versão**: 3.2.0  
**Última Atualização**: 23 de Julho de 2025  
**Principais Mudanças**: Sistema de mapeamento inteligente de parâmetros, correção de filtros não aplicados

### Manutenção

Para manter esta documentação atualizada:
1. Documente mudanças significativas na seção Changelog
2. Atualize exemplos de código quando modificar APIs
3. Adicione novos casos de troubleshooting descobertos
4. Mantenha a seção de filtros de data atualizada com novos padrões
5. Adicione novos mapeamentos conforme necessário

---

**Fim da Documentação Técnica v3.2**
