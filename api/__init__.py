# api/__init__.py
"""
API do Metabase Customizações

Módulos disponíveis:
- config: Configurações centralizadas
- metabase_client: Cliente para API do Metabase
- postgres_client: Cliente para conexão direta ao PostgreSQL
- query_extractor: Extrator de queries SQL do Metabase
- consulta_direta: Execução direta de queries no PostgreSQL
- filtros_captura: Captura de filtros do dashboard
- filtros_normalizacao: Normalização de parâmetros
- consulta_metabase: Execução de consultas (via API Metabase)
- processamentoDados_json: Processamento de dados JSON
- processamentoDados_transformacao: Transformações de dados
- processamentoDados_agregacao: Agregações e cálculos
"""

__version__ = '2.1.0'
__author__ = 'Metabase Customizações'

# Importa principais classes para facilitar uso
from .metabase_client import MetabaseClient, metabase_client
from .postgres_client import PostgresClient, postgres_client
from .query_extractor import QueryExtractor, query_extractor
from .consulta_direta import ConsultaDireta, consulta_direta
from .filtros_captura import FiltrosCaptura
from .filtros_normalizacao import FiltrosNormalizacao
from .consulta_metabase import ConsultaMetabase, consulta_metabase
from .processamentoDados_json import ProcessadorJSON
from .processamentoDados_transformacao import ProcessadorTransformacao
from .processamentoDados_agregacao import ProcessadorAgregacao

__all__ = [
    'MetabaseClient',
    'metabase_client',
    'PostgresClient',
    'postgres_client',
    'QueryExtractor',
    'query_extractor',
    'ConsultaDireta',
    'consulta_direta',
    'FiltrosCaptura',
    'FiltrosNormalizacao',
    'ConsultaMetabase',
    'consulta_metabase',
    'ProcessadorJSON',
    'ProcessadorTransformacao',
    'ProcessadorAgregacao'
]
