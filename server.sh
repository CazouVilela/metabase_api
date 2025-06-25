#!/bin/bash
# server.sh - Gerenciador do servidor Metabase Customizações

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$PROJECT_DIR/server.pid"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/server.log"
PYTHON_CMD="python3"
SERVER_SCRIPT="run_server.py"
DEFAULT_PORT=3500

# Cria diretório de logs se não existir
mkdir -p "$LOG_DIR"

# Funções auxiliares
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verifica se o servidor está rodando
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    else
        return 1
    fi
}

# Inicia o servidor
start_server() {
    if is_running; then
        print_warning "Servidor já está rodando (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    print_status "Iniciando servidor..."
    
    # Verifica dependências Python
    $PYTHON_CMD -c "import flask" 2>/dev/null
    if [ $? -ne 0 ]; then
        print_error "Flask não instalado. Execute: pip install -r requirements.txt"
        return 1
    fi
    
    # Inicia o servidor em background
    cd "$PROJECT_DIR"
    nohup $PYTHON_CMD "$SERVER_SCRIPT" --mode dev > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    # Aguarda o servidor iniciar
    sleep 2
    
    if is_running; then
        print_success "Servidor iniciado com sucesso (PID: $PID)"
        print_status "Logs em: $LOG_FILE"
        print_status "Acesse: http://localhost:$DEFAULT_PORT"
        return 0
    else
        print_error "Falha ao iniciar o servidor"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Para o servidor
stop_server() {
    if ! is_running; then
        print_warning "Servidor não está rodando"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    print_status "Parando servidor (PID: $PID)..."
    
    kill "$PID" 2>/dev/null
    sleep 2
    
    if is_running; then
        print_warning "Servidor não parou, forçando..."
        kill -9 "$PID" 2>/dev/null
        sleep 1
    fi
    
    rm -f "$PID_FILE"
    print_success "Servidor parado"
    return 0
}

# Reinicia o servidor
restart_server() {
    print_status "Reiniciando servidor..."
    stop_server
    sleep 2
    start_server
}

# Mostra status do servidor
show_status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        print_success "Servidor está rodando (PID: $PID)"
        
        # Mostra informações adicionais
        echo ""
        echo "📊 Informações do Processo:"
        ps -p "$PID" -o pid,vsz=MEMORY,cpu,etime=ELAPSED -h
        
        # Mostra últimas linhas do log
        echo ""
        echo "📋 Últimas linhas do log:"
        tail -n 10 "$LOG_FILE"
        
        # Verifica se está respondendo
        echo ""
        echo "🔍 Verificando resposta..."
        curl -s -o /dev/null -w "   Status HTTP: %{http_code}\n" "http://localhost:$DEFAULT_PORT/health"
        
    else
        print_error "Servidor não está rodando"
    fi
}

# Mostra logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        print_status "Mostrando logs (Ctrl+C para sair)..."
        tail -f "$LOG_FILE"
    else
        print_error "Arquivo de log não encontrado"
    fi
}

# Executa testes
run_tests() {
    print_status "Executando testes..."
    cd "$PROJECT_DIR"
    $PYTHON_CMD "$SERVER_SCRIPT" --mode test
}

# Mostra informações
show_info() {
    cd "$PROJECT_DIR"
    $PYTHON_CMD "$SERVER_SCRIPT" --mode info
}

# Limpa arquivos temporários
clean() {
    print_status "Limpando arquivos temporários..."
    rm -f "$PID_FILE"
    rm -rf "$PROJECT_DIR/__pycache__"
    rm -rf "$PROJECT_DIR/api/__pycache__"
    rm -rf "$PROJECT_DIR/proxy_server/__pycache__"
    find "$PROJECT_DIR" -name "*.pyc" -delete
    print_success "Limpeza concluída"
}

# Menu principal
show_menu() {
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║         METABASE CUSTOMIZAÇÕES - GERENCIADOR         ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""
    echo "Uso: $0 {start|stop|restart|status|logs|test|info|clean}"
    echo ""
    echo "Comandos:"
    echo "  start    - Inicia o servidor"
    echo "  stop     - Para o servidor"
    echo "  restart  - Reinicia o servidor"
    echo "  status   - Mostra status do servidor"
    echo "  logs     - Mostra logs em tempo real"
    echo "  test     - Executa testes"
    echo "  info     - Mostra informações do sistema"
    echo "  clean    - Limpa arquivos temporários"
    echo ""
}

# Processa comando
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
        show_status
        ;;
    logs)
        show_logs
        ;;
    test)
        run_tests
        ;;
    info)
        show_info
        ;;
    clean)
        clean
        ;;
    *)
        show_menu
        exit 1
        ;;
esac

exit $?
