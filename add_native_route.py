#!/usr/bin/env python3
"""
Adiciona a rota Native Performance ao servidor
"""

import os
from pathlib import Path
import shutil

def add_native_route():
    """Adiciona a rota /api/query/native ao routes.py"""
    
    routes_file = Path.home() / "metabase_customizacoes" / "proxy_server" / "routes.py"
    
    # Faz backup
    backup_file = routes_file.with_suffix('.py.backup_native')
    shutil.copy(routes_file, backup_file)
    print(f"✅ Backup salvo: {backup_file}")
    
    # Lê arquivo
    with open(routes_file, 'r') as f:
        content = f.read()
    
    # Verifica se já existe
    if "api_query_native_performance" in content:
        print("⚠️  Rota native já existe!")
        return
    
    # Código da nova rota
    native_route_code = '''
    @app.route('/api/query/native', methods=['GET'])
    def api_query_native_performance():
        """
        API que replica EXATAMENTE a performance do Metabase nativo
        Sem chunks, sem streaming - carrega tudo otimizado
        """
        from api.query_extractor import query_extractor
        from api.filtros_captura import FiltrosCaptura
        import time
        import json
        import gzip
        from flask import Response
        
        try:
            # Obtém parâmetros
            question_id = request.args.get('question_id', '51')
            question_id = int(question_id)
            
            # Captura filtros
            filtros = FiltrosCaptura.capturar_parametros_request()
            
            print(f"\\n🎯 [NATIVE PERFORMANCE] Executando como Metabase nativo")
            print(f"   Question ID: {question_id}")
            print(f"   Filtros: {len(filtros)}")
            
            # Por enquanto, vamos usar a API direct mas com formato nativo
            from api.consulta_direta import consulta_direta
            
            # Executa query
            start_time = time.time()
            resultado = consulta_direta.executar_consulta_direta_simples(question_id, filtros)
            execution_time = time.time() - start_time
            
            # Converte para formato nativo do Metabase
            if isinstance(resultado, list) and len(resultado) > 0:
                # Extrai colunas
                cols = [
                    {
                        'name': key,
                        'display_name': key.replace('_', ' ').title(),
                        'base_type': 'type/Text'
                    }
                    for key in resultado[0].keys()
                ]
                
                # Converte para formato colunar
                rows = []
                for item in resultado:
                    row = [item.get(col['name']) for col in cols]
                    rows.append(row)
                
                # Monta resposta no formato nativo
                response_data = {
                    'data': {
                        'cols': cols,
                        'rows': rows,
                        'rows_truncated': len(rows),
                        'results_metadata': {
                            'columns': cols
                        }
                    },
                    'status': 'completed',
                    'row_count': len(rows),
                    'running_time': int(execution_time * 1000)
                }
                
                # Serializa e comprime
                json_data = json.dumps(response_data, separators=(',', ':'))
                compressed = gzip.compress(json_data.encode('utf-8'))
                
                print(f"✅ [NATIVE] {len(rows):,} linhas em {execution_time:.2f}s")
                print(f"📦 Response: {len(json_data)} → {len(compressed)} bytes "
                      f"({100 - len(compressed)/len(json_data)*100:.1f}% compressão)")
                
                # Retorna resposta comprimida
                response = Response(compressed)
                response.headers['Content-Type'] = 'application/json'
                response.headers['Content-Encoding'] = 'gzip'
                
                return response
            else:
                return jsonify({'error': 'Sem dados'}), 404
                
        except Exception as e:
            import traceback
            print(f"\\n❌ [NATIVE PERFORMANCE] Erro: {str(e)}")
            print(traceback.format_exc())
            
            return jsonify({
                'error': str(e),
                'tipo': 'erro_native_performance',
                'question_id': question_id
            }), 500
'''
    
    # Encontra onde inserir (após a rota /api/query/stream)
    insert_marker = "@app.route('/api/query/stream', methods=['GET'])"
    
    # Encontra a função completa api_query_stream
    start_pos = content.find(insert_marker)
    if start_pos == -1:
        print("❌ Não encontrei onde inserir a rota!")
        return
    
    # Encontra o fim da função (próxima @app.route ou fim da seção de rotas)
    current_pos = start_pos
    bracket_count = 0
    in_function = False
    
    while current_pos < len(content):
        if content[current_pos] == '\n':
            # Verifica se é uma nova rota
            next_line_start = current_pos + 1
            next_line_end = content.find('\n', next_line_start)
            if next_line_end > -1:
                next_line = content[next_line_start:next_line_end].strip()
                if next_line.startswith('@app.route') or next_line.startswith('# ---'):
                    # Encontrou próxima rota ou seção
                    insert_pos = current_pos
                    break
        current_pos += 1
    
    if insert_pos == -1:
        insert_pos = content.find('\n    @app.route', start_pos + 100)
    
    # Insere a nova rota
    new_content = content[:insert_pos] + native_route_code + content[insert_pos:]
    
    # Salva
    with open(routes_file, 'w') as f:
        f.write(new_content)
    
    print("✅ Rota /api/query/native adicionada!")

def test_route():
    """Testa se a rota foi adicionada"""
    import requests
    
    print("\n🧪 Testando nova rota...")
    
    try:
        response = requests.get("http://localhost:3500/api/query/native?question_id=51", timeout=5)
        
        if response.status_code == 200:
            print("✅ Rota funcionando!")
            
            # Verifica se tem gzip
            if response.headers.get('Content-Encoding') == 'gzip':
                print("✅ Resposta comprimida com gzip")
            
            # Parse dados
            data = response.json()
            if 'data' in data and 'rows' in data['data']:
                print(f"✅ {len(data['data']['rows'])} linhas retornadas")
            else:
                print("⚠️  Formato de resposta diferente do esperado")
                
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"   Resposta: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Erro ao testar: {e}")

def main():
    print("🚀 Adicionando rota Native Performance")
    print("=" * 50)
    
    add_native_route()
    
    print("\n📝 Próximos passos:")
    print("1. Reinicie o servidor:")
    print("   pkill -f proxy_server")
    print("   ./restart_server.sh")
    print("\n2. Teste a rota:")
    print("   http://localhost:8080/metabase_customizacoes/componentes/tabela_virtual/debug.html")

if __name__ == "__main__":
    main()
