// componentes/recursos_compartilhados/js/api-client.js
/**
 * Cliente API compartilhado para comunicação com backend
 */

class MetabaseAPIClient {
  constructor() {
    this.baseUrl = this.detectBaseUrl();
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutos
    this.defaultTimeout = 5 * 60 * 1000; // 5 minutos para requests
    
    console.log(`📡 API Client inicializado: ${this.baseUrl}`);
  }
  
  /**
   * Detecta URL base automaticamente
   */
  detectBaseUrl() {
    const path = window.location.pathname;
    
    // Se estiver em /metabase_customizacoes/componentes/...
    const basePath = path.split('/componentes')[0];
    
    // Se não encontrar, usa vazio (relativo)
    return basePath || '';
  }
  
  /**
   * Busca dados de uma pergunta com filtros
   * @param {string|number} questionId - ID da pergunta
   * @param {Object} filters - Filtros a aplicar
   * @returns {Promise<Object>} Dados da resposta
   */
  async queryData(questionId, filters = {}) {
    const cacheKey = this.getCacheKey(questionId, filters);
    
    // Verifica cache
    const cached = this.getFromCache(cacheKey);
    if (cached) {
      console.log('📦 Dados retornados do cache');
      return cached;
    }
    
    try {
      const url = this.buildUrl('/api/query', {
        question_id: questionId,
        ...filters
      });
      
      console.log(`🔄 Requisição para: ${url}`);
      
      const response = await this.fetchWithTimeout(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Accept-Encoding': 'gzip'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Adiciona ao cache
      this.addToCache(cacheKey, data);
      
      return data;
      
    } catch (error) {
      console.error('❌ Erro na requisição:', error);
      throw error;
    }
  }
  
  /**
   * Busca informações de uma pergunta
   * @param {string|number} questionId - ID da pergunta
   * @returns {Promise<Object>} Metadados da pergunta
   */
  async getQuestionInfo(questionId) {
    try {
      const url = this.buildUrl(`/api/question/${questionId}/info`);
      
      const response = await this.fetchWithTimeout(url);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      return await response.json();
      
    } catch (error) {
      console.error('❌ Erro ao buscar info da pergunta:', error);
      throw error;
    }
  }
  
  /**
   * Fetch com timeout
   * @private
   */
  async fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const timeout = options.timeout || this.defaultTimeout;
    
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, timeout);
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      return response;
      
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new Error(`Timeout após ${timeout/1000}s`);
      }
      
      throw error;
    }
  }
  
  /**
   * Constrói URL com parâmetros
   * @private
   */
  buildUrl(endpoint, params = {}) {
    const url = new URL(this.baseUrl + endpoint, window.location.origin);
    
    // Adiciona parâmetros
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        if (Array.isArray(value)) {
          // Para arrays, adiciona múltiplas vezes o mesmo parâmetro
          value.forEach(v => {
            url.searchParams.append(key, v);
          });
        } else {
          url.searchParams.append(key, value);
        }
      }
    });
    
    return url.toString();
  }
  
  /**
   * Gera chave de cache
   * @private
   */
  getCacheKey(questionId, filters) {
    const filterStr = JSON.stringify(filters);
    return `q${questionId}:${filterStr}`;
  }
  
  /**
   * Obtém dados do cache
   * @private
   */
  getFromCache(key) {
    const cached = this.cache.get(key);
    
    if (cached) {
      const age = Date.now() - cached.timestamp;
      
      if (age < this.cacheTimeout) {
        return cached.data;
      }
      
      // Cache expirado
      this.cache.delete(key);
    }
    
    return null;
  }
  
  /**
   * Adiciona ao cache
   * @private
   */
  addToCache(key, data) {
    // Limita tamanho do cache
    if (this.cache.size > 20) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
  
  /**
   * Limpa o cache
   */
  clearCache() {
    this.cache.clear();
    console.log('🗑️ Cache limpo');
  }
  
  /**
   * Obtém estatísticas do cache
   */
  getCacheStats() {
    return {
      size: this.cache.size,
      entries: Array.from(this.cache.keys())
    };
  }
  
  /**
   * Executa query SQL nativa (se suportado pelo backend)
   * @param {string} sql - Query SQL
   * @param {Object} params - Parâmetros
   * @returns {Promise<Object>} Resultado
   */
  async executeNativeQuery(sql, params = {}) {
    try {
      const response = await this.fetchWithTimeout(
        this.buildUrl('/api/native/query'),
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ sql, params })
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      return await response.json();
      
    } catch (error) {
      console.error('❌ Erro na query nativa:', error);
      throw error;
    }
  }
}

// Exporta para diferentes ambientes
if (typeof module !== 'undefined' && module.exports) {
  module.exports = MetabaseAPIClient;
} else if (typeof define === 'function' && define.amd) {
  define([], function() { return MetabaseAPIClient; });
} else {
  window.MetabaseAPIClient = MetabaseAPIClient;
}
