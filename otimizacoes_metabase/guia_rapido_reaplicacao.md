# GUIA RÁPIDO - REAPLICAÇÃO DE OTIMIZAÇÕES

**Use este guia quando:**
- Atualizar versão do Metabase e o docker-compose.yml for sobrescrito
- Criar nova instalação do Metabase
- Restaurar configurações após problema

---

## ⚡ MÉTODO RÁPIDO (RECOMENDADO)

### 1. Parar container atual
```bash
cd /home/cazouvilela/projetos/metabase/config/docker
docker compose down
```

### 2. Restaurar arquivo otimizado
```bash
cp /home/cazouvilela/projetos/metabase/otimizacoes_metabase/docker-compose.yml.otimizado \
   ./docker-compose.yml
```

### 3. Verificar arquivo .env
```bash
# Verificar se .env existe e tem a senha correta
ls -la ../.env

# Se não existir, criar com:
# METABASE_PASSWORD=sua_senha_aqui

# Garantir permissão correta
chmod 600 ../.env
```

### 4. Iniciar container
```bash
docker compose up -d
```

### 5. Verificar funcionamento
```bash
# Ver logs
docker logs metabase -f

# Aguardar mensagem:
# "Metabase Initialization COMPLETE in XX.X s"

# Testar acesso
curl http://localhost:3000/api/health
```

**Tempo total:** ~2 minutos

---

## 🔧 MÉTODO MANUAL (SE NECESSÁRIO)

Use se precisar aplicar configurações em um docker-compose.yml existente.

### Checklist de Configurações

Editar: `/home/cazouvilela/projetos/metabase/config/docker/docker-compose.yml`

#### ✅ 1. JVM HEAP
```yaml
JAVA_OPTS: "-Xms8G -Xmx24G -XX:+UseG1GC -XX:MaxGCPauseMillis=500 -XX:+UseStringDeduplication -XX:ParallelGCThreads=10"
```

#### ✅ 2. QUERY LIMITS
```yaml
MB_UNAGGREGATED_QUERY_ROW_LIMIT: "20000000"
MB_QUERY_TIMEOUT_SECONDS: "1800"
```

#### ✅ 3. CACHE
```yaml
MB_QUERY_CACHING_ENABLED: "true"
MB_QUERY_CACHING_TTL_RATIO: "100"
```

#### ✅ 4. JETTY
```yaml
MB_JETTY_THREADS: "100"
MB_JETTY_MAX_QUEUED_REQUESTS: "2000"
```

#### ✅ 5. CONNECTION POOL
```yaml
MB_APPLICATION_DB_MAX_CONNECTION_POOL_SIZE: "50"
```

#### ✅ 6. POSTGRESQL CONNECTION
```yaml
MB_DB_TYPE: "postgres"
MB_DB_DBNAME: "metabase"
MB_DB_PORT: "5432"
MB_DB_USER: "metabase_user"
MB_DB_PASS: "${METABASE_PASSWORD}"
MB_DB_HOST: "host.docker.internal"
```

#### ✅ 7. RECURSOS DOCKER
```yaml
mem_limit: 64g
mem_reservation: 16g
cpus: '10.0'
```

#### ✅ 8. EXTRA_HOSTS
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

#### ✅ 9. RESTART POLICY
```yaml
restart: always
```

#### ✅ 10. ENV FILE PATH
```yaml
env_file: ../.env  # Relativo ao docker-compose.yml
```

### Aplicar mudanças:
```bash
cd /home/cazouvilela/projetos/metabase/config/docker
docker compose down
docker compose up -d
docker logs metabase -f
```

---

## 🚨 TROUBLESHOOTING

### Container não inicia

**Problema:** `docker compose up -d` retorna erro

**Soluções:**
```bash
# 1. Verificar sintaxe do YAML
docker compose config

# 2. Verificar se .env existe
ls -la ../.env

# 3. Ver logs detalhados
docker compose up

# 4. Remover container antigo
docker stop metabase
docker rm metabase
docker compose up -d
```

### "Connection refused" ao PostgreSQL

**Problema:** Metabase não conecta ao PostgreSQL

**Soluções:**
```bash
# 1. Verificar se PostgreSQL está rodando
systemctl status postgresql-17

# 2. Verificar conexão do container
docker exec metabase nc -zv host.docker.internal 5432

# 3. Verificar pg_hba.conf
sudo cat /var/lib/pgsql/17/data/pg_hba.conf | grep 172.17

# Deve ter:
# host    metabase    metabase_user    172.17.0.0/16    scram-sha-256

# 4. Verificar listen_addresses
sudo cat /var/lib/pgsql/17/data/postgresql.conf | grep listen_addresses

# Deve ter:
# listen_addresses = 'localhost,172.17.0.1'
```

