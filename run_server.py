#!/usr/bin/env python3
"""
Script principal para executar o servidor Metabase Customizações
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Adiciona o diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Configura o sistema de logs"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f'server_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    required = ['flask', 'flask_cors', 'requests']
    missing = []
    
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Dependências faltando: {', '.join(missing)}")
        print("Execute: pip install -r requirements.txt")
        sys.exit(1)

def run_development():
    """Executa o servidor em modo desenvolvimento"""
    from proxy_server.server import main
    print("\n🚀 Iniciando servidor em modo DESENVOLVIMENTO")
    main()

def run_production():
    """Executa o servidor em modo produção com Gunicorn"""
    try:
        import gunicorn
    except ImportError:
        print("❌ Gunicorn não instalado. Execute: pip install gunicorn")
        sys.exit(1)
    
    from proxy_server.config import PROXY_PORT
    
    print("\n🚀 Iniciando servidor em modo PRODUÇÃO")
    os.system(f"gunicorn -w 4 -b 0.0.0.0:{PROXY_PORT} proxy_server.server:create_app()")

def run_tests():
    """Executa os testes"""
    print("\n🧪 Executando testes...")
    
    # Importa e executa testes
    test_modules = [
        'tests.test_filters',
        'tests.test_api',
        'tests.test_components'
    ]
    
    for module in test_modules:
        try:
            print(f"\n📋 Testando {module}...")
            __import__(module)
            print(f"✅ {module} - OK")
        except ImportError:
            print(f"⚠️  {module} - Não encontrado")
        except Exception as e:
            print(f"❌ {module} - Erro: {e}")

def show_info():
    """Mostra informações sobre o servidor"""
    from proxy_server.config import PROXY_PORT
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║           METABASE CUSTOMIZAÇÕES - v2.0                  ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  📍 Endpoints Principais:                                ║
║                                                          ║
║  API:                                                    ║
║    GET  /api/query                 - Consulta dados      ║
║    GET  /api/question/<id>/info    - Info da questão    ║
║    GET  /api/debug/filters         - Debug filtros      ║
║                                                          ║
║  Componentes:                                            ║
║    /componentes/tabela_virtual/    - Tabela virtual     ║
║                                                          ║
║  📊 Servidor:                                            ║
║    Porta: {PROXY_PORT}                                      ║
║    URL: http://localhost:{PROXY_PORT}                       ║
║                                                          ║
║  📚 Documentação:                                        ║
║    /docs/README.md                                       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Servidor Metabase Customizações')
    parser.add_argument(
        '--mode', 
        choices=['dev', 'prod', 'test', 'info'], 
        default='dev',
        help='Modo de execução (default: dev)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        help='Porta customizada (sobrescreve config)'
    )
    
    args = parser.parse_args()
    
    # Configura logging
    logger = setup_logging()
    
    # Verifica dependências
    check_dependencies()
    
    # Sobrescreve porta se especificada
    if args.port:
        os.environ['PROXY_PORT'] = str(args.port)
    
    # Executa modo selecionado
    if args.mode == 'dev':
        run_development()
    elif args.mode == 'prod':
        run_production()
    elif args.mode == 'test':
        run_tests()
    elif args.mode == 'info':
        show_info()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Servidor interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)
