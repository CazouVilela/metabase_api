# Documentação da API - Metabase Customizações

## Visão Geral

A API do Metabase Customizações fornece endpoints para executar queries do Metabase com filtros dinâmicos, otimizados para performance.

Base URL: `https://seu-dominio.com/metabase_customizacoes/api`

## Autenticação

A API não requer autenticação direta. A segurança é gerenciada através do Metabase e das permissões do banco de dados.

## Endpoints

### 1. Executar Query

Executa uma query do Metabase com filtros aplicados.

**Endpoint:** `GET /query`

**Parâmetros:**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| question_id | integer | Sim | ID da pergunta no Metabase |
| [filtros] | string/array | Não | Filtros dinâmicos (ver seção Filtros) |

**Exemplo de Requisição:**
```
GET /api/query?question_id=51&conta=EMPRESA+LTDA&campanha=Campanha+2024
```

**Resposta (200 OK):**
```json
{
  "data": {
    "cols": [
      {
        "name": "date",
        "base_type": "type/Date",
        "display_name": "Data"
      },
      {
        "name": "account_name",
        "base_type": "type/Text",
        "display_name": "Conta"
      }
    ],
    "rows": [
      ["2024-01-01", "EMPRESA LTDA"],
      ["2024-01-02", "EMPRESA LTDA"]
    ]
  },
  "row_count": 2,
  "running_time": 145,
  "status": "completed"
}
```

**Códigos de Status:**
- `200` - Sucesso
- `400` - Parâmetros inválidos
- `500` - Erro interno do servidor

### 2. Informações da Questão

Obtém metadados sobre uma questão do Metabase.

**Endpoint:** `GET /question/{id}/info`

**Exemplo:**
```
GET /api/question/51/info
```

**Resposta:**
```json
{
  "id": 51,
  "name": "Análise de Campanhas",
  "database_id": 2,
  "dataset_query": {
    "type": "native",
    "native": {
      "query": "SELECT * FROM ...",
      "template-tags": {
        "conta": {
          "type": "text",
          "required": false
        }
      }
    }
  }
}
```

### 3. Debug de Filtros

Útil para diagnosticar problemas com filtros.

**Endpoint:** `GET /debug/filters`

**Exemplo:**
```
GET /api/debug/filters?conta=EMPRESA&campanha[]=Camp1&campanha[]=Camp2
```

**Resposta:**
```json
{
  "captured_filters": {
    "conta": "EMPRESA",
    "campanha": ["Camp1", "Camp2"]
  },
  "debug": {
    "total_filters": 2,
    "multi_value_filters": [
      {
        "name": "campanha",
        "count": 2,
        "values": ["Camp1", "Camp2"]
      }
    ],
    "special_chars": []
  },
  "query_string": "conta=EMPRESA&campanha[]=Camp1&campanha[]=Camp2"
}
```

### 4. Estatísticas do Cache

Mostra informações sobre o cache Redis.

**Endpoint:** `GET /debug/cache/stats`

**Resposta:**
```json
{
  "enabled": true,
  "keys_count": 42,
  "memory_used": "12.5MB",
  "hits": 1524,
  "misses": 238,
  "hit_rate": "86.5%"
}
```

### 5. Health Check

Verifica o status da API.

**Endpoint:** `GET /health`

**Resposta:**
```json
{
  "status": "healthy",
  "cache": {
    "enabled": true,
    "connected": true
  },
  "database": {
    "connected": true
  },
  "metabase": {
    "connected": true
  }
}
```

## Filtros

### Formato de Filtros

Os filtros podem ser passados de várias formas:

#### Valor único:
```
?conta=EMPRESA+LTDA
```

#### Múltiplos valores:
```
?campanha=Camp1&campanha=Camp2&campanha=Camp3
```

#### Range de datas:
```
?data=2024-01-01~2024-01-31
```

### Filtros Suportados

| Filtro | Campo SQL | Tipo | Exemplo |
|--------|-----------|------|---------|
| conta | account_name | string/array | EMPRESA LTDA |
| campanha | campaign_name | string/array | Campanha 2024 |
| adset | adset_name | string/array | AdSet 1 |
| plataforma | publisher_platform | string/array | facebook |
| device | impression_device | string/array | mobile |
| data | date | date/range | 2024-01-01~2024-01-31 |

### Caracteres Especiais

A API suporta todos os caracteres especiais em filtros:
- `+` (mais)
- `&` (ampersand)
- `|` (pipe)
- `%` (percent)
- `#` (hash)
- Etc.

Exemplo:
```
?campanha=Campanha+%2B+Especial+%7C+2024
```

## Formato de Resposta

### Formato Nativo (Colunar)

O formato padrão é otimizado para performance:

```json
{
  "data": {
    "cols": [...],    // Metadados das colunas
    "rows": [...]     // Dados em formato de array
  },
  "row_count": 1000,
  "running_time": 250,
  "from_cache": false
}
```

### Headers de Resposta

- `Content-Type: application/json`
- `Content-Encoding: gzip` (quando comprimido)
- `X-Metabase-Client: native-performance`

## Performance

### Otimizações

1. **Pool de Conexões**: Reutilização de conexões PostgreSQL
2. **Cache Redis**: Resultados são cacheados por 5 minutos
3. **Compressão Gzip**: Respostas grandes são comprimidas
4. **Query Nativa**: Execução direta no PostgreSQL

### Limites

- Timeout de query: 300 segundos
- Tamanho máximo de resposta: Sem limite (usa streaming)
- Número máximo de filtros: Sem limite

## Tratamento de Erros

### Estrutura de Erro

```json
{
  "error": "Mensagem de erro",
  "tipo": "tipo_do_erro",
  "details": {
    "question_id": 51,
    "filters": {...}
  }
}
```

### Tipos de Erro

- `parametro_invalido` - Parâmetros da requisição inválidos
- `question_not_found` - Questão não encontrada
- `query_error` - Erro na execução da query
- `timeout` - Query excedeu o tempo limite
- `erro_interno` - Erro interno do servidor

## Exemplos de Uso

### JavaScript (Frontend)

```javascript
// Usando o cliente compartilhado
const data = await apiClient.queryData(51, {
  conta: 'EMPRESA LTDA',
  campanha: ['Camp1', 'Camp2'],
  data: '2024-01-01~2024-01-31'
});
```

### cURL

```bash
# Query simples
curl "https://seu-dominio.com/metabase_customizacoes/api/query?question_id=51&conta=EMPRESA"

# Múltiplos valores
curl "https://seu-dominio.com/metabase_customizacoes/api/query?question_id=51&campanha=Camp1&campanha=Camp2"

# Com caracteres especiais
curl "https://seu-dominio.com/metabase_customizacoes/api/query?question_id=51&campanha=Camp%20%2B%20Especial"
```

### Python

```python
import requests

response = requests.get(
    'https://seu-dominio.com/metabase_customizacoes/api/query',
    params={
        'question_id': 51,
        'conta': 'EMPRESA LTDA',
        'campanha': ['Camp1', 'Camp2']
    }
)

data = response.json()
```

## Webhooks e Eventos

A API não suporta webhooks atualmente. Para monitorar mudanças, use polling com o cache habilitado.

## Rate Limiting

Não há rate limiting implementado. Recomenda-se usar o cache do lado do cliente para evitar requisições desnecessárias.

## Versionamento

A API não possui versionamento explícito. Mudanças são retrocompatíveis.

## Suporte

Para suporte, abra uma issue no repositório ou entre em contato com a equipe de desenvolvimento.
