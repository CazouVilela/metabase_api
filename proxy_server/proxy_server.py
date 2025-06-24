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

# ---------- arquivos estáticos (HTML, JS, CSS) ----------
@app.route('/componentes/dashboard_tabela/<path:filename>')
def static_files(filename):
    directory = os.path.abspath(STATIC_DIR)
    return send_from_directory(directory, filename)

# ---------- endpoint principal ----------
@app.route('/query')
def query():
    question_id = int(request.args.get('question_id', '51'))
    params = request.args.to_dict()
    params.pop('question_id', None)           # remove id da questão

    # Converte query-string → lista de parâmetros compatível com Metabase
    metabase_params = []
    for key, value in params.items():
        if not value:
            continue                          # ignora filtros vazios

        # intervalo de datas (ex.: 2025-05-25~2025-06-24)
        if key == "data" and "~" in value:
            start_date, end_date = value.split("~")
            metabase_params.append({
                "type": "date/range",
                "target": ["variable", ["template-tag", key]],
                "value": [start_date, end_date]
            })
        # filtros texto / campo
        else:
            metabase_params.append({
                "type": "string/=",
                "target": ["variable", ["template-tag", key]],
                "value": value
            })

    print("📥 Filtros recebidos:", metabase_params)

    # repassa exatamente a lista já estruturada
    data = query_question(question_id, params=metabase_params)
    return jsonify(data)

# ---------- execução local ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PROXY_PORT)
