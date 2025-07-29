/**
 * Configuração do componente gráfico
 * Ajuste os mapeamentos de colunas se necessário
 */
const CHART_CONFIG = {
    // Mapeamento de colunas
    // Se suas colunas têm nomes diferentes, ajuste aqui
    columnMapping: {
        date: 'date',               // Coluna de data
        account: 'account_name',    // Coluna de nome da conta
        impressions: 'impressions', // Coluna de impressões
        clicks: 'clicks',           // Coluna de clicks
        spend: 'spend'              // Coluna de investimento
    },
    
    // Configurações visuais
    visual: {
        // Cores para cada conta (será ciclado se houver mais contas)
        accountColors: [
            '#2E86DE', '#5F27CD', '#00B894', '#FDCB6E', '#E74C3C',
            '#0984E3', '#6C5CE7', '#00CEC9', '#FAB1A0', '#FF7675',
            '#74B9FF', '#A29BFE', '#55EFC4', '#FFEAA7', '#FF6B6B'
        ],
        
        // Cores das linhas
        clicksColor: '#FF6B6B',     // Vermelho para clicks
        spendColor: '#4CAF50',      // Verde para investimento
        
        // Altura mínima do gráfico
        minHeight: 400
    },
    
    // Configurações de agregação
    aggregation: {
        // Formato de data para agrupamento (não alterar)
        dateFormat: 'YYYY-MM'
    },
    
    // Timeout para requisições
    requestTimeout: 30000, // 30 segundos
    
    // Debug
    debug: true // Mostra logs detalhados no console
};

// Exportar para uso global
window.CHART_CONFIG = CHART_CONFIG;
