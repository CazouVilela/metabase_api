// data-loader.js - Versão funcional garantida
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
