from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

from metabase_customizacoes.api.metabase_api import query_question
from .config import PROXY_PORT, STATIC_DIR, API_JS_DIR

app = Flask(__name__)
CORS(app)

@app.route('/componentes/<path:filename>')
def static_files(filename):
    directory = os.path.abspath(STATIC_DIR)
    return send_from_directory(directory, filename)


@app.route('/api/<path:filename>')
def api_js_files(filename):
    directory = os.path.abspath(API_JS_DIR)
    return send_from_directory(directory, filename)

@app.route('/query')
def query():
    question_id = int(request.args.get('question_id', '51'))
    params = request.args.to_dict()
    params.pop('question_id', None)
    data = query_question(question_id, params)
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PROXY_PORT)
