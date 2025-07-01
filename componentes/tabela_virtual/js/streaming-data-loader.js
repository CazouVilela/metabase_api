// componentes/tabela_virtual/js/streaming-data-loader.js
/**
 * Módulo de carregamento de dados com suporte a streaming SSE
 */

class StreamingDataLoader {
  constructor() {
    this.eventSource = null;
    this.isStreaming = false;
    this.chunks = [];
    this.allData = [];
    
    // Callbacks
    this.onChunk = null;
    this.onComplete = null;
    this.onError = null;
    this.onProgress = null;
    
    // Métricas de tempo
    this.metrics = {
      tempoInicio: null,
      tempoSQL: null,
      tempoPrimeiroChunk: null,
      tempoUltimoChunk: null,
      tempoTotal: null,
      tempoRenderizacao: null,
      chunksRecebidos: 0,
      linhasRecebidas: 0
    };
  }

  /**
   * Inicia streaming de dados
   */
  async startStreaming(questionId, filtros, options = {}) {
    if (this.isStreaming) {
      Utils.log('⚠️ Streaming já em andamento');
      return;
    }

    // Reset
    this.reset();
    this.isStreaming = true;
    this.metrics.tempoInicio = performance.now();
    
    Utils.log('🌊 Iniciando streaming de dados...');

    // Constrói URL
    const url = this.buildStreamUrl(questionId, filtros, options);
    
    // Cria EventSource
    this.eventSource = new EventSource(url);
    
    // Handlers de eventos
    this.eventSource.addEventListener('start', (e) => {
      const data = JSON.parse(e.data);
      Utils.log('🚀 Streaming iniciado:', data);
    });

    this.eventSource.addEventListener('chunk', (e) => {
      this.handleChunk(e);
    });

    this.eventSource.addEventListener('complete', (e) => {
      this.handleComplete(e);
    });

    this.eventSource.addEventListener('error', (e) => {
      this.handleError(e);
    });

    this.eventSource.onerror = (error) => {
      this.handleStreamError(error);
    };
  }

  /**
   * Processa chunk recebido
   */
  handleChunk(event) {
    try {
      const chunk = JSON.parse(event.data);
      const agora = performance.now();
      
      // Primeira chunk = tempo SQL
      if (this.metrics.chunksRecebidos === 0) {
        this.metrics.tempoPrimeiroChunk = agora;
        this.metrics.tempoSQL = (agora - this.metrics.tempoInicio) / 1000;
        
        Utils.log(`⏱️  [TEMPO SQL]: ${this.metrics.tempoSQL.toFixed(2)}s`);
      }
      
      // Atualiza métricas
      this.metrics.chunksRecebidos++;
      this.metrics.linhasRecebidas += chunk.rows_in_chunk;
      this.metrics.tempoUltimoChunk = agora;
      
      // Adiciona dados
      this.chunks.push(chunk);
      this.allData = this.allData.concat(chunk.rows);
      
      // Log do chunk
      const tempoDecorrido = (agora - this.metrics.tempoInicio) / 1000;
      Utils.log(`📦 Chunk ${chunk.chunk_number}: ${chunk.rows_in_chunk.toLocaleString('pt-BR')} linhas ` +
                `(Total: ${this.metrics.linhasRecebidas.toLocaleString('pt-BR')} em ${tempoDecorrido.toFixed(2)}s)`);
      
      // Callback
      if (this.onChunk) {
        this.onChunk(chunk, this.metrics);
      }
      
      // Progress
      if (this.onProgress) {
        this.onProgress({
          chunksRecebidos: this.metrics.chunksRecebidos,
          linhasRecebidas: this.metrics.linhasRecebidas,
          tempoDecorrido: tempoDecorrido
        });
      }
      
    } catch (error) {
      Utils.log('❌ Erro ao processar chunk:', error);
    }
  }

