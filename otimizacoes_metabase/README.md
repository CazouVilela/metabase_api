# OTIMIZAÇÕES METABASE - DOCUMENTAÇÃO COMPLETA

**Data:** 01/11/2025
**Sistema:** Fedora 43 - 125GB RAM, 16 cores, 7.3TB SSD
**Versão Metabase:** Latest (atualizada periodicamente)

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Cenário de Uso](#cenário-de-uso)
3. [Configurações Aplicadas](#configurações-aplicadas)
4. [Explicação Detalhada](#explicação-detalhada)
5. [Comparativo ANTES/DEPOIS](#comparativo-antesdepois)
6. [Como Reaplicar](#como-reaplicar)
7. [Verificação](#verificação)

---

## 🎯 VISÃO GERAL

Este documento descreve as otimizações aplicadas ao Metabase para suportar:
- **Queries muito pesadas** com milhões de linhas e múltiplas colunas
- **Poucos usuários simultâneos** (máximo 10)
- **Acesso esporádico** (1-2x por dia)
- **Prioridade:** Performance de queries > Concorrência

**Objetivo:** Maximizar a capacidade de processar queries grandes e complexas, aproveitando os recursos abundantes do servidor.

---

## 👥 CENÁRIO DE USO

**Características:**
- Máximo 10 usuários simultâneos
- Acesso esporádico (não contínuo)
- Queries pesadas: 5-20 milhões de linhas
- Múltiplas colunas por query (30-100 colunas)
- Dashboards com muitos gráficos (10-20 por página)

**Recursos Disponíveis:**
- 125GB RAM total
- 16 cores CPU
- 7.3TB SSD NVMe
- PostgreSQL 17 dedicado (servidor nativo)

---

## ⚙️ CONFIGURAÇÕES APLICADAS

### 1. JVM HEAP

```yaml
JAVA_OPTS: "-Xms8G -Xmx24G -XX:+UseG1GC -XX:MaxGCPauseMillis=500 -XX:+UseStringDeduplication -XX:ParallelGCThreads=10"
```

**Parâmetros:**
- `Xms8G`: Heap inicial (piso)
- `Xmx24G`: Heap máximo (teto)
- `UseG1GC`: Garbage Collector G1 (otimizado para heaps grandes)
- `MaxGCPauseMillis=500`: Pausas de GC até 500ms
- `UseStringDeduplication`: Economiza memória com strings duplicadas
- `ParallelGCThreads=10`: 10 threads para GC (alinhado com CPUs Docker)

**Decisão:**
- Piso baixo (8GB): Economiza ~4GB quando ocioso vs teto
- Teto alto (24GB): Suporta queries muito pesadas
- Trade-off: JVM NUNCA devolve memória ao OS após alocar

### 2. QUERY LIMITS

```yaml
MB_UNAGGREGATED_QUERY_ROW_LIMIT: "20000000"  # 20 milhões
MB_QUERY_TIMEOUT_SECONDS: "1800"             # 30 minutos
```

**Decisão:**
- 20M linhas: Suporta queries muito grandes
- 30 minutos: Tempo suficiente para queries complexas

### 3. CACHE

```yaml
MB_QUERY_CACHING_ENABLED: "true"
MB_QUERY_CACHING_TTL_RATIO: "100"
```

**Decisão:**
- Cache ativado: Reduz carga no PostgreSQL
- TTL alto: Dados não mudam frequentemente

### 4. JETTY (WEB SERVER)

```yaml
MB_JETTY_THREADS: "100"
MB_JETTY_MAX_QUEUED_REQUESTS: "2000"
```

**Decisão:**
- 100 threads: Suficiente para 10 usuários × 10 gráficos
- Queue 2000: Grande margem de segurança

### 5. DATABASE CONNECTION POOL

```yaml
MB_APPLICATION_DB_MAX_CONNECTION_POOL_SIZE: "50"
```

**Decisão:**
- 50 conexões: 10 usuários × 10 gráficos = 100 queries simultâneas
- Com reutilização de conexões: 50 conexões atendem bem
- PostgreSQL configurado para max_connections=150

### 6. RECURSOS DOCKER

```yaml
mem_limit: 64g          # Limite máximo
mem_reservation: 16g    # Proteção sob pressão
cpus: '10.0'            # 10 cores
```

**Decisão:**
- 64GB limite: JVM 24GB + overhead 8GB + margem generosa 32GB
- 16GB reservation: Garante recursos mínimos sob pressão de memória
- 10 CPUs: Balanceado (PostgreSQL usa os outros 6 cores dinamicamente)

---

## 📊 EXPLICAÇÃO DETALHADA

### Por que Xms8G e não Xms2G?

**Problema com Xms baixo:**
```
Startup: JVM aloca apenas 2GB
Primeira query pesada (15GB necessários):
  → JVM expande: 2GB → 4GB → 8GB → 15GB
  → Cada expansão = Full GC (pausa 1-5 segundos)
  → Usuário vê: Lentidão de 5-10s extras
```

**Com Xms8G:**
```
Startup: JVM aloca 8GB
Primeira query pesada:
  → JVM expande: 8GB → 15GB (UMA expansão)
  → Full GC: 1 pausa de ~500ms
  → Usuário vê: Query mais rápida
```

**Trade-off escolhido:**
- Economiza 4GB quando ocioso (vs Xms12G)
- Ainda evita múltiplas expansões
- Compromisso: Performance + Economia

### Por que mem_limit 64GB e não 48GB?

**Cálculo conservador:** 24GB + 8GB + 16GB = 48GB
**Escolhido:** 64GB

**Razões:**
1. Sistema tem 125GB RAM (64GB é apenas 51%)
2. Queries podem ter picos acima do esperado
3. JVM pode usar mais memória off-heap (direct buffers, metaspace)
4. Margem de segurança evita OOM (Out of Memory) kills

**Comportamento:**
- Container usa memória **sob demanda** (não reserva 64GB)
- Limite é proteção, não alocação
- Sistema continua com ~60GB+ livres quando Metabase ocioso

### Por que 10 CPUs e não 16?

**Compartilhamento de recursos:**
- PostgreSQL é NATIVO (não Docker): usa cores diretamente
- Metabase Docker: 10 cores
- PostgreSQL: Acessa todos os 16 cores (sem limitação)
- Sistema: Tem cores livres para outras operações

**Cenário real:**
```
Query pesada simultânea:
  • Metabase: Usa até 10 cores (processamento JVM)
  • PostgreSQL: Usa cores disponíveis (até 16)
  • Sistema: Balanceia automaticamente
  • Resultado: Ambos têm recursos suficientes
```

### Por que 50 conexões no pool?

**Cálculo:**
```
10 usuários × 10 gráficos = 100 queries simultâneas potenciais
```

**Mas:**
- Conexões são **reutilizadas** (não 1:1 com queries)
- Nem todos os gráficos carregam exatamente ao mesmo tempo
- Pool de 50 com reutilização rápida atende 100+ queries

**PostgreSQL configurado para:**
- max_connections = 150
- Metabase: 50 conexões
- Airbyte: ~20 conexões
- Outras apps: ~80 conexões
- Total: Balanceado

---

## 📈 COMPARATIVO ANTES/DEPOIS

| Configuração               | ANTES        | DEPOIS       | Mudança |
|----------------------------|--------------|--------------|---------|
| JVM Heap Mínimo            | 4 GB         | 8 GB         | +100%   |
| JVM Heap Máximo            | 8 GB         | 24 GB        | +200%   |
| RAM Docker Limite          | 10 GB        | 64 GB        | +540%   |
| RAM Docker Reserva         | 4 GB         | 16 GB        | +300%   |
| CPUs Docker                | 4 cores      | 10 cores     | +150%   |
| Jetty Threads              | 50           | 100          | +100%   |
| Jetty Queue                | 1000         | 2000         | +100%   |
| DB Connection Pool         | 20           | 50           | +150%   |
| Query Timeout              | 600s (10min) | 1800s (30min)| +200%   |
| Row Limit                  | 20.000.000   | 20.000.000   | MANTIDO |

**Ganhos esperados:**
- Queries pesadas: +100% throughput
- Usuários simultâneos: +150% capacidade
- Timeout de queries: +200% tempo disponível
- Estabilidade: Redução drástica de OOM errors

---

## 🔧 COMO REAPLICAR

### Cenário 1: Atualização de Versão do Metabase

Se atualizar a imagem Docker do Metabase, as configurações do `docker-compose.yml` são **preservadas** automaticamente.

**Não é necessário fazer nada**, a menos que o arquivo `docker-compose.yml` seja sobrescrito.

### Cenário 2: docker-compose.yml foi sobrescrito

**Opção A - Restaurar arquivo completo:**
```bash
cd /home/cazouvilela/projetos/metabase/config/docker
cp /home/cazouvilela/projetos/metabase/otimizacoes_metabase/docker-compose.yml.otimizado ./docker-compose.yml
docker compose down
docker compose up -d
```

**Opção B - Aplicar configurações manualmente:**

Editar `/home/cazouvilela/projetos/metabase/config/docker/docker-compose.yml`:

1. **Atualizar JAVA_OPTS:**
   ```yaml
   JAVA_OPTS: "-Xms8G -Xmx24G -XX:+UseG1GC -XX:MaxGCPauseMillis=500 -XX:+UseStringDeduplication -XX:ParallelGCThreads=10"
   ```

2. **Atualizar Query Limits:**
   ```yaml
   MB_UNAGGREGATED_QUERY_ROW_LIMIT: "20000000"
   MB_QUERY_TIMEOUT_SECONDS: "1800"
   ```

3. **Atualizar Jetty:**
   ```yaml
   MB_JETTY_THREADS: "100"
   MB_JETTY_MAX_QUEUED_REQUESTS: "2000"
   ```

4. **Atualizar Connection Pool:**
   ```yaml
   MB_APPLICATION_DB_MAX_CONNECTION_POOL_SIZE: "50"
   ```

5. **Atualizar Recursos Docker:**
   ```yaml
   mem_limit: 64g
   mem_reservation: 16g
   cpus: '10.0'
   ```

6. **Reiniciar container:**
   ```bash
   cd /home/cazouvilela/projetos/metabase/config/docker
   docker compose down
   docker compose up -d
   ```

### Cenário 3: Criar novo docker-compose.yml do zero

Use o arquivo de referência:
```bash
cp /home/cazouvilela/projetos/metabase/otimizacoes_metabase/docker-compose.yml.otimizado \
   /home/cazouvilela/projetos/metabase/config/docker/docker-compose.yml
```

Ajuste apenas:
- Imagem do Metabase (se versão específica)
- Senha PostgreSQL (variável `${METABASE_PASSWORD}`)
- Path do arquivo .env (se necessário)

---

## ✅ VERIFICAÇÃO

### 1. Verificar container está rodando:
```bash
docker ps | grep metabase
```

Esperado: Status "Up" com portas 3000:3000

### 2. Verificar logs de inicialização:
```bash
docker logs metabase --tail 50
```

Esperado:
```
Metabase Initialization COMPLETE in XX.X s
```

### 3. Verificar configurações JVM:
```bash
docker exec metabase ps aux | grep java
```

Esperado: Ver `-Xms8G -Xmx24G` nos argumentos

### 4. Verificar recursos Docker:
```bash
docker inspect metabase | grep -A 5 "Memory\|NanoCpus"
```

Esperado:
- Memory: 68719476736 (64GB em bytes)
- MemoryReservation: 17179869184 (16GB em bytes)
- NanoCpus: 10000000000 (10 cores)

### 5. Verificar conexão PostgreSQL:
```bash
docker exec metabase nc -zv host.docker.internal 5432
```

Esperado:
```
host.docker.internal [172.17.0.1] 5432 (postgresql) open
```

### 6. Testar Metabase (navegador):
```
http://localhost:3000
```

Ou via proxy reverso:
```
http://seu-dominio.com:8080
```

---

## ⚠️ NOTAS IMPORTANTES

### O que NÃO fazer:

❌ **NÃO alterar `MB_UNAGGREGATED_QUERY_ROW_LIMIT`** para valores muito maiores
   → 20 milhões já é muito alto, valores maiores podem causar OOM

❌ **NÃO reduzir `mem_limit` abaixo de 48GB**
   → Risco de container ser morto por OOM quando JVM atingir 24GB

❌ **NÃO aumentar `max_parallel_workers_per_gather` no PostgreSQL acima de 8**
   → Pode saturar CPUs e piorar performance

❌ **NÃO remover `mem_reservation`**
   → Proteção importante sob pressão de memória do sistema

### Segurança:

✅ **Arquivo .env deve ter permissão 600:**
```bash
chmod 600 /home/cazouvilela/projetos/metabase/config/.env
```

✅ **PostgreSQL NÃO deve ser exposto externamente:**
- Apenas localhost + Docker gateway (172.17.0.1)
- Firewall NÃO deve ter regra para porta 5432

✅ **Metabase deve ser acessado via proxy reverso (Nginx):**
- Porta 3000: localhost only
- Porta 8080: via Nginx (com SSL se possível)

---

## 📞 SUPORTE

**Arquivos de referência:**
- `docker-compose.yml.otimizado`: Arquivo completo pronto para usar
- `comparativo_antes_depois.md`: Tabela detalhada de mudanças
- `guia_rapido_reaplicacao.md`: Checklist rápido

**Logs importantes:**
```bash
# Metabase
docker logs metabase -f

# PostgreSQL
sudo journalctl -u postgresql-17 -f

# Sistema
dmesg | grep -i oom
```

**Em caso de problemas:**
1. Verificar logs do Metabase e PostgreSQL
2. Verificar uso de recursos: `htop` ou `docker stats`
3. Verificar conexão PostgreSQL
4. Restaurar backup se necessário

---

**Documentação criada em:** 01/11/2025
**Última atualização:** 01/11/2025
**Responsável:** Claude Code (Sonnet 4.5)
