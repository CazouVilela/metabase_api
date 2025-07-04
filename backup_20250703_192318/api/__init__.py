# api/__init__.py
"""
API do Metabase Customizações - Versão Otimizada
Usa apenas o método Native Performance
"""

__version__ = '3.0.0'
__author__ = 'Metabase Customizações'

# Importa apenas os módulos necessários para Native Performance
from .native_performance import native_api, executar_query_performance_nativa
from .postgres_client import PostgresClient, postgres_client
from .query_extractor import QueryExtractor, query_extractor
from .filtros_captura import FiltrosCaptura
from .filtros_normalizacao import FiltrosNormalizacao
from .metabase_client import MetabaseClient, metabase_client

__all__ = [
    'native_api',
    'executar_query_performance_nativa',
    'PostgresClient',
    'postgres_client',
    'QueryExtractor',
    'query_extractor',
    'FiltrosCaptura',
    'FiltrosNormalizacao',
    'MetabaseClient',
    'metabase_client'
]
