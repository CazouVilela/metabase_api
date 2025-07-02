#!/usr/bin/env python3
"""
Corrige o frontend para processar corretamente a resposta Native Performance
"""

import os
from pathlib import Path
import shutil

def check_columnar_processor():
    """Verifica se columnar-data-processor.js existe"""
    file_path = Path.home() / "metabase_customizacoes" / "componentes" / "tabela_virtual" / "js" / "columnar-data-processor.js"
    
    if not file_path.exists():
        print("❌ columnar-data-processor.js NÃO EXISTE!")
        print("   Você precisa criar este arquivo do artifact!")
        return False
    
    print("✅ columnar-data-processor.js existe")
    return True

def fix_index_html():
    """Corrige ordem de carregamento no index.html"""
    index_path = Path.home() / "metabase_customizacoes" / "componentes" / "tabela_virtual" / "index.html"
    
    with open(index_path, 'r') as f:
        content = f.read()
    
    # Verifica se columnar-data-processor.js está incluído
    if 'columnar-data-processor.js' not in content:
        print("⚠️ columnar-data-processor.js não está no index.html")
        
        # Adiciona antes do data-loader.js
        old_line = '  <script src="js/data-loader.js"></script>'
        new_lines = '''  <script src="js/columnar-data-processor.js"></script>
  <script src="js/data-loader.js"></script>'''
        
        content = content.replace(old_line, new_lines)
        
        with open(index_path, 'w') as f:
            f.write(content)
        
        print("✅ index.html atualizado")
    else:
        print("✅ columnar-data-processor.js já está no index.html")

def fix_data_loader():
    """Adiciona suporte correto para Native Performance no data-loader.js"""
    loader_path = Path.home() / "metabase_customizacoes" / "componentes" / "tabela_virtual" / "js" / "data-loader.js"
    
    # Faz backup
    backup_path = loader_path.with_suffix('.js.backup_native')
    shutil.copy(loader_path, backup_path)
    print(f"📦 Backup salvo: {backup_path}")
    
    with open(loader_path, 'r') as f:
        content = f.read()
    
    # Verifica se já tem o método correto
    if "loadDataNativePerformance" not in content:
        print("⚠️ Adicionando método loadDataNativePerformance...")
        
        # Adiciona o método antes do fechamento da classe
        method_code = '''
  /**
   * Carrega dados usando API com performance nativa do Metabase
   * SEM CHUNKS, SEM STREAMING - Tudo de uma vez, otimizado
   */
  async loadDataNativePerformance(questionId, filtros) {
    if (this.isLoading) {
      Utils.log('⚠️ Carregamento já em andamento');
      return null;
    }

    if (this.abortController) {
      this.abortController.abort();
    }

    this.isLoading = true;
    this.abortController = new AbortController();

    try {
      const url = this.buildUrl(questionId, filtros, 'native');
      
      const startTime = performance.now();
      Utils.log(`🚀 [NATIVE PERFORMANCE] Carregando como Metabase nativo...`);

      const response = await fetch(url, {
        signal: this.abortController.signal,
        headers: {
          'Accept': 'application/json',
          'Accept-Encoding': 'gzip'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Parse da resposta
      const nativeData = await response.json();
      const elapsed = Utils.getElapsedTime(startTime);

      // Processa formato nativo
      if (nativeData.data && nativeData.data.rows) {
        // Formato nativo do Metabase
        const cols = nativeData.data.cols;
        const rows = nativeData.data.rows;
        
        Utils.log(`✅ [NATIVE] ${rows.length:,} linhas em ${elapsed}s (formato colunar)`);
        
        // Converte para formato de objetos
        const columnNames = cols.map(col => col.name);
        const result = [];
        
        for (let i = 0; i < rows.length; i++) {
          const obj = {};
          for (let j = 0; j < columnNames.length; j++) {
            obj[columnNames[j]] = rows[i][j];
          }
          result.push(obj);
        }
        
        return result;
      }
      
      // Se já vier como array, retorna direto
      return nativeData;

    } catch (error) {
      if (error.name === 'AbortError') {
        Utils.log('🛑 Requisição cancelada');
        return null;
      }
      
      Utils.log('❌ Erro ao carregar (native):', error);
      throw error;
      
    } finally {
      this.isLoading = false;
      this.abortController = null;
    }
  }
'''
        
        # Encontra onde inserir (antes do fechamento da classe)
        insert_pos = content.rfind('\n}')
        if insert_pos > -1:
            content = content[:insert_pos] + method_code + content[insert_pos:]
            
            with open(loader_path, 'w') as f:
                f.write(content)
            
            print("✅ Método adicionado ao data-loader.js")
        else:
            print("❌ Não consegui encontrar onde inserir o método")

def create_test_page():
    """Cria página de teste simples"""
    test_path = Path.home() / "metabase_customizacoes" / "componentes" / "tabela_virtual" / "test.html"
    
    with open(test_path, 'w') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Teste Native Performance</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        button { padding: 10px 20px; margin: 5px; }
        #result { margin-top: 20px; }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>Teste Native Performance</h1>
    
    <button onclick="testNative()">Testar Native API</button>
    <button onclick="testDirect()">Testar Direct API</button>
    
    <div id="result"></div>
    
    <script>
        async function testNative() {
            const result = document.getElementById('result');
            result.innerHTML = 'Carregando Native...';
            
            const start = performance.now();
            
            try {
                const response = await fetch('/api/query/native?question_id=51');
                const data = await response.json();
                const elapsed = ((performance.now() - start) / 1000).toFixed(2);
                
                if (data.data && data.data.rows) {
                    result.innerHTML = `<div class="success">✅ Native: ${data.data.rows.length} linhas em ${elapsed}s</div>`;
                } else {
                    result.innerHTML = `<div class="error">❌ Formato inesperado</div>`;
                    console.log(data);
                }
            } catch (e) {
                result.innerHTML = `<div class="error">❌ Erro: ${e.message}</div>`;
            }
        }
        
        async function testDirect() {
            const result = document.getElementById('result');
            result.innerHTML = 'Carregando Direct...';
            
            const start = performance.now();
            
            try {
                const response = await fetch('/api/query/direct?question_id=51');
                const data = await response.json();
                const elapsed = ((performance.now() - start) / 1000).toFixed(2);
                
                result.innerHTML = `<div class="success">✅ Direct: ${data.length} linhas em ${elapsed}s</div>`;
            } catch (e) {
                result.innerHTML = `<div class="error">❌ Erro: ${e.message}</div>`;
            }
        }
    </script>
</body>
</html>""")
    
    print(f"✅ Página de teste criada: test.html")

def main():
    print("🔧 Corrigindo frontend para processar Native Performance")
    print("=" * 60)
    
    # Verifica se arquivo existe
    if not check_columnar_processor():
        print("\n⚠️ PRIMEIRO: Crie o arquivo columnar-data-processor.js do artifact!")
        return
    
    # Corrige arquivos
    fix_index_html()
    fix_data_loader()
    create_test_page()
    
    print("\n✅ Correções aplicadas!")
    print("\n📝 Próximos passos:")
    print("1. Reinicie o servidor: ./restart_server.sh")
    print("2. Limpe o cache do navegador (Ctrl+Shift+R)")
    print("3. Teste com a página de debug:")
    print("   http://localhost:8080/metabase_customizacoes/componentes/tabela_virtual/debug_native_response.html")
    print("\n4. Ou teste com a página simplificada:")
    print("   http://localhost:8080/metabase_customizacoes/componentes/tabela_virtual/test.html")

if __name__ == "__main__":
    main()
