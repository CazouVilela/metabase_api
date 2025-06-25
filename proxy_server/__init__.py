# proxy_server/__init__.py
"""
Servidor Proxy para Metabase Customizações

Este módulo implementa o servidor proxy que:
- Roteia requisições entre frontend e API
- Gerencia CORS
- Serve arquivos estáticos dos componentes
"""

__version__ = '2.0.0'

from .server import create_app
from .config import PROXY_PORT, SERVER_CONFIG

__all__ = ['create_app', 'PROXY_PORT', 'SERVER_CONFIG']
