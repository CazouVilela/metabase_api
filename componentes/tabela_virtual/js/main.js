// componentes/tabela_virtual/js/main.js
/**
 * Arquivo principal - Versão OTIMIZADA para grandes volumes
 */

class App {
  constructor() {
    this.questionId = null;
    this.virtualTable = null;
    this.apiClient = null;
    this.dataProcessor = null;
    
    // REMOVIDO: lastDataResponse que duplicava dados
    // Agora usa referência direta da virtualTable quando necessário
    
    // Elementos DOM
    this.elements = {
      container: document.getElementById('table-container'),
      debug: document.getElementById('debug-container')
    };
    
    // Controle de memória
    this.memoryCheckInterval = null;
    this.lastMemoryWarning = 0;
    this.isLoading = false;
  }

  /**
   * Inicializa a aplicação
   */
  async init() {
    Utils.log('🚀 Iniciando aplicação (Versão Ultra-Otimizada)...');
    
    try {
      // Adiciona estilos necessários para virtualização
      this.injectVirtualizationStyles();
      
      // Obtém ID da questão
      this.questionId = Utils.getUrlParams().question_id || '51';
      
      // Inicializa serviços compartilhados
      this.apiClient = new MetabaseAPIClient();
      this.dataProcessor = new DataProcessor();
      
      // Cria tabela virtual
      this.virtualTable = new VirtualTable(this.elements.container);
      
      // Configura listeners
      this.setupListeners();
      
      // Inicia monitoramento de memória
      this.startMemoryMonitoring();
      
      // Carrega dados iniciais
      await this.loadData('inicialização');
      
      // Inicia monitoramento automático de filtros (com delay para evitar conflitos)
      setTimeout(() => {
        filterManager.startMonitoring(2000); // Verifica a cada 2 segundos
      }, 3000); // Aguarda 3 segundos antes de iniciar monitoramento
      
      // Mostra informações no console
      this.showConsoleInfo();
      
    } catch (error) {
      Utils.log('❌ Erro na inicialização:', error);
      this.virtualTable.renderError(error);
    }
  }

  /**
   * Injeta estilos necessários para virtualização
   */
  injectVirtualizationStyles() {
    const styleId = 'virtual-table-styles';
    
    // Verifica se já foi injetado
    if (document.getElementById(styleId)) return;
    
    const styles = `
      .virtual-scroll-area {
        position: relative;
        overflow-y: auto;
        overflow-x: auto;
        height: 600px;
        border: 1px solid #ddd;
      }
      .virtual-scroll-spacer {
        position: relative;
        width: 100%;
        min-width: max-content;
      }
      .virtual-content {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        min-width: max-content;
      }
      .virtual-content table {
        width: 100%;
        border-collapse: collapse;
        min-width: max-content;
      }
      .virtual-content tr {
        display: table-row;
        border-bottom: 1px solid #eee;
      }
      .virtual-content td {
        padding: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 300px;
      }
      #table-wrapper > table {
        position: sticky;
        top: 0;
        background: white;
        z-index: 10;
        border-bottom: 2px solid #ddd;
        min-width: max-content;
      }
      .clusterize-scroll {
        max-height: 600px;
        overflow: auto;
      }
    `;
    
    const styleElement = document.createElement('style');
    styleElement.id = styleId;
    styleElement.textContent = styles;
    document.head.appendChild(styleElement);
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
        this.exportData();
      }
      
