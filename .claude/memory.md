# METABASE CUSTOMIZAÇÕES - Memória do Projeto

> **📚 Referência**: Este projeto segue o template documentado em [TEMPLATE_PROJETO.md](.claude/TEMPLATE_PROJETO.md)

<!-- CHAPTER: 0 Configurações da IDE -->

## 🔧 Configurações da IDE

> **⚠️ LEITURA OBRIGATÓRIA**: Este projeto utiliza a IDE Customizada.
>
> **Documentação essencial** (leia sempre ao carregar o projeto):
> - [RELACIONAMENTO_COM_IDE.md](.claude/RELACIONAMENTO_COM_IDE.md) - **Como este projeto se relaciona com a IDE**
> - [TEMPLATE_PROJETO.md](.claude/TEMPLATE_PROJETO.md) - Template de organização de projetos
> - [GUIA_SISTEMA_PROJETOS.md](.claude/GUIA_SISTEMA_PROJETOS.md) - Sistema de gerenciamento de projetos

### Comandos Slash Disponíveis

- `/iniciar` - Gerenciar projetos (listar, ativar, criar novo)
- `/subir` - Git commit + push automatizado
- `/subir_estavel` - Git commit + push + tag de versão estável
- `/tryGPT "prompt"` - Consultar ChatGPT manualmente
- `/implantacao_automatica` - Deploy com comparação Claude vs ChatGPT

### Funcionalidades da IDE

Este projeto utiliza:
- **Terminal virtual** integrado (xterm.js)
- **Explorador de arquivos** lateral com tree view
- **Sistema de planejamento** hierárquico (interface web)
- **Draft/Rascunho** automático por projeto
- **Memórias persistentes** com capítulos
- **Visualização de commits** git com tags
- **Integração ChatGPT** via Playwright

<!-- CHAPTER: 1 Visão Geral -->

## 📋 Sobre o Projeto

Sistema de customizações para Metabase que permite criar componentes interativos (tabelas, gráficos, dashboards) em iframes, capturando filtros do dashboard principal e executando queries otimizadas.

### Informações Principais

**Versão Atual**: v1.0.0
**Stack**: Python Flask + JavaScript + Redis + PostgreSQL
**Status**: ✅ Em produção

### Características Principais

- **Performance Nativa**: Execução de queries com a mesma performance do Metabase nativo
- **Cache Redis**: Cache inteligente com compressão gzip
- **Filtros Dinâmicos**: Captura automática de filtros do dashboard
- **Componentes Modulares**: Arquitetura preparada para múltiplos tipos de visualização
- **Recursos Compartilhados**: Código reutilizável entre componentes

### Contexto

Este projeto é a **API de customização do Metabase**, não o Metabase em si (que roda via Docker separadamente). Desenvolvido para permitir a criação de gráficos customizados que:
1. São inseridos em dashboards do Metabase via iframes
2. Capturam filtros do dashboard principal
3. Executam queries otimizadas diretamente no PostgreSQL
4. Usam cache Redis para melhor performance

<!-- CHAPTER: 2 Arquitetura -->

## 🏗️ Arquitetura

### Stack Tecnológico

**Backend**:
- Python 3.x
- Flask (API REST)
- Redis (cache)
- PostgreSQL (database direto)

**Frontend**:
- JavaScript vanilla
- HTML5 + CSS3
- Componentização modular

**Infraestrutura**:
- Nginx (proxy reverso)
- Metabase (plataforma BI - separado)

### Estrutura de Diretórios

