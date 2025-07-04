/**
 * Gerenciador de filtros compartilhado
 * @module filter-manager
 */

class FilterManager {
    constructor() {
        this.currentFilters = {};
        this.lastState = '';
        this.observers = [];
        
        // Mapa de normalização de nomes
        this.normalizationMap = {
            'posição': 'posicao',
            'posicao': 'posicao',
            'anúncio': 'anuncio',
            'anuncio': 'anuncio',
            'conversões_consideradas': 'conversoes_consideradas',
            'conversoes_consideradas': 'conversoes_consideradas',
            'objetivo': 'objective',
            'objective': 'objective'
        };
        
        // Parâmetros que podem ter múltiplos valores
        this.multiValueParams = [
            'campanha', 'conta', 'adset', 'ad_name', 'plataforma',
            'posicao', 'device', 'objective', 'optimization_goal',
            'buying_type', 'action_type_filter', 'anuncio',
            'conversoes_consideradas'
        ];
    }
    
    /**
     * Captura filtros do dashboard parent
     * @returns {Object} Filtros capturados
     */
    captureFromParent() {
        try {
            // Verifica se está em iframe
            if (!this.isInIframe()) {
                console.log('⚠️ Não está em iframe, usando filtros da URL atual');
                return this.captureFromUrl(window.location.href);
            }
            
            const parentUrl = window.parent.location.href;
            return this.captureFromUrl(parentUrl);
            
        } catch (e) {
            console.error('❌ Erro ao acessar parent URL:', e);
            return {};
        }
    }
    
    /**
     * Captura filtros de uma URL específica
     * @param {string} url - URL para extrair filtros
     * @returns {Object} Filtros extraídos
     */
    captureFromUrl(url) {
        const urlParts = url.split('?');
        if (urlParts.length < 2) return {};
        
        const queryString = urlParts[1];
        const params = {};
        
        // Parse manual para suportar múltiplos valores
        queryString.split('&').forEach(param => {
            if (!param.includes('=')) return;
            
            let [key, ...valueParts] = param.split('=');
            let value = valueParts.join('=');
            
            // Decodifica
            key = this.decodeParameter(key);
            key = this.normalizeParamName(key);
            value = this.decodeParameter(value);
            
            if (value && value.trim() !== '') {
                this.addParameter(params, key, value);
            }
        });
        
        console.log('📋 Filtros capturados:', params);
        return params;
    }
    
    /**
     * Decodifica parâmetro (trata dupla codificação)
     * @private
     */
    decodeParameter(str) {
        try {
            // Substitui + por espaço
            str = str.replace(/\+/g, ' ');
            
            // Primeira decodificação
            str = decodeURIComponent(str);
            
            // Se ainda tem %, tenta decodificar novamente
            if (str.includes('%')) {
                try {
                    str = decodeURIComponent(str);
                } catch (e) {
                    // Mantém como está se falhar
                }
            }
            
            return str;
        } catch (e) {
            console.warn('⚠️ Erro ao decodificar:', str);
            return str;
        }
    }
    
    /**
     * Normaliza nome do parâmetro
     * @private
     */
    normalizeParamName(name) {
        return this.normalizationMap[name] || name;
    }
    
    /**
     * Adiciona parâmetro (suporta múltiplos valores)
     * @private
     */
    addParameter(params, key, value) {
        if (this.multiValueParams.includes(key)) {
            if (params[key]) {
                // Já existe - converte para array ou adiciona
                if (Array.isArray(params[key])) {
                    params[key].push(value);
                } else {
                    params[key] = [params[key], value];
                }
            } else {
                params[key] = value;
            }
        } else {
            params[key] = value;
        }
    }
    
    /**
     * Verifica se filtros mudaram
     * @param {Object} newFilters - Novos filtros
     * @returns {boolean} True se mudaram
     */
    hasChanged(newFilters) {
        const newState = JSON.stringify(newFilters);
        const changed = newState !== this.lastState;
        
        if (changed) {
            this.lastState = newState;
            this.currentFilters = newFilters;
        }
        
        return changed;
    }
    
    /**
     * Adiciona observer para mudanças
     * @param {Function} callback - Função a chamar quando mudar
     */
    onChange(callback) {
        this.observers.push(callback);
    }
    
    /**
     * Remove observer
     * @param {Function} callback - Função a remover
     */
    offChange(callback) {
        this.observers = this.observers.filter(cb => cb !== callback);
    }
    
    /**
     * Notifica observers sobre mudanças
     */
    notifyChanges() {
        this.observers.forEach(callback => {
            try {
                callback(this.currentFilters);
            } catch (e) {
                console.error('❌ Erro em observer:', e);
            }
        });
    }
    
    /**
     * Inicia monitoramento automático
     * @param {number} interval - Intervalo em ms
     */
    startMonitoring(interval = 1000) {
        if (this.monitoringInterval) {
            this.stopMonitoring();
        }
        
        this.monitoringInterval = setInterval(() => {
            const filters = this.captureFromParent();
            if (this.hasChanged(filters)) {
                console.log('🔄 Filtros mudaram');
                this.notifyChanges();
            }
        }, interval);
        
        console.log('👁️ Monitoramento de filtros iniciado');
    }
    
    /**
     * Para monitoramento
     */
    stopMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
            console.log('🛑 Monitoramento de filtros parado');
        }
    }
    
    /**
     * Verifica se está em iframe
     * @returns {boolean}
     */
    isInIframe() {
        try {
            return window.self !== window.top;
        } catch (e) {
            return true;
        }
    }
    
    /**
     * Gera informações de debug
     * @returns {Object} Informações de debug
     */
    getDebugInfo() {
        const info = {
            total: Object.keys(this.currentFilters).length,
            filters: this.currentFilters,
            multiValue: [],
            specialChars: []
        };
        
        Object.entries(this.currentFilters).forEach(([key, value]) => {
            if (Array.isArray(value)) {
                info.multiValue.push({
                    name: key,
                    count: value.length,
                    values: value
                });
            }
            
            // Verifica caracteres especiais
            const values = Array.isArray(value) ? value : [value];
            values.forEach(v => {
                const specialChars = this.findSpecialChars(v);
                if (specialChars.length > 0) {
                    info.specialChars.push({
                        filter: key,
                        value: v,
                        chars: specialChars
                    });
                }
            });
        });
        
        return info;
    }
    
    /**
     * Encontra caracteres especiais em valor
     * @private
     */
    findSpecialChars(value) {
        const specialChars = ['+', '&', '%', '=', '?', '#', '|', '/', '*', '@', '!', '$', '^', '(', ')', '[', ']', '{', '}'];
        return specialChars.filter(char => value.includes(char));
    }
    
    /**
     * Converte filtros para query string
     * @returns {string} Query string
     */
    toQueryString() {
        const params = new URLSearchParams();
        
        Object.entries(this.currentFilters).forEach(([key, value]) => {
            if (Array.isArray(value)) {
                value.forEach(v => params.append(key, v));
            } else {
                params.append(key, value);
            }
        });
        
        return params.toString();
    }
}

// Exporta instância única
const filterManager = new FilterManager();

// Exporta para diferentes ambientes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = filterManager;
} else if (typeof define === 'function' && define.amd) {
    define([], function() { return filterManager; });
} else {
    window.filterManager = filterManager;
}
