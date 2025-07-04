"""
Rotas relacionadas a queries
"""

from flask import Blueprint, request, jsonify
from api.services.query_service import QueryService
from api.utils.filters import FilterProcessor

bp = Blueprint('query', __name__)
query_service = QueryService()
filter_processor = FilterProcessor()

@bp.route('/query', methods=['GET', 'POST'])
def execute_query():
    """
    Executa query com filtros do dashboard
    Suporta GET e POST para flexibilidade
    """
    try:
        # Obtém parâmetros
        if request.method == 'POST':
            data = request.get_json() or {}
            question_id = data.get('question_id', '51')
            filters = data.get('filters', {})
        else:
            question_id = request.args.get('question_id', '51')
            filters = filter_processor.capture_from_request(request)
        
        # Converte para int
        question_id = int(question_id)
        
        print(f"\n🚀 [API] Executando query")
        print(f"   Question ID: {question_id}")
        print(f"   Filtros: {len(filters)}")
        
        # Executa query
        response = query_service.execute_query(question_id, filters)
        
        return response
        
    except ValueError as e:
        return jsonify({
            'error': str(e),
            'tipo': 'parametro_invalido'
        }), 400
        
    except Exception as e:
        import traceback
        print(f"\n❌ [API] Erro: {str(e)}")
        print(traceback.format_exc())
        
        return jsonify({
            'error': str(e),
            'tipo': 'erro_interno',
            'question_id': question_id
        }), 500

@bp.route('/question/<int:question_id>/info', methods=['GET'])
def get_question_info(question_id):
    """Obtém informações sobre uma questão"""
    try:
        info = query_service.get_question_info(question_id)
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/question/<int:question_id>/export/<format>', methods=['GET'])
def export_data(question_id, format):
    """Exporta dados em diferentes formatos"""
    try:
        filters = filter_processor.capture_from_request(request)
        
        if format not in ['csv', 'excel', 'json']:
            return jsonify({'error': 'Formato não suportado'}), 400
        
        # TODO: Implementar exportação
        return jsonify({
            'message': 'Exportação em desenvolvimento',
            'format': format,
            'question_id': question_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
