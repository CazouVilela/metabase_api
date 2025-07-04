"""
Servidor principal da API
"""

import sys
import os
from flask import Flask
from flask_cors import CORS

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import API_CONFIG, DEBUG, LOG_LEVEL
from api.routes import query_routes, debug_routes, static_routes

def create_app():
    """Cria e configura a aplicação Flask"""
    app = Flask(__name__)
    
    # Configurações do Flask
    app.config['DEBUG'] = DEBUG
    app.config['JSON_AS_ASCII'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # Habilita CORS
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Registra blueprints
    app.register_blueprint(query_routes.bp, url_prefix='/api')
    app.register_blueprint(debug_routes.bp, url_prefix='/api/debug')
    app.register_blueprint(static_routes.bp)
    
    # Configura logging
    if not DEBUG:
        import logging
        from logging.handlers import RotatingFileHandler
        
        os.makedirs('logs', exist_ok=True)
        
        file_handler = RotatingFileHandler(
            'logs/api.log',
            maxBytes=10240000,
            backupCount=10
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(getattr(logging, LOG_LEVEL))
        app.logger.info('API startup')
    
    return app

def main():
    """Função principal para executar o servidor"""
    app = create_app()
    
    print(f"\n🚀 Servidor API iniciando na porta {API_CONFIG['port']}")
    print(f"   Modo: {'Desenvolvimento' if DEBUG else 'Produção'}")
    print(f"   URL: http://localhost:{API_CONFIG['port']}")
    print(f"\n📍 Endpoints principais:")
    print(f"   POST /api/query - Executa queries")
    print(f"   GET  /api/debug/filters - Debug de filtros")
    print(f"   GET  /componentes/<path> - Serve componentes")
    print(f"\n✨ Servidor pronto!\n")
    
    app.run(
        host='0.0.0.0',
        port=API_CONFIG['port'],
        debug=DEBUG,
        threaded=True
    )

if __name__ == '__main__':
    main()
