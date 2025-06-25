from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import json
import urllib.parse

# Garante que a raiz do projeto está no PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.metabase_api import query_question
from proxy_server.config import PROXY_PORT, STATIC_DIR

app = Flask(__name__)
CORS(app)

# ---------- arquivos estáticos (HTML, JS, CSS) ----------
@app.route('/componentes/dashboard_tabela/<path:filename>')
def static_files(filename):
    directory = os.path.abspath(STATIC_DIR)
    return send_from_directory(directory, filename)

# ---------- função para obter parâmetros com suporte a múltiplos valores ----------
def get_all_parameters():
    """
    Obtém todos os parâmetros da requisição, incluindo múltiplos valores
    para a mesma chave
    """
    params = {}
    
    # Pega a query string raw
    raw_query = request.query_string.decode('utf-8')
    if not raw_query:
        return params
    
    # Lista de todos os parâmetros conhecidos que podem ter múltiplos valores
    multi_value_params = [
        'campanha', 'conta', 'adset', 'ad_name', 'plataforma', 
        'posicao', 'device', 'objective', 'optimization_goal', 
        'buying_type', 'action_type_filter'
    ]
    
    # Para cada parâmetro conhecido, verifica se tem múltiplos valores
    for param_name in multi_value_params:
        values = request.args.getlist(param_name)
        if values:
            # Remove valores vazios
            values = [v for v in values if v and v.strip()]
            if values:
                if len(values) == 1:
                    params[param_name] = values[0]
                else:
                    params[param_name] = values
    
    # Adiciona outros parâmetros únicos (como question_id, data, etc)
    for key in request.args:
        if key not in multi_value_params and key not in params:
            value = request.args.get(key)
            if value and value.strip():
                params[key] = value
    
    return params

# ---------- endpoint principal ----------
@app.route('/query')
def query():
    # Obtém todos os parâmetros incluindo múltiplos valores
    all_params = get_all_parameters()
    
    # Extrai question_id
    question_id = all_params.pop('question_id', '51')
    if question_id:
        question_id = int(question_id)
    
    print("\n🔍 DEBUG - Parâmetros recebidos:")
    for key, value in all_params.items():
        if isinstance(value, list):
            print(f"  • {key}: {len(value)} valores")
            for i, v in enumerate(value):
                print(f"    [{i+1}] '{v}'")
        else:
            print(f"  • {key}: '{value}'")
    
    # Converte para formato Metabase
    metabase_params = []
    
    for key, value in all_params.items():
        # Ignora chaves sem valor
        if not value:
            continue
        
        # Se é uma lista (múltiplos valores), processa cada um
        if isinstance(value, list):
            print(f"\n  🔸 Processando '{key}' com {len(value)} valores")
            
            # Para múltiplos valores, o Metabase espera um array no value
            param = {
                "type": "string/=",
                "target": ["dimension", ["template-tag", key]],
                "value": value  # Envia como array
            }
            metabase_params.append(param)
            print(f"     ✓ Adicionado como dimension string/= com array de {len(value)} valores")
            
        else:
            # Valor único
            print(f"\n  🔸 Processando '{key}' = '{value}'")
            
            # Trata diferentes tipos de parâmetros
            if key == "data" and "~" in value:
                # Data com intervalo
                dates = value.split("~")
                if len(dates) == 2:
                    param = {
                        "type": "date/range",
                        "target": ["variable", ["template-tag", key]],
                        "value": f"{dates[0]}~{dates[1]}"
                    }
                    metabase_params.append(param)
                    print(f"     ✓ Adicionado como date/range")
            else:
                # Parâmetro único normal
                param = {
                    "type": "string/=",
                    "target": ["dimension", ["template-tag", key]],
                    "value": [value]  # Sempre array, mesmo para valor único
                }
                metabase_params.append(param)
                print(f"     ✓ Adicionado como dimension string/= (valor único em array)")
    
    print(f"\n📦 Total de parâmetros formatados: {len(metabase_params)}")
    print("📤 Parâmetros enviados ao Metabase:")
    print(json.dumps(metabase_params, indent=2, ensure_ascii=False))
    
    try:
        # Executa a query
        data = query_question(question_id, params=metabase_params)
        
        # Log de resposta
        if isinstance(data, list):
            print(f"\n✅ Resposta recebida: {len(data)} linhas")
            
            if len(data) < 5000 and len(data) > 0:
                print("   🎯 Filtros aplicados com sucesso!")
                
                # Se tem filtros com múltiplos valores, destaca
                multi_value_filters = [k for k, v in all_params.items() if isinstance(v, list)]
                if multi_value_filters:
                    print(f"   📌 Filtros com múltiplos valores: {', '.join(multi_value_filters)}")
                    
            elif len(data) == 0 and len(metabase_params) > 0:
                print("   ⚠️  0 linhas - possível problema com valores dos filtros")
            elif len(data) >= 5000:
                print("   ⚠️  Retornou limite máximo - filtros podem não estar funcionando")
                
        else:
            print(f"\n✅ Resposta recebida: {type(data)}")
            
        return jsonify(data)
        
    except Exception as e:
        print(f"\n❌ Erro ao executar query: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ---------- endpoint de teste manual ----------
@app.route('/test')
def test():
    """Endpoint para testar filtros manualmente com múltiplos valores"""
    # Teste com múltiplos valores na campanha
    test_params = [
        {
            "type": "string/=",
            "target": ["dimension", ["template-tag", "campanha"]],
            "value": [
                "Barra Shopping | Road | Tráfego | Always On | MultiVocê | 07.02",
                "Barra Shopping | ROAD | Tráfego | Always On | Institucional / Acesso Multi | 24.10",
                "Barra Shopping | Road | Reconhecimento | Always On | MultiVocê | 07.02"
            ]
        },
        {
            "type": "string/=",
            "target": ["dimension", ["template-tag", "conta"]],
            "value": ["ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA"]
        }
    ]
    
    print("\n🧪 TESTE MANUAL - Testando com múltiplos valores:")
    print(json.dumps(test_params, indent=2, ensure_ascii=False))
    
    data = query_question(51, params=test_params)
    
    if isinstance(data, list):
        return jsonify({
            "success": True,
            "rows_returned": len(data),
            "message": "Teste com múltiplos valores no filtro campanha",
            "filters": {
                "campanha": "3 valores",
                "conta": "1 valor"
            },
            "sample": data[:3] if len(data) > 0 else []
        })
    else:
        return jsonify({"error": "Unexpected response format", "data": data})

# ---------- endpoint de debug melhorado ----------
@app.route('/debug/decode')
def debug_decode():
    """Mostra como os parâmetros estão sendo decodificados, incluindo múltiplos valores"""
    raw_query = request.query_string.decode('utf-8')
    all_params = get_all_parameters()
    
    result = {
        "raw_query_string": raw_query,
        "parsed_parameters": {},
        "multi_value_parameters": []
    }
    
    # Mostra todos os parâmetros parseados
    for key, value in all_params.items():
        if isinstance(value, list):
            result["parsed_parameters"][key] = {
                "type": "multiple",
                "count": len(value),
                "values": value
            }
            result["multi_value_parameters"].append(key)
        else:
            result["parsed_parameters"][key] = {
                "type": "single",
                "value": value
            }
    
    # Adiciona estatísticas
    result["statistics"] = {
        "total_parameters": len(all_params),
        "multi_value_count": len(result["multi_value_parameters"]),
        "single_value_count": len(all_params) - len(result["multi_value_parameters"])
    }
    
    return jsonify(result)

# ---------- execução local ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PROXY_PORT, debug=True)
