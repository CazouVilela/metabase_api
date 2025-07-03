const FILTER_MAPPING = {
    'data': { metabaseParam: 'data', friendlyName: 'Data', type: 'date' },
    'conta': { metabaseParam: 'conta', friendlyName: 'Conta', type: 'string' },
    'campanha': { metabaseParam: 'campanha', friendlyName: 'Campanha', type: 'string' },
    'adset': { metabaseParam: 'adset', friendlyName: 'Conjunto de Anúncios', type: 'string' },
    'anuncio': { metabaseParam: 'ad_name', friendlyName: 'Anúncio', type: 'string' },
    'device': { metabaseParam: 'device', friendlyName: 'Dispositivo', type: 'string' },
    'plataforma': { metabaseParam: 'plataforma', friendlyName: 'Plataforma', type: 'string' },
    'posicao': { metabaseParam: 'posicao', friendlyName: 'Posição', type: 'string' },
    'objetivo': { metabaseParam: 'objective', friendlyName: 'Objetivo', type: 'string' },
    'buying_type': { metabaseParam: 'buying_type', friendlyName: 'Tipo de Compra', type: 'string' },
    'optimization_goal': { metabaseParam: 'optimization_goal', friendlyName: 'Meta de Otimização', type: 'string' },
    'conversoes_consideradas': { metabaseParam: 'action_type_filter', friendlyName: 'Conversões Consideradas', type: 'string' }
};

const FIELD_VARIATIONS = {
    'conjunto de anúncios': 'adset',
    'conjunto de anuncios': 'adset',
    'adset': 'adset',
    'anúncio': 'anuncio',
    'anuncio': 'anuncio',
    'peça': 'anuncio',
    'peca': 'anuncio',
    'ad': 'anuncio',
    'device': 'device',
    'dispositivo': 'device',
    'buying type': 'buying_type',
    'tipo de compra': 'buying_type',
    'optimization goal': 'optimization_goal',
    'meta de otimização': 'optimization_goal',
    'meta de otimizacao': 'optimization_goal',
    'conversões consideradas': 'conversoes_consideradas',
    'conversoes consideradas': 'conversoes_consideradas'
};

function normalize(text) {
    return text ? text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim() : '';
}

function findFieldByLabel(label) {
    const norm = normalize(label);
    if (FILTER_MAPPING[norm]) return norm;
    if (FIELD_VARIATIONS[norm]) return FIELD_VARIATIONS[norm];
    for (const [field, cfg] of Object.entries(FILTER_MAPPING)) {
        if (normalize(cfg.friendlyName) === norm) return field;
    }
    return null;
}

if (typeof window !== 'undefined') {
    window.filterMapping = FILTER_MAPPING;
    window.fieldVariations = FIELD_VARIATIONS;
    window.findFieldByLabel = findFieldByLabel;
}
