// componentes/tabela_virtual/js/virtual-table.js
/**
 * Módulo de renderização de tabela virtual com suporte a formato colunar
 * VERSÃO ULTRA-OTIMIZADA: Renderização apenas de linhas visíveis
 */

class VirtualTable {
  constructor(container) {
    this.container = container;
    this.data = [];      // Para formato de objetos (compatibilidade)
    this.columns = [];   // Para formato de objetos
    this.cols = [];      // Para formato colunar (metadados)
    this.rows = [];      // Para formato colunar (dados)
    this.isColumnarFormat = false;
    this.clusterize = null;
    this.updateCount = 0;
    
    // Configurações de virtualização
    this.visibleRows = 100; // Quantas linhas manter no DOM
    this.bufferRows = 100;  // Buffer acima e abaixo (aumentado para evitar buracos)
    this.rowHeight = 30;    // Altura estimada de cada linha
    this.scrollTop = 0;
    this.visibleStart = 0;
    this.visibleEnd = 0;
    this.scrollHandler = null; // Para remover listener depois
  }

  /**
   * Renderiza dados no formato nativo do Metabase (colunar) - ULTRA OTIMIZADO
   */
  renderNative(response) {
    const startTime = performance.now();
    
    // Validação de dados
    if (!response || !response.data || !response.data.cols || !response.data.rows) {
      Utils.log('⚠️ Resposta inválida, mostrando tabela vazia');
      this.renderEmpty();
      return;
    }
    
    // Armazena no formato colunar - NÃO CONVERTE!
    this.cols = response.data.cols;
    this.rows = response.data.rows;
    this.isColumnarFormat = true;
    this.updateCount++;

    const totalRows = this.rows.length;
    
    // Se não tem linhas, mostra vazio
    if (totalRows === 0) {
      this.renderEmpty();
      return;
    }
    
    Utils.log(`🎨 Renderizando ${totalRows.toLocaleString('pt-BR')} linhas (virtualização real)...`);

    // Cria estrutura HTML
    this.createStructureColumnar();

    // Usa virtualização customizada para grandes volumes
    if (totalRows > 10000) {
      this.renderWithCustomVirtualization();
    } else {
      // Para volumes menores, usa Clusterize se disponível
      if (typeof Clusterize !== 'undefined') {
        this.renderWithClusterizeSimple();
      } else {
        Utils.log('⚠️ ClusterizeJS não encontrado, usando virtualização customizada');
        this.renderWithCustomVirtualization();
      }
    }

    const elapsed = Utils.getElapsedTime(startTime);
    Utils.log(`✅ Renderizado em ${elapsed}s`);
    
    if (totalRows > 10000) {
      Utils.log(`💡 Virtualização real ativa: Apenas ~300 de ${totalRows.toLocaleString('pt-BR')} linhas estão no DOM`);
      Utils.log(`🚀 Economia de memória: ~${Math.round((1 - (300 / totalRows)) * 100)}%`);
      
      // Mostra estatísticas em tabela
      console.table({
        'Total de Linhas': totalRows.toLocaleString('pt-BR'),
        'Linhas no DOM': '~300',
        'Economia de Memória': `~${Math.round((1 - (300 / totalRows)) * 100)}%`,
        'Técnica': 'Virtualização Real'
      });
    }

    // Mostra notificação
    if (this.updateCount > 1) {
      Utils.showNotification('🔄 Tabela atualizada', 'success');
    }
  }

