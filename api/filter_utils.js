function normalize(text) {
    return text
        ? text
            .toString()
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .trim()
        : '';
}

function isPlaceholder(text, field) {
    if (!text) return true;
    const placeholders = ['tudo', 'all', 'selecionar', 'selecionar...', 'select', 'select...', 'todos', 'todas'];
    const norm = normalize(text);
    if (placeholders.includes(norm)) return true;

    const mapping = window.filterMapping && window.filterMapping[field];
    if (mapping) {
        if (norm === normalize(mapping.friendlyName) || norm === normalize(field)) {
            return true;
        }
    }

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
        'previous 7 days': 'past7days',
        'previous 30 days': 'past30days',
        'last 7 days': 'past7days',
        'last 30 days': 'past30days',
        'this week': 'thisweek',
        'this month': 'thismonth',
        'this year': 'thisyear'
    };

    if (direct[t]) return direct[t];

    const prev = t.match(/(?:previous|últimos?|last|past)\s+(\d+)\s+(?:days?|dias?)/);
    if (prev) return `past${parseInt(prev[1])}days`;

    if (/^\d{2}[/-]\d{2}[/-]\d{4}$/.test(text)) {
        const [d, m, y] = text.split(/[/-]/);
        return `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`;
    }

    if (/^\d{4}-\d{2}-\d{2}$/.test(text) || text.includes('~')) {
        return text;
    }

    console.warn(`Formato de data não reconhecido: "${text}"`);
    return text;
}

function isMultipleSelection(text) {
    if (!text) return false;
    const indicators = [
        'seleção', 'seleções',
        'selection', 'selections',
        'selected',
        'selecionado', 'selecionados',
        'valores', 'values',
        'itens', 'items'
    ];

    if (/\d+\s*(seleç|select|valor|value|item)/i.test(text)) return true;

    const lower = text.toLowerCase();
    return indicators.some(i => lower.includes(i));
}

function attemptToGetRealValues(widget) {
    try {
        const reactKey = Object.keys(widget).find(k =>
            k.startsWith('__reactInternalFiber') ||
            k.startsWith('__reactFiber') ||
            k.startsWith('__react')
        );

        if (!reactKey) return null;

        let current = widget[reactKey];
        let attempts = 0;

        while (current && attempts < 20) {
            attempts++;

            if (current.memoizedProps) {
                const keys = ['value', 'values', 'selectedValue', 'selectedValues', 'selected'];
                for (const key of keys) {
                    const val = current.memoizedProps[key];
                    if (Array.isArray(val) && val.length > 0) {
                        return val;
                    }
                }
            }

            if (current.memoizedState && Array.isArray(current.memoizedState)) {
                for (const state of current.memoizedState) {
                    if (state && state.value && Array.isArray(state.value)) {
                        return state.value;
                    }
                }
            }

            current = current.return;
        }
    } catch (e) {
        /* empty */
    }

    return null;
}

function extractMultipleValues(fieldset, widget) {
    try {
        const dropdown = fieldset.querySelector('[role="listbox"], .ant-select-dropdown, [class*="dropdown"]');
        if (dropdown) {
            const selected = dropdown.querySelectorAll('[aria-selected="true"], .selected, [class*="selected"]');
            if (selected.length > 0) {
                return Array.from(selected).map(el => el.textContent.trim()).filter(Boolean);
            }
        }

        const tags = fieldset.querySelectorAll('.ant-tag, [class*="tag"], [class*="chip"], [class*="selected-value"]');
        if (tags.length > 0) {
            return Array.from(tags).map(tag => tag.textContent.replace(/[×✕✖]/, '').trim()).filter(Boolean);
        }
    } catch (e) {
        console.error('Erro ao extrair valores múltiplos:', e);
    }

    return null;
}

function captureDashboardFilters() {
    const result = {};

    if (window.parent === window) return result;

    try {
        let containers = window.parent.document.querySelectorAll('.Parameter');
        if (containers.length === 0) {
            containers = window.parent.document.querySelectorAll('fieldset');
        }

        containers.forEach(container => {
            let labelEl = container.querySelector('label, .Parameter-name, [class*="Parameter-name"], legend');
            if (!labelEl) return;

            const field = typeof window.findFieldByLabel === 'function' ? window.findFieldByLabel(labelEl.textContent) : null;
            if (!field) return;

            const mapping = window.filterMapping && window.filterMapping[field];
            if (!mapping) return;

            const widget = container.querySelector('[data-testid*="parameter-value-widget"], .Parameter-content input, .Parameter-content [role="button"], [role="button"], input, .lnsju');
            if (!widget) return;

            const raw = widget.textContent?.trim() || widget.value?.trim();
            if (!raw || isPlaceholder(raw, field)) return;

            let value = raw;
            if (mapping.type === 'date' || field === 'data') {
                value = convertDateToAPIFormat(raw);
            } else if (isMultipleSelection(raw)) {
                value = attemptToGetRealValues(widget) || extractMultipleValues(container, widget) || [raw];
            }

            result[mapping.metabaseParam] = value;
        });
    } catch (e) {
        if (!e.message.includes('cross-origin')) {
            console.error('Erro ao capturar filtros:', e);
        }
    }

    return result;
}

if (typeof window !== 'undefined') {
    window.captureDashboardFilters = captureDashboardFilters;
}
