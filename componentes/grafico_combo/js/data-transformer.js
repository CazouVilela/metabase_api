/**
 * DataTransformer - Transforma dados da API para formato Highcharts
 * Responsável por agregação mensal e preparação das séries
 */
class DataTransformer {
    constructor() {
        this.monthNames = {
            'pt': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
            'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        };
    }

    /**
     * Transforma dados da API para formato do gráfico
     * @param {Object} apiData - Dados brutos da API
     * @returns {Object} Dados formatados para Highcharts
     */
    transformData(apiData) {
        console.log('[DataTransformer] Iniciando transformação de dados:', {
            temDados: !!apiData,
            temData: !!apiData?.data,
            temRows: !!apiData?.data?.rows,
            totalRows: apiData?.data?.rows?.length || 0,
            totalCols: apiData?.data?.cols?.length || 0
        });

        if (!apiData || !apiData.data || !apiData.data.rows || apiData.data.rows.length === 0) {
            console.warn('[DataTransformer] Dados vazios ou inválidos');
            return this.getEmptyData();
        }

        const { cols, rows } = apiData.data;
        
        // Mapear índices das colunas
        const columnMap = this.mapColumns(cols);
        console.log('[DataTransformer] Mapa de colunas:', columnMap);
        console.log('[DataTransformer] Primeira linha de dados:', rows[0]);
        
        // Agrupar dados por mês/ano
        const monthlyData = this.aggregateByMonth(rows, columnMap);
        console.log('[DataTransformer] Dados agregados por mês:', Object.keys(monthlyData).length, 'meses');
        
        // Preparar dados para o gráfico
        const chartData = this.prepareChartData(monthlyData);
        console.log('[DataTransformer] Dados preparados:', {
            categorias: chartData.categories.length,
            series: chartData.series.length,
            totalContas: chartData.stats.totalAccounts
        });
        
        return chartData;
    }

    /**
     * Mapeia nomes de colunas para índices
     */
    mapColumns(cols) {
        const map = {};
        const config = window.CHART_CONFIG?.columnMapping || {};
        
        // Criar mapa básico
        cols.forEach((col, index) => {
            map[col.name] = index;
        });
        
        // Aplicar mapeamento customizado se existir
        const mappedColumns = {};
        
        // Mapear para os nomes esperados
        Object.entries(config).forEach(([key, colName]) => {
            if (map[colName] !== undefined) {
                mappedColumns[key] = map[colName];
            }
        });
        
        // Se não encontrou todas as colunas necessárias, tentar auto-detectar
        if (Object.keys(mappedColumns).length < 5) {
            console.warn('[DataTransformer] Mapeamento incompleto, tentando auto-detectar...');
            
            // Tentar encontrar colunas por padrões comuns
            cols.forEach((col, index) => {
                const name = col.name.toLowerCase();
                
                // Data
                if (!mappedColumns.date && (name === 'date' || name === 'data' || name.includes('date'))) {
                    mappedColumns.date = index;
                    console.log(`[DataTransformer] Auto-detectado: date = ${col.name}`);
                }
                
                // Conta
                if (!mappedColumns.account && (name.includes('account') || name.includes('conta'))) {
                    mappedColumns.account = index;
                    console.log(`[DataTransformer] Auto-detectado: account = ${col.name}`);
                }
                
                // Impressões
                if (!mappedColumns.impressions && (name === 'impressions' || name.includes('impress'))) {
                    mappedColumns.impressions = index;
                    console.log(`[DataTransformer] Auto-detectado: impressions = ${col.name}`);
                }
                
                // Clicks
                if (!mappedColumns.clicks && (name === 'clicks' || name.includes('click'))) {
                    mappedColumns.clicks = index;
                    console.log(`[DataTransformer] Auto-detectado: clicks = ${col.name}`);
                }
                
                // Investimento
                if (!mappedColumns.spend && (name === 'spend' || name.includes('spend') || name.includes('invest') || name === 'cost')) {
                    mappedColumns.spend = index;
                    console.log(`[DataTransformer] Auto-detectado: spend = ${col.name}`);
                }
            });
        }
        
        console.log('[DataTransformer] Mapeamento final:', mappedColumns);
        console.log('[DataTransformer] Colunas disponíveis:', cols.map(c => c.name));
        
        return mappedColumns;
    }

    /**
     * Agrupa dados por mês/ano e conta
     */
    aggregateByMonth(rows, columnMap) {
        const aggregated = {};
        const startTime = Date.now();
        
        // Verificar se as colunas necessárias existem
        const requiredColumns = ['date', 'account', 'impressions', 'clicks', 'spend'];
        const missingColumns = requiredColumns.filter(col => columnMap[col] === undefined);
        
        if (missingColumns.length > 0) {
            console.error('[DataTransformer] Colunas obrigatórias não encontradas:', missingColumns);
            console.log('[DataTransformer] Colunas disponíveis:', Object.keys(columnMap));
            console.log('[DataTransformer] Verifique o mapeamento em config.js');
            return {};
        }
        
        // Pré-calcular índices para evitar lookups repetidos
        const dateIdx = columnMap.date;
        const accountIdx = columnMap.account;
        const impressionsIdx = columnMap.impressions;
        const clicksIdx = columnMap.clicks;
        const spendIdx = columnMap.spend;
        
        // Processar em lotes para melhor performance
        const batchSize = 1000;
        let processedRows = 0;
        
        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            
            try {
                const dateValue = row[dateIdx];
                if (!dateValue) continue;
                
                // Parse de data otimizado
                const dateStr = dateValue.substring(0, 7); // YYYY-MM
                const accountName = row[accountIdx] || 'Sem Conta';
                
                // Inicializar estrutura se necessário
                if (!aggregated[dateStr]) {
                    aggregated[dateStr] = {
                        date: new Date(dateValue),
                        accounts: {},
                        totals: { impressions: 0, clicks: 0, spend: 0 }
                    };
                }
                
                if (!aggregated[dateStr].accounts[accountName]) {
                    aggregated[dateStr].accounts[accountName] = {
                        impressions: 0,
                        clicks: 0,
                        spend: 0
                    };
                }
                
                // Somar valores - parse único
                const impressions = Number(row[impressionsIdx]) || 0;
                const clicks = Number(row[clicksIdx]) || 0;
                const spend = Number(row[spendIdx]) || 0;
                
                aggregated[dateStr].accounts[accountName].impressions += impressions;
                aggregated[dateStr].accounts[accountName].clicks += clicks;
                aggregated[dateStr].accounts[accountName].spend += spend;
                
                aggregated[dateStr].totals.impressions += impressions;
                aggregated[dateStr].totals.clicks += clicks;
                aggregated[dateStr].totals.spend += spend;
                
            } catch (error) {
                // Log apenas a cada 1000 erros para não poluir console
                if (i % 1000 === 0) {
                    console.error(`[DataTransformer] Erro ao processar linha ${i}:`, error);
                }
            }
            
            // Log de progresso a cada lote
            processedRows++;
            if (processedRows % batchSize === 0) {
                const progress = Math.round((processedRows / rows.length) * 100);
                console.log(`[DataTransformer] Processando... ${progress}%`);
            }
        }
        
        const aggregationTime = Date.now() - startTime;
        console.log(`[DataTransformer] Agregação concluída em ${aggregationTime}ms:`, {
            totalLinhas: rows.length,
            totalMeses: Object.keys(aggregated).length,
            meses: Object.keys(aggregated).sort()
        });
        
        return aggregated;
    }

