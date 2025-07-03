// componentes/tabela_virtual/js/main.js
/**
 * Arquivo principal - Versão Otimizada
 * Usa apenas Native Performance
 */

class App {
  constructor() {
    this.questionId = null;
    this.virtualTable = null;
    this.checkInterval = 1000;
    this.checkTimer = null;
    
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
    Utils.log('🚀 Iniciando aplicação (Native Performance)...');
    
    try {
      // Obtém ID da questão
      this.questionId = Utils.getUrlParams().question_id || '51';
      
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
    });

    // Observer para mudanças de filtros
    filtrosManager.onChange(() => {
      this.loadData('mudança de filtros');
    });
  }

  /**
   * Carrega dados usando Native Performance
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
      
      const startTime = performance.now();
      
      // Carrega dados com Native Performance
      const dados = await dataLoader.loadWithRetry(this.questionId, filtros);
      
      if (!dados) {
        this.virtualTable.renderEmpty();
        return;
      }

      // Renderiza tabela
      if (Array.isArray(dados) && dados.length > 0) {
        const loadTime = (performance.now() - startTime) / 1000;
        Utils.log(`⏱️  Tempo de carregamento (Native): ${loadTime.toFixed(2)}s`);
        
        const renderStart = performance.now();
        this.virtualTable.render(dados);
        const renderTime = (performance.now() - renderStart) / 1000;
        
        Utils.log(`⏱️  Tempo de renderização: ${renderTime.toFixed(2)}s`);
        Utils.log(`⏱️  TEMPO TOTAL: ${(loadTime + renderTime).toFixed(2)}s`);
        
        // Monitora memória se muitos dados
        if (dados.length > 10000) {
          this.monitorMemory();
        }
      } else if (dados.error) {
        throw new Error(dados.error);
      } else {
        this.virtualTable.renderEmpty();
      }
      
    } catch (error) {
      Utils.log('❌ Erro ao carregar dados:', error);
      this.virtualTable.renderError(error);
    }
  }

  /**
   * Monitora uso de memória
   */
  monitorMemory() {
    const mem = Utils.checkMemory();
    
    if (mem && mem.isHigh) {
      Utils.log('⚠️ Memória alta:', `${mem.used}MB de ${mem.limit}MB (${mem.percent}%)`);
      
      // Limpa cache se memória estiver muito alta
      if (mem.percent > 90) {
        dataLoader.clearCache();
      }
    }
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
    console.log('%c🎯 Metabase Tabela Virtual (Native Performance)', 'font-size: 20px; color: #2196F3');
    console.log('%cAtalhos disponíveis:', 'font-weight: bold');
    console.log('  Ctrl+R: Recarregar dados');
    console.log('  Ctrl+E: Exportar CSV');
    console.log('\n%cComandos úteis:', 'font-weight: bold');
    console.log('  app.loadData() - Recarrega dados');
    console.log('  app.getStats() - Mostra estatísticas');
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
      performance: 'Native (Otimizado)'
    };
    
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
    
    dataLoader.clearCache();
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
