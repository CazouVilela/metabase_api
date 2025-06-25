// componentes/tabela_virtual/js/virtual-table.js
/**
 * Módulo de renderização de tabela virtual
 */

class VirtualTable {
  constructor(container) {
    this.container = container;
    this.data = [];
    this.columns = [];
    this.clusterize = null;
    this.updateCount = 0;
  }

  /**
   * Renderiza tabela com dados
   */
  render(data) {
    const startTime = performance.now();
    
    this.data = data;
    this.columns = Object.keys(data[0] || {});
    this.updateCount++;

    Utils.log(`🎨 Renderizando ${data.length} linhas...`);

    // Cria estrutura HTML
    this.createStructure();

    // Usa ClusterizeJS para virtualização
    if (data.length > 1000) {
      this.renderWithClusterize();
    } else {
      this.renderSimple();
    }

    const elapsed = Utils.getElapsedTime(startTime);
    Utils.log(`✅ Renderizado em ${elapsed}s`);

    // Mostra notificação
    if (this.updateCount > 1) {
      Utils.showNotification('🔄 Tabela atualizada', 'success');
    }
  }

  /**
   * Cria estrutura base da tabela
   */
  createStructure() {
    const totalFormatted = Utils.formatNumber(this.data.length);
    
    this.container.innerHTML = `
      <div class="table-info">
        <div class="table-info-left">
          <div class="record-count">
            📊 Total: <strong>${totalFormatted}</strong> registros
          </div>
          ${this.data.length > 1000 ? '<span class="performance-badge">⚡ Virtualização Ativa</span>' : ''}
        </div>
        <div class="table-info-right">
          <span class="update-time">✅ ${Utils.formatDateTime()}</span>
          <span class="text-muted">(Update #${this.updateCount})</span>
        </div>
      </div>
      <div id="table-wrapper"></div>
    `;
  }

  /**
   * Renderização com ClusterizeJS (virtualizada)
   */
  renderWithClusterize() {
    const wrapper = document.getElementById('table-wrapper');
    
    // Header da tabela
    const headerHtml = this.createHeader();
    
    // Prepara linhas como strings HTML
    const rows = this.data.map(row => this.createRowHtml(row));
    
    // HTML do container
    wrapper.innerHTML = `
      ${headerHtml}
      <div id="scrollArea" class="clusterize-scroll">
        <table>
          <tbody id="contentArea" class="clusterize-content">
            <tr class="clusterize-no-data">
              <td colspan="${this.columns.length}">Carregando...</td>
            </tr>
          </tbody>
        </table>
      </div>
    `;

    // Destrói instância anterior se existir
    if (this.clusterize) {
      this.clusterize.destroy();
    }

    // Inicializa ClusterizeJS
    this.clusterize = new Clusterize({
      rows: rows,
      scrollId: 'scrollArea',
      contentId: 'contentArea',
      rows_in_block: 50,
      blocks_in_cluster: 4,
      show_no_data_row: false
    });
  }

  /**
   * Renderização simples (sem virtualização)
   */
  renderSimple() {
    const wrapper = document.getElementById('table-wrapper');
    
    // Constrói HTML como string
    let html = [this.createHeader()];
    
    html.push('<div class="clusterize-scroll"><table><tbody>');
    
    // Adiciona linhas
    this.data.forEach(row => {
      html.push(this.createRowHtml(row));
    });
    
    html.push('</tbody></table></div>');
    
    wrapper.innerHTML = html.join('');
  }

  /**
   * Cria HTML do header
   */
  createHeader() {
    const headers = this.columns.map(col => 
      `<th title="${col}">${Utils.escapeHtml(col)}</th>`
    ).join('');
    
    return `
      <table>
        <thead>
          <tr>${headers}</tr>
        </thead>
      </table>
    `;
  }

  /**
   * Cria HTML de uma linha
   */
  createRowHtml(row) {
    const cells = this.columns.map(col => {
      const value = row[col];
      const escaped = Utils.escapeHtml(value);
      return `<td title="${escaped}">${escaped}</td>`;
    }).join('');
    
    return `<tr>${cells}</tr>`;
  }

  /**
   * Renderiza estado vazio
   */
  renderEmpty() {
    this.container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <p>Nenhum dado encontrado com os filtros aplicados</p>
      </div>
    `;
  }

  /**
   * Renderiza estado de erro
   */
  renderError(error) {
    this.container.innerHTML = `
      <div class="error-message">
        <strong>❌ Erro ao carregar dados</strong>
        <pre>${Utils.escapeHtml(error.message)}</pre>
      </div>
    `;
  }

  /**
   * Renderiza loading
   */
  renderLoading(message = 'Carregando dados...') {
    this.container.innerHTML = `
      <div class="loading-container">
        <div class="spinner"></div>
        <p>${message}</p>
      </div>
    `;
  }

  /**
   * Atualiza apenas informações da tabela
   */
  updateInfo() {
    const infoElement = this.container.querySelector('.table-info-right');
    if (infoElement) {
      infoElement.innerHTML = `
        <span class="update-time">✅ ${Utils.formatDateTime()}</span>
        <span class="text-muted">(Update #${this.updateCount})</span>
      `;
    }
  }

  /**
   * Exporta dados para CSV
   */
  exportToCsv() {
    if (!this.data || this.data.length === 0) {
      Utils.showNotification('Nenhum dado para exportar', 'warning');
      return;
    }

    // Header
    let csv = this.columns.join(',') + '\n';
    
    // Dados
    this.data.forEach(row => {
      const values = this.columns.map(col => {
        const value = row[col] || '';
        // Escapa valores com vírgulas ou quebras de linha
        if (value.toString().includes(',') || value.toString().includes('\n')) {
          return `"${value.toString().replace(/"/g, '""')}"`;
        }
        return value;
      });
      
      csv += values.join(',') + '\n';
    });

    // Download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `export_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    Utils.showNotification('✅ Dados exportados', 'success');
  }

  /**
   * Destrói a tabela e limpa recursos
   */
  destroy() {
    if (this.clusterize) {
      this.clusterize.destroy();
      this.clusterize = null;
    }
    
    this.data = [];
    this.columns = [];
    this.container.innerHTML = '';
  }

  /**
   * Obtém estatísticas da tabela
   */
  getStats() {
    return {
      totalRows: this.data.length,
      totalColumns: this.columns.length,
      updateCount: this.updateCount,
      isVirtualized: this.clusterize !== null
    };
  }
}

// Não cria instância global aqui, será criada no main.js
