from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

# Garante que a raiz do projeto está no PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.metabase_api import query_question
from proxy_server.config import PROXY_PORT, STATIC_DIR

app = Flask(__name__)
CORS(app)

@app.route('/componentes/dashboard_tabela/<path:filename>')
def static_files(filename):
    directory = os.path.abspath(STATIC_DIR)
    return send_from_directory(directory, filename)

@app.route('/query')
def query():
    question_id = int(request.args.get('question_id', '51'))
    params = request.args.to_dict()
    params.pop('question_id', None)

    print("🔍 Params recebidos:", params)

    # 👉 Adiciona um valor padrão caso esteja vazio
    if not params:
        print("⚠️ Nenhum parâmetro recebido. Usando valor default.")
        params = {"campanha": "XPTO"}  # Substitua por um valor válido para testes

    try:
        data = query_question(question_id, params)
        return jsonify(data)
    except Exception as e:
        print(f"❌ Erro ao consultar a pergunta: {e}")
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PROXY_PORT)
