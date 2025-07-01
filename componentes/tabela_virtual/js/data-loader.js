// componentes/tabela_virtual/js/data-loader.js
/**
 * Módulo de carregamento de dados
 */

class DataLoader {
  constructor() {
    this.baseUrl = this.getBaseUrl();
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutos
    this.isLoading = false;
    this.abortController = null;
  }

  /**
   * Obtém URL base da API
   */
  getBaseUrl() {
    // Remove /componentes/tabela_virtual do path
    const path = window.location.pathname;
    const basePath = path.split('/componentes')[0];
    return basePath || '';
  }

  /**
   * Carrega dados da API
   */
  async loadData(questionId, filtros) {
    // Verifica se já está carregando
    if (this.isLoading) {
      Utils.log('⚠️ Carregamento já em andamento');
      return null;
    }

    // Cancela requisição anterior se houver
    if (this.abortController) {
      this.abortController.abort();
    }

    this.isLoading = true;
    this.abortController = new AbortController();

    try {
      // Monta URL
      const url = this.buildUrl(questionId, filtros);
      
      // Verifica cache
      const cached = this.getFromCache(url);
      if (cached) {
        Utils.log('📦 Dados do cache');
        return cached;
      }

      // Faz requisição
      const startTime = performance.now();
      Utils.log('📡 Buscando dados...', url);

      const response = await fetch(url, {
        signal: this.abortController.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      const elapsed = Utils.getElapsedTime(startTime);

      Utils.log(`✅ ${data.length} linhas em ${elapsed}s`);

      // Adiciona ao cache
      this.addToCache(url, data);

      return data;

    } catch (error) {
      if (error.name === 'AbortError') {
        Utils.log('🛑 Requisição cancelada');
        return null;
      }
      
      Utils.log('❌ Erro ao carregar dados:', error);
      throw error;
      
    } finally {
      this.isLoading = false;
      this.abortController = null;
    }
  }

  /**
   * Constrói URL com parâmetros
   */
  buildUrl(questionId, filtros, useDirect = true) {
    // Usa endpoint direto por padrão para melhor performance
    const endpoint = useDirect ? '/api/query/direct' : '/api/query';
    const params = new URLSearchParams();
    params.append('question_id', questionId);

    // Adiciona database e schema se disponíveis
    const urlParams = Utils.getUrlParams();
    if (urlParams.database) params.append('database', urlParams.database);
    if (urlParams.schema) params.append('schema', urlParams.schema);

    // Adiciona filtros
    Object.entries(filtros).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach(v => params.append(key, v));
      } else {
        params.append(key, value);
      }
    });

    return `${this.baseUrl}${endpoint}?${params.toString()}`;
  }

  /**
   * Carrega dados com streaming (para datasets grandes)
   */
  async loadDataWithStreaming(questionId, filtros, callbacks = {}) {
    Utils.log('🌊 Usando carregamento com streaming...');
    
    return new Promise((resolve, reject) => {
      // Verifica se streaming loader está disponível
      if (typeof streamingLoader === 'undefined') {
        reject(new Error('Streaming loader não está carregado'));
        return;
      }
      
      // Configura callbacks
      streamingLoader.onChunk = callbacks.onChunk;
      streamingLoader.onProgress = callbacks.onProgress;
      streamingLoader.onError = (error) => {
        reject(error);
      };
      streamingLoader.onComplete = (data, metrics) => {
        resolve({
          data,
          metrics,
          streaming: true
        });
      };
      
      // Inicia streaming
      streamingLoader.startStreaming(questionId, filtros, {
        chunkSize: 5000
      });
    });
  }

  /**
   * Decide se deve usar streaming baseado no contexto
   */
  async shouldUseStreaming(questionId, filtros) {
    // Usa streaming se tiver muitos filtros removidos (indica dataset grande)
    const numFiltros = Object.keys(filtros).length;
    
    // Se tem poucos filtros, provavelmente é um dataset grande
    if (numFiltros < 3) {
      Utils.log('📊 Poucos filtros detectados, usando streaming');
      return true;
    }
    
    // Por enquanto, sempre usa modo direto sem streaming
    // No futuro, pode fazer uma estimativa primeiro
    return false;
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
      
      // Cache expirado
      this.cache.delete(url);
    }
    
    return null;
  }

  /**
   * Adiciona dados ao cache
   */
  addToCache(url, data) {
    // Limita tamanho do cache
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
   * Limpa cache
   */
  clearCache() {
    this.cache.clear();
    Utils.log('🗑️ Cache limpo');
  }

  /**
   * Cancela requisição em andamento
   */
  cancel() {
    if (this.abortController) {
      this.abortController.abort();
    }
  }

  /**
   * Carrega dados com retry
   */
  async loadWithRetry(questionId, filtros, maxRetries = 3) {
    let lastError;

    for (let i = 0; i < maxRetries; i++) {
      try {
        const data = await this.loadData(questionId, filtros);
        if (data) return data;
        
      } catch (error) {
        lastError = error;
        Utils.log(`⚠️ Tentativa ${i + 1} falhou:`, error.message);
        
        // Aguarda antes de tentar novamente
        if (i < maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
      }
    }

    throw lastError || new Error('Falha ao carregar dados');
  }

  /**
   * Monitora uso de memória durante carregamento
   */
  monitorMemory() {
    if (!performance.memory) return;

    const interval = setInterval(() => {
      const mem = Utils.checkMemory();
      
      if (mem && mem.isHigh) {
        Utils.log('⚠️ Memória alta:', `${mem.used}MB de ${mem.limit}MB (${mem.percent}%)`);
        
        // Limpa cache se memória estiver muito alta
        if (mem.percent > 90) {
          this.clearCache();
        }
      }
      
      if (!this.isLoading) {
        clearInterval(interval);
      }
    }, 2000);
  }

  /**
   * Estatísticas de carregamento
   */
  getStats() {
    return {
      cacheSize: this.cache.size,
      isLoading: this.isLoading,
      baseUrl: this.baseUrl
    };
  }
}

// Instância global
const dataLoader = new DataLoader();