  /**
   * Virtualização customizada para grandes volumes
   */
  renderWithCustomVirtualization() {
    try {
      const wrapper = document.getElementById('table-wrapper');
      const totalRows = this.rows.length;
      const totalHeight = totalRows * this.rowHeight;
      
      // Header da tabela
      const headerHtml = this.createHeaderColumnar();
      
      // HTML do container com scroll virtual
      wrapper.innerHTML = `
        ${headerHtml}
        <div id="scrollArea" class="virtual-scroll-area" style="height: 600px; overflow-y: auto; position: relative;">
          <div class="virtual-scroll-spacer" style="height: ${totalHeight}px; position: relative;">
            <div id="contentArea" class="virtual-content" style="position: absolute; top: 0; width: 100%;">
              <!-- Linhas serão inseridas aqui -->
            </div>
          </div>
        </div>
      `;

      const scrollArea = document.getElementById('scrollArea');
      const contentArea = document.getElementById('contentArea');
      
      // Função para renderizar apenas linhas visíveis
      const renderVisibleRows = () => {
        const scrollTop = scrollArea.scrollTop;
        const viewportHeight = scrollArea.clientHeight;
        
        // Calcula quais linhas devem estar visíveis
        const startRow = Math.max(0, Math.floor(scrollTop / this.rowHeight) - this.bufferRows);
        const endRow = Math.min(totalRows, Math.ceil((scrollTop + viewportHeight) / this.rowHeight) + this.bufferRows);
        
        // Se não mudou significativamente, não re-renderiza
        if (Math.abs(startRow - this.visibleStart) < 20 && Math.abs(endRow - this.visibleEnd) < 20) {
          return;
        }
        
        this.visibleStart = startRow;
        this.visibleEnd = endRow;
        
        // Gera HTML apenas para linhas visíveis
        const fragments = [];
        fragments.push('<table style="position: absolute; width: 100%;"><tbody>');
        
        for (let i = startRow; i < endRow; i++) {
          const row = this.rows[i];
          const top = i * this.rowHeight;
          fragments.push(`<tr style="position: absolute; top: ${top}px; width: 100%; height: ${this.rowHeight}px;">`);
          
          for (let j = 0; j < row.length; j++) {
            const value = row[j];
            const col = this.cols[j];
            const displayValue = this.formatCellValue(value, col);
            const escaped = Utils.escapeHtml(displayValue);
            fragments.push(`<td title="${escaped}">${escaped}</td>`);
          }
          
          fragments.push('</tr>');
        }
        
        fragments.push('</tbody></table>');
        
        // Atualiza DOM uma única vez
        contentArea.innerHTML = fragments.join('');
        
        // Atualiza info de linhas visíveis
        const visibleInfo = document.getElementById('visible-info');
        if (visibleInfo) {
          visibleInfo.textContent = `(Mostrando linhas ${startRow + 1}-${endRow} de ${totalRows.toLocaleString('pt-BR')})`;
        }
        
        // Log discreto apenas no primeiro render
        if (this.updateCount === 1 && this.visibleStart === 0) {
          Utils.log(`📊 Renderizando linhas ${startRow} a ${endRow} de ${totalRows.toLocaleString('pt-BR')}`);
        }
      };
      
      // Renderiza inicial
      renderVisibleRows();
      
      // Adiciona listener de scroll com throttle agressivo
      let scrollTimeout;
      let lastScrollTime = 0;
      
      this.scrollHandler = (e) => {
        const now = Date.now();
        
        // Throttle: máximo uma atualização a cada 16ms (60fps)
        if (now - lastScrollTime < 16) {
          if (scrollTimeout) clearTimeout(scrollTimeout);
          scrollTimeout = setTimeout(renderVisibleRows, 16);
          return;
        }
        
        lastScrollTime = now;
        renderVisibleRows();
      };
      
      scrollArea.addEventListener('scroll', this.scrollHandler);
      
      Utils.log(`✅ Virtualização real ativa: ${totalRows.toLocaleString('pt-BR')} linhas, mas apenas ~${this.visibleRows + this.bufferRows * 2} linhas no DOM`);
      Utils.log(`💡 Role a tabela normalmente - as linhas são renderizadas sob demanda`);
      
    } catch (error) {
      Utils.log('❌ Erro na virtualização customizada:', error);
      // Fallback para renderização simples
      this.renderWithClusterizeSimple();
    }
  }

