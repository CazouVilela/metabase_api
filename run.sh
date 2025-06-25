#!/bin/bash
# Script para iniciar o servidor proxy

echo "🚀 Iniciando servidor proxy do Metabase..."
cd "$(dirname "$0")"
python proxy_server/proxy_server.py
