// componentes/recursos_compartilhados/js/api-client.js
/**
 * Cliente API unificado para comunicação com backend
 */

class MetabaseAPIClient {
  constructor() {
    this.baseUrl = window.location.origin + '/metabase_customizacoes';
    this.cache = new Map();
    this.cacheTimeout = 300000; // 5 minutos
    
    // Estatísticas
    this.stats = {
      requests: 0,
      cacheHits: 0,
      cacheMisses: 0
    };
    
    console.log('📡 API Client inicializado:', this.baseUrl);
  }
  
  /**
   * Busca dados de uma query
   * @param {string|number} questionId - ID da pergunta
   * @param {Object} filters - Filtros a aplicar
   * @returns {Promise<Object>} Dados da query
   */
  async queryData(questionId, filters = {}) {
    try {
      // Gera chave do cache
      const cacheKey = this.generateCacheKey(questionId, filters);
      
      // Desabilita cache temporariamente para evitar problemas
      // TODO: Investigar problema com cache retornando dados vazios
      /*
      if (Object.keys(filters).length === 0) {
        const cached = this.getFromCache(cacheKey);
        if (cached && cached.data && cached.data.rows && cached.data.rows.length > 0) {
          this.stats.cacheHits++;
          console.log('📦 Dados válidos retornados do cache');
          return cached;
        }
      }
      */
      
      this.stats.cacheMisses++;
      this.stats.requests++;
      
      // Monta URL com parâmetros
      const url = new URL(`${this.baseUrl}/api/query`);
      url.searchParams.append('question_id', questionId);
      
      // Adiciona filtros como parâmetros
      Object.entries(filters).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach(v => url.searchParams.append(key, v));
        } else if (value !== null && value !== undefined && value !== '') {
          url.searchParams.append(key, value);
        }
      });
      
      console.log('🔄 Requisição para:', url.toString());
      
      // Faz requisição
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Valida resposta
      if (!data || !data.data || !data.data.rows) {
        console.warn('⚠️ Resposta inválida da API:', data);
        throw new Error('Resposta inválida da API');
      }
      
      // Cache desabilitado temporariamente
      /*
      if (data.data.rows.length > 0 && Object.keys(filters).length === 0) {
        this.setCache(cacheKey, data);
      }
      */
      
      console.log(`✅ Dados recebidos: ${data.data.rows.length} linhas (${data.data.cols.length} colunas)`);
      
      // Log de debug
      if (data.data.rows.length === 0) {
        console.warn('⚠️ API retornou 0 linhas - verifique os filtros ou a query');
      }
      
      return data;
      
    } catch (error) {
      console.error('❌ Erro ao buscar dados:', error);
      
      // Em caso de erro, limpa cache para forçar nova requisição
      const cacheKey = this.generateCacheKey(questionId, filters);
      this.cache.delete(cacheKey);
      
      throw error;
    }
  }
  
  /**
   * Gera chave única para cache
   * @private
   */
  generateCacheKey(questionId, filters) {
    const filterStr = JSON.stringify(filters, Object.keys(filters).sort());
    return `q${questionId}_${filterStr}`;
  }
  
  /**
   * Obtém dados do cache
   * @private
   */
  getFromCache(key) {
    const cached = this.cache.get(key);
    
    if (!cached) return null;
    
    // Verifica se expirou
    if (Date.now() - cached.timestamp > this.cacheTimeout) {
      this.cache.delete(key);
      return null;
    }
    
    // Verifica se os dados são válidos
    if (!cached.data || !cached.data.data || !cached.data.data.rows) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data;
  }
  
  /**
   * Armazena no cache
   * @private
   */
  setCache(key, data) {
    // Limita tamanho do cache
    if (this.cache.size > 10) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    
    this.cache.set(key, {
      data: data,
      timestamp: Date.now()
    });
  }
  
  /**
   * Limpa cache
   */
  clearCache() {
    this.cache.clear();
    console.log('🗑️ Cache limpo');
  }
  
  /**
   * Obtém estatísticas
   */
  getStats() {
    return {
      ...this.stats,
      cacheSize: this.cache.size,
      hitRate: this.stats.requests > 0 
        ? Math.round((this.stats.cacheHits / this.stats.requests) * 100) 
        : 0
    };
  }
  
  /**
   * Exporta dados para CSV (via backend)
   */
  async exportCsv(questionId, filters = {}) {
    try {
      const url = new URL(`${this.baseUrl}/api/export/csv`);
      url.searchParams.append('question_id', questionId);
      
      Object.entries(filters).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach(v => url.searchParams.append(key, v));
        } else if (value !== null && value !== undefined && value !== '') {
          url.searchParams.append(key, value);
        }
      });
      
      const response = await fetch(url.toString());
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const blob = await response.blob();
      const downloadUrl = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `export_${questionId}_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      URL.revokeObjectURL(downloadUrl);
      
      console.log('✅ CSV exportado com sucesso');
      
    } catch (error) {
      console.error('❌ Erro ao exportar CSV:', error);
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
