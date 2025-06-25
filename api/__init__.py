# api/__init__.py
"""
API do Metabase Customizações

Módulos disponíveis:
- config: Configurações centralizadas
- metabase_client: Cliente para API do Metabase
- filtros_captura: Captura de filtros do dashboard
- filtros_normalizacao: Normalização de parâmetros
- consulta_metabase: Execução de consultas
- processamentoDados_json: Processamento de dados JSON
- processamentoDados_transformacao: Transformações de dados
- processamentoDados_agregacao: Agregações e cálculos
"""

__version__ = '2.0.0'
__author__ = 'Metabase Customizações'

# Importa principais classes para facilitar uso
from .metabase_client import MetabaseClient, metabase_client
from .filtros_captura import FiltrosCaptura
from .filtros_normalizacao import FiltrosNormalizacao
from .consulta_metabase import ConsultaMetabase, consulta_metabase
from .processamentoDados_json import ProcessadorJSON
from .processamentoDados_transformacao import ProcessadorTransformacao
from .processamentoDados_agregacao import ProcessadorAgregacao

__all__ = [
    'MetabaseClient',
    'metabase_client',
    'FiltrosCaptura',
    'FiltrosNormalizacao',
    'ConsultaMetabase',
    'consulta_metabase',
    'ProcessadorJSON',
    'ProcessadorTransformacao',
    'ProcessadorAgregacao'
]
