#!/bin/bash

# check_status.sh - Verifica o status de todos os serviços

echo "🔍 Verificando status dos serviços..."

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Função para verificar porta
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✓ $service está rodando na porta $port${NC}"
        return 0
    else
        echo -e "${RED}✗ $service NÃO está rodando na porta $port${NC}"
        return 1
    fi
}

echo ""
echo "=== SERVIÇOS PRINCIPAIS ==="
echo ""

# Flask API
check_port 3500 "Flask API"

# Metabase
check_port 3000 "Metabase"

# nginx
check_port 8080 "nginx proxy"

# PostgreSQL
check_port 5432 "PostgreSQL"

echo ""
echo "=== PROCESSOS ==="
echo ""

# ngrok
if pgrep -x "ngrok" > /dev/null; then
    echo -e "${GREEN}✓ ngrok está rodando${NC}"
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o '"public_url":"[^"]*' | grep -o 'http[^"]*' | head -1)
    if [ ! -z "$NGROK_URL" ]; then
        echo -e "  URL: ${GREEN}$NGROK_URL${NC}"
    fi
else
    echo -e "${RED}✗ ngrok NÃO está rodando${NC}"
fi

# Python/Flask
if pgrep -f "python.*server.py" > /dev/null; then
    echo -e "${GREEN}✓ Processo Python (Flask) está ativo${NC}"
else
    echo -e "${RED}✗ Processo Python (Flask) NÃO está ativo${NC}"
fi

echo ""
echo "=== CONECTIVIDADE ==="
echo ""

# Teste local da API
if curl -s http://localhost:3500/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API respondendo localmente${NC}"
else
    echo -e "${RED}✗ API não responde localmente${NC}"
fi

# Teste através do nginx
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API acessível via nginx${NC}"
else
    echo -e "${RED}✗ API não acessível via nginx${NC}"
fi

echo ""
echo "=== LOGS RECENTES ==="
echo ""

if [ -f flask.log ]; then
    echo "Últimas linhas do flask.log:"
    tail -5 flask.log | sed 's/^/  /'
fi

if [ -f ngrok.log ]; then
    echo ""
    echo "Últimas linhas do ngrok.log:"
    tail -5 ngrok.log | sed 's/^/  /'
fi

echo ""
echo "=== DIAGNÓSTICO ==="
echo ""

# Verifica problemas comuns
if ! check_port 3500 "Flask" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Flask não está rodando. Execute: ./start_services.sh${NC}"
fi

if ! pgrep -x "ngrok" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ ngrok não está rodando. Execute: ./start_services.sh${NC}"
fi

if ! check_port 8080 "nginx" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ nginx não está escutando na porta 8080${NC}"
    echo "  Verifique: sudo nginx -t"
    echo "  Reinicie: sudo systemctl restart nginx"
fi
