# proxy_server/routes.py
"""
Definição de rotas do servidor proxy - Versão Otimizada
Usa apenas o método Native Performance
"""

from flask import jsonify, send_from_directory, request, Response
import os
import json
import time

def register_routes(app):
    """Registra todas as rotas da aplicação"""
    
    # Diretórios base
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.join(BASE_DIR, '..')
    COMPONENTES_DIR = os.path.join(PROJECT_ROOT, 'componentes')
    STATIC_DIR = os.path.join(PROJECT_ROOT, 'static')
    
    # ------- ROTA PRINCIPAL DA API (NATIVE ONLY) -------
    
    @app.route('/api/query', methods=['GET'])
    @app.route('/api/query/native', methods=['GET'])
    def api_query_native():
        """API com performance nativa - ÚNICO método de query"""
        from api.native_performance import executar_query_performance_nativa
        from api.filtros_captura import FiltrosCaptura
        
        try:
            # Obtém parâmetros
            question_id = request.args.get('question_id', '51')
            question_id = int(question_id)
            
            # Captura filtros
            filtros = FiltrosCaptura.capturar_parametros_request()
            
            print(f"\n🚀 [NATIVE PERFORMANCE] Executando query")
            print(f"   Question ID: {question_id}")
            print(f"   Filtros: {len(filtros)}")
            
            # Executa com performance nativa
            return executar_query_performance_nativa(question_id, filtros)
            
        except ValueError:
            return jsonify({
                'error': f'ID da pergunta inválido: {question_id}',
                'tipo': 'parametro_invalido'
            }), 400
            
        except Exception as e:
            import traceback
            print(f"\n❌ [NATIVE PERFORMANCE] Erro: {str(e)}")
            print(traceback.format_exc())
            
            return jsonify({
                'error': str(e),
                'tipo': 'erro_native_performance',
                'question_id': question_id
            }), 500
    
    # ------- ROTAS AUXILIARES -------
    
    @app.route('/api/question/<int:question_id>/info', methods=['GET'])
    def api_question_info(question_id):
        """Obtém informações sobre uma questão"""
        from api.metabase_client import metabase_client
        
        try:
            info = metabase_client.get_question_info(question_id)
            return jsonify(info)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/debug/filters', methods=['GET'])
    def api_debug_filters():
        """Debug de filtros capturados"""
        from api.filtros_captura import FiltrosCaptura
        
        filtros = FiltrosCaptura.capturar_parametros_request()
        debug_info = FiltrosCaptura.debug_filtros(filtros)
        
        return jsonify({
            'filtros_capturados': filtros,
            'debug': debug_info,
            'query_string': request.query_string.decode('utf-8')
        })
    
    # ------- ROTAS DE ARQUIVOS ESTÁTICOS -------
    
    @app.route('/componentes/<componente>/')
    def serve_componente_index(componente):
        """Serve index.html quando acessar o diretório do componente"""
        componente_dir = os.path.join(COMPONENTES_DIR, componente)
        if os.path.exists(componente_dir):
            index_file = os.path.join(componente_dir, 'index.html')
            if os.path.exists(index_file):
                return send_from_directory(componente_dir, 'index.html')
        return jsonify({'error': 'Componente não encontrado'}), 404
    
    @app.route('/componentes/<path:subpath>')
    def serve_componente(subpath):
        """Serve arquivos dos componentes"""
        clean_path = subpath.split('?')[0]
        
        if clean_path.endswith('/'):
            clean_path = clean_path[:-1]
        
        path_parts = clean_path.split('/')
        
        if len(path_parts) >= 1:
            componente = path_parts[0]
            componente_dir = os.path.join(COMPONENTES_DIR, componente)
            
            if os.path.exists(componente_dir):
                if len(path_parts) > 1:
                    arquivo = '/'.join(path_parts[1:])
                    file_path = os.path.join(componente_dir, arquivo)
                    
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        return send_from_directory(componente_dir, arquivo)
                else:
                    index_file = os.path.join(componente_dir, 'index.html')
                    if os.path.exists(index_file):
                        return send_from_directory(componente_dir, 'index.html')
        
        return jsonify({'error': 'Arquivo não encontrado', 'path': subpath}), 404
    
    @app.route('/static/<path:filepath>')
    def serve_static(filepath):
        """Serve arquivos estáticos compartilhados"""
        return send_from_directory(STATIC_DIR, filepath)
    
    # ------- ROTAS DE STATUS -------
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check do servidor"""
        return jsonify({
            'status': 'healthy',
            'service': 'metabase-proxy',
            'version': '3.0.0',
            'method': 'native-performance'
        })
    
    @app.route('/', methods=['GET'])
    def index():
        """Página inicial com informações"""
        return jsonify({
            'service': 'Metabase Customizações API',
            'version': '3.0.0',
            'performance': 'NATIVE (Otimizado)',
            'endpoints': {
                'queries': {
                    '/api/query': 'Executa queries com performance nativa',
                    '/api/query/native': 'Alias para /api/query'
                },
                'info': {
                    '/api/question/<id>/info': 'Informações sobre questão',
                    '/api/debug/filters': 'Debug de filtros'
                },
                'componentes': {
                    '/componentes/<componente>/': 'Componentes frontend'
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
