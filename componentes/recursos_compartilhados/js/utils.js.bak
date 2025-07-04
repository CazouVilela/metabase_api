// componentes/tabela_virtual/js/utils.js
/**
 * Utilitários gerais da aplicação
 */

const Utils = {
  /**
   * Formata número com separadores de milhares
   */
  formatNumber(num) {
    return num.toLocaleString('pt-BR');
  },

  /**
   * Formata data/hora
   */
  formatDateTime(date = new Date()) {
    return date.toLocaleTimeString('pt-BR');
  },

  /**
   * Debounce para evitar chamadas excessivas
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  /**
   * Calcula tempo decorrido
   */
  getElapsedTime(startTime) {
    return ((performance.now() - startTime) / 1000).toFixed(2);
  },

  /**
   * Mostra mensagem temporária
   */
  showNotification(message, type = 'info', duration = 3000) {
    const indicator = document.getElementById('update-indicator');
    if (indicator) {
      indicator.textContent = message;
      indicator.className = `update-indicator ${type}`;
      indicator.classList.add('show');
      
      setTimeout(() => {
        indicator.classList.remove('show');
      }, duration);
    }
  },

  /**
   * Log com timestamp
   */
  log(message, data = null) {
    const timestamp = new Date().toLocaleTimeString('pt-BR');
    console.log(`[${timestamp}] ${message}`, data || '');
  },

  /**
   * Verifica se está em iframe
   */
  isInIframe() {
    try {
      return window.self !== window.top;
    } catch (e) {
      return true;
    }
  },

  /**
   * Obtém parâmetros da URL
   */
  getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const result = {};
    
    for (let [key, value] of params) {
      result[key] = value;
    }
    
    return result;
  },

  /**
   * Escape HTML para evitar XSS
   */
  escapeHtml(text) {
    if (text == null) return '';
    
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    
    return String(text).replace(/[&<>"']/g, m => map[m]);
  },

  /**
   * Verifica performance de memória
   */
  checkMemory() {
    if (performance.memory) {
      const used = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024);
      const total = Math.round(performance.memory.totalJSHeapSize / 1024 / 1024);
      const limit = Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024);
      const percent = Math.round((used / limit) * 100);
      
      return {
        used,
        total,
        limit,
        percent,
        isHigh: percent > 80
      };
    }
    
    return null;
  },

  /**
   * Cria elemento com classes e atributos
   */
  createElement(tag, options = {}) {
    const element = document.createElement(tag);
    
    if (options.className) {
      element.className = options.className;
    }
    
    if (options.text) {
      element.textContent = options.text;
    }
    
    if (options.html) {
      element.innerHTML = options.html;
    }
    
    if (options.attrs) {
      Object.entries(options.attrs).forEach(([key, value]) => {
        element.setAttribute(key, value);
      });
    }
    
    return element;
  },

  /**
   * Aguarda elemento estar disponível no DOM
   */
  waitForElement(selector, timeout = 5000) {
    return new Promise((resolve, reject) => {
      const element = document.querySelector(selector);
      if (element) {
        resolve(element);
        return;
      }
      
      const observer = new MutationObserver((mutations, obs) => {
        const element = document.querySelector(selector);
        if (element) {
          obs.disconnect();
          resolve(element);
        }
      });
      
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
      
      setTimeout(() => {
        observer.disconnect();
        reject(new Error(`Elemento ${selector} não encontrado`));
      }, timeout);
    });
  }
};
