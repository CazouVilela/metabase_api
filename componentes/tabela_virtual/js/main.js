// componentes/tabela_virtual/js/main.js
/**
 * Arquivo principal - coordena todos os módulos
 */

class App {
  constructor() {
    this.questionId = null;
    this.virtualTable = null;
    this.checkInterval = 1000;
    this.checkTimer = null;
    this.useStreaming = false;
    
    // Elementos DOM
    this.elements = {
      container: document.getElementById('table-container'),
      debug: document.getElementById('debug-container')
    };
  }

  /**
   * Inicializa a aplicação
   */
  async init() {
    Utils.log('🚀 Iniciando aplicação...');
    
    try {
      // Obtém ID da questão
      this.questionId = Utils.getUrlParams().question_id || '51';
      
      // Verifica se deve usar streaming
      this.useStreaming = Utils.getUrlParams().streaming === 'true';
      
      // Cria tabela virtual
      this.virtualTable = new VirtualTable(this.elements.container);
      
      // Configura listeners
      this.setupListeners();
      
      // Carrega dados iniciais
      await this.loadData('inicialização');
      
      // Inicia monitoramento
      this.startMonitoring();
      
      // Mostra informações no console
      this.showConsoleInfo();
      
    } catch (error) {
      Utils.log('❌ Erro na inicialização:', error);
      this.virtualTable.renderError(error);
    }
  }

  /**
   * Configura event listeners
   */
  setupListeners() {
    // Monitora mudanças de visibilidade
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        Utils.log('🔄 Janela voltou ao foco');
        this.loadData('retorno ao foco');
      }
    });

    // Adiciona atalhos de teclado
    document.addEventListener('keydown', (e) => {
      // Ctrl/Cmd + R: Recarregar dados
      if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        this.loadData('atalho teclado');
      }
      
      // Ctrl/Cmd + E: Exportar CSV
      if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        this.virtualTable.exportToCsv();
      }
      
      // Ctrl/Cmd + S: Toggle streaming
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        this.useStreaming = !this.useStreaming;
        Utils.showNotification(`Streaming ${this.useStreaming ? 'ativado' : 'desativado'}`, 'info');
        this.loadData('toggle streaming');
      }
    });

    // Observer para mudanças de filtros
    filtrosManager.onChange(() => {
      this.loadData('mudança de filtros');
    });
  }

  /**
   * Carrega dados
   */
  async loadData(motivo = 'manual') {
    try {
      // Captura filtros
      const filtros = filtrosManager.capturarFiltrosParent();
      
      // Verifica se mudaram
      if (!filtrosManager.filtrosMudaram(filtros) && motivo !== 'inicialização') {
        Utils.log('📍 Filtros não mudaram, pulando atualização');
        return;
      }

      Utils.log(`🔄 Carregando dados (${motivo})...`);
      
      // Atualiza debug
      filtrosManager.renderizarDebug(this.elements.debug);
      
      // Mostra loading
      this.virtualTable.renderLoading();
      
      // Decide se usa streaming baseado no contexto
      const shouldStream = this.useStreaming || await this.shouldUseStreaming(filtros);
      
      if (shouldStream) {
        // Carregamento com streaming
        await this.loadDataWithStreaming(filtros);
      } else {
        // Carregamento tradicional
        await this.loadDataTraditional(filtros);
      }
      
    } catch (error) {
      Utils.log('❌ Erro ao carregar dados:', error);
      this.virtualTable.renderError(error);
    }
  }

  /**
   * Carregamento tradicional (sem streaming)
   */

