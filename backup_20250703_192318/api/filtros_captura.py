# api/filtros_captura.py
"""
Módulo para captura de filtros do dashboard
"""

from typing import Dict, List, Any, Union
from flask import request
import urllib.parse

class FiltrosCaptura:
    """Classe para capturar e processar filtros de requisições"""
    
    # Lista de parâmetros que podem ter múltiplos valores
    MULTI_VALUE_PARAMS = [
        'campanha', 'conta', 'adset', 'ad_name', 'plataforma', 
        'posicao', 'device', 'objective', 'optimization_goal', 
        'buying_type', 'action_type_filter', 'anuncio',
        'conversoes_consideradas'
    ]
    
    # Parâmetros especiais que não são filtros
    SPECIAL_PARAMS = ['question_id', 'format', 'limit', 'offset']
    
    @staticmethod
    def capturar_parametros_request() -> Dict[str, Union[str, List[str]]]:
        """
        Captura todos os parâmetros da requisição atual
        Suporta múltiplos valores para o mesmo parâmetro
        
        Returns:
            Dict com parâmetros capturados
        """
        params = {}
        
        # Pega a query string raw
        raw_query = request.query_string.decode('utf-8')
        if not raw_query:
            return params
        
        # Processa todos os parâmetros
        for key in request.args:
            # Pula parâmetros especiais
            if key in FiltrosCaptura.SPECIAL_PARAMS:
                continue
                
            # Verifica se é um parâmetro multi-valor
            if key in FiltrosCaptura.MULTI_VALUE_PARAMS:
                values = request.args.getlist(key)
                # Remove valores vazios
                values = [v for v in values if v and v.strip()]
                
                if values:
                    if len(values) == 1:
                        params[key] = values[0]
                    else:
                        params[key] = values
            else:
                # Parâmetro único
                value = request.args.get(key)
                if value and value.strip():
                    params[key] = value
        
        return params
    
    @staticmethod
    def extrair_filtros_url(url: str) -> Dict[str, Union[str, List[str]]]:
        """
        Extrai filtros de uma URL completa
        
        Args:
            url: URL completa com query string
            
        Returns:
            Dict com filtros extraídos
        """
        params = {}
        
        # Parse da URL
        parsed = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed.query)
        
        for key, values in query_params.items():
            if key in FiltrosCaptura.SPECIAL_PARAMS:
                continue
                
            # Remove valores vazios
            values = [v for v in values if v and v.strip()]
            
            if values:
                if len(values) == 1:
                    params[key] = values[0]
                else:
                    params[key] = values
        
        return params
    
    @staticmethod
    def formatar_para_metabase(filtros: Dict[str, Union[str, List[str]]]) -> List[Dict]:
        """
        Formata filtros capturados para o formato esperado pelo Metabase
        
        Args:
            filtros: Dict com filtros capturados
            
        Returns:
            Lista de parâmetros formatados para o Metabase
        """
        metabase_params = []
        
        for key, value in filtros.items():
            if not value:
                continue
            
            # Se é uma lista (múltiplos valores)
            if isinstance(value, list):
                param = {
                    "type": "string/=",
                    "target": ["dimension", ["template-tag", key]],
                    "value": value  # Envia como array
                }
                metabase_params.append(param)
                
            else:
                # Valor único
                # Trata diferentes tipos de parâmetros
                if key == "data" and "~" in str(value):
                    # Data com intervalo
                    dates = str(value).split("~")
                    if len(dates) == 2:
                        param = {
                            "type": "date/range",
                            "target": ["variable", ["template-tag", key]],
                            "value": f"{dates[0]}~{dates[1]}"
                        }
                        metabase_params.append(param)
                else:
                    # Parâmetro único normal
                    param = {
                        "type": "string/=",
                        "target": ["dimension", ["template-tag", key]],
                        "value": [value]  # Sempre array, mesmo para valor único
                    }
                    metabase_params.append(param)
        
        return metabase_params
    
    @staticmethod
    def debug_filtros(filtros: Dict) -> Dict:
        """
        Gera informações de debug sobre os filtros
        
        Args:
            filtros: Dict com filtros
            
        Returns:
            Dict com informações de debug
        """
        debug_info = {
            'total_filtros': len(filtros),
            'filtros_multiplos': [],
            'filtros_simples': [],
            'valores_especiais': []
        }
        
        for key, value in filtros.items():
            if isinstance(value, list):
                debug_info['filtros_multiplos'].append({
                    'nome': key,
                    'quantidade': len(value),
                    'valores': value
                })
            else:
                debug_info['filtros_simples'].append({
                    'nome': key,
                    'valor': value
                })
                
                # Verifica caracteres especiais
                special_chars = ['+', '&', '%', '=', '?', '#', '|', '/', '*']
                found_chars = [c for c in special_chars if c in str(value)]
                if found_chars:
                    debug_info['valores_especiais'].append({
                        'filtro': key,
                        'valor': value,
                        'caracteres': found_chars
                    })
        
        return debug_info