```
metabase/
├── .claude/
│   ├── memory.md                         # Este arquivo
│   ├── draft.md                          # Rascunho (auto-gerenciado)
│   ├── commands/ → symlink               # Comandos compartilhados
│   ├── settings.local.json → symlink     # Permissões compartilhadas
│   ├── GUIA_SISTEMA_PROJETOS.md → symlink
│   ├── TEMPLATE_PROJETO.md → symlink
│   └── RELACIONAMENTO_COM_IDE.md → symlink
│
├── api/                                  # Backend Flask
│   ├── server.py                         # Servidor principal
│   ├── routes/                           # Endpoints
│   │   ├── query_routes.py              # Rotas de query
│   │   ├── debug_routes.py              # Rotas de debug
│   │   └── static_routes.py             # Rotas de arquivos estáticos
│   ├── services/                         # Serviços de negócio
│   │   ├── query_service.py             # Execução de queries
│   │   ├── metabase_service.py          # Comunicação com Metabase
│   │   └── cache_service.py             # Gerenciamento de cache
│   ├── utils/                            # Utilitários
│   │   ├── filters.py                   # Processamento de filtros
│   │   └── query_parser.py              # Parser de queries SQL
│   ├── config.py                         # Configurações
│   ├── metabase_client.py               # Cliente Metabase
│   ├── postgres_client.py               # Cliente PostgreSQL
│   ├── native_performance.py            # Otimizações de performance
│   ├── query_extractor.py               # Extrator de queries
│   ├── filtros_captura.py               # Captura de filtros
│   └── filtros_normalizacao.py          # Normalização de filtros
│
├── componentes/                          # Frontend
│   ├── recursos_compartilhados/         # Código reutilizável
│   │   ├── js/                          # JavaScript compartilhado
│   │   │   ├── api-client.js           # Cliente API
│   │   │   ├── filter-manager.js       # Gerenciamento de filtros
│   │   │   ├── data-processor.js       # Processamento de dados
│   │   │   └── export-utils.js         # Utilitários de exportação
│   │   └── css/                         # Estilos compartilhados
│   │       └── base.css                # CSS base
│   │
│   └── tabela_virtual/                  # Componente de tabela
│       ├── index.html
│       ├── css/tabela.css
│       └── js/
│           ├── main.js
│           └── table-renderer.js
│
├── config/                               # Configurações Docker
│   ├── docker/                          # Docker metabase (separado)
│   └── settings.py                      # Settings centralizados
│
├── nginx/                                # Configurações Nginx
│   └── metabase.conf
│
├── scripts/                              # Scripts utilitários
│   ├── start.sh                         # Inicialização
│   └── test.sh                          # Testes
│
├── otimizacoes_metabase/                # Otimizações específicas
├── proxy_server/                         # Proxy configurações
├── logs/                                 # Logs da aplicação
├── tests/                                # Testes automatizados
├── docs/                                 # Documentação adicional
├── documentacao/                         # Docs detalhadas (padronizado)
├── static/                               # Arquivos estáticos
├── venv/                                 # Ambiente virtual Python
│
├── .env                                  # Variáveis de ambiente (NÃO commitar)
├── .env.example                          # Exemplo de variáveis
├── .gitignore                            # Arquivos ignorados
├── README.md                             # Documentação principal
└── requirements.txt                      # Dependências Python
```

### Fluxo de Funcionamento

1. **Dashboard Metabase** → Aplica filtros
2. **Iframe com componente** → Captura filtros via `postMessage`
3. **Frontend (JS)** → Envia request para API com filtros
4. **API Flask** → Verifica cache Redis
5. **Se não em cache** → Executa query no PostgreSQL
6. **Retorna dados** → Frontend renderiza componente
7. **Armazena em cache** → Para próximas requisições

<!-- CHAPTER: 3 API e Endpoints -->

## 🔌 APIs e Endpoints

**Documentação completa**: Ver [README.md](../README.md) seção "API"

### Endpoints Principais

#### Executar Query
```
GET /api/query?question_id=51&filtro1=valor1&filtro2=valor2
```
Executa uma query baseada em uma question do Metabase, aplicando filtros dinâmicos.

**Parâmetros**:
- `question_id` (required): ID da question no Metabase
- `filtro*` (optional): Filtros capturados do dashboard

**Resposta**: JSON com dados da query

#### Informações da Questão
```
GET /api/question/{id}/info
```
Retorna metadados sobre uma question do Metabase.

#### Debug de Filtros
```
GET /api/debug/filters
```
Endpoint para debugar captura e processamento de filtros.

### Serviços Internos

**QueryService** (`services/query_service.py`):
- Executa queries otimizadas
- Gerencia substituição de parâmetros
- Aplica filtros dinâmicos

**MetabaseService** (`services/metabase_service.py`):
- Autenticação no Metabase
- Extração de queries de questions
- Comunicação com API do Metabase

**CacheService** (`services/cache_service.py`):
- Cache Redis com TTL configurável
- Compressão gzip
- Invalidação inteligente

### Utilitários

**FilterManager** (Frontend):
- Captura filtros do dashboard pai via `postMessage`
- Normaliza nomes de filtros
- Converte para formato da API

**PostgresClient** (`api/postgres_client.py`):
- Conexão direta com PostgreSQL
- Pool de conexões
- Execução de queries nativas

<!-- CHAPTER: 4 Componentes Frontend -->

## 🎨 Componentes Frontend

### Componentes Disponíveis

#### 1. Tabela Virtual
Localização: `componentes/tabela_virtual/`

**Características**:
- Renderização otimizada com virtualização
- Suporte para 100k+ linhas
- Exportação para CSV
- Formatação automática (números, datas, moedas)
- Responsivo

**Uso no Metabase**:
```html
<iframe
  src="https://dominio.com/metabase_customizacoes/componentes/tabela_virtual/?question_id=51"
  width="100%"
  height="600"
  frameborder="0">
</iframe>
```

### Recursos Compartilhados

Todos os componentes têm acesso a:

**api-client.js**:
```javascript
const data = await apiClient.queryData(questionId, filters);
```

**filter-manager.js**:
```javascript
const filters = filterManager.captureFromParent();
```

**data-processor.js**:
- Formatação de dados
- Transformações
- Validações

**export-utils.js**:
- Exportação CSV
- Exportação Excel (futuro)
- Exportação PDF (futuro)

### Criando Novo Componente

1. Criar estrutura:
```bash
mkdir -p componentes/meu_componente/{js,css}
touch componentes/meu_componente/index.html
touch componentes/meu_componente/js/main.js
touch componentes/meu_componente/css/styles.css
```

2. Importar recursos compartilhados no `index.html`:
```html
<script src="../recursos_compartilhados/js/api-client.js"></script>
<script src="../recursos_compartilhados/js/filter-manager.js"></script>
```

3. Usar no `main.js`:
```javascript
const filters = filterManager.captureFromParent();
const data = await apiClient.queryData(questionId, filters);
// Renderizar seu componente
```

<!-- CHAPTER: 5 Configurações -->

## ⚙️ Configurações

### Variáveis de Ambiente (.env)

```env
# Metabase
METABASE_URL=http://localhost:3000
METABASE_USERNAME=seu_email@example.com
METABASE_PASSWORD=sua_senha

# PostgreSQL (acesso direto ao banco)
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
CACHE_TTL=300  # 5 minutos
```

**⚠️ IMPORTANTE**: Nunca commitar o arquivo `.env`! Use `.env.example` como template.

### Instalação

1. **Clone e configure**:
```bash
cd /home/cazouvilela/projetos/metabase
cp .env.example .env
nano .env  # Edite com suas credenciais
```

2. **Ambiente virtual**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Redis** (opcional mas recomendado):
```bash
sudo dnf install redis
sudo systemctl enable --now redis
redis-cli ping  # Deve retornar PONG
```

4. **Nginx**:
```bash
sudo cp nginx/metabase.conf /etc/nginx/conf.d/
sudo nginx -t
sudo nginx -s reload
```

### Execução

**Desenvolvimento**:
```bash
./scripts/start.sh
```

**Produção**:
```bash
./scripts/start.sh prod
```

**Testes**:
```bash
./scripts/test.sh
```

### Portas

- **API**: 3500 (configurável via `API_PORT`)
- **Metabase**: 3000 (separado, via Docker)
- **Redis**: 6379
- **PostgreSQL**: 5432

<!-- CHAPTER: 6 Desenvolvimento -->

## 🛠️ Desenvolvimento

### Workflow de Desenvolvimento

1. **Ativar ambiente virtual**:
```bash
source venv/bin/activate
```

2. **Rodar em modo dev**:
```bash
./scripts/start.sh
```

3. **Fazer alterações** no código

4. **Testar**:
```bash
pytest tests/
```

5. **Commit**:
```bash
/subir  # Usa comando slash da IDE
```

### Estrutura de Testes

```
tests/
├── test_api/
├── test_services/
├── test_utils/
└── conftest.py
```

**Executar testes**:
```bash
# Todos os testes
pytest tests/

# Com cobertura
pytest --cov=api tests/

# Teste específico
pytest tests/test_api/test_query_routes.py
```

### Formatação de Código

```bash
# Formatar Python
black api/

# Verificar estilo
flake8 api/

# Type checking
mypy api/
```

### Debug

**Debug de filtros**:
```bash
curl http://localhost:3500/api/debug/filters
```

**Logs**:
```bash
tail -f logs/api.log
```

**Redis**:
```bash
redis-cli
> KEYS *
> GET key_name
```

### Próximos Componentes Planejados

- [ ] Gráficos interativos (Chart.js ou D3.js)
- [ ] KPIs dinâmicos com animações
- [ ] Mapas de calor
- [ ] Dashboards customizados completos
- [ ] Gráficos de Gantt
- [ ] Timeline interativa

<!-- CHAPTER: 7 Troubleshooting -->

## 🐛 Troubleshooting

### Erro de Conexão com PostgreSQL

**Sintomas**: API não consegue executar queries

**Soluções**:
1. Verificar credenciais no `.env`
2. Testar conexão:
   ```bash
   psql -h localhost -U usuario -d banco
   ```
3. Verificar se PostgreSQL está rodando:
   ```bash
   sudo systemctl status postgresql
   ```

### Cache Não Funciona

**Sintomas**: Queries sempre executam (não usam cache)

**Soluções**:
1. Verificar Redis:
   ```bash
   redis-cli ping  # Deve retornar PONG
   ```
2. Verificar `.env`:
   ```
   REDIS_ENABLED=true
   CACHE_ENABLED=true
   ```
3. Ver logs do Redis:
   ```bash
   sudo journalctl -u redis -f
   ```