      // Ctrl/Cmd + M: Mostrar estatísticas de memória
      if ((e.ctrlKey || e.metaKey) && e.key === 'm') {
        e.preventDefault();
        this.showMemoryStats();
      }
    });

    // Observer para mudanças de filtros
    filterManager.onChange(() => {
      // Evita recarregar se já está carregando
      if (this.isLoading) {
        Utils.log('⏳ Ignorando mudança de filtros - já está carregando');
        return;
      }
      
      Utils.log('📍 Filtros mudaram, atualizando dados...');
      this.loadData('mudança de filtros');
    });
    
    // Handler global para erros de memória
    window.addEventListener('error', (event) => {
      if (event.message && event.message.includes('out of memory')) {
        this.handleOutOfMemoryError();
      }
    });
  }

  /**
   * Carrega dados mantendo formato colunar quando possível
   */
  async loadData(motivo = 'manual') {
    // Evita múltiplas requisições simultâneas
    if (this.isLoading) {
      Utils.log('⏳ Requisição já em andamento, ignorando...');
      return;
    }
    
    this.isLoading = true;
    
    try {
      Utils.log(`🔄 Carregando dados (${motivo})...`);
      
      // IMPORTANTE: Sempre captura os filtros atuais do parent
      const filtros = filterManager.captureFromParent();
      
      // Atualiza debug
      this.renderDebug();
      
      // Mostra loading
      this.virtualTable.renderLoading();
      
      // Força garbage collection se possível
      if (window.gc) {
        window.gc();
        Utils.log('🗑️ Garbage collection forçado');
      }
      
      const startTime = performance.now();
      
      // Carrega dados usando apiClient compartilhado
      const response = await this.apiClient.queryData(this.questionId, filtros);
      
      if (!response || !response.data || !response.data.rows || response.data.rows.length === 0) {
        Utils.log('⚠️ Nenhum dado retornado da API');
        this.virtualTable.renderEmpty();
        return;
      }

      // Verifica se tem o formato nativo do Metabase (colunar)
      if (response.data && response.data.rows && response.data.cols) {
        const rowCount = response.data.rows.length;
        
        Utils.log(`📊 Dados recebidos: ${rowCount.toLocaleString('pt-BR')} linhas em formato colunar nativo`);
        
        const loadTime = (performance.now() - startTime) / 1000;
        Utils.log(`⏱️  Tempo de carregamento: ${loadTime.toFixed(2)}s`);
        
        const renderStart = performance.now();
        
        // USA FORMATO COLUNAR NATIVO - Muito mais eficiente!
        this.virtualTable.renderNative(response);
        
        const renderTime = (performance.now() - renderStart) / 1000;
        Utils.log(`⏱️  Tempo de renderização: ${renderTime.toFixed(2)}s`);
        Utils.log(`⏱️  TEMPO TOTAL: ${(loadTime + renderTime).toFixed(2)}s`);
        
        // Limpa resposta da memória após renderização
        response.data = null;
        
      } else {
        // Fallback: formato antigo
        let dados = [];
        
        if (response.data && response.data.rows) {
          dados = this.dataProcessor.processNativeResponse(response);
        } else if (Array.isArray(response)) {
          dados = response;
        }

        // Renderiza tabela no formato antigo
        if (dados.length > 0) {
          this.virtualTable.render(dados);
          // Limpa dados após renderização
          dados = null;
        } else {
          this.virtualTable.renderEmpty();
        }
      }
      
      // Força limpeza de memória
      if (response) {
        response.data = null;
      }
      
    } catch (error) {
      Utils.log('❌ Erro ao carregar dados:', error);
      
      // Se for erro de memória, trata especialmente
      if (error.message && error.message.toLowerCase().includes('memory')) {
        this.handleOutOfMemoryError();
      } else {
        this.virtualTable.renderError(error);
      }
    } finally {
      // Sempre libera o flag no final
      this.isLoading = false;
    }
  }

  /**
   * Trata erro de falta de memória
   */
  handleOutOfMemoryError() {
    // Para monitoramento de memória
    this.stopMemoryMonitoring();
    
    this.elements.container.innerHTML = `
      <div class="alert alert-danger" style="margin: 20px;">
        <h3>❌ Erro: Memória Insuficiente</h3>
        <p>O navegador não conseguiu processar o volume de dados.</p>
        
        <h4>Soluções recomendadas:</h4>
        <ul>
          <li><strong>Aplique filtros no dashboard</strong> para reduzir o volume de dados</li>
          <li>Feche outras abas do navegador para liberar memória</li>
          <li>Use um navegador de 64 bits (Chrome/Edge/Firefox)</li>
          <li>Se precisar trabalhar com volumes grandes, exporte para CSV e use Excel/ferramentas especializadas</li>
        </ul>
        
        <div style="margin-top: 20px;">
          <button class="btn btn-primary" onclick="window.location.reload()">
            🔄 Recarregar Página
          </button>
          ${this.virtualTable && this.virtualTable.rows && this.virtualTable.rows.length > 0 ? `
          <button class="btn btn-success" onclick="app.exportDataEmergency()">
            📥 Tentar Exportar CSV
          </button>
          ` : ''}
        </div>
      </div>
    `;
  }

  /**
   * Exportação de emergência (quando há erro de memória)
   */
  exportDataEmergency() {
    try {
      if (this.virtualTable && this.virtualTable.rows) {
        Utils.showNotification('Tentando exportar dados...', 'info');
        this.virtualTable.exportToCsvColumnar();
      }
    } catch (e) {
      Utils.showNotification('Não foi possível exportar: ' + e.message, 'error');
    }
  }

  /**
   * Monitoramento de memória
   */
  startMemoryMonitoring() {
    if (!performance.memory) {
      Utils.log('⚠️ API de memória não disponível neste navegador');
      return;
    }
    
    this.memoryCheckInterval = setInterval(() => {
      const mem = Utils.checkMemory();
      
      if (mem && mem.percent > 80) {
        const now = Date.now();
        
        // Evita spam de avisos (1 por minuto)
        if (now - this.lastMemoryWarning > 60000) {
          this.lastMemoryWarning = now;
          
          Utils.log(`⚠️ Memória alta: ${mem.percent}% (${mem.used}MB/${mem.limit}MB)`);
          
          // Limpa caches
          this.clearCaches();
          
          if (mem.percent > 90) {
            Utils.showNotification('⚠️ Memória crítica! Considere aplicar filtros.', 'warning');
          }
        }
      }
    }, 5000); // Verifica a cada 5 segundos
  }

  /**
   * Para monitoramento de memória
   */
  stopMemoryMonitoring() {
    if (this.memoryCheckInterval) {
      clearInterval(this.memoryCheckInterval);
      this.memoryCheckInterval = null;
    }
  }

  /**
   * Limpa todos os caches
   */
  clearCaches() {
    // Cache do API client
    if (this.apiClient && this.apiClient.cache) {
      this.apiClient.cache.clear();
    }
    
    // Cache da tabela virtual
    if (this.virtualTable && this.virtualTable.clearCache) {
      this.virtualTable.clearCache();
    }
    
    Utils.log('🗑️ Caches limpos para liberar memória');
  }

  /**
   * Renderiza informações de debug
   */
  renderDebug() {
    const debugInfo = filterManager.getDebugInfo();
    
    let html = `
      <details ${debugInfo.total > 0 ? 'open' : ''}>
        <summary>
          🔍 Debug de Filtros 
          <span class="text-small text-muted">(${debugInfo.total} ativos)</span>
        </summary>
        <div class="debug-info">
    `;
    
    if (debugInfo.multiValue.length > 0) {
      html += '<div class="mt-2"><strong>🔹 Filtros com Múltiplos Valores:</strong></div>';
      debugInfo.multiValue.forEach(f => {
        html += `
          <div class="mt-1 text-small">
            <strong>${f.name}:</strong> ${f.count} valores
            <ul style="margin: 5px 0 0 20px;">
              ${f.values.map(v => `<li>${Utils.escapeHtml(v)}</li>`).join('')}
            </ul>
          </div>
        `;
      });
    }
    
    if (debugInfo.specialChars.length > 0) {
      html += '<div class="mt-2"><strong>⚠️ Caracteres Especiais:</strong></div>';
      debugInfo.specialChars.forEach(f => {
        html += `
          <div class="mt-1 text-small">
            <strong>${f.filter}:</strong> ${f.chars.map(c => `<code>${c}</code>`).join(', ')}
          </div>
        `;
      });
    }
    
    html += `
          <details class="mt-2">
            <summary>JSON completo</summary>
            <pre>${JSON.stringify(debugInfo.filters, null, 2)}</pre>
          </details>
        </div>
      </details>
    `;
    
    this.elements.debug.innerHTML = html;
  }

  /**
   * Exporta dados (otimizado para formato colunar)
   */
  exportData() {
    // Usa dados diretamente da tabela virtual
    if (this.virtualTable.isColumnarFormat && this.virtualTable.rows && this.virtualTable.rows.length > 0) {
      this.virtualTable.exportToCsvColumnar();
    } else if (this.virtualTable.data && this.virtualTable.data.length > 0) {
      // Formato antigo
      if (typeof ExportUtils !== 'undefined') {
        ExportUtils.exportToCSV(this.virtualTable.data, `export_${new Date().toISOString().split('T')[0]}`);
      } else {
        this.virtualTable.exportToCsv();
      }
    } else {
      Utils.showNotification('Nenhum dado para exportar', 'warning');
    }
  }

  /**
   * Mostra estatísticas de memória
   */
  showMemoryStats() {
    const stats = this.getStats();
    const mem = stats.memoria;
    
    let message = '📊 Estatísticas:\n\n';
    message += `Linhas: ${stats.tabela.totalRows.toLocaleString('pt-BR')}\n`;
    message += `Formato: ${stats.tabela.format}\n`;
    
    if (stats.tabela.cache) {
      message += `\nCache HTML:\n`;
      message += `- Tamanho: ${stats.tabela.cache.size}/${stats.tabela.cache.maxSize}\n`;
      message += `- Taxa de acerto: ${stats.tabela.cache.hitRate}%\n`;
    }
    
    if (mem) {
      message += `\nMemória:\n`;
      message += `- Usado: ${mem.used}MB\n`;
      message += `- Limite: ${mem.limit}MB\n`;
      message += `- Percentual: ${mem.percent}%\n`;
    }
    
    alert(message);
  }

  /**
   * Mostra informações no console
   */
  showConsoleInfo() {
    console.log('%c🎯 Metabase Tabela Virtual (Ultra-Otimizada)', 'font-size: 20px; color: #2196F3');
    console.log('%cAtalhos disponíveis:', 'font-weight: bold');
    console.log('  Ctrl+R: Recarregar dados');
    console.log('  Ctrl+E: Exportar CSV');
    console.log('  Ctrl+M: Mostrar estatísticas de memória');
    console.log('\n%cComandos úteis:', 'font-weight: bold');
    console.log('  app.loadData() - Recarrega dados');
    console.log('  app.getStats() - Mostra estatísticas completas');
    console.log('  app.showMemoryStats() - Mostra uso de memória');
    console.log('  app.clearCaches() - Limpa caches');
    console.log('  app.exportData() - Exporta dados');
    console.log('  app.debugFilters() - Mostra estado dos filtros');
    console.log('  app.loadDataNoFilters() - Carrega sem filtros (debug)');
    console.log('  filterManager.currentFilters - Mostra filtros ativos');
    console.log('  filterManager.stopMonitoring() - Para monitoramento');
    console.log('\n%cOtimizações:', 'font-weight: bold');
    console.log('  ✅ Virtualização real: apenas ~100 linhas no DOM');
    console.log('  ✅ Renderização sob demanda durante scroll');
    console.log('  ✅ Zero duplicação de dados');
    console.log('  ✅ Suporta milhões de linhas sem problemas');
    console.log('\n%cDica de Debug:', 'font-weight: bold; color: orange');
    console.log('  Se a tabela estiver sumindo, execute no console:');
    console.log('  1. filterManager.stopMonitoring() - Para o monitoramento');
    console.log('  2. app.debugFilters() - Verifica estado dos filtros');
    console.log('  3. app.loadData("debug manual") - Recarrega manualmente');
    console.log('  4. app.loadDataNoFilters() - Carrega sem filtros');
  }

  /**
   * Obtém estatísticas da aplicação
   */
  getStats() {
    const stats = {
      questionId: this.questionId,
      filtros: filterManager.currentFilters,
      tabela: this.virtualTable.getStats(),
      memoria: Utils.checkMemory(),
      monitoramento: {
        filtros: filterManager.monitoringInterval ? 'ativo' : 'inativo',
        memoria: this.memoryCheckInterval ? 'ativo' : 'inativo'
      },
      performance: 'Ultra-otimizado com virtualização real'
    };
    
    return stats;
  }

  /**
   * Carrega dados sem filtros (para debug)
   */
  async loadDataNoFilters() {
    console.log('🔧 Carregando dados sem filtros...');
    filterManager.stopMonitoring();
    filterManager.currentFilters = {};
    await this.loadData('debug sem filtros');
  }

  /**
   * Debug de filtros
   */
  debugFilters() {
    console.log('🔍 Debug de Filtros:');
    console.log('  Filtros atuais:', filterManager.currentFilters);
    console.log('  Total de filtros:', Object.keys(filterManager.currentFilters).length);
    console.log('  Monitoramento:', filterManager.monitoringInterval ? 'Ativo' : 'Inativo');
    console.log('  Está carregando:', this.isLoading);
    console.log('  Question ID:', this.questionId);
    
    // Tenta capturar filtros novamente
    const newFilters = filterManager.captureFromParent();
    console.log('  Filtros capturados agora:', newFilters);
    
    // Compara
    const hasChanged = JSON.stringify(newFilters) !== JSON.stringify(filterManager.currentFilters);
    console.log('  Mudou desde última captura:', hasChanged);
    
    return {
      current: filterManager.currentFilters,
      captured: newFilters,
      changed: hasChanged
    };
  }

  /**
   * Destrói a aplicação
   */
  destroy() {
    // Para monitoramentos
    filterManager.stopMonitoring();
    this.stopMemoryMonitoring();
    
    // Destrói tabela
    if (this.virtualTable) {
      this.virtualTable.destroy();
      this.virtualTable = null;
    }
    
    // Limpa caches
    this.clearCaches();
    
    // Limpa referências
    this.apiClient = null;
    this.dataProcessor = null;
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

// Tratamento global de erros
window.addEventListener('unhandledrejection', event => {
  console.error('Erro não tratado:', event.reason);
  
  if (event.reason && event.reason.message && event.reason.message.toLowerCase().includes('memory')) {
    if (window.app) {
      window.app.handleOutOfMemoryError();
    }
  }
});
