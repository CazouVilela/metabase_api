/**
 * Cliente API compartilhado para todos os componentes
 * @module api-client
 */

class MetabaseAPIClient {
    constructor() {
        this.baseUrl = this.detectBaseUrl();
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutos
        this.defaultTimeout = 300000; // 5 minutos
    }
    
    /**
     * Detecta URL base automaticamente
     */
    detectBaseUrl() {
        const path = window.location.pathname;
        const basePath = path.split('/componentes')[0] || '';
        return basePath + '/api';
    }
    
    /**
     * Executa query com filtros
     * @param {number|string} questionId - ID da questão
     * @param {Object} filters - Filtros a aplicar
     * @returns {Promise<Object>} Dados da query
     */
    async queryData(questionId, filters = {}) {
        return this.get('/query', {
            question_id: questionId,
            ...filters
        });
    }
    
    /**
     * Obtém informações sobre uma questão
     * @param {number|string} questionId - ID da questão
     * @returns {Promise<Object>} Informações da questão
     */
    async getQuestionInfo(questionId) {
        return this.get(`/question/${questionId}/info`);
    }
    
    /**
     * Debug de filtros
     * @param {Object} filters - Filtros para debug
     * @returns {Promise<Object>} Informações de debug
     */
    async debugFilters(filters = {}) {
        return this.get('/debug/filters', filters);
    }
    
    /**
     * Obtém estatísticas do cache
     * @returns {Promise<Object>} Estatísticas do cache
     */
    async getCacheStats() {
        return this.get('/debug/cache/stats');
    }
    
    /**
     * Limpa o cache do servidor
     * @returns {Promise<Object>} Confirmação
     */
    async clearServerCache() {
        return this.post('/debug/cache/clear');
    }
    
    /**
     * Faz requisição GET genérica
     * @param {string} endpoint - Endpoint da API
     * @param {Object} params - Parâmetros da query
     * @returns {Promise<any>} Resposta da API
     */
    async get(endpoint, params = {}) {
        const url = this.buildUrl(endpoint, params);
        
        // Verifica cache local
        const cached = this.getFromCache(url);
        if (cached) {
            console.log('📦 Dados do cache local:', url);
            return cached;
        }
        
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip'
                },
                signal: this.createAbortSignal()
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Adiciona ao cache local
            this.addToCache(url, data);
            
            return data;
            
        } catch (error) {
            console.error('❌ Erro na API:', error);
            throw error;
        }
    }
    
    /**
     * Faz requisição POST
     * @param {string} endpoint - Endpoint da API
     * @param {Object} data - Dados a enviar
     * @returns {Promise<any>} Resposta da API
     */
    async post(endpoint, data = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
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
     * Constrói URL com parâmetros
     * @private
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
     * @private
     */
    createAbortSignal() {
        const controller = new AbortController();
        
        setTimeout(() => {
            controller.abort();
        }, this.defaultTimeout);
        
        return controller.signal;
    }
    
    /**
     * Obtém dados do cache local
     * @private
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
     * Adiciona dados ao cache local
     * @private
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
     * Limpa cache local
     */
    clearLocalCache() {
        this.cache.clear();
        console.log('🗑️ Cache local limpo');
    }
    
    /**
     * Verifica health da API
     * @returns {Promise<boolean>} Status da API
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

// Exporta instância única (singleton)
const apiClient = new MetabaseAPIClient();

// Exporta para diferentes ambientes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = apiClient;
} else if (typeof define === 'function' && define.amd) {
    define([], function() { return apiClient; });
} else {
    window.apiClient = apiClient;
}
