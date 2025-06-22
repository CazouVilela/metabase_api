// graph_config.js - Configurações dos gráficos do dashboard

window.GRAPH_CONFIG = {
    // Tipo de gráfico padrão
    chart: {
        type: 'line',  // 'line', 'bar', 'doughnut', etc.
        height: 400
    },
    
    // Cores do tema
    colors: {
        primary: ['#667eea', '#764ba2', '#f093fb', '#4facfe'],
        success: '#4caf50',
        warning: '#ff9800',
        danger: '#f44336'
    },
    
    // Configurações de formato
    formats: {
        currency: {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2
        },
        percentage: {
            style: 'percent',
            minimumFractionDigits: 2
        },
        number: {
            notation: 'compact',
            compactDisplay: 'short'
        }
    },
    
    // Métricas padrão para exibir
    defaultMetrics: ['spend', 'impressions', 'clicks', 'conversions'],
    
    // Configurações de agregação
    aggregation: {
        defaultPeriod: 7,  // últimos 7 dias
        groupBy: 'date'    // agrupar por data
    }
};