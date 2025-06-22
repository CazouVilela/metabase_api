// metabase-dashboard-integration.js

// Configuração para conectar com a pergunta 51 do Metabase
const METABASE_CONFIG = {
    url: 'http://localhost:3000', // ou 'https://metabasedashboards.ngrok.io'
    questionId: 51
};

// Função principal para carregar e processar dados
async function loadAndProcessMetabaseData() {
    try {
        // Verificar se os dados já foram carregados pela API
        if (!window.metabaseDados || !window.metabaseDados.formatted) {
            console.error('Dados do Metabase não encontrados. Execute primeiro a API de teste.');
            return null;
        }

        const rawData = window.metabaseDados.formatted;
        console.log(`📊 Processando ${rawData.length} linhas de dados...`);

        // Validar colunas necessárias
        const requiredColumns = ['date', 'campaign_name', 'impressions', 'clicks', 'spend', 'conversions'];
        const availableColumns = window.metabaseDados.metadata.columns.map(col => col.name);
        
        const missingColumns = requiredColumns.filter(col => !availableColumns.includes(col));
        if (missingColumns.length > 0) {
            console.warn(`⚠️ Colunas faltando: ${missingColumns.join(', ')}`);
        }

        // Processar dados
        const processedData = processDataForDashboard(rawData);
        
        // Criar gráfico automaticamente
        if (typeof createChart === 'function') {
            createChart(processedData);
            console.log('✅ Dashboard criado com sucesso!');
        }

        return processedData;

    } catch (error) {
        console.error('❌ Erro ao processar dados:', error);
        return null;
    }
}

// Função para processar os dados no formato esperado pelo dashboard
function processDataForDashboard(data) {
    // Agrupar dados por data e campanha
    const groupedData = {};
    const campaigns = new Set();
    const dates = new Set();
    
    data.forEach(row => {
        // Garantir que a data está no formato correto
        const date = formatDate(row.date);
        const campaign = row.campaign_name || 'Sem Campanha';
        
        dates.add(date);
        campaigns.add(campaign);
        
        if (!groupedData[date]) {
            groupedData[date] = {};
        }
        
        if (!groupedData[date][campaign]) {
            groupedData[date][campaign] = {
                impressions: 0,
                clicks: 0,
                spend: 0,
                conversions: 0,
                revenue: 0
            };
        }
        
        // Somar valores (tratando nulls)
        groupedData[date][campaign].impressions += row.impressions || 0;
        groupedData[date][campaign].clicks += row.clicks || 0;
        groupedData[date][campaign].spend += row.spend || 0;
        groupedData[date][campaign].conversions += row.conversions || 0;
        groupedData[date][campaign].revenue += row.revenue || 0;
    });
    
    // Ordenar datas
    const sortedDates = Array.from(dates).sort();
    const campaignsList = Array.from(campaigns).sort();
    
    console.log(`📅 Período: ${sortedDates[0]} até ${sortedDates[sortedDates.length - 1]}`);
    console.log(`🎯 Campanhas encontradas: ${campaignsList.join(', ')}`);
    
    // Preparar dados para o gráfico
    const seriesData = {
        dates: sortedDates,
        campaigns: campaignsList,
        impressions: {},
        clicks: {},
        spend: {},
        conversions: {},
        // Métricas calculadas
        cpm: [],
        ctr: [],
        cpc: [],
        convRate: [],
        cpConv: [],
        roas: []
    };
    
    // Inicializar arrays para cada campanha
    campaignsList.forEach(campaign => {
        seriesData.impressions[campaign] = [];
        seriesData.clicks[campaign] = [];
        seriesData.spend[campaign] = [];
        seriesData.conversions[campaign] = [];
    });
    
    // Preencher dados e calcular métricas
    sortedDates.forEach(date => {
        let totalImpressions = 0;
        let totalClicks = 0;
        let totalSpend = 0;
        let totalConversions = 0;
        let totalRevenue = 0;
        
        campaignsList.forEach(campaign => {
            const data = groupedData[date] && groupedData[date][campaign] || {};
            
            seriesData.impressions[campaign].push(data.impressions || 0);
            seriesData.clicks[campaign].push(data.clicks || 0);
            seriesData.spend[campaign].push(data.spend || 0);
            seriesData.conversions[campaign].push(data.conversions || 0);
            
            totalImpressions += data.impressions || 0;
            totalClicks += data.clicks || 0;
            totalSpend += data.spend || 0;
            totalConversions += data.conversions || 0;
            totalRevenue += data.revenue || 0;
        });
        
        // Calcular métricas com proteção contra divisão por zero
        // CPM = (Spend / Impressions) * 1000
        seriesData.cpm.push(totalImpressions > 0 ? (totalSpend / (totalImpressions / 1000)) : null);
        
        // CTR = (Clicks / Impressions) * 100
        seriesData.ctr.push(totalImpressions > 0 ? (totalClicks / totalImpressions * 100) : null);
        
        // CPC = Spend / Clicks
        seriesData.cpc.push(totalClicks > 0 ? (totalSpend / totalClicks) : null);
        
        // ConvRate = (Conversions / Clicks) * 100
        seriesData.convRate.push(totalClicks > 0 ? (totalConversions / totalClicks * 100) : null);
        
        // CPConv = Spend / Conversions
        seriesData.cpConv.push(totalConversions > 0 ? (totalSpend / totalConversions) : null);
        
        // ROAS = (Revenue / Spend) * 100
        seriesData.roas.push(totalSpend > 0 ? ((totalRevenue / totalSpend) * 100) : null);
    });
    
    // Log de resumo
    console.log('📊 Resumo dos dados processados:');
    console.log(`- Total de datas: ${sortedDates.length}`);
    console.log(`- Total de campanhas: ${campaignsList.length}`);
    console.log(`- Total de impressões: ${Object.values(seriesData.impressions).flat().reduce((a, b) => a + b, 0).toLocaleString()}`);
    console.log(`- Total de cliques: ${Object.values(seriesData.clicks).flat().reduce((a, b) => a + b, 0).toLocaleString()}`);
    console.log(`- Total gasto: $${Object.values(seriesData.spend).flat().reduce((a, b) => a + b, 0).toFixed(2)}`);
    
    return seriesData;
}

// Função auxiliar para formatar datas
function formatDate(dateValue) {
    if (!dateValue) return 'Sem Data';
    
    // Se já for uma string no formato ISO, retornar
    if (typeof dateValue === 'string' && dateValue.match(/^\d{4}-\d{2}-\d{2}/)) {
        return dateValue.split('T')[0];
    }
    
    // Tentar converter para Date
    const date = new Date(dateValue);
    if (!isNaN(date.getTime())) {
        return date.toISOString().split('T')[0];
    }
    
    return dateValue.toString();
}

// Função para exportar dados processados
function exportProcessedData() {
    const data = processedData || processDataForDashboard(window.metabaseDados.formatted);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'dashboard-data.json';
    a.click();
    URL.revokeObjectURL(url);
}

// Atalhos úteis
window.dashboardHelpers = {
    load: loadAndProcessMetabaseData,
    process: processDataForDashboard,
    export: exportProcessedData,
    config: METABASE_CONFIG
};

console.log('🚀 Dashboard helpers carregados! Use:');
console.log('- dashboardHelpers.load() para carregar dados do Metabase');
console.log('- dashboardHelpers.export() para exportar dados processados');
