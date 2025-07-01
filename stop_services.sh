#!/bin/bash

# stop_services.sh - Script para parar os serviços do Metabase Customizações

echo "🛑 Parando serviços do Metabase Customizações..."

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Parar servidor Flask
echo -e "\n${YELLOW}Parando servidor Flask...${NC}"
if pkill -f "python.*proxy_server.server"; then
    echo -e "${GREEN}✓ Servidor Flask parado${NC}"
elif pkill -f "python.*run_server.py"; then
    echo -e "${GREEN}✓ Servidor Flask parado${NC}"
else
    echo -e "${YELLOW}! Servidor Flask não estava rodando${NC}"
fi

# 2. Parar ngrok
echo -e "\n${YELLOW}Parando ngrok...${NC}"
if pkill -f ngrok; then
    echo -e "${GREEN}✓ ngrok parado${NC}"
else
    echo -e "${YELLOW}! ngrok não estava rodando${NC}"
fi

# 3. Limpar arquivos de log antigos (opcional)
echo -e "\n${YELLOW}Deseja limpar os arquivos de log? (s/N)${NC}"
read -r response
if [[ "$response" =~ ^([sS][iI][mM]|[sS])$ ]]; then
    rm -f flask.log ngrok.log
    echo -e "${GREEN}✓ Logs removidos${NC}"
fi

echo -e "\n${GREEN}✨ Serviços parados!${NC}"
