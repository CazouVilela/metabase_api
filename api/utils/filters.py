"""
Utilitários para processamento de filtros
"""

from typing import Dict, List, Union, Any
from flask import Request
import urllib.parse

class FilterProcessor:
    """Processa e normaliza filtros de requisições"""
    
    # Lista de parâmetros que podem ter múltiplos valores
    MULTI_VALUE_PARAMS = [
        'campanha', 'conta', 'adset', 'ad_name', 'plataforma', 
        'posicao', 'device', 'objective', 'optimization_goal', 
        'buying_type', 'action_type_filter', 'anuncio',
        'conversoes_consideradas'
    ]
    
    # Parâmetros especiais que não são filtros
    SPECIAL_PARAMS = ['question_id', 'format', 'limit', 'offset']
    
    # Mapa de normalização de nomes
    NORMALIZATION_MAP = {
        'posição': 'posicao',
        'posicao': 'posicao',
        'anúncio': 'anuncio',
        'anuncio': 'anuncio',
        'conversões_consideradas': 'conversoes_consideradas',
        'conversoes_consideradas': 'conversoes_consideradas',
        'objetivo': 'objective',
        'objective': 'objective'
    }
    
    def capture_from_request(self, request: Request) -> Dict[str, Union[str, List[str]]]:
        """
        Captura todos os parâmetros da requisição
        Suporta múltiplos valores para o mesmo parâmetro
        """
        params = {}
        
        # Pega todos os parâmetros
        for key in request.args:
            # Pula parâmetros especiais
            if key in self.SPECIAL_PARAMS:
                continue
            
            # Normaliza nome
            normalized_key = self.normalize_param_name(key)
            
            # Verifica se é um parâmetro multi-valor
            if normalized_key in self.MULTI_VALUE_PARAMS:
                values = request.args.getlist(key)
                # Remove valores vazios
                values = [v for v in values if v and v.strip()]
                
                if values:
                    if len(values) == 1:
                        params[normalized_key] = values[0]
                    else:
                        params[normalized_key] = values
            else:
                # Parâmetro único
                value = request.args.get(key)
                if value and value.strip():
                    params[normalized_key] = value
        
        return params
    
    def normalize_param_name(self, name: str) -> str:
        """Normaliza o nome de um parâmetro"""
        # Decodifica se necessário
        try:
            decoded_name = urllib.parse.unquote(name)
            if decoded_name != name:
                name = decoded_name
        except:
            pass
        
        # Retorna o nome normalizado ou o original
        return self.NORMALIZATION_MAP.get(name, name)
    
    def format_for_metabase(self, filters: Dict[str, Union[str, List[str]]]) -> List[Dict]:
        """
        Formata filtros para o formato esperado pelo Metabase
        """
        metabase_params = []
        
        for key, value in filters.items():
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
    
    def debug_info(self, filters: Dict) -> Dict:
        """Gera informações de debug sobre os filtros"""
        debug_info = {
            'total_filters': len(filters),
            'multi_value_filters': [],
            'single_value_filters': [],
            'special_chars': []
        }
        
        for key, value in filters.items():
            if isinstance(value, list):
                debug_info['multi_value_filters'].append({
                    'name': key,
                    'count': len(value),
                    'values': value
                })
            else:
                debug_info['single_value_filters'].append({
                    'name': key,
                    'value': value
                })
                
                # Verifica caracteres especiais
                special_chars = ['+', '&', '%', '=', '?', '#', '|', '/', '*']
                found_chars = [c for c in special_chars if c in str(value)]
                if found_chars:
                    debug_info['special_chars'].append({
                        'filter': key,
                        'value': value,
                        'chars': found_chars
                    })
        
        return debug_info
