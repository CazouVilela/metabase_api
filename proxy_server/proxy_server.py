from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import os

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

    print("🔍 Params recebidos:", params)  # para debug1

    data = query_question(question_id, params)
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PROXY_PORT)
