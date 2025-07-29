/**
 * Main App - Controlador principal do componente gráfico
 * Integra filtros, API, transformação de dados e renderização
 */
class ChartApp {
    constructor() {
        // Verificar se as classes necessárias existem
        if (typeof FilterManager === 'undefined') {
            throw new Error('FilterManager não encontrado. Verifique se filter-manager.js foi carregado.');
        }
        
        // Serviços
        this.filterManager = new FilterManager();
        
        // Tentar carregar APIClient (opcional se usarmos fetch direto)
        try {
            if (typeof APIClient !== 'undefined') {
                this.apiClient = new APIClient();
            } else if (typeof ApiClient !== 'undefined') {
                this.apiClient = new ApiClient();
            } else {
                console.warn('[ChartApp] APIClient não encontrado, usando fetch direto');
                this.apiClient = null;
            }
        } catch (error) {
            console.warn('[ChartApp] Erro ao criar APIClient:', error);
            this.apiClient = null;
        }
        
        this.dataTransformer = new DataTransformer();
        this.chartBuilder = new ChartBuilder('chart-container');
        
        // Estado
        this.currentData = null;
        this.isLoading = false;
        
        // Obter question_id da URL
        try {
            this.questionId = this.getQuestionIdFromURL();
            /**
     * Debug detalhado dos dados
     */
    debugData() {
        console.log('[Debug] === DEBUG DE DADOS DO GRÁFICO ===');
        
        if (!this.currentData || !this.currentData.raw) {
            console.log('[Debug] Nenhum dado carregado ainda');
            console.log('[Debug] Execute: chartApp.refresh() para carregar dados');
            return;
        }
        
        const { raw, transformed } = this.currentData;
        console.log('[Debug] Estrutura dos dados brutos:');
        console.log('- Total de linhas:', raw.data?.rows?.length || 0);
        console.log('- Total de colunas:', raw.data?.cols?.length || 0);
        
        if (raw.data?.cols) {
            console.log('\n[Debug] Colunas disponíveis:');
            console.table(raw.data.cols.map((col, idx) => ({
                índice: idx,
                nome: col.name,
                tipo: col.base_type,
                exibição: col.display_name
            })));
        }
        
        if (raw.data?.rows && raw.data.rows.length > 0) {
            console.log('\n[Debug] Amostra de dados (primeiras 3 linhas):');
            const sample = raw.data.rows.slice(0, 3).map(row => {
                const obj = {};
                raw.data.cols.forEach((col, idx) => {
                    obj[col.name] = row[idx];
                });
                return obj;
            });
            console.table(sample);
        }
        
        if (transformed) {
            console.log('\n[Debug] Dados transformados:');
            console.log('- Total de meses:', transformed.categories?.length || 0);
            console.log('- Total de contas:', transformed.stats?.totalAccounts || 0);
            console.log('- Período:', transformed.stats?.dateRange ? 
                `${transformed.stats.dateRange.start?.toLocaleDateString()} a ${transformed.stats.dateRange.end?.toLocaleDateString()}` : 
                'Não definido');
            
            if (transformed.categories && transformed.categories.length > 0) {
                console.log('- Meses:', transformed.categories.join(', '));
            }
        }
        
        console.log('\n[Debug] Para ajustar mapeamento de colunas:');
        console.log('1. Edite o arquivo: js/config.js');
        console.log('2. Ajuste o objeto columnMapping com os nomes corretos');
        console.log('3. Execute: chartApp.refresh() para recarregar');
        
        return {
            colunas: raw.data?.cols?.map(c => c.name) || [],
            totalLinhas: raw.data?.rows?.length || 0,
            primeiraLinha: raw.data?.rows?.[0] || [],
            dadosTransformados: transformed ? {
                meses: transformed.categories?.length || 0,
                contas: transformed.stats?.totalAccounts || 0
            } : null
        };
    }
} catch (error) {
            console.error('[ChartApp] Erro ao obter question_id:', error);
            this.questionId = null;
        }
        
        // Elementos DOM
        this.elements = {
            loading: document.getElementById('loading'),
            totalContas: document.getElementById('total-contas'),
            periodoDados: document.getElementById('periodo-dados'),
            ultimaAtualizacao: document.getElementById('ultima-atualizacao'),
            updateStatus: document.getElementById('update-status'),
            btnExport: document.getElementById('btn-export-data'),
            btnFullscreen: document.getElementById('btn-fullscreen')
        };
        
        // Bind de métodos
        this.loadData = this.loadData.bind(this);
        this.handleFilterChange = this.handleFilterChange.bind(this);
        
        // Comandos de debug globais
        window.chartApp = {
            getData: () => this.currentData,
            getFilters: () => this.filterManager.currentFilters,
            getStats: () => this.getStats(),
            getQuestionId: () => this.questionId,
            refresh: () => this.loadData('manual'),
            stopMonitoring: () => this.filterManager.stopMonitoring(),
            exportData: () => this.exportData(),
            debugData: () => this.debugData()
        };
    }

