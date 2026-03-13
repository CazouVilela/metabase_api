"""
Configurações centralizadas do projeto
Carrega variáveis de ambiente e define defaults
"""

import os
from pathlib import Path

# Carrega config/.env via loader isolado por branch
import importlib.util
_loader_path = Path(__file__).parent / 'env.config.py'
_spec = importlib.util.spec_from_file_location('env_config', _loader_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# Metabase Configuration
METABASE_CONFIG = {
    'url': os.getenv('METABASE_URL', 'http://localhost:3000'),
    'username': os.getenv('METABASE_USERNAME'),
    'password': os.getenv('METABASE_PASSWORD')
}


# PostgreSQL Configuration
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'agencias'),
    'user': os.getenv('DB_USER', 'cazouvilela'),
    'password': os.getenv('DB_PASSWORD'),
    'options': f"-c statement_timeout={os.getenv('API_TIMEOUT', '300')}000 -c work_mem={os.getenv('WORK_MEM', '256MB')}"
}

# Schema separado (não é parte da conexão)
DB_SCHEMA = os.getenv('DB_SCHEMA', 'road')



# Redis Configuration
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', '6379')),
    'enabled': os.getenv('REDIS_ENABLED', 'true').lower() == 'true'
}

# API Configuration
API_CONFIG = {
    'port': int(os.getenv('API_PORT', '3500')),
    'timeout': int(os.getenv('API_TIMEOUT', '300')),
    'max_retries': int(os.getenv('API_MAX_RETRIES', '3')),
    'chunk_size': int(os.getenv('API_CHUNK_SIZE', '1000'))
}

# Cache Configuration
CACHE_CONFIG = {
    'enabled': os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
    'ttl': int(os.getenv('CACHE_TTL', '300'))
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'max_pool_size': int(os.getenv('MAX_POOL_SIZE', '20')),
    'max_rows_without_warning': int(os.getenv('MAX_ROWS_WITHOUT_WARNING', '10000'))
}

# Development Configuration
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Validation
def validate_config():
    """Valida se as configurações essenciais estão presentes"""
    errors = []
    
    if not METABASE_CONFIG['username']:
        errors.append("METABASE_USERNAME não configurado")
    if not METABASE_CONFIG['password']:
        errors.append("METABASE_PASSWORD não configurado")
    if not DATABASE_CONFIG['password']:
        errors.append("DB_PASSWORD não configurado")
    
    if errors:
        raise ValueError(f"Erros de configuração: {', '.join(errors)}")

# Valida na importação
if not DEBUG:
    validate_config()
