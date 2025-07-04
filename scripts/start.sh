#!/bin/bash
# Script de inicialização do Metabase Customizações

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Diretório do projeto
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$PROJECT_DIR"

echo -e "${BLUE}🚀 Iniciando Metabase Customizações${NC}"
echo "=================================="

# Verifica arquivo .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Arquivo .env não encontrado!${NC}"
    echo -e "${YELLOW}Copie o .env.example e configure:${NC}"
    echo "  cp .env.example .env"
    exit 1
fi

# Carrega variáveis de ambiente
source .env

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 não encontrado!${NC}"
    exit 1
fi

# Verifica/cria ambiente virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Criando ambiente virtual...${NC}"
    python3 -m venv venv
fi

# Ativa ambiente virtual
source venv/bin/activate

# Instala/atualiza dependências
echo -e "${YELLOW}📦 Verificando dependências...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Verifica Redis (opcional)
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis está rodando${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis não está rodando (cache desabilitado)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Redis não instalado (cache desabilitado)${NC}"
fi

# Verifica PostgreSQL
echo -e "${YELLOW}🔍 Verificando conexão com PostgreSQL...${NC}"
python3 -c "
import psycopg2
from config.settings import DATABASE_CONFIG
try:
    conn = psycopg2.connect(**DATABASE_CONFIG)
    conn.close()
    print('${GREEN}✅ PostgreSQL conectado${NC}')
except Exception as e:
    print('${RED}❌ Erro ao conectar PostgreSQL:${NC}', str(e))
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Verifica Metabase
echo -e "${YELLOW}🔍 Verificando conexão com Metabase...${NC}"
python3 -c "
import requests
from config.settings import METABASE_CONFIG
try:
    r = requests.get(f\"{METABASE_CONFIG['url']}/api/health\", timeout=5)
    if r.status_code == 200:
        print('${GREEN}✅ Metabase está rodando${NC}')
    else:
        print('${YELLOW}⚠️  Metabase respondeu com status:${NC}', r.status_code)
except Exception as e:
    print('${RED}❌ Metabase não está acessível${NC}')
    print('   Verifique se está rodando em:', METABASE_CONFIG['url'])
"

# Mata processos antigos
echo -e "${YELLOW}🔄 Verificando processos existentes...${NC}"
pkill -f "api.server" 2>/dev/null
sleep 2

# Inicia servidor
echo -e "${GREEN}🚀 Iniciando servidor API...${NC}"
echo "=================================="

# Modo de execução
if [ "$1" == "prod" ]; then
    echo -e "${BLUE}Modo: PRODUÇÃO${NC}"
    gunicorn -w 4 -b 0.0.0.0:${API_PORT:-3500} \
             --timeout 300 \
             --access-logfile logs/access.log \
             --error-logfile logs/error.log \
             "api.server:create_app()"
else
    echo -e "${BLUE}Modo: DESENVOLVIMENTO${NC}"
    python -m api.server
fi