/**
   * Carregamento tradicional (sem streaming)
   */
  async loadDataTraditional(filtros) {
    const startTime = performance.now();
    
    // Por padrão, usa API Native Dataset para melhor performance
    const useNativeAPI = Utils.getUrlParams().native !== 'false';
    
    let dados;
    
    try {
      if (useNativeAPI) {
        // Usa API Native (muito mais rápido!)
        dados = await dataLoader.loadDataNative(this.questionId, filtros, 'dataset');
      } else {
        // Método antigo (Query direta)
        dados = await dataLoader.loadWithRetry(this.questionId, filtros);
      }
      
      if (!dados) {
        this.virtualTable.renderEmpty();
        return;
      }

      // Renderiza tabela
      if (Array.isArray(dados) && dados.length > 0) {
        const loadTime = (performance.now() - startTime) / 1000;
        const method = useNativeAPI ? 'Native API' : 'Direct SQL';
        Utils.log(`⏱️  Tempo de carregamento (${method}): ${loadTime.toFixed(2)}s`);
        
        const renderStart = performance.now();
        this.virtualTable.render(dados);
        const renderTime = (performance.now() - renderStart) / 1000;
        
        Utils.log(`⏱️  Tempo de renderização: ${renderTime.toFixed(2)}s`);
        Utils.log(`⏱️  TEMPO TOTAL: ${(loadTime + renderTime).toFixed(2)}s`);
        
        // Monitora memória se muitos dados
        if (dados.length > 10000) {
          dataLoader.monitorMemory();
        }
      } else if (dados.error) {
        throw new Error(dados.error);
      } else {
        this.virtualTable.renderEmpty();
      }
    } catch (error) {
      // Se falhar com native, tenta método antigo
      if (useNativeAPI) {
        Utils.log('⚠️ Native API falhou, tentando Direct SQL...');
        const dados = await dataLoader.loadWithRetry(this.questionId, filtros);
        if (dados && dados.length > 0) {
          this.virtualTable.render(dados);
        } else {
          throw error;
        }
      } else {
        throw error;
      }
    }
  }





  /**
   * Carregamento com streaming
   */
  async loadDataWithStreaming(filtros) {
    Utils.log('🌊 Iniciando carregamento com streaming...');
    
    // Verifica se a função existe no dataLoader
    if (!dataLoader.loadDataWithStreaming) {
      Utils.log('❌ Função loadDataWithStreaming não encontrada no dataLoader');
      // Fallback para carregamento tradicional
      return this.loadDataTraditional(filtros);
    }
    
    // Verifica se streaming loader está disponível
    if (typeof streamingLoader === 'undefined') {
      Utils.log('⚠️ Streaming loader não carregado, usando método tradicional');
      return this.loadDataTraditional(filtros);
    }
    
    let chunksRenderizados = 0;
    let dadosAcumulados = [];
    let primeiraRenderizacao = true;
    
    // Configura callbacks
    const callbacks = {
      onChunk: (chunk, metrics) => {
        // Acumula dados
        dadosAcumulados = dadosAcumulados.concat(chunk.rows);
        chunksRenderizados++;
        
        // Renderiza incrementalmente a cada N chunks ou N linhas
        const shouldRender = 
          primeiraRenderizacao ||
          chunksRenderizados % 5 === 0 || 
          dadosAcumulados.length >= 10000;
        
        if (shouldRender && dadosAcumulados.length > 0) {
          const renderStart = performance.now();
          
          if (primeiraRenderizacao) {
            // Primeira renderização - cria estrutura
            this.virtualTable.render(dadosAcumulados);
            primeiraRenderizacao = false;
          } else {
            // Renderizações subsequentes - atualiza dados
            this.virtualTable.updateData(dadosAcumulados);
          }
          
          const renderTime = (performance.now() - renderStart) / 1000;
          Utils.log(`🎨 Renderização incremental: ${renderTime.toFixed(3)}s`);
        }
        
        // Atualiza contador
        this.virtualTable.updateRowCount(metrics.linhasRecebidas);
      },
      
      onProgress: (progress) => {
        // Atualiza UI com progresso
        const percent = Math.min(100, (progress.chunksRecebidos / 20) * 100);
        this.virtualTable.updateLoadingProgress(
          `Carregando... ${progress.linhasRecebidas.toLocaleString('pt-BR')} linhas`,
          percent
        );
      }
    };
    
    try {
      // Inicia streaming
      const resultado = await dataLoader.loadDataWithStreaming(
        this.questionId, 
        filtros,
        callbacks
      );
      
      // Renderização final se necessário
      if (resultado.data && resultado.data.length > 0) {
        if (primeiraRenderizacao) {
          this.virtualTable.render(resultado.data);
        } else {
          this.virtualTable.updateData(resultado.data);
        }
        
        // Mostra métricas finais
        const metrics = resultado.metrics;
        Utils.showNotification(
          `✅ ${metrics.linhasRecebidas.toLocaleString('pt-BR')} linhas carregadas em ${metrics.tempoTotal.toFixed(1)}s`,
          'success',
          5000
        );
      } else {
        this.virtualTable.renderEmpty();
      }
      
    } catch (error) {
      throw error;
    }
  }

  /**
   * Carrega script do streaming loader dinamicamente
   */
  async loadStreamingScript() {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'js/streaming-data-loader.js';
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  /**
   * Decide se deve usar streaming
   */
  async shouldUseStreaming(filtros) {
    // Usa streaming se tiver poucos filtros (indica dataset grande)
    const numFiltros = Object.keys(filtros).length;
    return numFiltros < 3;
  }

  /**
   * Inicia monitoramento de mudanças
   */
  startMonitoring() {
    const check = async () => {
      // Verifica filtros
      const filtros = filtrosManager.capturarFiltrosParent();
      
      if (filtrosManager.filtrosMudaram(filtros)) {
        Utils.log('🔄 Filtros mudaram, atualizando...');
        filtrosManager.notificarMudanca();
        
        // Reset intervalo para 1s após mudança
        this.checkInterval = 1000;
      } else {
        // Aumenta intervalo gradualmente até 5s
        this.checkInterval = Math.min(5000, this.checkInterval + 500);
      }
      
      // Agenda próxima verificação
      this.checkTimer = setTimeout(check, this.checkInterval);
    };
    
    // Inicia verificação
    this.checkTimer = setTimeout(check, this.checkInterval);
  }

  /**
   * Para monitoramento
   */
  stopMonitoring() {
    if (this.checkTimer) {
      clearTimeout(this.checkTimer);
      this.checkTimer = null;
    }
  }

  /**
   * Mostra informações no console
   */
  showConsoleInfo() {
    console.log('%c🎯 Metabase Tabela Virtual', 'font-size: 20px; color: #2196F3');
    console.log('%cAtalhos disponíveis:', 'font-weight: bold');
    console.log('  Ctrl+R: Recarregar dados');
    console.log('  Ctrl+E: Exportar CSV');
    console.log('  Ctrl+S: Toggle streaming');
    console.log('\n%cComandos úteis:', 'font-weight: bold');
    console.log('  app.loadData() - Recarrega dados');
    console.log('  app.getStats() - Mostra estatísticas');
    console.log('  app.useStreaming = true - Ativa streaming');
    console.log('  dataLoader.clearCache() - Limpa cache');
    console.log('  filtrosManager.filtrosAtuais - Mostra filtros ativos');
  }

  /**
   * Obtém estatísticas da aplicação
   */
  getStats() {
    const stats = {
      questionId: this.questionId,
      filtros: filtrosManager.filtrosAtuais,
      tabela: this.virtualTable.getStats(),
      loader: dataLoader.getStats(),
      memoria: Utils.checkMemory(),
      streaming: this.useStreaming
    };
    
    // Adiciona stats do streaming se disponível
    if (typeof streamingLoader !== 'undefined') {
      stats.streamingStats = streamingLoader.getStats();
    }
    
    return stats;
  }

  /**
   * Destrói a aplicação
   */
  destroy() {
    this.stopMonitoring();
    
    if (this.virtualTable) {
      this.virtualTable.destroy();
    }
    
    dataLoader.cancel();
    dataLoader.clearCache();
    
    // Para streaming se estiver ativo
    if (typeof streamingLoader !== 'undefined') {
      streamingLoader.stop();
    }
  }
}

// Inicializa quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', async () => {
  // Cria instância global da aplicação
  window.app = new App();
  await app.init();
});

// Cleanup ao sair
window.addEventListener('beforeunload', () => {
  if (window.app) {
    window.app.destroy();
  }
});
