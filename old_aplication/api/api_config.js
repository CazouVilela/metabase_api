// ============================================
// CONFIGURAÇÕES SEGURAS DA API (SEM TOKEN!)
// ============================================

const CONFIG = {
    // URL do proxy local (não expõe o Metabase diretamente)
    // Mudar de:
    // proxyUrl: getParameterByName('proxy_url') || 'http://localhost:8091',

    // Para usar o proxy através do nginx:
    proxyUrl: getParameterByName('proxy_url') || '/proxy',

    // ID da pergunta padrão
    defaultQuestionId: parseInt(getParameterByName('question_id')) || 51,

    // Configurações gerais da API
    api: {
        timeout: 30000,  // 30 segundos
        retries: 3,
        retryDelay: 1000  // 1 segundo entre tentativas
    }
};

// ============================================
// MAPEAMENTO DE FILTROS DINÂMICO E FLEXÍVEL
// ============================================

// Mapeamento padrão: campo_dashboard -> parametro_api
const defaultFilterMapping = {
    'data': {
        metabaseParam: 'data',
        friendlyName: 'Data',
        type: 'date'
    },
    'conta': {
        metabaseParam: 'conta',
        friendlyName: 'Conta',
        type: 'string'
    },
    'campanha': {
        metabaseParam: 'campanha',
        friendlyName: 'Campanha',
        type: 'string'
    },
    'adset': {
        metabaseParam: 'adset',
        friendlyName: 'Conjunto de Anúncios',
        type: 'string'
    },
    'anuncio': {
        metabaseParam: 'ad_name',
        friendlyName: 'Anúncio',
        type: 'string'
    },
    'device': {
        metabaseParam: 'device',
        friendlyName: 'Dispositivo',
        type: 'string'
    },
    'plataforma': {
        metabaseParam: 'plataforma',
        friendlyName: 'Plataforma',
        type: 'string'
    },
    'posicao': {
        metabaseParam: 'posicao',
        friendlyName: 'Posição',
        type: 'string'
    },
    'objetivo': {
        metabaseParam: 'objective',
        friendlyName: 'Objetivo',
        type: 'string'
    },
    'buying_type': {
        metabaseParam: 'buying_type',
        friendlyName: 'Tipo de Compra',
        type: 'string'
    },
    'optimization_goal': {
        metabaseParam: 'optimization_goal',
        friendlyName: 'Meta de Otimização',
        type: 'string'
    },
    'conversoes_consideradas': {
        metabaseParam: 'action_type_filter',
        friendlyName: 'Conversões Consideradas',
        type: 'string'
    }
};

// Inicializar filterMapping com valores padrão
let filterMapping = JSON.parse(JSON.stringify(defaultFilterMapping));


// Adicione estas linhas no api_config.js APÓS a criação do filterMapping inicial
// para adicionar suporte a variações de nomes/labels

// Adicionar variações comuns dos campos para melhor matching
const fieldVariations = {
    // Conjunto de anúncios
    'conjunto de anúncios': 'adset',
    'conjunto de anuncios': 'adset',
    'adset': 'adset',

    // Anúncio/Peça
    'anúncio': 'anuncio',
    'anuncio': 'anuncio',
    'peça': 'anuncio',
    'peca': 'anuncio',
    'ad': 'anuncio',

    // Device/Dispositivo
    'device': 'device',
    'dispositivo': 'device',

    // Buying type
    'buying type': 'buying_type',
    'tipo de compra': 'buying_type',
    'buying_type': 'buying_type',

    // Optimization goal
    'optimization goal': 'optimization_goal',
    'meta de otimização': 'optimization_goal',
    'meta de otimizacao': 'optimization_goal',
    'optimization_goal': 'optimization_goal',

    // Conversões
    'conversões consideradas': 'conversoes_consideradas',
    'conversoes consideradas': 'conversoes_consideradas',
    'action type filter': 'conversoes_consideradas',
    'action_type_filter': 'conversoes_consideradas'
};

// Adicionar as variações ao filterMapping
Object.entries(fieldVariations).forEach(([variation, field]) => {
    if (!filterMapping[variation] && filterMapping[field]) {
        filterMapping[variation] = { ...filterMapping[field] };
    }
});

// Função auxiliar melhorada para matching de campos
window.findFieldByLabel = function (label) {
    if (!label) return null;

    const normalized = label.toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '') // Remove acentos
        .trim();

    // Buscar no filterMapping
    for (const [field, config] of Object.entries(filterMapping)) {
        const fieldNorm = field.toLowerCase();
        const friendlyNorm = config.friendlyName.toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '');

        if (normalized === fieldNorm || normalized === friendlyNorm) {
            return field;
        }
    }

    // Buscar nas variações
    return fieldVariations[normalized] || null;
};


