#!/bin/bash
# setup_redis.sh - Instala e configura Redis para cache como Metabase usa

echo "🚀 Configurando Redis para performance nativa..."
echo ""

# Verifica se está no Fedora
if ! grep -q "Fedora" /etc/os-release; then
    echo "⚠️  Este script foi feito para Fedora"
    exit 1
fi

# Instala Redis
echo "📦 Instalando Redis..."
sudo dnf install -y redis

# Configura Redis para performance
echo "⚙️  Configurando Redis..."
sudo tee /etc/redis/redis.conf > /dev/null <<EOF
# Configurações otimizadas para cache do Metabase
bind 127.0.0.1
port 6379
daemonize yes
supervised systemd

# Performance
maxmemory 2gb
maxmemory-policy allkeys-lru
save ""

# Otimizações
tcp-backlog 511
timeout 0
tcp-keepalive 300

# Logs
loglevel notice
logfile /var/log/redis/redis.log
EOF

# Cria diretório de logs
sudo mkdir -p /var/log/redis
sudo chown redis:redis /var/log/redis

# Inicia Redis
echo "🔄 Iniciando Redis..."
sudo systemctl enable redis
sudo systemctl restart redis

# Verifica se está rodando
sleep 2
if sudo systemctl is-active --quiet redis; then
    echo "✅ Redis instalado e rodando!"
    
    # Testa conexão
    echo "🧪 Testando conexão..."
    if redis-cli ping | grep -q PONG; then
        echo "✅ Redis respondendo corretamente!"
    else
        echo "❌ Redis não está respondendo"
        exit 1
    fi
else
    echo "❌ Falha ao iniciar Redis"
    sudo systemctl status redis
    exit 1
fi

# Instala dependência Python
echo ""
echo "📦 Instalando redis-py..."
pip install redis

echo ""
echo "✨ Redis configurado com sucesso!"
echo ""
echo "📊 Informações:"
echo "   Host: localhost"
echo "   Porta: 6379"
echo "   Memória máxima: 2GB"
echo "   Política: LRU (Least Recently Used)"
echo ""
echo "🔧 Comandos úteis:"
echo "   redis-cli          - Console do Redis"
echo "   redis-cli INFO     - Estatísticas"
echo "   redis-cli FLUSHALL - Limpar cache"
echo ""
