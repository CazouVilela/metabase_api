// static/js/api-client.js
/**
 * Cliente JavaScript para comunicação com a API
 * Pode ser reutilizado por todos os componentes
 */

class ApiClient {
  constructor() {
    this.baseUrl = this.getBaseUrl();
    this.timeout = 300000; // 5 minutos
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutos
  }

  /**
   * Obtém URL base da API
   */
  getBaseUrl() {
    // Remove path do componente para obter base
    const path = window.location.pathname;
    const basePath = path.split('/componentes')[0] || '';
    return basePath + '/api';
  }

  /**
   * Faz requisição GET
   */
  async get(endpoint, params = {}) {
    const url = this.buildUrl(endpoint, params);
    
    // Verifica cache
    const cached = this.getFromCache(url);
    if (cached) {
      console.log('📦 Dados do cache:', url);
      return cached;
    }

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        },
        signal: this.createAbortSignal()
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Adiciona ao cache
      this.addToCache(url, data);
      
      return data;

    } catch (error) {
      console.error('❌ Erro na API:', error);
      throw error;
    }
  }

  /**
   * Faz requisição POST
   */
  async post(endpoint, data = {}) {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data),
        signal: this.createAbortSignal()
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('❌ Erro na API:', error);
      throw error;
    }
  }

  /**
   * Executa query com filtros
   */
  async query(questionId, filtros = {}) {
    return this.get('/query', {
      question_id: questionId,
      ...filtros
    });
  }

  /**
   * Obtém informações de uma questão
   */
  async getQuestionInfo(questionId) {
    return this.get(`/question/${questionId}/info`);
  }

  /**
   * Debug de filtros
   */
  async debugFilters(filtros = {}) {
    return this.get('/debug/filters', filtros);
  }

  /**
   * Executa query com processamento
   */
  async queryWithProcessing(questionId, filtros = {}, processamento = null) {
    const params = {
      question_id: questionId,
      ...filtros
    };

    if (processamento) {
      params.processamento = processamento;
    }

    return this.get('/query', params);
  }

  /**
   * Constrói URL com parâmetros
   */
  buildUrl(endpoint, params) {
    const url = new URL(`${this.baseUrl}${endpoint}`, window.location.origin);
    
    Object.entries(params).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach(v => url.searchParams.append(key, v));
      } else if (value !== null && value !== undefined) {
        url.searchParams.append(key, value);
      }
    });

    return url.toString();
  }

  /**
   * Cria sinal de abort para timeout
   */
  createAbortSignal() {
    const controller = new AbortController();
    
    setTimeout(() => {
      controller.abort();
    }, this.timeout);

    return controller.signal;
  }

  /**
   * Obtém dados do cache
   */
  getFromCache(url) {
    const cached = this.cache.get(url);
    
    if (cached) {
      const age = Date.now() - cached.timestamp;
      
      if (age < this.cacheTimeout) {
        return cached.data;
      }
      
      this.cache.delete(url);
    }
    
    return null;
  }

  /**
   * Adiciona dados ao cache
   */
  addToCache(url, data) {
    // Limita tamanho do cache
    if (this.cache.size > 20) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    this.cache.set(url, {
      data,
      timestamp: Date.now()
    });
  }

  /**
   * Limpa cache
   */
  clearCache() {
    this.cache.clear();
    console.log('🗑️ Cache da API limpo');
  }

  /**
   * Exporta dados para CSV
   */
  async exportToCsv(questionId, filtros = {}) {
    const endpoint = '/export/csv';
    const params = {
      question_id: questionId,
      ...filtros
    };

    try {
      const response = await fetch(this.buildUrl(endpoint, params));
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      
      a.href = url;
      a.download = `export_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('❌ Erro ao exportar:', error);
      throw error;
    }
  }

  /**
   * Monitora health da API
   */
  async checkHealth() {
    try {
      const response = await fetch(`${this.baseUrl.replace('/api', '')}/health`, {
        method: 'GET',
        signal: this.createAbortSignal()
      });

      return response.ok;
    } catch (error) {
      return false;
    }
  }
}

// Instância global do cliente
const apiClient = new ApiClient();

// Exporta para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ApiClient, apiClient };
}
