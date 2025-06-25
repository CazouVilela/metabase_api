#!/bin/bash
# Script para controlar o servidor proxy
# Execute com: ./server.sh [start|stop|restart|status]

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configurações
PORT=3500
SCRIPT_PATH="proxy_server/proxy_server.py"

# Função para verificar se o servidor está rodando
check_server() {
    if lsof -i:$PORT >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Função para obter o PID do servidor
get_server_pid() {
    lsof -ti:$PORT 2>/dev/null
}

# Função para iniciar o servidor
start_server() {
    if check_server; then
        echo -e "${YELLOW}⚠️  Servidor já está rodando na porta $PORT${NC}"
        echo "Use './server.sh restart' para reiniciar"
    else
        echo -e "${GREEN}🚀 Iniciando servidor...${NC}"
        python $SCRIPT_PATH &
        sleep 2
        if check_server; then
            echo -e "${GREEN}✅ Servidor iniciado com sucesso!${NC}"
            echo "PID: $(get_server_pid)"
        else
            echo -e "${RED}❌ Falha ao iniciar o servidor${NC}"
        fi
    fi
}

# Função para parar o servidor
stop_server() {
    if check_server; then
        PID=$(get_server_pid)
        echo -e "${YELLOW}🛑 Parando servidor (PID: $PID)...${NC}"
        kill $PID
        sleep 1
        if check_server; then
            echo -e "${RED}⚠️  Servidor ainda rodando, forçando parada...${NC}"
            kill -9 $PID
        fi
        echo -e "${GREEN}✅ Servidor parado${NC}"
    else
        echo -e "${YELLOW}ℹ️  Servidor não está rodando${NC}"
    fi
}

# Função para reiniciar o servidor
restart_server() {
    echo -e "${YELLOW}🔄 Reiniciando servidor...${NC}"
    stop_server
    sleep 1
    start_server
}

# Função para verificar status
check_status() {
    if check_server; then
        PID=$(get_server_pid)
        echo -e "${GREEN}✅ Servidor está RODANDO${NC}"
        echo "   PID: $PID"
        echo "   Porta: $PORT"
        echo ""
        echo "Processos relacionados:"
        ps aux | grep -E "(python.*proxy_server|$PORT)" | grep -v grep
    else
        echo -e "${RED}❌ Servidor está PARADO${NC}"
    fi
}

# Menu principal
case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        check_status
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status}"
        echo ""
        echo "Comandos:"
        echo "  start   - Inicia o servidor"
        echo "  stop    - Para o servidor"
        echo "  restart - Reinicia o servidor"
        echo "  status  - Verifica status do servidor"
        echo ""
        echo "Exemplo: ./server.sh status"
        exit 1
        ;;
esac