### Filtros Não São Capturados

**Sintomas**: Componente não recebe filtros do dashboard

**Soluções**:
1. Verificar se iframe está no **mesmo domínio** (limitação do `postMessage`)
2. Confirmar que nomes dos filtros correspondem
3. Usar endpoint de debug:
   ```bash
   curl http://localhost:3500/api/debug/filters
   ```
4. Verificar console do navegador (F12) para erros JavaScript

### API Não Inicia

**Sintomas**: `./scripts/start.sh` falha

**Soluções**:
1. Verificar ambiente virtual ativado
2. Verificar dependências instaladas:
   ```bash
   pip install -r requirements.txt
   ```
3. Verificar porta 3500 disponível:
   ```bash
   lsof -i :3500
   ```
4. Ver logs detalhados:
   ```bash
   python api/server.py
   ```

### Performance Lenta

**Sintomas**: Queries demoram muito

**Soluções**:
1. Ativar cache Redis (`REDIS_ENABLED=true`)
2. Otimizar queries SQL (usar EXPLAIN)
3. Adicionar índices no PostgreSQL
4. Aumentar `CACHE_TTL` para queries estáveis
5. Verificar `native_performance.py` para otimizações

### Metabase Retorna Erro 401

**Sintomas**: API não consegue autenticar no Metabase

**Soluções**:
1. Verificar credenciais no `.env`
2. Testar login manual no Metabase
3. Verificar se `METABASE_URL` está correto
4. Ver logs da API para detalhes do erro

<!-- CHAPTER: 8 Próximas Features -->

## 🚀 Próximas Funcionalidades

### Prioridade Alta

- [ ] **Componente de Gráfico de Barras** customizado
- [ ] **Componente de Gráfico de Linhas** com zoom
- [ ] **Dashboard customizado completo** (grid layout)
- [ ] **Exportação para Excel** (além de CSV)
- [ ] **Testes automatizados** completos (coverage > 80%)

### Prioridade Média

- [ ] **Autenticação própria** (JWT) para componentes
- [ ] **Websockets** para atualização em tempo real
- [ ] **Suporte a múltiplos bancos** (MySQL, SQLite)
- [ ] **Interface de administração** para gerenciar componentes
- [ ] **Logs estruturados** (JSON) com rastreamento

### Prioridade Baixa

- [ ] **Temas customizáveis** (dark mode, light mode)
- [ ] **Internacionalização** (i18n)
- [ ] **Versionamento de API** (v1, v2)
- [ ] **Rate limiting** para proteção
- [ ] **Documentação Swagger/OpenAPI**

### Ideias Futuras

- [ ] **Machine Learning** - Previsões e anomalias
- [ ] **Alertas automáticos** - Notificações por email/Slack
- [ ] **Agendamento de relatórios** - PDFs automáticos
- [ ] **Colaboração em tempo real** - Comentários em gráficos
- [ ] **Mobile-first components** - Otimização para mobile

<!-- CHAPTER: 9 Referências -->

## 📚 Referências

### Documentação Interna

- [README.md](../README.md) - Documentação principal
- [TEMPLATE_PROJETO.md](.claude/TEMPLATE_PROJETO.md) - Template de organização
- [RELACIONAMENTO_COM_IDE.md](.claude/RELACIONAMENTO_COM_IDE.md) - Como usar a IDE
- [GUIA_SISTEMA_PROJETOS.md](.claude/GUIA_SISTEMA_PROJETOS.md) - Sistema de projetos

### Documentação da Pasta `/documentacao`

Para documentação detalhada de APIs, specs técnicas e guias de uso, consulte:
- `/documentacao/` - **Toda documentação detalhada deve estar aqui**

### Tecnologias Utilizadas

**Python**:
- [Flask](https://flask.palletsprojects.com/) - Framework web
- [psycopg2](https://www.psycopg.org/) - PostgreSQL adapter
- [redis-py](https://redis-py.readthedocs.io/) - Cliente Redis

**JavaScript**:
- [Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API) - HTTP requests
- [postMessage](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage) - Cross-frame communication

**Infraestrutura**:
- [Nginx](https://nginx.org/en/docs/) - Proxy reverso
- [Redis](https://redis.io/documentation) - Cache
- [PostgreSQL](https://www.postgresql.org/docs/) - Database

**Metabase**:
- [Metabase API](https://www.metabase.com/docs/latest/api-documentation) - Documentação oficial
- [Metabase Questions](https://www.metabase.com/docs/latest/questions/start) - Queries

### Repositório

- **GitHub**: https://github.com/CazouVilela/metabase (assumido)
- **Branch principal**: `master` ou `main`

---

**Última Atualização**: 2025-01-04
**Versão**: 1.0.0
**Status**: ✅ Em produção
**Mantenedor**: Cazou Vilela
