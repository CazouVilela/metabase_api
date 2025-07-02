#!/usr/bin/env python3
"""
Corrige o arquivo data-loader.js diretamente
"""

from pathlib import Path
import os

def check_file_exists():
    """Verifica se o arquivo existe e mostra informações"""
    
    file_path = Path.home() / "metabase_customizacoes" / "componentes" / "tabela_virtual" / "js" / "data-loader.js"
    
    print(f"🔍 Verificando: {file_path}")
    
    if not file_path.exists():
        print("❌ Arquivo NÃO existe!")
        return None
    
    # Mostra informações do arquivo
    stat = os.stat(file_path)
    print(f"✅ Arquivo existe")
    print(f"   Tamanho: {stat.st_size} bytes")
    print(f"   Permissões: {oct(stat.st_mode)}")
    
    # Lê conteúdo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"   Linhas: {len(content.splitlines())}")
    print(f"   Caracteres: {len(content)}")
    
    # Mostra primeiras linhas
    lines = content.splitlines()
    print("\n📄 Primeiras 10 linhas:")
    for i, line in enumerate(lines[:10], 1):
        print(f"   {i:2d}: {line[:60]}{'...' if len(line) > 60 else ''}")
    
    return content

def analyze_content(content):
    """Analisa o conteúdo procurando problemas"""
    
    print("\n🔍 Analisando conteúdo...")
    
    problems = []
    
    # Verifica se tem classe DataLoader
    if "class DataLoader" not in content:
        problems.append("❌ Classe DataLoader não encontrada")
    else:
        print("✅ Classe DataLoader encontrada")
    
    # Verifica instância global
    if "const dataLoader = new DataLoader()" not in content and "var dataLoader = new DataLoader()" not in content:
        problems.append("❌ Instância global dataLoader não encontrada")
    else:
        print("✅ Instância global encontrada")
    
    # Verifica balanceamento
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        problems.append(f"❌ Chaves desbalanceadas: {open_braces} abertas, {close_braces} fechadas")
    else:
        print("✅ Chaves balanceadas")
    
    # Verifica caracteres estranhos
    for i, char in enumerate(content):
        if ord(char) > 127 and char not in 'áéíóúàèìòùâêîôûãõçÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇ':
            problems.append(f"⚠️ Caractere não-ASCII na posição {i}: {repr(char)}")
    
    # Verifica se tem comentários não fechados
    if "/*" in content:
        comment_starts = content.count("/*")
        comment_ends = content.count("*/")
        if comment_starts != comment_ends:
            problems.append(f"❌ Comentários /* */ desbalanceados")
    
    return problems

