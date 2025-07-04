"""
Configurações centralizadas do projeto
Carrega variáveis de ambiente e define defaults
"""

from dotenv import load_dotenv

# Carrega arquivo .env
import os
from pathlib import Path

# Carrega .env da raiz do projeto ou de config/
env_path = Path(__file__).parent.parent / '.env'
if not env_path.exists():
    env_path = Path(__file__).parent / '.env'
    
load_dotenv(env_path)

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
