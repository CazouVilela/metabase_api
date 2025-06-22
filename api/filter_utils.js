function normalize(text) {
    return text ? text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim() : '';
}

function isPlaceholder(value, friendly, field) {
    const placeholders = ['tudo','all','selecionar','selecionar...','select','select...','todos','todas'];
    const norm = normalize(value);
    if (placeholders.includes(norm)) return true;
    if (norm === normalize(friendly) || norm === normalize(field)) return true;
    return false;
}

function convertDateToAPIFormat(text) {
    if (!text) return text;
    const t = normalize(text);
    const direct = {
        'ontem': 'yesterday',
        'hoje': 'today',
        'últimos 7 dias': 'past7days',
        'ultimos 7 dias': 'past7days',
        'últimos 30 dias': 'past30days',
        'ultimos 30 dias': 'past30days',
        'esta semana': 'thisweek',
        'este mês': 'thismonth',
        'este mes': 'thismonth',
        'este ano': 'thisyear',
        'yesterday': 'yesterday',
        'today': 'today',
        'past7days': 'past7days',
        'past30days': 'past30days',
        'thisweek': 'thisweek',
        'thismonth': 'thismonth',
        'thisyear': 'thisyear'
    };
    if (direct[t]) return direct[t];
    const match = t.match(/(?:last|past|previous|ultimos?)\s*(\d+)\s*(?:dias?|days?)/);
    if (match) return `past${parseInt(match[1])}days`;
    if (/^\d{2}[/-]\d{2}[/-]\d{4}$/.test(text)) {
        const [d,m,y]=text.split(/[/-]/);
        return `${y}-${m.padStart(2,'0')}-${d.padStart(2,'0')}`;
    }
    if (/^\d{4}-\d{2}-\d{2}$/.test(text) || text.includes('~')) return text;
    return text;
}

function captureDashboardFilters() {
    const result = {};
    if (window.parent === window) return result;
    try {
        let containers = window.parent.document.querySelectorAll('.Parameter');
        if (containers.length === 0) {
            containers = window.parent.document.querySelectorAll('fieldset');
        }
        containers.forEach(cont => {
            const labelEl = cont.querySelector('label, legend, .Parameter-name, [class*="Parameter-name"]');
            if (!labelEl || typeof window.findFieldByLabel !== 'function') return;
            const field = window.findFieldByLabel(labelEl.textContent);
            if (!field) return;
            const mapping = window.filterMapping ? window.filterMapping[field] : null;
            if (!mapping) return;
            const widget = cont.querySelector('[data-testid*="parameter-value-widget"], [role="button"], input, select');
            if (!widget) return;
            const raw = (widget.value || widget.textContent || '').trim();
            if (!raw || isPlaceholder(raw, mapping.friendlyName, field)) return;
            let value = raw;
            if (mapping.type === 'date') value = convertDateToAPIFormat(raw);
            result[mapping.metabaseParam] = value;
        });
    } catch (e) {
        console.error('Erro ao capturar filtros', e);
    }
    return result;
}

if (typeof window !== 'undefined') {
    window.captureDashboardFilters = captureDashboardFilters;
}
