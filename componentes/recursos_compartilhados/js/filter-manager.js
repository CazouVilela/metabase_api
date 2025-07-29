// componentes/recursos_compartilhados/js/filter-manager.js
/**
 * Gerenciador de filtros compartilhado
 * Captura e monitora filtros do dashboard Metabase
 */

class FilterManager {
  constructor() {
    this.currentFilters = {};
    this.lastFilterString = '';
    this.observers = [];
    this.monitoringInterval = null;
    this.isFirstCapture = true;
  }
  
  /**
   * Captura filtros da URL do parent (dashboard)
   * @returns {Object} Filtros capturados
   */
  captureFromParent() {
    const filters = {};
    
    try {
      // Tenta acessar a URL do parent
      const parentUrl = window.parent.location.href;
      const url = new URL(parentUrl);
      
      // Parâmetros conhecidos que devemos ignorar
      const ignoredParams = [
        'question_id', 'dashboard', 'tab', 'refresh', 
        'fullscreen', 'titled', 'hide_filters', 'hide_download_button'
      ];
      
      // Captura todos os parâmetros exceto os ignorados
      for (const [key, value] of url.searchParams.entries()) {
        if (!ignoredParams.includes(key)) {
          // Se já existe a chave, converte para array
          if (filters[key]) {
            if (!Array.isArray(filters[key])) {
              filters[key] = [filters[key]];
            }
            filters[key].push(this.decodeValue(value));
          } else {
            filters[key] = this.decodeValue(value);
          }
        }
      }
      
      // Se não conseguiu capturar do parent, tenta da própria URL
    } catch (error) {
      // Fallback: captura da própria URL do iframe
      const url = new URL(window.location.href);
      
      for (const [key, value] of url.searchParams.entries()) {
        if (key !== 'question_id') {
          if (filters[key]) {
            if (!Array.isArray(filters[key])) {
              filters[key] = [filters[key]];
            }
            filters[key].push(this.decodeValue(value));
          } else {
            filters[key] = this.decodeValue(value);
          }
        }
      }
    }
    
    // Processa arrays de valores únicos
    Object.keys(filters).forEach(key => {
      if (Array.isArray(filters[key])) {
        // Remove duplicatas
        filters[key] = [...new Set(filters[key])];
        
        // Se sobrou apenas um valor, desembrulha do array
        if (filters[key].length === 1) {
          filters[key] = filters[key][0];
        }
      }
    });
    
    console.log('📋 Filtros capturados:', filters);
    
    return filters;
  }
  
  /**
   * Decodifica valor do parâmetro
   * @private
   */
  decodeValue(value) {
    try {
      // Tenta decodificar como URI component
      const decoded = decodeURIComponent(value);
      
      // Se for um número, converte
      if (/^\d+$/.test(decoded)) {
        return parseInt(decoded);
      }
      if (/^\d+\.\d+$/.test(decoded)) {
        return parseFloat(decoded);
      }
      
      return decoded;
    } catch (e) {
      // Se falhar, retorna valor original
      return value;
    }
  }
  
  /**
   * Compara se filtros mudaram
   * @private
   */
  hasFiltersChanged(newFilters) {
    // Converte para string para comparação profunda
    const newFilterString = JSON.stringify(newFilters, Object.keys(newFilters).sort());
    
    // Na primeira captura, sempre considera como não mudado
    if (this.isFirstCapture) {
      this.isFirstCapture = false;
      this.lastFilterString = newFilterString;
      this.currentFilters = { ...newFilters };
      return false;
    }
    
    // Compara com último estado
    const changed = newFilterString !== this.lastFilterString;
    
    if (changed) {
      this.lastFilterString = newFilterString;
    }
    
    return changed;
  }
  
  /**
   * Inicia monitoramento automático de mudanças
   * @param {number} interval - Intervalo em ms (padrão: 1000)
   */
  startMonitoring(interval = 1000) {
    // Para monitoramento anterior se existir
    this.stopMonitoring();
    
    // Reseta flag de primeira captura
    this.isFirstCapture = true;
    
    // Captura inicial
    this.currentFilters = this.captureFromParent();
    
    // Inicia monitoramento
    this.monitoringInterval = setInterval(() => {
      const newFilters = this.captureFromParent();
      
      if (this.hasFiltersChanged(newFilters)) {
        console.log('🔄 Filtros mudaram');
        console.log('  Antes:', this.currentFilters);
        console.log('  Depois:', newFilters);
        this.currentFilters = { ...newFilters };
        
        // Notifica observers
        this.observers.forEach(callback => {
          try {
            callback(this.currentFilters);
          } catch (error) {
            console.error('Erro em observer:', error);
          }
        });
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
   * Adiciona observer para mudanças
   * @param {Function} callback - Função a chamar quando filtros mudarem
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
   * Obtém informações de debug
   */
  getDebugInfo() {
    const info = {
      filters: this.currentFilters,
      total: Object.keys(this.currentFilters).length,
      multiValue: [],
      specialChars: []
    };
    
    // Analisa filtros
    Object.entries(this.currentFilters).forEach(([key, value]) => {
      // Verifica múltiplos valores
      if (Array.isArray(value)) {
        info.multiValue.push({
          name: key,
          count: value.length,
          values: value
        });
      }
      
      // Verifica caracteres especiais
      const valueStr = Array.isArray(value) ? value.join(' ') : String(value);
      const specialChars = valueStr.match(/[^a-zA-Z0-9\s\-_.]/g);
      
      if (specialChars) {
        info.specialChars.push({
          filter: key,
          chars: [...new Set(specialChars)]
        });
      }
    });
    
    return info;
  }
  
  /**
   * Reseta filtros
   */
  reset() {
    this.currentFilters = {};
    this.lastFilterString = '';
    this.isFirstCapture = true;
    this.observers = [];
    this.stopMonitoring();
  }
}

// Cria instância global única
const filterManager = new FilterManager();

// Exporta para diferentes ambientes
if (typeof module !== 'undefined' && module.exports) {
  module.exports = filterManager;
} else if (typeof define === 'function' && define.amd) {
  define([], function() { return filterManager; });
} else {
  window.filterManager = filterManager;
}
