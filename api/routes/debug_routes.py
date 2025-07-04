"""
Rotas de debug e diagnóstico
"""

from flask import Blueprint, request, jsonify
from api.utils.filters import FilterProcessor
from api.services.cache_service import CacheService
import urllib.parse

bp = Blueprint('debug', __name__)
filter_processor = FilterProcessor()
cache_service = CacheService()

@bp.route('/filters', methods=['GET'])
def debug_filters():
    """Debug de filtros capturados"""
    filters = filter_processor.capture_from_request(request)
    debug_info = filter_processor.debug_info(filters)
    
    return jsonify({
        'captured_filters': filters,
        'debug': debug_info,
        'query_string': request.query_string.decode('utf-8'),
        'raw_args': dict(request.args),
        'lists': {k: request.args.getlist(k) for k in request.args}
    })

@bp.route('/decode', methods=['GET'])
def debug_decode():
    """Debug de decodificação de parâmetros"""
    raw_query = request.query_string.decode('utf-8')
    parsed_params = {}
    
    # Parse manual
    if raw_query:
        for param in raw_query.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                decoded_key = urllib.parse.unquote(key)
                decoded_value = urllib.parse.unquote(value)
                
                if decoded_key in parsed_params:
                    # Converte para lista se já existe
                    if not isinstance(parsed_params[decoded_key], list):
                        parsed_params[decoded_key] = [parsed_params[decoded_key]]
                    parsed_params[decoded_key].append(decoded_value)
                else:
                    parsed_params[decoded_key] = decoded_value
    
    # Identifica parâmetros com múltiplos valores
    multi_value_params = [k for k, v in parsed_params.items() if isinstance(v, list)]
    
    # Formata resposta detalhada
    response = {
        'raw_query_string': raw_query,
        'parsed_parameters': {},
        'multi_value_parameters': multi_value_params,
        'total_parameters': len(parsed_params)
    }
    
    # Adiciona detalhes de cada parâmetro
    for key, value in parsed_params.items():
        response['parsed_parameters'][key] = {
            'value': value,
            'is_list': isinstance(value, list),
            'encoded_key': urllib.parse.quote(key),
            'encoded_value': urllib.parse.quote(str(value)) if not isinstance(value, list) else [urllib.parse.quote(v) for v in value]
        }
    
    return jsonify(response)

@bp.route('/cache/stats', methods=['GET'])
def cache_stats():
    """Estatísticas do cache"""
    return jsonify(cache_service.get_stats())

@bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Limpa o cache"""
    cache_service.clear_all()
    return jsonify({'message': 'Cache limpo com sucesso'})

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check detalhado"""
    health_status = {
        'status': 'healthy',
        'cache': cache_service.get_stats(),
        'config': {
            'debug_mode': True,
            'cache_enabled': cache_service.enabled
        }
    }
    
    return jsonify(health_status)
