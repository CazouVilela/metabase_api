"""
Rotas para servir arquivos estáticos e componentes
"""

import os
from flask import Blueprint, send_from_directory, jsonify

bp = Blueprint('static', __name__)

# Diretórios base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '../..'))
COMPONENTES_DIR = os.path.join(PROJECT_ROOT, 'componentes')
STATIC_DIR = os.path.join(PROJECT_ROOT, 'static')

@bp.route('/')
def index():
    """Página inicial com informações da API"""
    return jsonify({
        'service': 'Metabase Customizações API',
        'version': '3.0.0',
        'performance': 'NATIVE (Otimizado)',
        'endpoints': {
            'queries': {
                '/api/query': 'Executa queries com performance nativa',
                '/api/question/<id>/info': 'Informações sobre questão'
            },
            'debug': {
                '/api/debug/filters': 'Debug de filtros',
                '/api/debug/decode': 'Debug de decodificação',
                '/api/debug/cache/stats': 'Estatísticas do cache',
                '/api/debug/health': 'Health check detalhado'
            },
            'componentes': {
                '/componentes/<componente>/': 'Componentes frontend'
            },
            'static': {
                '/static/<arquivo>': 'Arquivos estáticos compartilhados'
            }
        }
    })

@bp.route('/componentes/<componente>/')
def serve_componente_index(componente):
    """Serve index.html quando acessar o diretório do componente"""
    componente_dir = os.path.join(COMPONENTES_DIR, componente)
    if os.path.exists(componente_dir):
        index_file = os.path.join(componente_dir, 'index.html')
        if os.path.exists(index_file):
            return send_from_directory(componente_dir, 'index.html')
    return jsonify({'error': 'Componente não encontrado'}), 404

@bp.route('/componentes/<path:subpath>')
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

@bp.route('/static/<path:filepath>')
def serve_static(filepath):
    """Serve arquivos estáticos compartilhados"""
    return send_from_directory(STATIC_DIR, filepath)

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check básico"""
    return jsonify({
        'status': 'healthy',
        'service': 'metabase-customizacoes',
        'version': '3.0.0'
    })
