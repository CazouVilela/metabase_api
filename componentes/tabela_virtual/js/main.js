// componentes/tabela_virtual/js/main.js
/**
 * Arquivo principal - Versão com Recursos Compartilhados e Formato Colunar
 */

class App {
  constructor() {
    this.questionId = null;
    this.virtualTable = null;
    this.apiClient = null;
    this.dataProcessor = null;
    this.lastDataResponse = null; // Armazena última resposta para exportação
    
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
    Utils.log('🚀 Iniciando aplicação (Recursos Compartilhados + Formato Colunar)...');
    
    try {
      // Obtém ID da questão
      this.questionId = Utils.getUrlParams().question_id || '51';
      
      // Inicializa serviços compartilhados
      this.apiClient = new MetabaseAPIClient();
      this.dataProcessor = new DataProcessor();
      
      // Cria tabela virtual
      this.virtualTable = new VirtualTable(this.elements.container);
      
      // Configura listeners
      this.setupListeners();
      
      // Carrega dados iniciais
      await this.loadData('inicialização');
      
      // Inicia monitoramento automático de filtros
      filterManager.startMonitoring(1000); // Verifica a cada 1 segundo
      
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
        this.exportData();
      }
    });

    // Observer para mudanças de filtros
    filterManager.onChange(() => {
      Utils.log('📍 Filtros mudaram, atualizando dados...');
      this.loadData('mudança de filtros');
    });
    
    // Handler global para erros de memória
    window.addEventListener('error', (event) => {
      if (event.message && event.message.includes('Out of Memory')) {
        this.handleOutOfMemoryError();
      }
    });
  }

  /**
   * Carrega dados mantendo formato colunar quando possível
   */
  async loadData(motivo = 'manual') {
    try {
      Utils.log(`🔄 Carregando dados (${motivo})...`);
      
      // IMPORTANTE: Sempre captura os filtros atuais do parent
      const filtros = filterManager.captureFromParent();
      
      // Atualiza debug
      this.renderDebug();
      
      // Mostra loading
      this.virtualTable.renderLoading();
      
      const startTime = performance.now();
      
      // Carrega dados usando apiClient compartilhado
      const response = await this.apiClient.queryData(this.questionId, filtros);
      
      if (!response) {
        this.virtualTable.renderEmpty();
        return;
      }

      // Armazena resposta para possível exportação
      this.lastDataResponse = response;

      // Verifica se tem o formato nativo do Metabase (colunar)
      if (response.data && response.data.rows && response.data.cols) {
        const rowCount = response.data.rows.length;
        
        Utils.log(`📊 Dados recebidos: ${rowCount} linhas em formato colunar nativo`);
        
        const loadTime = (performance.now() - startTime) / 1000;
        Utils.log(`⏱️  Tempo de carregamento: ${loadTime.toFixed(2)}s`);
        
        const renderStart = performance.now();
        
        // USA FORMATO COLUNAR NATIVO - Muito mais eficiente!
        this.virtualTable.renderNative(response);
        
        const renderTime = (performance.now() - renderStart) / 1000;
        Utils.log(`⏱️  Tempo de renderização: ${renderTime.toFixed(2)}s`);
        Utils.log(`⏱️  TEMPO TOTAL: ${(loadTime + renderTime).toFixed(2)}s`);
        
        // Monitora memória
        if (rowCount > 10000) {
          this.monitorMemory();
        }
        
      } else {
        // Fallback: Processa dados no formato antigo se necessário
        let dados = [];
        
        if (response.data && response.data.rows) {
          dados = this.dataProcessor.processNativeResponse(response);
        } else if (Array.isArray(response)) {
          dados = response;
        }

        // Renderiza tabela no formato antigo
        if (dados.length > 0) {
          const loadTime = (performance.now() - startTime) / 1000;
          Utils.log(`⏱️  Tempo de carregamento: ${loadTime.toFixed(2)}s`);
          
          const renderStart = performance.now();
          this.virtualTable.render(dados);
          const renderTime = (performance.now() - renderStart) / 1000;
          
          Utils.log(`⏱️  Tempo de renderização: ${renderTime.toFixed(2)}s`);
          Utils.log(`⏱️  TEMPO TOTAL: ${(loadTime + renderTime).toFixed(2)}s`);
        } else {
          this.virtualTable.renderEmpty();
        }
      }
      
    } catch (error) {
      Utils.log('❌ Erro ao carregar dados:', error);
      
      // Se for erro de memória, trata especialmente
      if (error.message && error.message.includes('memory')) {
        this.handleOutOfMemoryError();
      } else {
        this.virtualTable.renderError(error);
      }
    }
  }

  /**
   * Trata erro de falta de memória
   */
  handleOutOfMemoryError() {
    this.elements.container.innerHTML = `
      <div class="alert alert-danger" style="margin: 20px;">
        <h3>❌ Erro: Memória Insuficiente</h3>
        <p>O navegador não conseguiu processar o volume de dados.</p>
        
        <h4>Soluções recomendadas:</h4>
        <ul>
          <li>Aplique filtros no dashboard para reduzir o volume de dados</li>
          <li>Feche outras abas do navegador para liberar memória</li>
          <li>Use um navegador de 64 bits</li>
          <li>Aumente a memória do Chrome iniciando com: <code>--max-old-space-size=4096</code></li>
        </ul>
        
        ${this.lastDataResponse ? `
        <div style="margin-top: 20px;">
          <p>Os dados foram carregados do servidor. Você ainda pode:</p>
          <button class="btn btn-success" onclick="app.exportData()">
            📥 Exportar para CSV
          </button>
        </div>
        ` : ''}
      </div>
    `;
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
    // Se temos dados no formato colunar
    if (this.virtualTable.isColumnarFormat && this.virtualTable.rows && this.virtualTable.rows.length > 0) {
      // Usa exportação colunar otimizada
      this.virtualTable.exportToCsvColumnar();
    } else if (this.lastDataResponse && this.lastDataResponse.data && this.lastDataResponse.data.rows) {
      // Se tem resposta guardada mas tabela não está em formato colunar
      Utils.showNotification('Preparando exportação completa...', 'info');
      
      // Cria tabela temporária para exportar
      const tempTable = new VirtualTable(document.createElement('div'));
      tempTable.cols = this.lastDataResponse.data.cols;
      tempTable.rows = this.lastDataResponse.data.rows;
      tempTable.isColumnarFormat = true;
      tempTable.exportToCsvColumnar();
    } else if (this.virtualTable.data && this.virtualTable.data.length > 0) {
      // Fallback para formato antigo
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
   * Monitora uso de memória
   */
  monitorMemory() {
    const mem = Utils.checkMemory();
    
    if (mem && mem.isHigh) {
      Utils.log('⚠️ Memória alta:', `${mem.used}MB de ${mem.limit}MB (${mem.percent}%)`);
      
      // Limpa cache se memória estiver muito alta
      if (mem.percent > 90 && this.apiClient) {
        // O apiClient tem cache interno
        this.apiClient.cache.clear();
        Utils.log('🗑️ Cache limpo devido a memória alta');
      }
    }
  }

  /**
   * Mostra informações no console
   */
  showConsoleInfo() {
    console.log('%c🎯 Metabase Tabela Virtual (Formato Colunar Otimizado)', 'font-size: 20px; color: #2196F3');
    console.log('%cAtalhos disponíveis:', 'font-weight: bold');
    console.log('  Ctrl+R: Recarregar dados');
    console.log('  Ctrl+E: Exportar CSV');
    console.log('\n%cComandos úteis:', 'font-weight: bold');
    console.log('  app.loadData() - Recarrega dados');
    console.log('  app.getStats() - Mostra estatísticas');
    console.log('  app.exportData() - Exporta dados');
    console.log('  filterManager.currentFilters - Mostra filtros ativos');
    console.log('  filterManager.stopMonitoring() - Para monitoramento');
    console.log('  filterManager.startMonitoring(500) - Inicia com intervalo customizado');
    console.log('\n%cPerformance:', 'font-weight: bold');
    console.log('  Suporta 600.000+ linhas usando formato colunar nativo');
    console.log('  3x menos uso de memória comparado ao formato de objetos');
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
      monitoramento: filterManager.monitoringInterval ? 'ativo' : 'inativo',
      performance: 'Formato Colunar Otimizado',
      ultimoVolume: this.lastDataResponse ? 
        (this.lastDataResponse.row_count || 
         (this.lastDataResponse.data && this.lastDataResponse.data.rows ? 
          this.lastDataResponse.data.rows.length : 0)) : 0
    };
    
    return stats;
  }

  /**
   * Destrói a aplicação
   */
  destroy() {
    // Para monitoramento de filtros
    filterManager.stopMonitoring();
    
    // Destrói tabela
    if (this.virtualTable) {
      this.virtualTable.destroy();
    }
    
    // Limpa cache do apiClient
    if (this.apiClient) {
      this.apiClient.cache.clear();
    }
    
    // Limpa referências
    this.lastDataResponse = null;
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
