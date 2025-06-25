# proxy_server/routes.py
"""
Definição de rotas do servidor proxy
"""

from flask import jsonify, send_from_directory, request
import os
from api.consulta_metabase import consulta_metabase
from api.filtros_captura import FiltrosCaptura

def register_routes(app):
    """Registra todas as rotas da aplicação"""
    
    # Diretórios base
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.join(BASE_DIR, '..')
    COMPONENTES_DIR = os.path.join(PROJECT_ROOT, 'componentes')
    STATIC_DIR = os.path.join(PROJECT_ROOT, 'static')
    
    # ------- ROTAS DA API -------
    
    @app.route('/api/query', methods=['GET'])
    def api_query():
        """Endpoint principal para consultas"""
        try:
            # Obtém o ID da questão
            question_id = request.args.get('question_id', '51')
            question_id = int(question_id)
            
            # Executa a consulta (filtros são capturados automaticamente)
            resultado = consulta_metabase.executar_consulta(question_id)
            
            return jsonify(resultado)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/question/<int:question_id>/info', methods=['GET'])
    def api_question_info(question_id):
        """Obtém informações sobre uma questão"""
        try:
            info = consulta_metabase.obter_info_questao(question_id)
            return jsonify(info)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/debug/filters', methods=['GET'])
    def api_debug_filters():
        """Debug de filtros capturados"""
        filtros = FiltrosCaptura.capturar_parametros_request()
        debug_info = FiltrosCaptura.debug_filtros(filtros)
        
        return jsonify({
            'filtros_capturados': filtros,
            'debug': debug_info,
            'query_string': request.query_string.decode('utf-8')
        })
    
    # ------- ROTAS DE ARQUIVOS ESTÁTICOS -------
    
    @app.route('/componentes/<path:subpath>')
    def serve_componente(subpath):
        """Serve arquivos dos componentes"""
        # Determina o diretório baseado no caminho
        path_parts = subpath.split('/')
        
        if len(path_parts) >= 2:
            componente = path_parts[0]
            arquivo = '/'.join(path_parts[1:])
            componente_dir = os.path.join(COMPONENTES_DIR, componente)
            
            if os.path.exists(componente_dir):
                return send_from_directory(componente_dir, arquivo)
        
        return "Arquivo não encontrado", 404
    
    @app.route('/static/<path:filepath>')
    def serve_static(filepath):
        """Serve arquivos estáticos compartilhados"""
        return send_from_directory(STATIC_DIR, filepath)
    
    # ------- ROTAS AUXILIARES -------
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check do servidor"""
        return jsonify({
            'status': 'healthy',
            'service': 'metabase-proxy',
            'version': '2.0.0'
        })
    
    @app.route('/', methods=['GET'])
    def index():
        """Página inicial com informações"""
        return jsonify({
            'service': 'Metabase Customizações API',
            'version': '2.0.0',
            'endpoints': {
                'api': {
                    '/api/query': 'Executa consultas com filtros',
                    '/api/question/<id>/info': 'Informações sobre questão',
                    '/api/debug/filters': 'Debug de filtros'
                },
                'componentes': {
                    '/componentes/<componente>/<arquivo>': 'Arquivos dos componentes'
                },
                'static': {
                    '/static/<arquivo>': 'Arquivos estáticos'
                }
            }
        })
    
    # ------- TRATAMENTO DE ERROS -------
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint não encontrado'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Erro interno do servidor'}), 500