// ============================================
// FUNÇÕES AUXILIARES
// ============================================

function getParameterByName(name) {
    const url = window.location.href;
    name = name.replace(/[\[\]]/g, '\\$&');
    const regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)');
    const results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, ' '));
}

// ============================================
// PROCESSAR MAPEAMENTO CUSTOMIZADO DA URL
// ============================================

// Formato esperado na URL:
// filterMapping={"anuncio":{"metabaseParam":"ad_name","friendlyName":"Peça"},"novo_campo":{"metabaseParam":"new_field","friendlyName":"Novo Campo"}}

const urlFilterMapping = getParameterByName('filterMapping');
if (urlFilterMapping) {
    try {
        const customMapping = JSON.parse(urlFilterMapping);

        // Mesclar com o mapeamento padrão
        Object.entries(customMapping).forEach(([field, config]) => {
            if (typeof config === 'string') {
                // Formato simples: campo -> parametro
                filterMapping[field] = {
                    metabaseParam: config,
                    friendlyName: field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' '),
                    type: 'string'
                };
            } else if (typeof config === 'object') {
                // Formato completo com todas as configurações
                filterMapping[field] = {
                    metabaseParam: config.metabaseParam || field,
                    friendlyName: config.friendlyName || field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' '),
                    type: config.type || 'string',
                    defaultValue: config.defaultValue || null,
                    fixed: config.fixed || false
                };
            }
        });

        console.log('✅ FilterMapping customizado aplicado:', customMapping);
    } catch (e) {
        console.error('❌ Erro ao parsear filterMapping da URL:', e);
    }
}

// ============================================
// FUNÇÕES DE UTILIDADE PARA OS FILTROS
// ============================================

// Obter labels amigáveis dinamicamente
function getFriendlyLabels() {
    const labels = {};
    Object.entries(filterMapping).forEach(([field, config]) => {
        labels[field] = config.friendlyName;
        // Adicionar também o parâmetro da API para retrocompatibilidade
        labels[config.metabaseParam] = config.friendlyName;
    });
    return labels;
}

// Obter mapeamento simples campo -> parametro
function getSimpleFilterMapping() {
    const simple = {};
    Object.entries(filterMapping).forEach(([field, config]) => {
        simple[field] = config.metabaseParam;
    });
    return simple;
}

// Obter lista de campos na ordem definida
function getFieldOrder() {
    return Object.keys(filterMapping);
}

// Aplicar filtros fixos
function applyFixedFilters(filters) {
    const processedFilters = { ...filters };

    Object.entries(filterMapping).forEach(([dashboardField, config]) => {
        if (config.fixed && config.defaultValue !== null) {
            processedFilters[config.metabaseParam] = config.defaultValue;
            console.log(`Filtro fixo aplicado: ${config.metabaseParam} = ${config.defaultValue}`);
        }
    });

    return processedFilters;
}

// Headers da API
function getApiHeaders() {
    return {
        'Content-Type': 'application/json'
    };
}

// ============================================
// CONFIGURAÇÃO DO SERVIDOR (OPCIONAL)
// ============================================

async function loadServerConfig() {
    try {
        const response = await fetch(`${CONFIG.proxyUrl}/api/client-config`);
        if (response.ok) {
            const serverConfig = await response.json();
            Object.assign(CONFIG, serverConfig);
            console.log('Configurações do servidor carregadas:', serverConfig);
        }
    } catch (error) {
        console.warn('Não foi possível carregar configurações do servidor:', error);
    }
}

// Carregar configurações ao iniciar
loadServerConfig();

// ============================================
// EXPORTS GLOBAIS
// ============================================

window.CONFIG = CONFIG;
window.filterMapping = filterMapping;
window.simpleFilterMapping = getSimpleFilterMapping();
window.friendlyLabels = getFriendlyLabels();
window.fieldOrder = getFieldOrder();
window.getApiHeaders = getApiHeaders;
window.applyFixedFilters = applyFixedFilters;
window.getFriendlyLabels = getFriendlyLabels;
window.getFieldOrder = getFieldOrder;

/*
console.log('✅ API Config carregada:', {
    proxyUrl: CONFIG.proxyUrl,
    questionId: CONFIG.defaultQuestionId,
    totalFilters: Object.keys(filterMapping).length,
    filterFields: Object.keys(filterMapping),
    friendlyLabels: getFriendlyLabels()
});
*/