    /**
     * Obtém o question_id da URL
     */
    getQuestionIdFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const questionId = urlParams.get('question_id');
        
        if (!questionId) {
            console.error('[ChartApp] Parâmetro question_id não encontrado na URL');
            throw new Error('Parâmetro question_id é obrigatório. Use: ?question_id=XX');
        }
        
        const id = parseInt(questionId, 10);
        
        if (isNaN(id) || id <= 0) {
            console.error('[ChartApp] question_id inválido:', questionId);
            throw new Error('question_id deve ser um número válido maior que zero');
        }
        
        console.log('[ChartApp] Usando question_id:', id);
        return id;
    }

    /**
     * Inicializa a aplicação
     */
    async init() {
        console.log('[ChartApp] Inicializando aplicação gráfico...');
        
        try {
            // Validar question_id
            if (!this.questionId) {
                throw new Error('question_id não configurado');
            }
            
            // Configurar eventos
            this.setupEventListeners();
            
            // Carregar dados iniciais
            await this.loadData('initial');
            
            // Iniciar monitoramento de filtros após 3 segundos
            setTimeout(() => {
                console.log('[ChartApp] Iniciando monitoramento de filtros');
                this.filterManager.startMonitoring(this.handleFilterChange, 2000);
            }, 3000);
            
        } catch (error) {
            console.error('[ChartApp] Erro na inicialização:', error);
            
            // Mostrar erro específico para question_id
            if (error.message.includes('question_id')) {
                this.showConfigError();
            } else {
                this.showError('Erro ao inicializar aplicação');
            }
        }
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Botão exportar
        this.elements.btnExport?.addEventListener('click', () => {
            this.exportData();
        });
        
        // Botão tela cheia
        this.elements.btnFullscreen?.addEventListener('click', () => {
            this.chartBuilder.toggleFullscreen();
            const isFullscreen = document.querySelector('.dashboard-container').classList.contains('fullscreen');
            this.elements.btnFullscreen.textContent = isFullscreen ? 'Sair da Tela Cheia' : 'Tela Cheia';
        });
        
        // Redimensionamento da janela
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.chartBuilder.resize();
            }, 250);
        });
    }

    /**
     * Carrega dados da API
     */
    async loadData(source = 'filter_change') {
        if (this.isLoading) {
            console.log('[ChartApp] Requisição já em andamento, ignorando...');
            return;
        }

        console.log(`[ChartApp] Carregando dados... (fonte: ${source})`);
        this.isLoading = true;
        this.showLoading(true);

        try {
            // Preparar parâmetros
            const filters = this.filterManager.currentFilters || {};
            const params = {
                question_id: this.questionId,
                ...filters
            };

            console.log('[ChartApp] Parâmetros da requisição:', params);

            // Buscar dados
            const startTime = Date.now();
            
            let response;
            
            // Tentar usar APIClient se disponível, senão usar fetch direto
            if (this.apiClient && this.apiClient.query) {
                response = await this.apiClient.query(params);
            } else {
                console.warn('[ChartApp] APIClient não disponível, usando fetch direto');
                
                // Construir URL com parâmetros
                const baseUrl = 'https://metabasedashboards.ngrok.io/metabase_customizacoes/api/query';
                const url = new URL(baseUrl);
                Object.entries(params).forEach(([key, value]) => {
                    if (value !== undefined && value !== null && value !== '') {
                        url.searchParams.append(key, value);
                    }
                });
                
                const fetchResponse = await fetch(url.toString());
                if (!fetchResponse.ok) {
                    throw new Error(`HTTP ${fetchResponse.status}: ${fetchResponse.statusText}`);
                }
                
                response = await fetchResponse.json();
            }
            
            const loadTime = Date.now() - startTime;

            console.log(`[ChartApp] Dados recebidos em ${loadTime}ms:`, {
                rows: response.data?.rows?.length || 0,
                cols: response.data?.cols?.length || 0
            });

            // Validar resposta
            if (!response || !response.data || !response.data.rows) {
                throw new Error('Resposta inválida da API');
            }

            // Transformar dados
            const chartData = this.dataTransformer.transformData(response);
            
            // Armazenar dados
            this.currentData = {
                raw: response,
                transformed: chartData,
                loadTime: loadTime,
                timestamp: new Date()
            };

            // Atualizar interface
            this.updateUI(chartData);
            
            // Construir gráfico
            this.chartBuilder.buildChart(chartData);
            
            // Habilitar exportação
            this.elements.btnExport.disabled = chartData.series.length === 0;

        } catch (error) {
            console.error('[ChartApp] Erro ao carregar dados:', error);
            this.showError(`Erro ao carregar dados: ${error.message}`);
            this.chartBuilder.showEmptyState();
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }

    /**
     * Atualiza elementos da UI com estatísticas
     */
    updateUI(chartData) {
        const { stats } = chartData;
        
        // Total de contas
        this.elements.totalContas.textContent = 
            `${stats.totalAccounts} ${stats.totalAccounts === 1 ? 'conta' : 'contas'}`;
        
        // Período dos dados
        this.elements.periodoDados.textContent = 
            this.dataTransformer.formatDateRange(stats.dateRange.start, stats.dateRange.end);
        
        // Última atualização
        const now = new Date();
        this.elements.ultimaAtualizacao.textContent = 
            `Atualizado às ${now.toLocaleTimeString('pt-BR')}`;
        
        // Status de atualização
        this.elements.updateStatus.textContent = 
            `${this.formatNumber(stats.totalImpressions)} impressões | ` +
            `${this.formatNumber(stats.totalClicks)} clicks | ` +
            `R$ ${this.formatNumber(stats.totalSpend, 2)}`;
    }

    /**
     * Manipula mudanças de filtros
     */
    handleFilterChange(newFilters, changedFilters) {
        console.log('[ChartApp] Filtros mudaram:', {
            novos: newFilters,
            mudancas: changedFilters
        });

        // Indicar que está atualizando
        this.elements.updateStatus.textContent = 'Atualizando com novos filtros...';
        
        // Recarregar dados
        this.loadData('filter_change');
    }

    /**
     * Mostra/esconde indicador de carregamento
     */
    showLoading(show) {
        if (show) {
            this.elements.loading.classList.add('active');
        } else {
            this.elements.loading.classList.remove('active');
        }
    }

    /**
     * Mostra mensagem de erro
     */
    showError(message) {
        this.elements.updateStatus.textContent = message;
        this.elements.updateStatus.style.color = '#f44336';
        
        setTimeout(() => {
            this.elements.updateStatus.style.color = '';
        }, 5000);
    }

    /**
     * Exporta dados do gráfico
     */
    exportData() {
        if (!this.currentData || !this.currentData.transformed) {
            console.warn('[ChartApp] Nenhum dado para exportar');
            return;
        }

        try {
            const csv = this.dataTransformer.exportToCSV(this.currentData.transformed);
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            
            link.setAttribute('href', url);
            link.setAttribute('download', `performance_campanhas_${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            console.log('[ChartApp] Dados exportados com sucesso');
            
        } catch (error) {
            console.error('[ChartApp] Erro ao exportar dados:', error);
            this.showError('Erro ao exportar dados');
        }
    }

    /**
     * Mostra erro de configuração
     */
    showConfigError() {
        const emptyState = document.getElementById('empty-state');
        if (emptyState) {
            emptyState.innerHTML = `
                <p style="color: #f44336; font-weight: bold;">Configuração Incorreta</p>
                <small>O parâmetro <code>question_id</code> é obrigatório.</small>
                <br>
                <small style="margin-top: 8px; display: block;">
                    Use a URL no formato:<br>
                    <code>...grafico_combo/?question_id=51</code>
                </small>
            `;
            emptyState.style.display = 'flex';
        }
        
        // Esconder loading
        this.showLoading(false);
        
        // Desabilitar botões se existirem
        if (this.elements.btnExport) {
            this.elements.btnExport.disabled = true;
        }
        if (this.elements.btnFullscreen) {
            this.elements.btnFullscreen.disabled = true;
        }
    }

    /**
     * Formata números para exibição
     */
    formatNumber(value, decimals = 0) {
        if (value === null || value === undefined) return '0';
        
        return new Intl.NumberFormat('pt-BR', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    }

    /**
     * Retorna estatísticas para debug
     */
    getStats() {
        return {
            questionId: this.questionId,
            dadosCarregados: !!this.currentData,
            totalLinhas: this.currentData?.raw?.data?.rows?.length || 0,
            totalMeses: this.currentData?.transformed?.categories?.length || 0,
            totalContas: this.currentData?.transformed?.stats?.totalAccounts || 0,
            filtrosAtivos: Object.keys(this.filterManager.currentFilters || {}).length,
            tempoCarregamento: this.currentData?.loadTime || 0,
            ultimaAtualizacao: this.currentData?.timestamp || null
        };
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    console.log('[ChartApp] DOM carregado, inicializando aplicação...');
    
    // Debug: verificar se as classes foram carregadas
    console.log('[ChartApp] Classes disponíveis:', {
        FilterManager: typeof FilterManager !== 'undefined',
        APIClient: typeof APIClient !== 'undefined',
        DataTransformer: typeof DataTransformer !== 'undefined',
        ChartBuilder: typeof ChartBuilder !== 'undefined'
    });
    
    try {
        const app = new ChartApp();
        
        // Mostrar configuração no console
        if (app.questionId) {
            console.log(`[ChartApp] Componente configurado com question_id=${app.questionId}`);
        }
        
        app.init();
    } catch (error) {
        console.error('[ChartApp] Erro ao criar aplicação:', error);
        
        // Mostrar erro na tela
        const emptyState = document.getElementById('empty-state');
        if (emptyState) {
            emptyState.innerHTML = `
                <p style="color: #f44336; font-weight: bold;">Erro de Inicialização</p>
                <small>${error.message}</small>
            `;
            emptyState.style.display = 'flex';
        }
    }
});
