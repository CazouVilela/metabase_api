#!/bin/bash
# Script para reiniciar o servidor com as correções

echo "🔄 Reiniciando servidor Metabase Customizações..."
echo ""

# Para qualquer processo Python rodando na porta 3500
echo "⏹️  Parando processos existentes..."
pkill -f "proxy_server.server" 2>/dev/null
pkill -f "python -m proxy_server" 2>/dev/null
sleep 2

# Limpa cache Python
echo "🗑️  Limpando cache Python..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# Verifica psycopg2
echo "📦 Verificando dependências..."
pip install psycopg2-binary --quiet

echo ""
echo "🚀 Iniciando servidor..."
echo "=" * 60
echo ""

# Inicia o servidor como módulo
cd ~/metabase_customizacoes
python -m proxy_server.server
