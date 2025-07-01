#!/usr/bin/env python3
"""
Corrige as rotas do Flask imediatamente
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def fix_routes_file():
    """Atualiza o arquivo routes.py com as correções"""
    print("🔧 Atualizando arquivo de rotas...")
    
    routes_file = Path.home() / "metabase_customizacoes" / "proxy_server" / "routes.py"
    
    # Lê o arquivo atual
    with open(routes_file, 'r') as f:
        content = f.read()
    
    # Backup
    backup_file = routes_file.with_suffix('.py.backup_working')
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"✓ Backup salvo em: {backup_file}")
    
    # Procura onde inserir a nova rota
    # Vamos procurar a linha que tem "# ------- ROTAS DE ARQUIVOS ESTÁTICOS -------"
    lines = content.split('\n')
    insert_index = -1
    
    for i, line in enumerate(lines):
        if "ROTAS DE ARQUIVOS ESTÁTICOS" in line:
            insert_index = i + 1
            break
    
    if insert_index == -1:
        # Se não encontrou, procura onde está @app.route('/componentes/<path:subpath>')
        for i, line in enumerate(lines):
            if "@app.route('/componentes/<path:subpath>')" in line:
                insert_index = i
                break
    
    if insert_index == -1:
        print("❌ Não consegui encontrar onde inserir as rotas!")
        return False
    
    # Código da nova rota
    new_route = '''    
    # Rota específica para componentes com barra final (serve index.html)
    @app.route('/componentes/<componente>/')
    def serve_componente_index(componente):
        """Serve index.html quando acessar só o diretório do componente com barra final"""
        componente_dir = os.path.join(COMPONENTES_DIR, componente)
        if os.path.exists(componente_dir):
            index_file = os.path.join(componente_dir, 'index.html')
            if os.path.exists(index_file):
                return send_from_directory(componente_dir, 'index.html')
        return jsonify({'error': 'Componente não encontrado'}), 404
'''
    
    # Verifica se a rota já existe
    if "serve_componente_index" not in content:
        # Insere a nova rota
        lines.insert(insert_index, new_route)
        new_content = '\n'.join(lines)
        
        # Salva o arquivo
        with open(routes_file, 'w') as f:
            f.write(new_content)
        
        print("✓ Rota adicionada ao arquivo routes.py")
    else:
        print("⚠️  Rota já existe no arquivo")
    
    # Também vamos melhorar a rota serve_componente existente
    # Procura a função serve_componente
    for i, line in enumerate(lines):
        if "def serve_componente(subpath):" in line:
            # Substitui o conteúdo da função
            # Encontra onde termina a função
            func_start = i
            func_end = i
            indent_count = len(line) - len(line.lstrip())
            
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].startswith(' ' * (indent_count + 1)):
                    func_end = j
                    break
            
            # Nova implementação da função
            improved_function = '''    def serve_componente(subpath):
        """Serve arquivos dos componentes"""
        # Remove query string se houver
        clean_path = subpath.split('?')[0]
        
        # Se termina com /, remove para consistência
        if clean_path.endswith('/'):
            clean_path = clean_path[:-1]
        
        path_parts = clean_path.split('/')
        
        if len(path_parts) >= 1:
            componente = path_parts[0]
            componente_dir = os.path.join(COMPONENTES_DIR, componente)
            
            if os.path.exists(componente_dir):
                if len(path_parts) > 1:
                    # Arquivo específico requisitado
                    arquivo = '/'.join(path_parts[1:])
                    file_path = os.path.join(componente_dir, arquivo)
                    
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        return send_from_directory(componente_dir, arquivo)
                else:
                    # Apenas o componente foi requisitado, serve index.html
                    index_file = os.path.join(componente_dir, 'index.html')
                    if os.path.exists(index_file):
                        return send_from_directory(componente_dir, 'index.html')
        
        return jsonify({'error': 'Arquivo não encontrado', 'path': subpath}), 404'''
            
            # Substitui a função
            lines[func_start:func_end] = improved_function.split('\n')
            
            # Salva novamente
            new_content = '\n'.join(lines)
            with open(routes_file, 'w') as f:
                f.write(new_content)
            
            print("✓ Função serve_componente melhorada")
            break
    
    return True

def restart_flask_server():
    """Reinicia o servidor Flask"""
    print("\n🔄 Reiniciando servidor Flask...")
    
    # Para todos os processos Flask
    subprocess.run(["pkill", "-f", "python.*proxy_server"], capture_output=True)
    subprocess.run(["pkill", "-f", "python.*server.py"], capture_output=True)
    time.sleep(2)
    
    # Muda para o diretório do projeto
    os.chdir(Path.home() / "metabase_customizacoes")
    
    # Inicia o servidor
    process = subprocess.Popen(
        [sys.executable, "-m", "proxy_server.server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    print("⏳ Aguardando servidor iniciar...")
    
    # Aguarda e captura output inicial
    start_time = time.time()
    while time.time() - start_time < 5:
        line = process.stdout.readline()
        if line:
            print(f"   {line.strip()}")
            if "Running on" in line or "Servidor pronto" in line:
                break
        time.sleep(0.1)
    
    time.sleep(2)
    return True

def test_routes():
    """Testa se as rotas estão funcionando"""
    print("\n🧪 Testando rotas...")
    
    import requests
    
    tests = [
        ("http://localhost:3500/health", "Health check"),
        ("http://localhost:3500/componentes/tabela_virtual/", "Componente com /"),
        ("http://localhost:3500/componentes/tabela_virtual", "Componente sem /"),
        ("http://localhost:3500/componentes/tabela_virtual/index.html", "index.html direto"),
    ]
    
    all_passed = True
    
    for url, name in tests:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"✅ {name}: OK")
            else:
                print(f"❌ {name}: {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"❌ {name}: Erro - {str(e)}")
            all_passed = False
    
    return all_passed

def main():
    print("🚀 Correção Imediata das Rotas do Flask\n")
    
    # 1. Corrige o arquivo
    if not fix_routes_file():
        print("❌ Falha ao corrigir arquivo de rotas")
        return
    
    # 2. Reinicia o servidor
    if not restart_flask_server():
        print("❌ Falha ao reiniciar servidor")
        return
    
    # 3. Testa
    print("\nAguardando servidor estabilizar...")
    time.sleep(2)
    
    if test_routes():
        print("\n✨ Sucesso! Todas as rotas estão funcionando!")
        print("\n📌 URLs para usar:")
        print("   Local: http://localhost:8080/metabase_customizacoes/componentes/tabela_virtual/?question_id=51")
        
        # Tenta obter URL do ngrok
        try:
            import requests
            response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get('tunnels'):
                    public_url = data['tunnels'][0]['public_url']
                    print(f"   Público: {public_url}/metabase_customizacoes/componentes/tabela_virtual/?question_id=51")
        except:
            pass
    else:
        print("\n⚠️  Algumas rotas ainda estão com problema")
        print("Verifique os logs para mais detalhes")

if __name__ == "__main__":
    main()