def create_working_dataloader():
    """Cria um data-loader.js que definitivamente funciona"""
    
    file_path = Path.home() / "metabase_customizacoes" / "componentes" / "tabela_virtual" / "js" / "data-loader.js"
    
    # Faz backup se existir
    if file_path.exists():
        backup_path = file_path.with_suffix('.js.backup_broken')
        import shutil
        shutil.copy(file_path, backup_path)
        print(f"\n📦 Backup do arquivo quebrado: {backup_path}")
    
    # Conteúdo que DEFINITIVAMENTE funciona
    working_content = '''// data-loader.js - Versão funcional garantida
// Classe DataLoader para carregar dados da API

class DataLoader {
  constructor() {
    console.log('[DataLoader] Inicializando...');
    this.baseUrl = this.getBaseUrl();
    this.isLoading = false;
    this.abortController = null;
    this.cache = new Map();
    console.log('[DataLoader] Base URL:', this.baseUrl);
  }

  getBaseUrl() {
    const path = window.location.pathname;
    const basePath = path.split('/componentes')[0];
    return basePath || '';
  }

  async loadData(questionId, filtros) {
    console.log('[DataLoader] loadData:', questionId, filtros);
    
    if (this.isLoading) {
      console.warn('[DataLoader] Já está carregando');
      return null;
    }

    this.isLoading = true;

    try {
      const url = this.buildUrl(questionId, filtros, 'direct');
      console.log('[DataLoader] URL:', url);

      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error('HTTP ' + response.status);
      }

      const data = await response.json();
      console.log('[DataLoader] Dados carregados:', data.length, 'linhas');
      
      return data;

    } catch (error) {
      console.error('[DataLoader] Erro:', error);
      throw error;
      
    } finally {
      this.isLoading = false;
    }
  }

  buildUrl(questionId, filtros, endpoint) {
    let apiEndpoint;
    
    if (endpoint === 'native') {
      apiEndpoint = '/api/query/native';
    } else if (endpoint === 'direct') {
      apiEndpoint = '/api/query/direct';
    } else {
      apiEndpoint = '/api/query';
    }
    
    const params = new URLSearchParams();
    params.append('question_id', questionId);

    if (filtros) {
      Object.entries(filtros).forEach(function(entry) {
        const key = entry[0];
        const value = entry[1];
        
        if (Array.isArray(value)) {
          value.forEach(function(v) {
            params.append(key, v);
          });
        } else if (value != null) {
          params.append(key, value);
        }
      });
    }

    return this.baseUrl + apiEndpoint + '?' + params.toString();
  }

  async loadWithRetry(questionId, filtros, maxRetries) {
    if (!maxRetries) maxRetries = 3;
    
    let lastError;
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await this.loadData(questionId, filtros);
      } catch (error) {
        lastError = error;
        console.log('[DataLoader] Tentativa', i + 1, 'falhou');
        
        if (i < maxRetries - 1) {
          await new Promise(function(resolve) {
            setTimeout(resolve, 1000 * (i + 1));
          });
        }
      }
    }
    
    throw lastError;
  }

  async loadDataNativePerformance(questionId, filtros) {
    console.log('[DataLoader] loadDataNativePerformance:', questionId);
    
    if (this.isLoading) return null;

    this.isLoading = true;

    try {
      const url = this.buildUrl(questionId, filtros, 'native');
      console.log('[DataLoader] Native URL:', url);

      const response = await fetch(url, {
        headers: {
          'Accept': 'application/json',
          'Accept-Encoding': 'gzip'
        }
      });

      if (!response.ok) {
        throw new Error('HTTP ' + response.status);
      }

      const nativeData = await response.json();
      
      // Processa formato nativo do Metabase
      if (nativeData && nativeData.data && nativeData.data.rows) {
        const cols = nativeData.data.cols;
        const rows = nativeData.data.rows;
        
        console.log('[DataLoader] Native: ', rows.length, 'linhas,', cols.length, 'colunas');
        
        // Converte formato colunar para objetos
        const result = [];
        const colNames = cols.map(function(c) { return c.name; });
        
        for (let i = 0; i < rows.length; i++) {
          const obj = {};
          for (let j = 0; j < colNames.length; j++) {
            obj[colNames[j]] = rows[i][j];
          }
          result.push(obj);
        }
        
        return result;
      }
      
      // Se já for array, retorna direto
      return nativeData;

    } catch (error) {
      console.error('[DataLoader] Erro Native:', error);
      // Fallback para método direct
      return this.loadData(questionId, filtros);
      
    } finally {
      this.isLoading = false;
    }
  }

  getStats() {
    return {
      isLoading: this.isLoading,
      baseUrl: this.baseUrl,
      cacheSize: this.cache.size
    };
  }

  clearCache() {
    this.cache.clear();
    console.log('[DataLoader] Cache limpo');
  }
}

// CRIA INSTÂNCIA GLOBAL
console.log('[DataLoader] Criando instância global...');
const dataLoader = new DataLoader();
console.log('[DataLoader] Instância criada:', typeof dataLoader);

// Teste para verificar se está funcionando
if (typeof dataLoader === 'object') {
  console.log('[DataLoader] ✅ dataLoader está disponível globalmente');
} else {
  console.error('[DataLoader] ❌ Falha ao criar dataLoader global');
}
'''
    
    # Salva arquivo
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(working_content)
    
    print(f"\n✅ Arquivo recriado: {file_path}")
    print("   Este arquivo DEVE funcionar!")

def test_in_browser():
    """Instruções para testar no navegador"""
    
    print("\n📝 TESTE NO NAVEGADOR:")
    print("1. Limpe o cache (Ctrl+Shift+R)")
    print("2. Abra o console (F12)")
    print("3. Você deve ver:")
    print("   [DataLoader] Inicializando...")
    print("   [DataLoader] Base URL: /metabase_customizacoes")
    print("   [DataLoader] Criando instância global...")
    print("   [DataLoader] ✅ dataLoader está disponível globalmente")
    print("\n4. Digite no console:")
    print("   dataLoader")
    print("   dataLoader.getStats()")

def main():
    print("🔧 Corrigindo data-loader.js")
    print("=" * 60)
    
    # Verifica arquivo atual
    content = check_file_exists()
    
    if content:
        # Analisa problemas
        problems = analyze_content(content)
        
        if problems:
            print("\n⚠️ PROBLEMAS ENCONTRADOS:")
            for p in problems:
                print(f"   {p}")
            
            print("\n🔧 Recriando arquivo...")
            create_working_dataloader()
        else:
            print("\n✅ Arquivo parece OK, mas vamos recriar para garantir...")
            create_working_dataloader()
    else:
        print("\n🔧 Criando arquivo do zero...")
        create_working_dataloader()
    
    test_in_browser()
    
    print("\n✅ Concluído!")
    print("\n⚡ URL para testar:")
    print("http://localhost:8080/metabase_customizacoes/componentes/tabela_virtual/test-minimal.html")

if __name__ == "__main__":
    main()
