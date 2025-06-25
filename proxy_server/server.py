# proxy_server/server.py
"""
Servidor proxy principal - apenas funcionalidades de proxy
"""

from flask import Flask
from flask_cors import CORS
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .config import PROXY_PORT
from .routes import register_routes

def create_app():
    """Cria e configura a aplicação Flask"""
    app = Flask(__name__)
    
    # Habilita CORS
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Registra as rotas
    register_routes(app)
    
    return app

def main():
    """Função principal para executar o servidor"""
    app = create_app()
    
    print(f"\n🚀 Servidor proxy iniciando na porta {PROXY_PORT}")
    print(f"   Acesse: http://localhost:{PROXY_PORT}")
    print(f"   Modo: Desenvolvimento")
    print(f"   CORS: Habilitado")
    print(f"\n📍 Endpoints disponíveis:")
    print(f"   GET  /api/query")
    print(f"   GET  /api/question/<id>/info")
    print(f"   GET  /componentes/<path>")
    print(f"   GET  /static/<path>")
    print(f"   GET  /health")
    print(f"\n✨ Servidor pronto!\n")
    
    app.run(
        host='0.0.0.0',
        port=PROXY_PORT,
        debug=True,
        threaded=True
    )

if __name__ == '__main__':
    main()
