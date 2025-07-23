// componentes/tabela_virtual/js/virtual-table.js
/**
 * Módulo de renderização de tabela virtual com suporte a formato colunar
 */

class VirtualTable {
  constructor(container) {
    this.container = container;
    this.data = [];      // Para formato de objetos (compatibilidade)
    this.columns = [];   // Para formato de objetos
    this.cols = [];      // Para formato colunar (metadados)
    this.rows = [];      // Para formato colunar (dados)
    this.isColumnarFormat = false; // Indica qual formato está em uso
    this.clusterize = null;
    this.updateCount = 0;
  }

  /**
   * Renderiza tabela com dados no formato de objetos (compatibilidade)
   */
  render(data) {
    const startTime = performance.now();
    
    this.data = data;
    this.columns = Object.keys(data[0] || {});
    this.isColumnarFormat = false;
    this.updateCount++;

    Utils.log(`🎨 Renderizando ${data.length} linhas (formato objeto)...`);

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
   * Renderiza dados no formato nativo do Metabase (colunar) - OTIMIZADO
   */
  renderNative(response) {
    const startTime = performance.now();
    
    // Armazena no formato colunar - NÃO CONVERTE!
    this.cols = response.data.cols;
    this.rows = response.data.rows;
    this.isColumnarFormat = true;
    this.updateCount++;

    Utils.log(`🎨 Renderizando ${this.rows.length} linhas (formato colunar nativo)...`);

    // Cria estrutura HTML
    this.createStructureColumnar();

    // Sempre usa virtualização para formato colunar
    this.renderWithClusterizeColumnar();

    const elapsed = Utils.getElapsedTime(startTime);
    Utils.log(`✅ Renderizado em ${elapsed}s com formato colunar`);

    // Mostra notificação
    if (this.updateCount > 1) {
      Utils.showNotification('🔄 Tabela atualizada', 'success');
    }
  }

  /**
   * Cria estrutura base da tabela (formato objeto)
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
   * Cria estrutura para formato colunar
   */
  createStructureColumnar() {
    const totalFormatted = Utils.formatNumber(this.rows.length);
    
    this.container.innerHTML = `
      <div class="table-info">
        <div class="table-info-left">
          <div class="record-count">
            📊 Total: <strong>${totalFormatted}</strong> registros
          </div>
          <span class="performance-badge">⚡ Formato Nativo (Otimizado)</span>
          ${this.rows.length > 100000 ? '<span class="performance-badge" style="background: #28a745;">✅ Suporta grandes volumes</span>' : ''}
        </div>
        <div class="table-info-right">
          <button class="btn btn-sm btn-secondary" onclick="app.exportData()">
            📥 Exportar CSV
          </button>
          <span class="update-time">✅ ${Utils.formatDateTime()}</span>
          <span class="text-muted">(Update #${this.updateCount})</span>
        </div>
      </div>
      <div id="table-wrapper"></div>
    `;
  }

  /**
   * Renderização com ClusterizeJS (formato objeto)
   */
  renderWithClusterize() {
    try {
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
        try {
          this.clusterize.destroy();
        } catch (e) {
          Utils.log('⚠️ Erro ao destruir Clusterize anterior:', e.message);
        }
        this.clusterize = null;
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
      
    } catch (error) {
      Utils.log('❌ Erro na virtualização:', error);
      // Fallback para renderização simples
      this.renderSimple();
    }
  }

  /**
   * Renderização otimizada com ClusterizeJS para formato colunar
   */
  renderWithClusterizeColumnar() {
    try {
      const wrapper = document.getElementById('table-wrapper');
      
      // Header da tabela
      const headerHtml = this.createHeaderColumnar();
      
      // HTML do container
      wrapper.innerHTML = `
        ${headerHtml}
        <div id="scrollArea" class="clusterize-scroll">
          <table>
            <tbody id="contentArea" class="clusterize-content">
              <tr class="clusterize-no-data">
                <td colspan="${this.cols.length}">Preparando visualização...</td>
              </tr>
            </tbody>
          </table>
        </div>
      `;

      // Destrói instância anterior
      if (this.clusterize) {
        try {
          this.clusterize.destroy();
        } catch (e) {
          Utils.log('⚠️ Erro ao destruir Clusterize:', e.message);
        }
        this.clusterize = null;
      }

      // Para volumes grandes, gera HTML progressivamente
      const totalRows = this.rows.length;
      let htmlRows = [];
      
      if (totalRows > 100000) {
        Utils.log('⚡ Volume grande detectado, usando geração progressiva de HTML...');
        
        // Gera apenas primeiras 5000 linhas inicialmente
        const initialBatch = 5000;
        for (let i = 0; i < Math.min(initialBatch, totalRows); i++) {
          htmlRows.push(this.createRowHtmlColumnar(this.rows[i], i));
        }
        
        // Inicializa Clusterize com batch inicial
        this.clusterize = new Clusterize({
          rows: htmlRows,
          scrollId: 'scrollArea',
          contentId: 'contentArea',
          rows_in_block: 50,
          blocks_in_cluster: 4,
          show_no_data_row: false
        });
        
        // Agenda geração do resto
        this.scheduleRemainingRows(initialBatch, totalRows);
        
      } else {
        // Volume menor: gera tudo de uma vez
        Utils.log('📊 Gerando HTML para todas as linhas...');
        
        for (let i = 0; i < totalRows; i++) {
          htmlRows.push(this.createRowHtmlColumnar(this.rows[i], i));
        }
        
        this.clusterize = new Clusterize({
          rows: htmlRows,
          scrollId: 'scrollArea',
          contentId: 'contentArea',
          rows_in_block: 50,
          blocks_in_cluster: 4,
          show_no_data_row: false
        });
      }
      
    } catch (error) {
      Utils.log('❌ Erro na renderização colunar:', error);
      this.renderError(error);
    }
  }

  /**
   * Agenda geração progressiva das linhas restantes
   */
  async scheduleRemainingRows(startIndex, totalRows) {
    const BATCH_SIZE = 10000;
    let currentIndex = startIndex;
    
    while (currentIndex < totalRows) {
      const endIndex = Math.min(currentIndex + BATCH_SIZE, totalRows);
      const batchRows = [];
      
      // Gera próximo batch
      for (let i = currentIndex; i < endIndex; i++) {
        batchRows.push(this.createRowHtmlColumnar(this.rows[i], i));
      }
      
      // Adiciona ao Clusterize
      if (this.clusterize) {
        this.clusterize.append(batchRows);
      }
      
      currentIndex = endIndex;
      
      // Atualiza progresso
      const progress = Math.round((currentIndex / totalRows) * 100);
      Utils.log(`📊 Progresso: ${progress}% (${currentIndex.toLocaleString('pt-BR')} de ${totalRows.toLocaleString('pt-BR')})`);
      
      // Pequena pausa para não travar
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    
    Utils.log('✅ Todas as linhas foram preparadas para visualização');
  }

  /**
   * Renderização simples (sem virtualização) - formato objeto
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
   * Cria HTML do header (formato objeto)
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
   * Cria header para formato colunar
   */
  createHeaderColumnar() {
    const headers = this.cols.map(col => {
      const displayName = col.display_name || col.name;
      return `<th title="${col.name}">${Utils.escapeHtml(displayName)}</th>`;
    }).join('');
    
    return `
      <table>
        <thead>
          <tr>${headers}</tr>
        </thead>
      </table>
    `;
  }

  /**
   * Cria HTML de uma linha (formato objeto)
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
   * Cria HTML de uma linha (formato colunar)
   */
  createRowHtmlColumnar(rowArray, rowIndex) {
    const cells = rowArray.map((value, colIndex) => {
      const col = this.cols[colIndex];
      let displayValue = this.formatCellValue(value, col);
      const escaped = Utils.escapeHtml(displayValue);
      return `<td title="${escaped}">${escaped}</td>`;
    }).join('');
    
    return `<tr>${cells}</tr>`;
  }

  /**
   * Formata valor da célula baseado no tipo
   */
  formatCellValue(value, col) {
    if (value === null || value === undefined) return '';
    
    if (col && col.base_type) {
      try {
        switch(col.base_type) {
          case 'type/Float':
          case 'type/Decimal':
            if (typeof value === 'number') {
              // Verifica se parece ser moeda
              if (col.name && /spend|cost|revenue|valor|price/i.test(col.name)) {
                return new Intl.NumberFormat('pt-BR', {
                  style: 'currency',
                  currency: 'BRL'
                }).format(value);
              }
              return value.toLocaleString('pt-BR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              });
            }
            break;
            
          case 'type/Integer':
          case 'type/BigInteger':
            if (typeof value === 'number') {
              return value.toLocaleString('pt-BR');
            }
            break;
            
          case 'type/Date':
            if (value) {
              const date = new Date(value);
              if (!isNaN(date.getTime())) {
                return date.toLocaleDateString('pt-BR');
              }
            }
            break;
            
          case 'type/DateTime':
            if (value) {
              const date = new Date(value);
              if (!isNaN(date.getTime())) {
                return date.toLocaleString('pt-BR');
              }
            }
            break;
        }
      } catch (e) {
        // Se falhar formatação, retorna valor original
      }
    }
    
    return String(value);
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
        <p class="loading-message">${message}</p>
        <div class="loading-progress" style="display: none;">
          <div class="progress-bar">
            <div class="progress-fill" style="width: 0%"></div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Exporta dados para CSV (formato objeto)
   */
  exportToCsv() {
    if (!this.data || this.data.length === 0) {
      Utils.showNotification('Nenhum dado para exportar', 'warning');
      return;
    }

    try {
      // Para grandes volumes, mostra progresso
      if (this.data.length > 10000) {
        Utils.showNotification('Preparando exportação de ' + this.data.length + ' registros...', 'info');
      }

      // Header
      let csv = this.columns.join(',') + '\n';
      
      // Dados (processa em chunks para não travar)
      const CHUNK_SIZE = 1000;
      for (let i = 0; i < this.data.length; i += CHUNK_SIZE) {
        const chunk = this.data.slice(i, Math.min(i + CHUNK_SIZE, this.data.length));
        
        chunk.forEach(row => {
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
      }

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
      
    } catch (error) {
      Utils.log('❌ Erro ao exportar:', error);
      Utils.showNotification('Erro ao exportar: ' + error.message, 'error');
    }
  }

  /**
   * Exporta CSV do formato colunar (OTIMIZADO)
   */
  exportToCsvColumnar() {
    if (!this.rows || this.rows.length === 0) {
      Utils.showNotification('Nenhum dado para exportar', 'warning');
      return;
    }

    try {
      const totalRows = this.rows.length;
      Utils.showNotification(`Preparando exportação de ${totalRows.toLocaleString('pt-BR')} registros...`, 'info');

      // Header
      const headers = this.cols.map(col => {
        const name = col.name;
        // Escapa se tiver vírgula
        if (name.includes(',')) {
          return `"${name}"`;
        }
        return name;
      });
      
      let csv = headers.join(',') + '\n';
      
      // Processa em chunks grandes para melhor performance
      const CHUNK_SIZE = 50000;
      
      for (let i = 0; i < totalRows; i += CHUNK_SIZE) {
        const endIndex = Math.min(i + CHUNK_SIZE, totalRows);
        
        for (let j = i; j < endIndex; j++) {
          const row = this.rows[j];
          const values = row.map((value, colIndex) => {
            if (value === null || value === undefined) return '';
            
            // Formata valor se necessário
            const col = this.cols[colIndex];
            let formattedValue = this.formatCellValue(value, col);
            
            // Escapa se necessário
            if (formattedValue.includes(',') || formattedValue.includes('\n') || formattedValue.includes('"')) {
              return `"${formattedValue.replace(/"/g, '""')}"`;
            }
            return formattedValue;
          });
          
          csv += values.join(',') + '\n';
        }
        
        // Atualiza progresso
        if (totalRows > 100000) {
          const progress = Math.round((endIndex / totalRows) * 100);
          Utils.showNotification(`Exportando... ${progress}%`, 'info');
        }
      }

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
      URL.revokeObjectURL(url);
      
      Utils.showNotification(`✅ ${totalRows.toLocaleString('pt-BR')} registros exportados com sucesso!`, 'success');
      
    } catch (error) {
      Utils.log('❌ Erro ao exportar:', error);
      Utils.showNotification('Erro ao exportar: ' + error.message, 'error');
    }
  }

  /**
   * Destrói a tabela e limpa recursos
   */
  destroy() {
    if (this.clusterize) {
      try {
        this.clusterize.destroy();
      } catch (e) {
        // Ignora erros ao destruir
      }
      this.clusterize = null;
    }
    
    // Limpa dados
    this.data = [];
    this.columns = [];
    this.cols = [];
    this.rows = [];
    this.isColumnarFormat = false;
    this.container.innerHTML = '';
  }

  /**
   * Obtém estatísticas da tabela
   */
  getStats() {
    return {
      totalRows: this.isColumnarFormat ? this.rows.length : this.data.length,
      totalColumns: this.isColumnarFormat ? this.cols.length : this.columns.length,
      updateCount: this.updateCount,
      isVirtualized: this.clusterize !== null,
      format: this.isColumnarFormat ? 'columnar' : 'objeto'
    };
  }
  
  /**
   * Obtém dados atuais (para compatibilidade)
   */
  getData() {
    return this.data;
  }
}

// Não cria instância global aqui, será criada no main.js
