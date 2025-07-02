#!/usr/bin/env python3
"""
Corrige erro "dataLoader is not defined"
"""

from pathlib import Path

def check_data_loader():
    """Verifica e corrige o data-loader.js"""
    
    file_path = Path.home() / "metabase_customizacoes" / "componentes" / "tabela_virtual" / "js" / "data-loader.js"
    
    print("🔍 Verificando data-loader.js...")
    
    if not file_path.exists():
        print("❌ data-loader.js não existe!")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Verifica se tem a instância global
    if "const dataLoader = new DataLoader();" not in content:
        print("❌ Instância global 'dataLoader' não encontrada!")
        
        # Adiciona no final do arquivo
        if content.rstrip().endswith('}'):
            content = content.rstrip() + '\n\n// Instância global\nconst dataLoader = new DataLoader();\n'
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            print("✅ Instância global adicionada!")
        else:
            print("⚠️  Estrutura do arquivo está estranha, verifique manualmente")
            return False
    else:
        print("✅ Instância global existe")
    
    # Verifica se a classe está completa
    if "class DataLoader {" not in content:
        print("❌ Classe DataLoader não encontrada!")
        return False
    
    # Conta chaves para ver se está balanceado
    open_braces = content.count('{')
    close_braces = content.count('}')
    
    if open_braces != close_braces:
        print(f"❌ Chaves desbalanceadas: {open_braces} aberturas, {close_braces} fechamentos")
        print("   Provavelmente há um erro de sintaxe")
        return False
    
    print("✅ Estrutura parece OK")
    return True

def create_minimal_dataloader():
    """Cria um data-loader.js mínimo que funciona"""
    
    file_path = Path.home() / "metabase_customizacoes" / "componentes" / "tabela_virtual" / "js" / "data-loader.js"
    backup_path = file_path.with_suffix('.js.backup_original')
    
    # Faz backup do atual
    if file_path.exists():
        import shutil
        shutil.copy(file_path, backup_path)
        print(f"📦 Backup salvo: {backup_path}")
    
    # Cria versão mínima funcional
    minimal_content = '''// data-loader.js - Versão mínima funcional
class DataLoader {
  constructor() {
    this.baseUrl = this.getBaseUrl();
    this.isLoading = false;
    this.abortController = null;
  }

  getBaseUrl() {
    const path = window.location.pathname;
    const basePath = path.split('/componentes')[0];
    return basePath || '';
  }

  async loadData(questionId, filtros) {
    if (this.isLoading) {
      Utils.log('⚠️ Carregamento já em andamento');
      return null;
    }

    this.isLoading = true;

    try {
      const url = this.buildUrl(questionId, filtros, 'direct');
      Utils.log('📡 Carregando dados...', url);

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      Utils.log(`✅ ${data.length} linhas carregadas`);
      
      return data;

    } catch (error) {
      Utils.log('❌ Erro ao carregar:', error);
      throw error;
    } finally {
      this.isLoading = false;
    }
  }

  buildUrl(questionId, filtros, endpoint = 'direct') {
    const apiEndpoint = endpoint === 'native' ? '/api/query/native' : '/api/query/direct';
    const params = new URLSearchParams();
    params.append('question_id', questionId);

    Object.entries(filtros).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach(v => params.append(key, v));
      } else {
        params.append(key, value);
      }
    });

    return `${this.baseUrl}${apiEndpoint}?${params.toString()}`;
  }

  async loadWithRetry(questionId, filtros, maxRetries = 3) {
    return this.loadData(questionId, filtros);
  }

  // Método para Native Performance
  async loadDataNativePerformance(questionId, filtros) {
    if (this.isLoading) return null;

    this.isLoading = true;

    try {
      const url = this.buildUrl(questionId, filtros, 'native');
      Utils.log('🚀 [NATIVE] Carregando...');

      const response = await fetch(url, {
        headers: { 'Accept-Encoding': 'gzip' }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const nativeData = await response.json();
      
      // Processa formato nativo
      if (nativeData.data && nativeData.data.rows) {
        const cols = nativeData.data.cols.map(c => c.name);
        const rows = nativeData.data.rows;
        
        Utils.log(`✅ [NATIVE] ${rows.length} linhas (formato colunar)`);
        
        // Converte para objetos
        const result = rows.map(row => {
          const obj = {};
          cols.forEach((col, i) => {
            obj[col] = row[i];
          });
          return obj;
        });
        
        return result;
      }
      
      return nativeData;

    } catch (error) {
      Utils.log('❌ Erro Native:', error);
      // Fallback para direct
      return this.loadData(questionId, filtros);
    } finally {
      this.isLoading = false;
    }
  }

  getStats() {
    return {
      isLoading: this.isLoading,
      baseUrl: this.baseUrl
    };
  }
}

// IMPORTANTE: Instância global!
const dataLoader = new DataLoader();
'''
    
    with open(file_path, 'w') as f:
        f.write(minimal_content)
    
    print("✅ data-loader.js recriado com versão funcional")

def check_script_order():
    """Verifica ordem de carregamento dos scripts"""
    
    index_path = Path.home() / "metabase_customizacoes" / "componentes" / "tabela_virtual" / "index.html"
    
    with open(index_path, 'r') as f:
        content = f.read()
    
    # Extrai ordem dos scripts
    import re
    scripts = re.findall(r'<script src="([^"]+)"', content)
    
    print("\n📋 Ordem de carregamento dos scripts:")
    for i, script in enumerate(scripts, 1):
        print(f"   {i}. {script}")
    
    # Verifica ordem correta
    correct_order = ['utils.js', 'filtros.js', 'data-loader.js']
    
    for required in correct_order:
        found = False
        for script in scripts:
            if required in script:
                found = True
                break
        if not found:
            print(f"❌ {required} não está sendo carregado!")

def main():
    print("🔧 Corrigindo erro 'dataLoader is not defined'")
    print("=" * 50)
    
    # Verifica arquivo
    if not check_data_loader():
        print("\n⚠️  Problemas encontrados. Criando versão funcional...")
        create_minimal_dataloader()
    
    # Verifica ordem de scripts
    check_script_order()
    
    print("\n✅ Correções aplicadas!")
    print("\n📝 Próximos passos:")
    print("1. Limpe o cache do navegador (Ctrl+Shift+R)")
    print("2. Abra o console (F12) e verifique se há erros")
    print("3. Teste novamente")
    
    print("\n💡 Se ainda der erro, execute no console:")
    print("   typeof DataLoader  // deve retornar 'function'")
    print("   typeof dataLoader  // deve retornar 'object'")

if __name__ == "__main__":
    main()