  /**
   * Processa conclusão do streaming
   */
  handleComplete(event) {
    try {
      const data = JSON.parse(event.data);
      const agora = performance.now();
      
      // Atualiza métricas finais
      this.metrics.tempoTotal = (agora - this.metrics.tempoInicio) / 1000;
      this.metrics.tempoTransmissao = data.tempo_transmissao_dados;
      
      // Logs detalhados
      Utils.log('\n✅ [STREAMING COMPLETO]');
      Utils.log(`   📊 Total de linhas: ${data.total_rows.toLocaleString('pt-BR')}`);
      Utils.log(`   📦 Total de chunks: ${data.total_chunks}`);
      Utils.log(`   ⏱️  Tempo SQL: ${data.tempo_sql.toFixed(2)}s`);
      Utils.log(`   ⏱️  Tempo transmissão: ${data.tempo_transmissao_dados.toFixed(2)}s`);
      Utils.log(`   ⏱️  Tempo total (servidor): ${data.tempo_total_transmissao.toFixed(2)}s`);
      Utils.log(`   ⏱️  Tempo total (cliente): ${this.metrics.tempoTotal.toFixed(2)}s`);
      Utils.log(`   🚀 Velocidade: ${Math.round(data.velocidade_media).toLocaleString('pt-BR')} linhas/s`);
      
      // Fecha EventSource
      this.close();
      
      // Callback
      if (this.onComplete) {
        const tempoInicioRender = performance.now();
        this.onComplete(this.allData, this.metrics);
        
        // Tempo de renderização
        this.metrics.tempoRenderizacao = (performance.now() - tempoInicioRender) / 1000;
        Utils.log(`   ⏱️  Tempo renderização: ${this.metrics.tempoRenderizacao.toFixed(2)}s`);
        
        // Tempo total incluindo renderização
        const tempoTotalCompleto = (performance.now() - this.metrics.tempoInicio) / 1000;
        Utils.log(`   ⏱️  TEMPO TOTAL (SQL + Transmissão + Renderização): ${tempoTotalCompleto.toFixed(2)}s`);
      }
      
    } catch (error) {
      Utils.log('❌ Erro ao processar conclusão:', error);
    }
  }

  /**
   * Processa erro no streaming
   */
  handleError(event) {
    try {
      const error = JSON.parse(event.data);
      Utils.log('❌ Erro no streaming:', error);
      
      this.close();
      
      if (this.onError) {
        this.onError(error);
      }
    } catch (e) {
      Utils.log('❌ Erro ao processar erro:', e);
    }
  }

  /**
   * Processa erro de conexão
   */
  handleStreamError(error) {
    Utils.log('❌ Erro de conexão SSE:', error);
    
    this.close();
    
    if (this.onError) {
      this.onError({
        error: 'Erro de conexão',
        details: error
      });
    }
  }

  /**
   * Constrói URL para streaming
   */
  buildStreamUrl(questionId, filtros, options) {
    const path = window.location.pathname;
    const basePath = path.split('/componentes')[0] || '';
    
    const params = new URLSearchParams();
    params.append('question_id', questionId);
    
    // Adiciona chunk_size se especificado
    if (options.chunkSize) {
      params.append('chunk_size', options.chunkSize);
    }
    
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
    
    return `${basePath}/api/query/stream?${params.toString()}`;
  }

  /**
   * Para o streaming
   */
  stop() {
    Utils.log('🛑 Parando streaming...');
    this.close();
  }

  /**
   * Fecha conexão SSE
   */
  close() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.isStreaming = false;
  }

  /**
   * Reset completo
   */
  reset() {
    this.close();
    this.chunks = [];
    this.allData = [];
    this.metrics = {
      tempoInicio: null,
      tempoSQL: null,
      tempoPrimeiroChunk: null,
      tempoUltimoChunk: null,
      tempoTotal: null,
      tempoRenderizacao: null,
      chunksRecebidos: 0,
      linhasRecebidas: 0
    };
  }

  /**
   * Verifica se deve usar streaming baseado no tamanho estimado
   */
  async shouldUseStreaming(questionId, filtros) {
    // Por enquanto, sempre usa streaming para datasets grandes
    // No futuro, pode fazer uma estimativa primeiro
    return true;
  }

  /**
   * Obtém métricas atuais
   */
  getMetrics() {
    return { ...this.metrics };
  }

  /**
   * Obtém estatísticas
   */
  getStats() {
    return {
      isStreaming: this.isStreaming,
      chunksRecebidos: this.metrics.chunksRecebidos,
      linhasRecebidas: this.metrics.linhasRecebidas,
      tempos: {
        sql: this.metrics.tempoSQL,
        transmissao: this.metrics.tempoTransmissao,
        renderizacao: this.metrics.tempoRenderizacao,
        total: this.metrics.tempoTotal
      }
    };
  }
}

// Instância global
const streamingLoader = new StreamingDataLoader();
