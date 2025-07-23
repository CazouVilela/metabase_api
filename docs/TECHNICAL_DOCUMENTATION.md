# Documentação Técnica Completa - Metabase Customizações v3.0

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
11. [Changelog v3.0](#11-changelog-v30)

---

## 1. Visão Geral

### 1.1 Propósito
Sistema de customização para Metabase que permite criar componentes interativos (tabelas, gráficos) em iframes dentro de dashboards, capturando filtros aplicados e executando queries otimizadas diretamente no PostgreSQL.

### 1.2 Principais Características
- **Performance Nativa**: Execução direta no PostgreSQL sem overhead do Metabase
- **Cache Inteligente**: Redis com compressão gzip e TTL configurável
- **Filtros Dinâmicos**: Captura automática com suporte a múltiplos valores e caracteres especiais
- **Virtualização**: Renderização eficiente de grandes volumes de dados (600k+ linhas)
- **Formato Colunar**: Otimização de memória usando formato nativo do Metabase (v3.0)
- **Monitoramento Automático**: Detecção e atualização em tempo real de mudanças de filtros (v3.0)
- **Modular**: Arquitetura de componentes reutilizáveis

### 1.3 Stack Tecnológico
- **Backend**: Flask 3.1.0 (Python 3.8+) + psycopg2
- **Frontend**: JavaScript ES6+ vanilla + ClusterizeJS
- **Cache**: Redis 5.0+
- **Database**: PostgreSQL 12+
- **Proxy**: Nginx
- **Deploy**: Gunicorn + systemd

### 1.4 Capacidades de Volume (v3.0)
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
        ↓ (extrai query)
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
- **Filter Processor**: Processa e normaliza filtros
- **Query Parser**: Manipula SQL e template tags

#### Frontend (v3.0)
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
├── componentes/                  # Frontend
│   ├── recursos_compartilhados/  # JS/CSS reutilizável (v3.0)
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
│       │   ├── main.js           # App principal (v3.0)
│       │   ├── virtual-table.js  # Tabela com formato colunar
│       │   └── utils.js          # Utilitários locais
│       └── css/
│           └── tabela.css        # Estilos específicos
├── config/                       # Configurações
├── nginx/                        # Config Nginx
├── scripts/                      # Scripts de gestão
└── docs/                         # Documentação
```

### 3.2 Arquivos Principais (v3.0)
- `api/server.py`: Servidor Flask principal
- `api/services/query_service.py`: Execução de queries
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
- `[filtros]`: Qualquer filtro dinâmico

**Resposta** (v3.0 - Formato Colunar):
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

**Fluxo interno**:
1. FilterProcessor captura filtros
2. QueryService.execute_query()
3. Retorna dados em formato colunar (não converte para objetos)
4. Response comprimida com gzip

### 4.3 Query Service (`api/services/query_service.py`)

**Otimizações para grandes volumes** (v3.0):
- Mantém formato colunar do PostgreSQL
- Não cria objetos desnecessários
- work_mem aumentado para 256MB
- Processamento direto de tipos

---

## 5. Frontend (Componentes)

### 5.1 Recursos Compartilhados (v3.0)

#### Filter Manager (`recursos_compartilhados/js/filter-manager.js`)

**Novo recurso principal**: Monitoramento automático de mudanças

```javascript
class FilterManager {
    captureFromParent() {
        // Captura filtros da URL do dashboard parent
    }
    
    startMonitoring(interval = 1000) {
        // Monitora mudanças automaticamente
        // Notifica observers quando detecta mudança
    }
    
    onChange(callback) {
        // Registra callback para mudanças
    }
}
```

**Funcionalidades**:
- ✅ Detecção automática de mudanças de filtros
- ✅ Suporte a múltiplos valores
- ✅ Normalização de parâmetros
- ✅ Decodificação de caracteres especiais

#### API Client (`recursos_compartilhados/js/api-client.js`)

```javascript
class MetabaseAPIClient {
    async queryData(questionId, filters) {
        // Retorna dados em formato colunar
        // Cache local automático
        // Timeout de 5 minutos
    }
}
```

#### Data Processor (`recursos_compartilhados/js/data-processor.js`)

```javascript
class DataProcessor {
    processNativeResponse(nativeData) {
        // Converte formato colunar → objetos
        // Usado apenas quando necessário
    }
}
```

### 5.2 Componente Tabela Virtual (v3.0)

#### Estrutura HTML (`tabela_virtual/index.html`)
```html
<!-- Scripts compartilhados obrigatórios -->
<script src="../recursos_compartilhados/js/api-client.js"></script>
<script src="../recursos_compartilhados/js/filter-manager.js"></script>
<script src="../recursos_compartilhados/js/data-processor.js"></script>
<script src="../recursos_compartilhados/js/export-utils.js"></script>

<!-- Scripts locais -->
<script src="js/utils.js"></script>
<script src="js/virtual-table.js"></script>
<script src="js/main.js"></script>
```

#### App Principal (`tabela_virtual/js/main.js`)

**Principais mudanças v3.0**:

```javascript
class App {
    async init() {
        // Usa recursos compartilhados
        this.apiClient = new MetabaseAPIClient();
        
        // Inicia monitoramento automático
        filterManager.startMonitoring(1000);
        
        // Registra callback para mudanças
        filterManager.onChange(() => {
            this.loadData('mudança de filtros');
        });
    }
    
    async loadData() {
        // Detecta formato colunar automaticamente
        if (response.data && response.data.rows && response.data.cols) {
            // Usa formato colunar otimizado
            this.virtualTable.renderNative(response);
        } else {
            // Fallback para formato de objetos
            this.virtualTable.render(dados);
        }
    }
}
```

#### Virtual Table (`tabela_virtual/js/virtual-table.js`)

**Nova funcionalidade principal**: Suporte a formato colunar

```javascript
class VirtualTable {
    renderNative(response) {
        // Mantém formato colunar (arrays)
        // 3x menos memória que objetos
        // Suporta 600k+ linhas
    }
    
    renderWithClusterizeColumnar() {
        // Gera HTML progressivamente
        // Batches de 10k linhas
        // Não trava o navegador
    }
    
    exportToCsvColumnar() {
        // Exporta em chunks de 50k
        // Mostra progresso
        // Formata valores corretamente
    }
}
```

---

## 6. Fluxos de Dados

### 6.1 Fluxo com Monitoramento Automático (v3.0)

```
1. Dashboard Metabase
   - Usuário muda filtro
   - URL atualiza: ?conta=EMPRESA&data=2024-01-01
   
2. FilterManager (monitoramento ativo)
   - Verifica URL a cada 1 segundo
   - Detecta mudança automaticamente
   - Notifica observers
   
3. App.loadData() é chamado
   - Captura filtros atuais
   - Envia requisição
   
4. Backend processa
   - Mantém formato colunar
   - Não converte para objetos
   
5. Frontend renderiza
   - Usa formato colunar se disponível
   - 3x menos memória
   - Suporta 600k+ linhas
```

### 6.2 Otimizações para Grandes Volumes (v3.0)

```
Volume < 250k linhas:
- Renderização normal
- Conversão para objetos OK

Volume 250k-600k linhas:
- Formato colunar obrigatório
- Renderização progressiva
- Geração de HTML em batches

Volume > 600k linhas:
- Formato colunar
- Pode requerer mais memória
- Exportação sempre funciona
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

# Performance (v3.0)
MAX_POOL_SIZE=20
WORK_MEM=256MB
MAX_ROWS_WITHOUT_WARNING=250000

# Development
DEBUG=false
LOG_LEVEL=INFO
```

### 7.2 Scripts de Gestão

#### start.sh
```bash
#!/bin/bash
- Verifica .env
- Cria/ativa venv
- pip install -r requirements.txt
- Testa PostgreSQL e Metabase
- Inicia servidor (dev ou gunicorn)
```

---

## 8. Otimizações e Performance

### 8.1 Backend

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

### 8.2 Frontend (v3.0)

#### Formato Colunar
**Antes (objetos)**:
```javascript
// 600k objetos × 39 propriedades = 23M propriedades
// ~1.2GB de memória
[
  {col1: "val", col2: "val", ...col39: "val"},
  // ... 600k objetos
]
```

**Depois (arrays)**:
```javascript
// 600k arrays simples
// ~400MB de memória (3x menos!)
{
  cols: [{name: "col1"}, ...],
  rows: [
    ["val", "val", ..."val"],
    // ... 600k arrays
  ]
}
```

#### Virtualização Otimizada
- ClusterizeJS com geração progressiva
- HTML criado sob demanda
- Apenas elementos visíveis renderizados

### 8.3 Monitoramento de Filtros (v3.0)

#### Implementação Eficiente
- Intervalo adaptativo (1s → 5s)
- Comparação por string JSON
- Observers assíncronos
- Zero polling quando não há mudanças

---

## 9. Troubleshooting

### 9.1 Problemas Comuns

#### "Out of Memory" com grandes volumes
**Solução v3.0**: O formato colunar resolve até ~600k linhas

1. Verificar no console:
```javascript
app.virtualTable.getStats() // Mostra formato em uso
```

2. Se ainda der erro:
- Aplicar filtros para reduzir volume
- Aumentar memória do Chrome: `--max-old-space-size=4096`
- Usar exportação CSV

#### "Filtros não atualizam automaticamente"
**Verificar**:
```javascript
// No console do iframe
filterManager.monitoringInterval // Deve mostrar número
filterManager.currentFilters     // Filtros atuais
```

**Solução**:
```javascript
// Reiniciar monitoramento
filterManager.stopMonitoring();
filterManager.startMonitoring(500); // Verifica a cada 500ms
```

### 9.2 Comandos de Debug (v3.0)

```javascript
// Console do navegador

// Estatísticas completas
app.getStats()

// Verificar formato de dados
app.virtualTable.isColumnarFormat // true = otimizado

// Monitoramento de filtros
filterManager.getDebugInfo()

// Forçar recarga
app.loadData('debug manual')

// Limpar cache
app.apiClient.clearCache()
```

---

## 10. Guia de Desenvolvimento

### 10.1 Adicionar Novo Componente

1. **Criar estrutura**:
```bash
mkdir -p componentes/meu_grafico/{js,css}
cp componentes/tabela_virtual/index.html componentes/meu_grafico/
```

2. **Modificar index.html**:
```html
<!-- Sempre incluir recursos compartilhados -->
<script src="../recursos_compartilhados/js/api-client.js"></script>
<script src="../recursos_compartilhados/js/filter-manager.js"></script>
```

3. **JavaScript principal**:
```javascript
class MeuGrafico {
    async init() {
        // Usar recursos compartilhados
        this.apiClient = new MetabaseAPIClient();
        
        // Monitoramento automático
        filterManager.startMonitoring(1000);
        filterManager.onChange(() => this.updateChart());
    }
}
```

### 10.2 Trabalhar com Grandes Volumes

```javascript
// Sempre verificar formato disponível
if (response.data && response.data.cols) {
    // Usar formato colunar
    this.processColumnarData(response.data);
} else {
    // Fallback para objetos
    this.processObjectData(data);
}
```

### 10.3 Melhores Práticas (v3.0)

1. **Performance**:
   - Sempre preferir formato colunar para > 100k linhas
   - Usar recursos compartilhados (não duplicar código)
   - Implementar exportação em chunks

2. **Memória**:
   - Evitar conversão desnecessária de dados
   - Usar virtualização para grandes volumes
   - Limpar referências quando não usadas

3. **UX**:
   - Mostrar progresso para operações longas
   - Feedback claro sobre volume de dados
   - Exportação sempre disponível

---

## 11. Changelog v3.0

### Novidades Principais

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

#### ⚡ Otimizações de Performance
- Renderização progressiva para grandes volumes
- Exportação otimizada em chunks
- Geração de HTML sob demanda

### Correções

- ✅ Corrigido erro "Out of Memory" para grandes volumes
- ✅ Corrigido monitoramento de filtros não funcionando
- ✅ Corrigido erro do ClusterizeJS ao destruir com muitos dados
- ✅ Melhorada decodificação de caracteres especiais

### Breaking Changes

- `filtros.js` removido em favor de `filter-manager.js`
- `data-loader.js` substituído por `api-client.js`
- Formato de resposta agora mantém estrutura colunar

### Migração de v2.0 para v3.0

1. Atualizar `index.html` para incluir recursos compartilhados
2. Substituir `filtrosManager` por `filterManager` no código
3. Adaptar para usar `renderNative()` com dados colunares
4. Remover arquivos duplicados (`filtros.js`, `data-loader.js`)

---

## Sobre Esta Documentação

**Versão**: 3.0.0  
**Última Atualização**: Janeiro 2025  
**Principais Mudanças**: Formato colunar, monitoramento automático, recursos compartilhados

### Contribuindo

Para manter esta documentação atualizada:
1. Documente mudanças significativas na seção Changelog
2. Atualize exemplos de código quando modificar APIs
3. Adicione novos troubleshooting descobertos
4. Mantenha o índice sincronizado

---

**Fim da Documentação Técnica v3.0**
