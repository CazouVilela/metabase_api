const FILTER_MAPPING = {
    'data': 'data',
    'conta': 'conta',
    'campanha': 'campanha',
    'adset': 'adset',
    'anuncio': 'ad_name',
    'device': 'device',
    'plataforma': 'plataforma',
    'posicao': 'posicao',
    'objetivo': 'objective',
    'buying type': 'buying_type',
    'optimization goal': 'optimization_goal',
    'conversoes consideradas': 'action_type_filter'
};

function normalize(text) {
    return text ? text.toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .trim() : '';
}

function captureFilters() {
    const filters = {};
    if (window.parent === window) return filters;
    try {
        const containers = window.parent.document.querySelectorAll('.Parameter, fieldset');
        containers.forEach(container => {
            const labelEl = container.querySelector('label, legend, .Parameter-name, [class*="Parameter-name"]');
            if (!labelEl) return;
            const paramName = FILTER_MAPPING[normalize(labelEl.textContent)];
            if (!paramName) return;
            const widget = container.querySelector('[role="button"], input, select');
            if (!widget) return;
            const value = (widget.value || widget.textContent || '').trim();
            if (!value || ['All','Tudo','Selecione...','Select...'].includes(value)) return;
            filters[paramName] = value;
        });
    } catch (e) {
        console.error('Erro ao capturar filtros', e);
    }
    return filters;
}

if (typeof window !== 'undefined') {
    window.captureDashboardFilters = captureFilters;
}
