#!/usr/bin/env python3
# run_server.py
"""
Script para iniciar o servidor proxy do Metabase Customizações
"""

import sys
import os

# Adiciona o diretório do projeto ao path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Importa e executa o servidor
from proxy_server.server import main

if __name__ == '__main__':
    main()