  /**
   * Renderização com Clusterize para volumes menores
   */
  renderWithClusterizeSimple() {
    try {
      const wrapper = document.getElementById('table-wrapper');
      const headerHtml = this.createHeaderColumnar();
      const totalRows = this.rows.length;
      
      wrapper.innerHTML = `
        ${headerHtml}
        <div id="scrollArea" class="clusterize-scroll">
          <table>
            <tbody id="contentArea" class="clusterize-content">
              <tr class="clusterize-no-data">
                <td colspan="${this.cols.length}">Carregando...</td>
              </tr>
            </tbody>
          </table>
        </div>
      `;

      // Destrói instância anterior
      if (this.clusterize) {
        try {
          this.clusterize.destroy();
        } catch (e) {}
        this.clusterize = null;
      }

      // Gera HTML de todas as linhas (ok para volumes menores)
      const rows = [];
      for (let i = 0; i < totalRows; i++) {
        rows.push(this.createRowHtmlColumnar(this.rows[i], i));
      }

      // Inicializa Clusterize
      this.clusterize = new Clusterize({
        rows: rows,
        scrollId: 'scrollArea',
        contentId: 'contentArea',
        rows_in_block: 50,
        blocks_in_cluster: 4,
        show_no_data_row: false
      });
      
      Utils.log(`✅ ${totalRows.toLocaleString('pt-BR')} linhas renderizadas com Clusterize`);
      
    } catch (error) {
      Utils.log('❌ Erro no Clusterize:', error);
      this.renderError(error);
    }
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
   * Cria estrutura para formato colunar
   */
  createStructureColumnar() {
    const totalFormatted = Utils.formatNumber(this.rows ? this.rows.length : 0);
    
    this.container.innerHTML = `
      <div class="table-info">
        <div class="table-info-left">
          <div class="record-count">
            📊 Total: <strong>${totalFormatted}</strong> registros
          </div>
          <span class="performance-badge">⚡ Virtualização Real</span>
          ${this.rows && this.rows.length > 10000 ? '<span class="performance-badge" style="background: #28a745;">✅ Apenas ~300 linhas no DOM</span>' : ''}
          <span id="visible-info" class="text-muted" style="font-size: 11px; opacity: 0.7; margin-left: 10px;"></span>
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
   * Exporta CSV do formato colunar (mantém otimizado)
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
        if (name.includes(',')) {
          return `"${name}"`;
        }
        return name;
      });
      
      let csv = headers.join(',') + '\n';
      
      // Processa em chunks
      const CHUNK_SIZE = 50000;
      
      for (let i = 0; i < totalRows; i += CHUNK_SIZE) {
        const endIndex = Math.min(i + CHUNK_SIZE, totalRows);
        
        for (let j = i; j < endIndex; j++) {
          const row = this.rows[j];
          const values = row.map((value, colIndex) => {
            if (value === null || value === undefined) return '';
            
            const col = this.cols[colIndex];
            let formattedValue = this.formatCellValue(value, col);
            
            if (formattedValue.includes(',') || formattedValue.includes('\n') || formattedValue.includes('"')) {
              return `"${formattedValue.replace(/"/g, '""')}"`;
            }
            return formattedValue;
          });
          
          csv += values.join(',') + '\n';
        }
        
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
      
      // IMPORTANTE: Libera memória
      setTimeout(() => {
        URL.revokeObjectURL(url);
        csv = null; // Libera string grande
      }, 100);
      
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
    // Remove scroll handler se existir
    if (this.scrollHandler) {
      const scrollArea = document.getElementById('scrollArea');
      if (scrollArea) {
        scrollArea.removeEventListener('scroll', this.scrollHandler);
      }
      this.scrollHandler = null;
    }
    
    if (this.clusterize) {
      try {
        this.clusterize.destroy();
      } catch (e) {}
      this.clusterize = null;
    }
    
    // Limpa dados - IMPORTANTE: não manter referências
    this.data = null;
    this.columns = null;
    this.cols = null;
    this.rows = null;
    this.isColumnarFormat = false;
    this.container.innerHTML = '';
  }

  /**
   * Obtém estatísticas da tabela
   */
  getStats() {
    return {
      totalRows: this.isColumnarFormat ? (this.rows ? this.rows.length : 0) : (this.data ? this.data.length : 0),
      totalColumns: this.isColumnarFormat ? (this.cols ? this.cols.length : 0) : (this.columns ? this.columns.length : 0),
      updateCount: this.updateCount,
      isVirtualized: true,
      format: this.isColumnarFormat ? 'columnar' : 'objeto',
      virtualization: {
        visibleRows: this.visibleRows,
        bufferRows: this.bufferRows,
        currentVisible: `${this.visibleStart}-${this.visibleEnd}`
      }
    };
  }

  // Métodos de compatibilidade (simplificados)...
  render(data) {
    const startTime = performance.now();
    
    this.data = data;
    this.columns = Object.keys(data[0] || {});
    this.isColumnarFormat = false;
    this.updateCount++;

    Utils.log(`🎨 Renderizando ${data.length} linhas (formato objeto)...`);

    this.createStructure();

    if (data.length > 1000) {
      this.renderWithClusterize();
    } else {
      this.renderSimple();
    }

    const elapsed = Utils.getElapsedTime(startTime);
    Utils.log(`✅ Renderizado em ${elapsed}s`);
  }

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

  renderWithClusterize() {
    try {
      const wrapper = document.getElementById('table-wrapper');
      const headerHtml = this.createHeader();
      const rows = this.data.map(row => this.createRowHtml(row));
      
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

      if (this.clusterize) {
        try {
          this.clusterize.destroy();
        } catch (e) {}
        this.clusterize = null;
      }

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
      this.renderSimple();
    }
  }

  renderSimple() {
    const wrapper = document.getElementById('table-wrapper');
    let html = [this.createHeader()];
    
    html.push('<div class="clusterize-scroll"><table><tbody>');
    this.data.forEach(row => {
      html.push(this.createRowHtml(row));
    });
    html.push('</tbody></table></div>');
    
    wrapper.innerHTML = html.join('');
  }

  createHeader() {
    const headers = this.columns.map(col => 
      `<th title="${col}">${Utils.escapeHtml(col)}</th>`
    ).join('');
    
    return `<table><thead><tr>${headers}</tr></thead></table>`;
  }

  createRowHtml(row) {
    const cells = this.columns.map(col => {
      const value = row[col];
      const escaped = Utils.escapeHtml(value);
      return `<td title="${escaped}">${escaped}</td>`;
    }).join('');
    
    return `<tr>${cells}</tr>`;
  }

  renderEmpty() {
    this.container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <p>Nenhum dado encontrado com os filtros aplicados</p>
      </div>
    `;
  }

  renderError(error) {
    this.container.innerHTML = `
      <div class="error-message">
        <strong>❌ Erro ao carregar dados</strong>
        <pre>${Utils.escapeHtml(error.message)}</pre>
      </div>
    `;
  }

  renderLoading(message = 'Carregando dados...') {
    this.container.innerHTML = `
      <div class="loading-container">
        <div class="spinner"></div>
        <p class="loading-message">${message}</p>
      </div>
    `;
  }

  exportToCsv() {
    if (!this.data || this.data.length === 0) {
      Utils.showNotification('Nenhum dado para exportar', 'warning');
      return;
    }

    try {
      let csv = this.columns.join(',') + '\n';
      const CHUNK_SIZE = 1000;
      
      for (let i = 0; i < this.data.length; i += CHUNK_SIZE) {
        const chunk = this.data.slice(i, Math.min(i + CHUNK_SIZE, this.data.length));
        
        chunk.forEach(row => {
          const values = this.columns.map(col => {
            const value = row[col] || '';
            if (value.toString().includes(',') || value.toString().includes('\n')) {
              return `"${value.toString().replace(/"/g, '""')}"`;
            }
            return value;
          });
          
          csv += values.join(',') + '\n';
        });
      }

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

  getData() {
    return this.data;
  }
}

// Não cria instância global aqui, será criada no main.js
