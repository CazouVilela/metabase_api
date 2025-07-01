# proxy_server/routes.py
"""
Definição de rotas do servidor proxy
"""

from flask import jsonify, send_from_directory, request, Response
import os
import json
import time
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
    
    @app.route('/api/query/direct', methods=['GET'])
    def api_query_direct():
        """Endpoint para consultas diretas ao PostgreSQL (performance otimizada)"""
        from api.consulta_direta import consulta_direta
        
        try:
            # Obtém parâmetros
            question_id = request.args.get('question_id', '51')
            try:
                question_id = int(question_id)
            except ValueError:
                return jsonify({
                    'error': f'ID da pergunta inválido: {question_id}',
                    'tipo': 'parametro_invalido'
                }), 400
            
            # Parâmetros opcionais de configuração
            database = request.args.get('database')
            schema = request.args.get('schema')
            
            # Configura se necessário
            if database or schema:
                if not consulta_direta.testar_configuracao(database, schema):
                    return jsonify({
                        'error': 'Falha ao configurar conexão com banco de dados',
                        'database': database or 'agencias',
                        'schema': schema or 'road',
                        'tipo': 'erro_configuracao'
                    }), 500
            
            # Executa consulta direta (sem streaming por enquanto)
            resultado = consulta_direta.executar_consulta_direta_simples(question_id)
            
            return jsonify(resultado)
            
        except Exception as e:
            import traceback
            erro_detalhado = traceback.format_exc()
            
            # Log no servidor
            print(f"\n❌ ERRO 500 - Detalhes:")
            print(erro_detalhado)
            
            # Retorna erro estruturado
            return jsonify({
                'error': str(e),
                'tipo': 'erro_execucao',
                'question_id': question_id,
                'detalhes': erro_detalhado.split('\n')[-3:-1]  # Últimas linhas do erro
            }), 500
    
    @app.route('/api/query/stream', methods=['GET'])
    def api_query_stream():
        """Endpoint de streaming SSE para consultas grandes"""
        from api.consulta_direta import consulta_direta
        
        # IMPORTANTE: Captura parâmetros ANTES do generator
        question_id = request.args.get('question_id', '51')
        try:
            question_id = int(question_id)
        except ValueError:
            return jsonify({
                'error': f'ID da pergunta inválido: {question_id}',
                'tipo': 'parametro_invalido'
            }), 400
        
        # Captura outros parâmetros
        database = request.args.get('database')
        schema = request.args.get('schema')
        chunk_size = int(request.args.get('chunk_size', 5000))
        
        # Captura TODOS os filtros antes do generator
        from api.filtros_captura import FiltrosCaptura
        filtros = FiltrosCaptura.capturar_parametros_request()
        
        def generate():
            start_total = time.time()
            
            try:
                # Usa as variáveis capturadas acima
                # NÃO usa request.args aqui dentro!
                
                # Configura se necessário
                if database or schema:
                    consulta_direta.testar_configuracao(database, schema)
                
                # Log inicial
                print(f"\n🚀 [STREAMING] Iniciando stream para pergunta {question_id}")
                print(f"   Chunk size: {chunk_size:,}")
                print(f"   Filtros: {filtros}")
                
                # Envia evento de início
                yield f"event: start\ndata: {json.dumps({'question_id': question_id, 'chunk_size': chunk_size, 'timestamp': time.time()})}\n\n"
                
                # Configura chunk size
                consulta_direta.chunk_size = chunk_size
                
                # Executa consulta com streaming
                chunks_enviados = 0
                total_linhas = 0
                tempo_sql = 0
                tempo_primeiro_chunk = None
                
                # Usa os filtros capturados
                resultado = consulta_direta.executar_consulta_direta(question_id, filtros, streaming=True)
                
                for chunk in resultado:
                    chunk_start = time.time()
                    
                    # Atualiza contadores
                    chunks_enviados += 1
                    total_linhas += len(chunk)
                    
                    # Tempo do primeiro chunk (tempo SQL)
                    if tempo_primeiro_chunk is None:
                        tempo_primeiro_chunk = chunk_start - start_total
                        tempo_sql = tempo_primeiro_chunk
                        print(f"⏱️  [STREAMING] Tempo SQL (primeiro chunk): {tempo_sql:.2f}s")
                    
                    # Prepara dados do chunk
                    chunk_data = {
                        'chunk_number': chunks_enviados,
                        'rows': chunk,
                        'rows_in_chunk': len(chunk),
                        'total_rows_so_far': total_linhas,
                        'timestamp': time.time()
                    }
                    
                    # Envia chunk
                    yield f"event: chunk\ndata: {json.dumps(chunk_data, default=str)}\n\n"
                    
                    # Log do chunk
                    tempo_decorrido = time.time() - start_total
                    print(f"📦 [STREAMING] Chunk {chunks_enviados}: {len(chunk):,} linhas "
                          f"(Total: {total_linhas:,} em {tempo_decorrido:.2f}s)")
                
                # Tempo total de transmissão
                tempo_total_transmissao = time.time() - start_total
                
                # Envia evento de conclusão
                completion_data = {
                    'total_chunks': chunks_enviados,
                    'total_rows': total_linhas,
                    'tempo_sql': tempo_sql,
                    'tempo_total_transmissao': tempo_total_transmissao,
                    'tempo_transmissao_dados': tempo_total_transmissao - tempo_sql,
                    'velocidade_media': total_linhas / tempo_total_transmissao if tempo_total_transmissao > 0 else 0,
                    'timestamp': time.time()
                }
                
                yield f"event: complete\ndata: {json.dumps(completion_data)}\n\n"
                
                # Log final
                print(f"\n✅ [STREAMING] Completo!")
                print(f"   Total de chunks: {chunks_enviados}")
                print(f"   Total de linhas: {total_linhas:,}")
                print(f"   Tempo SQL: {tempo_sql:.2f}s")
                print(f"   Tempo transmissão dados: {tempo_total_transmissao - tempo_sql:.2f}s")
                print(f"   Tempo total: {tempo_total_transmissao:.2f}s")
                print(f"   Velocidade: {total_linhas/tempo_total_transmissao:.0f} linhas/s")
                
            except Exception as e:
                import traceback
                erro = {
                    'error': str(e),
                    'tipo': 'erro_streaming',
                    'traceback': traceback.format_exc()
                }
                print(f"\n❌ [STREAMING] Erro: {str(e)}")
                yield f"event: error\ndata: {json.dumps(erro)}\n\n"
        
        # Retorna response SSE
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'  # Desabilita buffering no nginx
            }
        )
    
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
            'version': '2.1.0'
        })
    
    @app.route('/', methods=['GET'])
    def index():
        """Página inicial com informações"""
        return jsonify({
            'service': 'Metabase Customizações API',
            'version': '2.1.0',
            'endpoints': {
                'api': {
                    '/api/query': 'Executa consultas com filtros (API Metabase)',
                    '/api/query/direct': 'Executa consultas diretas no PostgreSQL',
                    '/api/query/stream': 'Streaming SSE para consultas grandes',
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