### Out of Memory (OOM)

**Problema:** Container morre com OOM

**Diagnóstico:**
```bash
# Ver logs do sistema
dmesg | grep -i oom

# Ver uso de memória
docker stats metabase

# Ver configuração
docker inspect metabase | grep -i memory
```

**Soluções:**
1. Se JVM > 24GB: Reduzir Xmx para 20GB
2. Se queries muito grandes: Reduzir `MB_UNAGGREGATED_QUERY_ROW_LIMIT`
3. Se tudo OK: Aumentar `mem_limit` para 80GB

### Queries lentas

**Problema:** Queries demorando muito

**Verificações:**
```bash
# 1. Ver uso de recursos
docker stats metabase
htop

# 2. Verificar se PostgreSQL está otimizado
sudo -u postgres psql -c "SHOW shared_buffers;"
sudo -u postgres psql -c "SHOW work_mem;"

# 3. Ver logs do Metabase
docker logs metabase | grep -i "query"

# 4. Verificar cache
# No Metabase UI: Admin > Performance > Caching
```

**Soluções:**
1. Aplicar otimizações PostgreSQL (se ainda não aplicadas)
2. Aumentar cache TTL no Metabase
3. Criar índices nas tabelas do PostgreSQL

---

## 📋 VERIFICAÇÃO PÓS-APLICAÇÃO

Execute este checklist após reaplicar configurações:

```bash
# 1. Container rodando?
docker ps | grep metabase
# Esperado: Status "Up"

# 2. Recursos corretos?
docker inspect metabase | grep -A 2 "Memory\|NanoCpus"
# Esperado:
#   Memory: 68719476736 (64GB)
#   MemoryReservation: 17179869184 (16GB)
#   NanoCpus: 10000000000 (10 cores)

# 3. JVM correto?
docker exec metabase ps aux | grep java | grep -o 'Xm[sx][0-9]*G'
# Esperado: Xms8G e Xmx24G

# 4. Conecta ao PostgreSQL?
docker exec metabase nc -zv host.docker.internal 5432
# Esperado: "open"

# 5. Inicialização completa?
docker logs metabase | grep "Initialization COMPLETE"
# Esperado: "Metabase Initialization COMPLETE in XX.X s"

# 6. API respondendo?
curl http://localhost:3000/api/health
# Esperado: {"status":"ok"}

# 7. Variáveis de ambiente corretas?
docker exec metabase env | grep MB_
# Verificar se todas as variáveis MB_* estão presentes
```

### ✅ Checklist Visual

- [ ] Container status: Up
- [ ] Memory limit: 64GB
- [ ] Memory reservation: 16GB
- [ ] CPUs: 10
- [ ] JVM Heap: 8-24GB
- [ ] PostgreSQL: Conectado
- [ ] Inicialização: Completa
- [ ] API: Respondendo
- [ ] Logs: Sem erros

---

## 🔄 ATUALIZAÇÃO DE VERSÃO DO METABASE

Quando atualizar a imagem do Metabase:

### 1. Backup atual
```bash
cd /home/cazouvilela/projetos/metabase/config/docker
cp docker-compose.yml docker-compose.yml.backup-$(date +%Y%m%d)
```

### 2. Atualizar imagem no docker-compose.yml
```yaml
# De:
image: metabase/metabase:latest

# Para versão específica (exemplo):
image: metabase/metabase:v0.50.0

# Ou manter latest para sempre pegar a mais nova
image: metabase/metabase:latest
```

### 3. Parar, atualizar e reiniciar
```bash
docker compose down
docker compose pull
docker compose up -d
docker logs metabase -f
```

### 4. Verificar se configurações foram preservadas
```bash
# Verificar JVM
docker exec metabase ps aux | grep Xmx

# Verificar recursos
docker stats metabase

# Testar funcionamento
curl http://localhost:3000/api/health
```

**IMPORTANTE:** O docker-compose.yml **não** é sobrescrito ao atualizar a imagem. Suas configurações são preservadas.

---

## 📞 LINKS ÚTEIS

**Documentação completa:**
```
/home/cazouvilela/projetos/metabase/otimizacoes_metabase/README.md
```

**Comparativo detalhado:**
```
/home/cazouvilela/projetos/metabase/otimizacoes_metabase/comparativo_antes_depois.md
```

**Arquivo de referência:**
```
/home/cazouvilela/projetos/metabase/otimizacoes_metabase/docker-compose.yml.otimizado
```

**Documentação oficial Metabase:**
- Environment Variables: https://www.metabase.com/docs/latest/configuring-metabase/environment-variables
- Performance: https://www.metabase.com/docs/latest/operations-guide/performance

---

**Criado em:** 01/11/2025
**Última atualização:** 01/11/2025
