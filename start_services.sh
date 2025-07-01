#!/bin/bash

# start_services.sh - Script para iniciar todos os serviços do Metabase Customizações

echo "🚀 Iniciando serviços do Metabase Customizações..."

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Diretório do projeto
PROJECT_DIR="$HOME/metabase_customizacoes"
cd "$PROJECT_DIR"

# Função para verificar se porta está em uso
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# 1. Verificar/Iniciar servidor Flask
echo -e "\n${YELLOW}1. Verificando servidor Flask...${NC}"
if check_port 3500; then
    echo -e "${GREEN}✓ Servidor Flask já está rodando na porta 3500${NC}"
else
    echo "Iniciando servidor Flask..."
    # Mata processos antigos se houver
    pkill -f "python.*proxy_server.server" 2>/dev/null
    pkill -f "python.*run_server.py" 2>/dev/null
    
    # Inicia o servidor em background (como módulo)
    nohup python -m proxy_server.server > flask.log 2>&1 &
    
    # Aguarda inicialização
    sleep 3
    
    if check_port 3500; then
        echo -e "${GREEN}✓ Servidor Flask iniciado com sucesso!${NC}"
    else
        echo -e "${RED}✗ Erro ao iniciar servidor Flask${NC}"
        echo "Verifique o arquivo flask.log para mais detalhes"
        exit 1
    fi
fi

# 2. Verificar/Iniciar ngrok
echo -e "\n${YELLOW}2. Verificando ngrok...${NC}"
if pgrep -x "ngrok" > /dev/null; then
    echo -e "${GREEN}✓ ngrok já está rodando${NC}"
    
    # Obtém URL atual
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'http[^"]*' | head -1)
    if [ ! -z "$NGROK_URL" ]; then
        echo -e "${GREEN}URL pública: $NGROK_URL${NC}"
    fi
else
    echo "Iniciando ngrok..."
    # Mata processos antigos
    pkill -f ngrok 2>/dev/null
    
    # Inicia ngrok em background
    nohup ngrok http 8080 > ngrok.log 2>&1 &
    
    # Aguarda inicialização
    sleep 3
    
    # Verifica e mostra URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'http[^"]*' | head -1)
    if [ ! -z "$NGROK_URL" ]; then
        echo -e "${GREEN}✓ ngrok iniciado com sucesso!${NC}"
        echo -e "${GREEN}URL pública: $NGROK_URL${NC}"
    else
        echo -e "${RED}✗ Erro ao iniciar ngrok${NC}"
        exit 1
    fi
fi

# 3. Verificar nginx
echo -e "\n${YELLOW}3. Verificando nginx...${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ nginx está rodando${NC}"
else
    echo "Iniciando nginx..."
    sudo systemctl start nginx
    
    if systemctl is-active --quiet nginx; then
        echo -e "${GREEN}✓ nginx iniciado com sucesso!${NC}"
    else
        echo -e "${RED}✗ Erro ao iniciar nginx${NC}"
        exit 1
    fi
fi

# 4. Verificar Metabase
echo -e "\n${YELLOW}4. Verificando Metabase...${NC}"
if check_port 3000; then
    echo -e "${GREEN}✓ Metabase está rodando na porta 3000${NC}"
else
    echo -e "${YELLOW}! Metabase não está rodando${NC}"
    echo "Para iniciar o Metabase, execute:"
    echo "  cd ~/metabase_customizacoes/config/docker"
    echo "  docker-compose up -d"
fi

# 5. Verificar PostgreSQL
echo -e "\n${YELLOW}5. Verificando PostgreSQL...${NC}"
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL está acessível${NC}"
else
    echo -e "${RED}✗ PostgreSQL não está acessível${NC}"
    echo "Verifique se o PostgreSQL está rodando"
fi

# Resumo final
echo -e "\n${YELLOW}========================================${NC}"
echo -e "${GREEN}✨ Serviços prontos!${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "URLs de acesso:"
echo -e "  Metabase local: ${GREEN}http://localhost:3000${NC}"
echo -e "  API local: ${GREEN}http://localhost:3500${NC}"
echo -e "  nginx proxy: ${GREEN}http://localhost:8080${NC}"
if [ ! -z "$NGROK_URL" ]; then
    echo -e "  URL pública: ${GREEN}$NGROK_URL${NC}"
fi
echo ""
echo "Teste o iframe:"
echo -e "  ${GREEN}$NGROK_URL/componentes/tabela_virtual/?question_id=51${NC}"
echo ""
echo "Logs disponíveis em:"
echo "  - flask.log (servidor Flask)"
echo "  - ngrok.log (túnel ngrok)"
echo ""
echo "Para parar os serviços, use o script stop_services.sh"