    /**
     * Prepara dados no formato do Highcharts
     */
    prepareChartData(monthlyData) {
        // Ordenar meses
        const sortedMonths = Object.keys(monthlyData).sort();
        
        // Obter lista única de contas
        const allAccounts = new Set();
        sortedMonths.forEach(month => {
            Object.keys(monthlyData[month].accounts).forEach(account => {
                allAccounts.add(account);
            });
        });
        
        // Preparar categorias (eixo X)
        const categories = sortedMonths.map(month => {
            const date = monthlyData[month].date;
            return `${this.monthNames.pt[date.getMonth()]}/${date.getFullYear()}`;
        });
        
        // Preparar séries de impressions (colunas empilhadas por conta)
        const impressionsSeries = Array.from(allAccounts).map((account, index) => ({
            name: account,
            type: 'column',
            yAxis: 0,
            stack: 'impressions',
            data: sortedMonths.map(month => {
                const value = monthlyData[month].accounts[account]?.impressions || 0;
                return Math.round(value);
            }),
            color: this.getColorForAccount(index),
            tooltip: {
                valueSuffix: ' impressões'
            }
        }));
        
        // Preparar série de clicks (linha)
        const clicksSeries = {
            name: 'Clicks Total',
            type: 'spline',
            yAxis: 1,
            data: sortedMonths.map(month => Math.round(monthlyData[month].totals.clicks)),
            color: window.CHART_CONFIG?.visual?.clicksColor || '#FF6B6B',
            marker: {
                enabled: true,
                radius: 4
            },
            tooltip: {
                valueSuffix: ' clicks'
            }
        };
        
        // Preparar série de spend (linha)
        const spendSeries = {
            name: 'Investimento Total',
            type: 'spline',
            yAxis: 2,
            data: sortedMonths.map(month => {
                return parseFloat(monthlyData[month].totals.spend.toFixed(2));
            }),
            color: window.CHART_CONFIG?.visual?.spendColor || '#4CAF50',
            dashStyle: 'shortdot',
            marker: {
                enabled: true,
                radius: 4
            },
            tooltip: {
                valuePrefix: 'R$ ',
                valueDecimals: 2
            }
        };
        
        // Calcular estatísticas
        const stats = this.calculateStats(monthlyData, sortedMonths, allAccounts);
        
        return {
            categories,
            series: [...impressionsSeries, clicksSeries, spendSeries],
            stats,
            rawData: monthlyData
        };
    }

