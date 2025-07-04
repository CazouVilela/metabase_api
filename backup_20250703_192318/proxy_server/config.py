# proxy_server/config.py
"""
Configurações do servidor proxy
"""

import os

# Porta do servidor
PROXY_PORT = 3500

# Diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

# Configurações de CORS
CORS_ORIGINS = "*"  # Em produção, especifique os domínios permitidos
CORS_METHODS = ["GET", "POST", "OPTIONS"]
CORS_HEADERS = ["Content-Type", "Authorization"]

# Configurações de servidor
SERVER_CONFIG = {
    'host': '0.0.0.0',
    'port': PROXY_PORT,
    'debug': True,
    'threaded': True
}

# Timeouts
REQUEST_TIMEOUT = 300  # 5 minutos

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
