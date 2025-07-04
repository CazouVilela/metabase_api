// data-loader.js - Versão Otimizada (Native Only)
// Usa apenas o método Native Performance

class DataLoader {
  constructor() {
    console.log('[DataLoader] Inicializando (Native Performance)...');
    this.baseUrl = this.getBaseUrl();
    this.isLoading = false;
    this.abortController = null;
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutos
  }

  getBaseUrl() {
    const path = window.location.pathname;
    const basePath = path.split('/componentes')[0];
    return basePath || '';
  }

  /**
   * Carrega dados usando APENAS o método Native
   */
  async loadData(questionId, filtros) {
    console.log('[DataLoader] loadData (Native):', questionId, filtros);
    
    if (this.isLoading) {
      console.warn('[DataLoader] Já está carregando');
      return null;
    }

    this.isLoading = true;

    try {
      // SEMPRE usa endpoint native/query
      const url = this.buildUrl(questionId, filtros);
      console.log('[DataLoader] URL Native:', url);

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
      return this.processNativeResponse(nativeData);

    } catch (error) {
      console.error('[DataLoader] Erro:', error);
      throw error;
      
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Processa resposta no formato nativo do Metabase
   */
  processNativeResponse(nativeData) {
    // Se tem o formato nativo (colunar)
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
    
    // Se já for array de objetos, retorna direto
    if (Array.isArray(nativeData)) {
      return nativeData;
    }
    
    console.error('[DataLoader] Formato de resposta inesperado:', nativeData);
    return [];
  }

  /**
   * Constrói URL - SEMPRE para endpoint native
   */
  buildUrl(questionId, filtros) {
    // SEMPRE usa /api/query (que agora é native)
    const apiEndpoint = '/api/query';
    
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

  /**
   * Carrega com retry
   */
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

  /**
   * Obtém dados do cache
   */
  getFromCache(url) {
    const cached = this.cache.get(url);
    
    if (cached) {
      const age = Date.now() - cached.timestamp;
      
      if (age < this.cacheTimeout) {
        console.log('📦 Dados do cache');
        return cached.data;
      }
      
      this.cache.delete(url);
    }
    
    return null;
  }

  /**
   * Adiciona ao cache
   */
  addToCache(url, data) {
    if (this.cache.size > 10) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    this.cache.set(url, {
      data,
      timestamp: Date.now()
    });
  }

  /**
   * Estatísticas
   */
  getStats() {
    return {
      isLoading: this.isLoading,
      baseUrl: this.baseUrl,
      cacheSize: this.cache.size,
      method: 'native-performance'
    };
  }

  /**
   * Limpa cache
   */
  clearCache() {
    this.cache.clear();
    console.log('[DataLoader] Cache limpo');
  }
}

// Cria instância global
console.log('[DataLoader] Criando instância global (Native)...');
const dataLoader = new DataLoader();
console.log('[DataLoader] ✅ Pronto para usar com Native Performance');
