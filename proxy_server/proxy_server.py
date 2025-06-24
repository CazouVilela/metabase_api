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

# ---------- endpoint principal ----------
@app.route('/query')
def query():
    question_id = int(request.args.get('question_id', '51'))
    
    # Captura TODOS os parâmetros da URL
    all_params = dict(request.args)
    all_params.pop('question_id', None)
    
    print("\n🔍 DEBUG - Parâmetros recebidos na URL:")
    for key, value in all_params.items():
        print(f"  • {key}: '{value}'")
    
    # Converte para formato Metabase
    metabase_params = []
    
    for key, value in all_params.items():
        # Ignora valores vazios
        if not value or value == '':
            continue
            
        # Decodifica caracteres especiais
        decoded_value = urllib.parse.unquote_plus(value)
        
        print(f"\n  🔸 Processando '{key}' = '{decoded_value}'")
        
        # CORREÇÃO PRINCIPAL: Usa "dimension" em vez de "variable"
        if key == "data" and "~" in decoded_value:
            # Data com intervalo - mantém "variable" para datas
            dates = decoded_value.split("~")
            if len(dates) == 2:
                param = {
                    "type": "date/range",
                    "target": ["variable", ["template-tag", key]],
                    "value": f"{dates[0]}~{dates[1]}"
                }
                metabase_params.append(param)
                print(f"     ✓ Adicionado como date/range")
        else:
            # IMPORTANTE: Usa "dimension" e valor como array!
            param = {
                "type": "string/=",
                "target": ["dimension", ["template-tag", key]],  # dimension, não variable!
                "value": [decoded_value]  # Array, não string simples!
            }
            metabase_params.append(param)
            print(f"     ✓ Adicionado como dimension string/=")
    
    print(f"\n📦 Total de parâmetros formatados: {len(metabase_params)}")
    print("📤 Parâmetros enviados ao Metabase:")
    print(json.dumps(metabase_params, indent=2, ensure_ascii=False))
    
    try:
        # Executa a query
        data = query_question(question_id, params=metabase_params)
        
        # Log de resposta
        if isinstance(data, list):
            print(f"\n✅ Resposta recebida: {len(data)} linhas")
            
            # Verifica se filtrou (menos que 5000)
            if len(data) < 5000:
                print("   🎯 Filtros aplicados com sucesso!")
            else:
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
    """Endpoint para testar filtros manualmente"""
    # Teste com o formato CORRETO que descobrimos
    test_params = [
        {
            "type": "string/=",
            "target": ["dimension", ["template-tag", "campanha"]],  # dimension!
            "value": ["Road | Engajamento | Degusta Burger 2025 | 26/05"]  # Array!
        },
        {
            "type": "string/=",
            "target": ["dimension", ["template-tag", "conta"]],
            "value": ["ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA"]
        }
    ]
    
    print("\n🧪 TESTE MANUAL - Enviando parâmetros (formato correto):")
    print(json.dumps(test_params, indent=2, ensure_ascii=False))
    
    data = query_question(51, params=test_params)
    
    if isinstance(data, list):
        # Verifica se os dados estão filtrados corretamente
        filtered_correctly = False
        if len(data) > 0:
            sample = data[0]
            if ('Road | Engajamento | Degusta Burger 2025 | 26/05' in str(sample.get('campaign_name', '')) and
                'ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA' in str(sample.get('account_name', ''))):
                filtered_correctly = True
        
        return jsonify({
            "success": True,
            "rows_returned": len(data),
            "filtered_correctly": filtered_correctly,
            "sample": data[:3] if len(data) > 0 else []
        })
    else:
        return jsonify({"error": "Unexpected response format", "data": data})

# ---------- execução local ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PROXY_PORT, debug=True)
