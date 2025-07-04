/**
 * Renderizador específico para tabela virtual
 * Usa ClusterizeJS para virtualização
 */

class TableRenderer {
    constructor(container) {
        this.container = container;
        this.data = [];
        this.metadata = [];
        this.clusterize = null;
        this.updateCount = 0;
    }
    
    /**
     * Renderiza tabela com dados
     */
    render(data, metadata = []) {
        const startTime = performance.now();
        
        this.data = data;
        this.metadata = metadata;
        this.updateCount++;
        
        console.log(`🎨 Renderizando ${data.length} linhas...`);
        
        // Cria estrutura HTML
        this.createStructure();
        
        // Usa ClusterizeJS para virtualização se muitos dados
        if (data.length > 1000) {
            this.renderWithClusterize();
        } else {
            this.renderSimple();
        }
        
        const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);
        console.log(`✅ Renderizado em ${elapsed}s`);
        
        // Mostra notificação de atualização
        if (this.updateCount > 1) {
            this.showUpdateNotification();
        }
    }
    
    /**
     * Cria estrutura base da tabela
     */
    createStructure() {
        const totalFormatted = this.data.length.toLocaleString('pt-BR');
        
        this.container.innerHTML = `
            <div class="table-info">
                <div class="table-info-left">
                    <div class="record-count">
                        📊 Total: <strong>${totalFormatted}</strong> registros
                    </div>
                    ${this.data.length > 1000 ? '<span class="performance-badge">⚡ Virtualização Ativa</span>' : ''}
                </div>
                <div class="table-info-right">
                    <button class="btn btn-sm btn-secondary" onclick="app.exportData()">
                        📥 Exportar CSV
                    </button>
                    <span class="update-time">✅ ${new Date().toLocaleTimeString('pt-BR')}</span>
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
        const columns = this.getColumns();
        
        // Header da tabela
        const headerHtml = this.createHeader(columns);
        
        // Prepara linhas como strings HTML
        const rows = this.data.map(row => this.createRowHtml(row, columns));
        
        // HTML do container
        wrapper.innerHTML = `
            ${headerHtml}
            <div id="scrollArea" class="clusterize-scroll">
                <table>
                    <tbody id="contentArea" class="clusterize-content">
                        <tr class="clusterize-no-data">
                            <td colspan="${columns.length}">Carregando...</td>
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
        const columns = this.getColumns();
        
        // Constrói HTML como string para performance
        let html = [this.createHeader(columns)];
        
        html.push('<div class="table-scroll"><table><tbody>');
        
        // Adiciona linhas
        this.data.forEach(row => {
            html.push(this.createRowHtml(row, columns));
        });
        
        html.push('</tbody></table></div>');
        
        wrapper.innerHTML = html.join('');
    }
    
    /**
     * Obtém colunas da tabela
     */
    getColumns() {
        // Se tem metadata, usa
        if (this.metadata && this.metadata.length > 0) {
            return this.metadata.map(col => col.name);
        }
        
        // Senão, extrai do primeiro registro
        return this.data.length > 0 ? Object.keys(this.data[0]) : [];
    }
    
    /**
     * Cria HTML do header
     */
    createHeader(columns) {
        const headers = columns.map(col => {
            const meta = this.metadata.find(m => m.name === col);
            const displayName = meta ? meta.displayName : col;
            return `<th title="${col}">${this.escapeHtml(displayName)}</th>`;
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
     * Cria HTML de uma linha
     */
    createRowHtml(row, columns) {
        const cells = columns.map(col => {
            const value = row[col];
            const meta = this.metadata.find(m => m.name === col);
            
            let displayValue = value;
            
            // Aplica formatador se houver
            if (meta && meta.formatter) {
                displayValue = dataProcessor.formatValue(value, meta.formatter);
            }
            
            const escaped = this.escapeHtml(displayValue);
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
                <h3>Nenhum dado encontrado</h3>
                <p class="text-muted">Não há dados com os filtros aplicados</p>
            </div>
        `;
    }
    
    /**
     * Renderiza estado de erro
     */
    renderError(error) {
        this.container.innerHTML = `
            <div class="alert alert-error">
                <strong>❌ Erro ao carregar dados</strong>
                <pre class="mt-2">${this.escapeHtml(error.message)}</pre>
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
                <p class="text-muted">${message}</p>
            </div>
        `;
    }
    
    /**
     * Mostra notificação de atualização
     */
    showUpdateNotification() {
        const indicator = document.getElementById('update-indicator');
        if (indicator) {
            indicator.textContent = '🔄 Dados atualizados';
            indicator.classList.add('show');
            
            setTimeout(() => {
                indicator.classList.remove('show');
            }, 3000);
        }
    }
    
    /**
     * Escape HTML
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
    }
    
    /**
     * Obtém dados atuais
     */
    getData() {
        return this.data;
    }
    
    /**
     * Obtém estatísticas
     */
    getStats() {
        return {
            totalRows: this.data.length,
            totalColumns: this.getColumns().length,
            updateCount: this.updateCount,
            isVirtualized: this.clusterize !== null
        };
    }
    
    /**
     * Destrói a tabela
     */
    destroy() {
        if (this.clusterize) {
            this.clusterize.destroy();
            this.clusterize = null;
        }
        
        this.data = [];
        this.metadata = [];
        this.container.innerHTML = '';
    }
}

// Exporta para uso no módulo principal
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TableRenderer;
} else {
    window.TableRenderer = TableRenderer;
}