    /**
     * Calcula estatísticas para exibição
     */
    calculateStats(monthlyData, sortedMonths, allAccounts) {
        let totalImpressions = 0;
        let totalClicks = 0;
        let totalSpend = 0;
        
        sortedMonths.forEach(month => {
            totalImpressions += monthlyData[month].totals.impressions;
            totalClicks += monthlyData[month].totals.clicks;
            totalSpend += monthlyData[month].totals.spend;
        });
        
        const firstMonth = monthlyData[sortedMonths[0]].date;
        const lastMonth = monthlyData[sortedMonths[sortedMonths.length - 1]].date;
        
        return {
            totalAccounts: allAccounts.size,
            totalMonths: sortedMonths.length,
            totalImpressions,
            totalClicks,
            totalSpend,
            avgCTR: totalImpressions > 0 ? (totalClicks / totalImpressions * 100) : 0,
            avgCPC: totalClicks > 0 ? (totalSpend / totalClicks) : 0,
            dateRange: {
                start: firstMonth,
                end: lastMonth
            }
        };
    }

    /**
     * Retorna cor para uma conta específica
     */
    getColorForAccount(index) {
        const colors = window.CHART_CONFIG?.visual?.accountColors || [
            '#2E86DE', '#5F27CD', '#00B894', '#FDCB6E', '#E74C3C',
            '#0984E3', '#6C5CE7', '#00CEC9', '#FAB1A0', '#FF7675',
            '#74B9FF', '#A29BFE', '#55EFC4', '#FFEAA7', '#FF6B6B'
        ];
        return colors[index % colors.length];
    }

    /**
     * Retorna estrutura de dados vazia
     */
    getEmptyData() {
        return {
            categories: [],
            series: [],
            stats: {
                totalAccounts: 0,
                totalMonths: 0,
                totalImpressions: 0,
                totalClicks: 0,
                totalSpend: 0,
                avgCTR: 0,
                avgCPC: 0,
                dateRange: {
                    start: null,
                    end: null
                }
            },
            rawData: {}
        };
    }

    /**
     * Formata data para exibição
     */
    formatDateRange(start, end) {
        if (!start || !end) return '-';
        
        const startStr = `${this.monthNames.pt[start.getMonth()]}/${start.getFullYear()}`;
        const endStr = `${this.monthNames.pt[end.getMonth()]}/${end.getFullYear()}`;
        
        return startStr === endStr ? startStr : `${startStr} - ${endStr}`;
    }

    /**
     * Exporta dados para CSV
     */
    exportToCSV(chartData) {
        const { categories, series, rawData } = chartData;
        const sortedMonths = Object.keys(rawData).sort();
        
        // Cabeçalho
        let csv = 'Mês/Ano,Conta,Impressões,Clicks,Investimento\n';
        
        // Dados
        sortedMonths.forEach(month => {
            const monthData = rawData[month];
            const monthLabel = `${this.monthNames.pt[monthData.date.getMonth()]}/${monthData.date.getFullYear()}`;
            
            Object.entries(monthData.accounts).forEach(([account, data]) => {
                csv += `"${monthLabel}","${account}",${Math.round(data.impressions)},${Math.round(data.clicks)},${data.spend.toFixed(2)}\n`;
            });
        });
        
        return csv;
    }
}
