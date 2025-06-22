// metabase-api.js - Versão Corrigida com Formato Correto de Parâmetros
class MetabaseAPI {
    constructor(config = {}) {
        // Usar proxy URL em vez de Metabase direto
        this.baseUrl = (config.baseUrl || window.CONFIG?.proxyUrl || 'http://localhost:8091').replace(/\/$/, '');

        // Não precisa mais do token!
        this.apiToken = null;

        // Configurações da API
        this.timeout = config.timeout || window.CONFIG?.api?.timeout || 30000;
        this.retries = config.retries || window.CONFIG?.api?.retries || 3;
        this.retryDelay = config.retryDelay || window.CONFIG?.api?.retryDelay || 1000;

        // Cache
        this.questionCache = {};

        // Configurações de monitoramento de filtros
        this.isInIframe = window.parent !== window;
        this.capturedFilters = {};
        this.lastFiltersJSON = '';
        this.checkInterval = null;
        this.checkFrequency = config.checkFrequency || 1000;
        this.filterChangeCallbacks = [];
        this.filterObserver = null;

        console.log('✅ MetabaseAPI inicializada (Modo Seguro):', {
            proxyUrl: this.baseUrl,
            isInIframe: this.isInIframe
        });
    }

    // Headers simplificados (sem token)
    getHeaders() {
        return {
            'Content-Type': 'application/json'
        };
    }

    // Buscar informações da pergunta (via proxy)
    async getQuestionInfo(questionId) {
        if (this.questionCache[questionId]) {
            return this.questionCache[questionId];
        }

        try {
            const response = await fetch(`${this.baseUrl}/api/card/${questionId}`, {
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`Erro ao buscar pergunta ${questionId}: ${response.status}`);
            }

            const cardInfo = await response.json();
            this.questionCache[questionId] = cardInfo;

            return cardInfo;
        } catch (error) {
            console.error('❌ Erro ao buscar info da pergunta:', error);
            throw error;
        }
    }

    // Buscar dados com filtros (via proxy) - VERSÃO CORRIGIDA
    async getFilteredData(questionId, filters = {}) {
        try {
            questionId = questionId || window.CONFIG?.defaultQuestionId;

            if (!questionId) {
                throw new Error('Question ID não fornecido');
            }

            // Se não houver filtros fornecidos, usar os capturados
            if (Object.keys(filters).length === 0 && Object.keys(this.capturedFilters).length > 0) {
                filters = this.capturedFilters;
                console.log('📋 Usando filtros capturados:', filters);
            }

            // Aplicar filtros fixos se existirem
            let processedFilters = filters;
            if (window.applyFixedFilters && typeof window.applyFixedFilters === 'function') {
                processedFilters = window.applyFixedFilters(filters);
            }

            // Buscar informações da pergunta para obter template tags
            const cardInfo = await this.getQuestionInfo(questionId);
            const templateTags = cardInfo.dataset_query?.native?.['template-tags'] || {};

            // Obter mapeamento de filtros
            const filterMapping = window.filterMapping || {};
            const simpleFilterMapping = window.simpleFilterMapping || {};

            // Construir array de parâmetros no formato correto do Metabase
            const parameters = [];

            Object.entries(processedFilters).forEach(([key, value]) => {
                // Pular valores vazios ou placeholders
                if (!value || value === '' || value === `{{${key}}}`) {
                    console.log(`⏭️ Pulando filtro vazio: ${key}`);
                    return;
                }

                // Determinar o nome do parâmetro correto
                let mappedKey;
                if (filterMapping[key]) {
                    mappedKey = filterMapping[key].metabaseParam || key;
                } else if (simpleFilterMapping[key]) {
                    mappedKey = simpleFilterMapping[key];
                } else {
                    mappedKey = key;
                }

                // Verificar se o template tag existe
                const templateTag = templateTags[mappedKey];
                if (!templateTag) {
                    console.warn(`⚠️ Template tag não encontrada para: ${mappedKey}`);
                    return;
                }

                // Determinar o tipo correto baseado no template tag
                let paramType = this.determineParameterType(mappedKey, value, templateTag);

                // Formatar o valor adequadamente
                const formattedValue = this.formatParameterValue(mappedKey, value, templateTag);

                // Construir o parâmetro no formato exato do Metabase
                const parameter = {
                    type: paramType,
                    target: ["variable", ["template-tag", mappedKey]],
                    value: formattedValue
                };

                parameters.push(parameter);
                console.log(`✅ Parâmetro adicionado: ${mappedKey} = ${JSON.stringify(formattedValue)} (tipo: ${paramType})`);
            });

            console.log('📤 Executando query com parâmetros:', parameters);

            // Executar query via proxy
            const response = await fetch(`${this.baseUrl}/api/card/${questionId}/query`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ parameters })
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ Erro na resposta:', errorText);
                throw new Error(`Erro ${response.status}: ${errorText}`);
            }

            const result = await response.json();

            // Se a query ainda está em execução, aguardar
            if (result.status === 'running') {
                console.log('⏳ Query em execução, aguardando...');
                await new Promise(resolve => setTimeout(resolve, 2000));
                return this.getFilteredData(questionId, filters);
            }

            // Formatar os dados
            const formattedData = this.formatData(result);

            console.log(`✅ Query executada com sucesso: ${formattedData.length} linhas retornadas`);

            return {
                raw: result,
                formatted: formattedData,
                metadata: {
                    questionId: questionId,
                    rows: formattedData.length,
                    columns: result.data?.cols || [],
                    appliedFilters: processedFilters,
                    originalFilters: filters,
                    parameters: parameters
                }
            };

        } catch (error) {
            console.error('❌ Erro ao buscar dados:', error);
            throw error;
        }
    }

    // Determinar o tipo correto do parâmetro baseado no template tag
    determineParameterType(paramName, value, templateTag) {
        // Obter o tipo do template tag
        const tagType = templateTag.type;
        const widgetType = templateTag['widget-type'];

        console.log(`🔍 Determinando tipo para ${paramName}: tagType=${tagType}, widgetType=${widgetType}`);

        // Para datas
        if (tagType === 'date' || widgetType === 'date/all-options' || paramName === 'data') {
            // Se for um valor de data relativa
            if (typeof value === 'string' && this.isRelativeDate(value)) {
                return 'date/all-options';
            }
            // Se for um range de datas
            if (typeof value === 'string' && value.includes('~')) {
                return 'date/range';
            }
            // Data única
            return 'date/single';
        }

        // Para números
        if (tagType === 'number' || widgetType === 'number') {
            return 'number';
        }

        // Para strings/text/dimension
        if (widgetType === 'string/=' || widgetType === 'text' || tagType === 'text' || tagType === 'dimension') {
            // Se for array, ainda é category
            if (Array.isArray(value)) {
                return 'category';
            }
            // Para valores únicos também usar category
            return 'category';
        }

        // Default para category (funciona para a maioria dos casos)
        return 'category';
    }

    // Verificar se é uma data relativa
    isRelativeDate(value) {
        const relativeDates = [
            'today', 'yesterday', 'thisweek', 'thismonth', 'thisyear',
            'lastweek', 'lastmonth', 'lastyear',
            'past7days', 'past30days', 'past60days', 'past90days',
            'past1days', 'past2days', 'past3days', 'past4days', 'past5days', 'past6days'
        ];

        // Verificar padrões como "past7days", "last7days", etc.
        if (relativeDates.includes(value.toLowerCase())) {
            return true;
        }

        // Verificar padrão dinâmico "pastXdays"
        if (/^(past|last|previous)\d+days?$/i.test(value)) {
            return true;
        }

        return false;
    }

    // Formatar valor do parâmetro
    formatParameterValue(paramName, value, templateTag) {
        // Se já for um array, retornar como está
        if (Array.isArray(value)) {
            return value;
        }

        // Para datas, aplicar conversão se necessário
        if ((paramName === 'data' || templateTag?.type === 'date' || templateTag?.['widget-type']?.includes('date')) && value) {
            // Se for data relativa conhecida, manter como está
            if (this.isRelativeDate(value)) {
                return value.toLowerCase();
            }

            // Se for range de datas (com ~), manter como está
            if (value.includes('~')) {
                return value;
            }

            // Se for data no formato brasileiro, converter para ISO
            if (value.match(/^\d{2}[/-]\d{2}[/-]\d{4}$/)) {
                const [day, month, year] = value.split(/[/-]/);
                return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
            }

            // Se já estiver no formato ISO, manter
            if (value.match(/^\d{4}-\d{2}-\d{2}$/)) {
                return value;
            }

            // Tentar converter outros formatos
            return this.convertDateToAPIFormat(value);
        }

        // Para outros valores, retornar como string
        return String(value);
    }

    // Converter formato de data para API
    convertDateToAPIFormat(displayText) {
        if (!displayText) return displayText;

        const textLower = displayText.toLowerCase();

        // Mapeamentos diretos
        const directMappings = {
            'ontem': 'yesterday',
            'hoje': 'today',
            'últimos 7 dias': 'past7days',
            'últimos 30 dias': 'past30days',
            'esta semana': 'thisweek',
            'este mês': 'thismonth',
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

        if (directMappings[textLower]) {
            return directMappings[textLower];
        }

        // Verificar padrões como "últimos X dias"
        const previousMatch = textLower.match(/(?:previous|últimos?|last)\s+(\d+)\s+(?:days?|dias?)/);
        if (previousMatch) {
            const days = parseInt(previousMatch[1]);
            return `past${days}days`;
        }

        // Se já estiver no formato correto, retornar
        if (displayText.includes('~') || displayText.match(/^\d{4}-\d{2}-\d{2}$/)) {
            return displayText;
        }

        console.warn(`⚠️ Formato de data não reconhecido: "${displayText}"`);
        return displayText;
    }

    // ============================================
    // MÉTODOS DE CAPTURA DE FILTROS
    // ============================================

    startFilterMonitoring() {
        if (!this.isInIframe) {
            console.warn('⚠️ Monitoramento de filtros só funciona dentro de iframe');
            return false;
        }

        this.checkInterval = setInterval(() => {
            this.captureFiltersFromParent();
        }, this.checkFrequency);

        this.installFilterObserver();

        console.log(`👁️ Monitoramento de filtros iniciado`);

        // Captura inicial após um delay
        setTimeout(() => this.captureFiltersFromParent(), 1500);

        return true;
    }

    stopFilterMonitoring() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }

        if (this.filterObserver) {
            this.filterObserver.disconnect();
            this.filterObserver = null;
        }

        console.log('🛑 Monitoramento de filtros parado');
    }

    // Capturar filtros do dashboard pai
    captureFiltersFromParent() {
        if (!this.isInIframe) return;

        try {
            // Primeiro tentar com .Parameter (estrutura original)
            let filterContainers = window.parent.document.querySelectorAll('.Parameter');

            // Se não encontrar, tentar com fieldset (nova estrutura)
            if (filterContainers.length === 0) {
                filterContainers = window.parent.document.querySelectorAll('fieldset');
            }

            const filters = {};

            filterContainers.forEach((container) => {
                let labelText = null;
                let widget = null;

                // Para estrutura .Parameter
                if (container.classList?.contains('Parameter')) {
                    const labelElement = container.querySelector('label, .Parameter-name, [class*="Parameter-name"]');
                    if (!labelElement) return;

                    labelText = labelElement.textContent?.trim().toLowerCase();
                    widget = container.querySelector('[data-testid*="parameter-value-widget"], .Parameter-content input, .Parameter-content [role="button"]');
                }
                // Para estrutura fieldset
                else if (container.tagName === 'FIELDSET') {
                    const legend = container.querySelector('legend');
                    if (!legend) return; // Sem legend = sem valor selecionado

                    labelText = legend.textContent?.trim().toLowerCase();
                    widget = container.querySelector('[role="button"], input, .lnsju');
                }

                if (!labelText || !widget) return;

                const displayText = widget.textContent?.trim() || widget.value?.trim();
                if (!displayText) return;

                // Encontrar o campo correspondente no mapeamento
                let matchedField = null;

                // Tentar match exato primeiro
                for (const [field, config] of Object.entries(window.filterMapping)) {
                    const friendlyNameLower = config.friendlyName.toLowerCase();
                    const fieldLower = field.toLowerCase();

                    if (labelText === friendlyNameLower || labelText === fieldLower) {
                        matchedField = field;
                        break;
                    }
                }

                // Se não encontrou, tentar match parcial
                if (!matchedField) {
                    matchedField = this.findFieldMapping(labelText);
                }

                if (!matchedField) {
                    return;
                }

                // Verificar se é placeholder
                if (this.isPlaceholder(displayText, matchedField)) {
                    return;
                }

                // Processar valor baseado no tipo
                const fieldConfig = window.filterMapping[matchedField];
                let processedValue = displayText;

                if (fieldConfig.type === 'date' || matchedField === 'data') {
                    processedValue = this.convertDateToAPIFormat(displayText);
                } else if (this.isMultipleSelection(displayText)) {
                    // Tentar obter valores reais para seleção múltipla
                    processedValue = this.attemptToGetRealValues(widget) || this.extractMultipleValues(container, widget) || [displayText];
                }

                filters[matchedField] = processedValue;
            });

            const currentJSON = JSON.stringify(filters);
            if (currentJSON !== this.lastFiltersJSON) {
                this.lastFiltersJSON = currentJSON;
                this.handleFiltersChange(filters);
            }

        } catch (error) {
            if (!error.message.includes('cross-origin')) {
                console.error('Erro na captura de filtros:', error);
            }
        }
    }

    // Método auxiliar para encontrar o mapeamento correto
    findFieldMapping(labelText) {
        if (!labelText || !window.filterMapping) return null;

        const labelLower = labelText.toLowerCase();
        const labelNormalized = this.normalizeText(labelText);

        // Casos especiais de mapeamento
        const specialMappings = {
            'conjunto de anúncios': 'adset',
            'conjunto de anuncios': 'adset',
            'adset': 'adset',
            'anúncio': 'anuncio',
            'anuncio': 'anuncio',
            'peça': 'anuncio',
            'peca': 'anuncio',
            'device': 'device',
            'dispositivo': 'device',
            'plataforma': 'plataforma',
            'posição': 'posicao',
            'posicao': 'posicao',
            'objetivo': 'objective',
            'buying type': 'buying_type',
            'tipo de compra': 'buying_type',
            'optimization goal': 'optimization_goal',
            'meta de otimização': 'optimization_goal',
            'meta de otimizacao': 'optimization_goal',
            'conversões consideradas': 'conversoes_consideradas',
            'conversoes consideradas': 'conversoes_consideradas'
        };

        return specialMappings[labelLower] || specialMappings[labelNormalized] || null;
    }

    // Extrair valores múltiplos
    extractMultipleValues(fieldset, valueElement) {
        try {
            // Estratégia 1: Buscar no dropdown aberto
            const dropdown = fieldset.querySelector('[role="listbox"], .ant-select-dropdown, [class*="dropdown"]');
            if (dropdown) {
                const selectedItems = dropdown.querySelectorAll('[aria-selected="true"], .selected, [class*="selected"]');
                if (selectedItems.length > 0) {
                    return Array.from(selectedItems).map(item => item.textContent?.trim()).filter(Boolean);
                }
            }

            // Estratégia 2: Buscar tags de seleção
            const tags = fieldset.querySelectorAll('.ant-tag, [class*="tag"], [class*="chip"], [class*="selected-value"]');
            if (tags.length > 0) {
                return Array.from(tags).map(tag => {
                    const text = tag.textContent?.replace(/[×✕✖]/, '').trim();
                    return text;
                }).filter(Boolean);
            }

            return null;
        } catch (error) {
            console.error('Erro ao extrair valores múltiplos:', error);
            return null;
        }
    }

    // Método auxiliar para normalização de texto
    normalizeText(text) {
        return text
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '') // Remove acentos
            .toLowerCase()
            .trim();
    }

    // Verificar se é placeholder
    isPlaceholder(text, paramName) {
        const placeholders = ['Tudo', 'All', 'Selecione...', 'Select...', 'Todos', 'Todas'];

        if (placeholders.includes(text)) return true;

        // Verificar se o texto é igual ao nome do campo ou label amigável
        const fieldConfig = window.filterMapping[paramName];
        if (fieldConfig) {
            const friendlyName = fieldConfig.friendlyName;
            if (text === friendlyName || text === paramName) return true;

            // Verificar versão normalizada
            const normalizedText = this.normalizeText(text);
            const normalizedFriendly = this.normalizeText(friendlyName);
            const normalizedParam = this.normalizeText(paramName);

            if (normalizedText === normalizedFriendly || normalizedText === normalizedParam) {
                return true;
            }
        }

        return false;
    }

    // Verificar se é seleção múltipla
    isMultipleSelection(text) {
        if (!text) return false;

        const multipleIndicators = [
            'seleção', 'seleções',
            'selection', 'selections',
            'selected',
            'selecionado', 'selecionados',
            'valores', 'values',
            'itens', 'items'
        ];

        const textLower = text.toLowerCase();

        // Verificar se contém número + indicador
        const hasNumberAndIndicator = /\d+\s*(seleç|select|valor|value|item)/i.test(text);
        if (hasNumberAndIndicator) return true;

        // Verificar indicadores comuns
        return multipleIndicators.some(indicator => textLower.includes(indicator));
    }

    // Tentar obter valores reais de seleção múltipla
    attemptToGetRealValues(widget) {
        try {
            const reactKey = Object.keys(widget).find(k =>
                k.startsWith('__reactInternalFiber') ||
                k.startsWith('__reactFiber') ||
                k.startsWith('__react')
            );

            if (!reactKey) return null;

            const fiber = widget[reactKey];
            let current = fiber;
            let attempts = 0;

            while (current && attempts < 20) {
                attempts++;

                if (current.memoizedProps) {
                    const arrayProps = ['value', 'values', 'selectedValue', 'selectedValues', 'selected'];
                    for (const prop of arrayProps) {
                        const val = current.memoizedProps[prop];
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
            // Silencioso
        }

        return null;
    }

    // Instalar observer de mudanças
    installFilterObserver() {
        if (this.filterObserver) return;

        try {
            this.filterObserver = new MutationObserver(() => {
                clearTimeout(this._captureTimeout);
                this._captureTimeout = setTimeout(() => {
                    this.captureFiltersFromParent();
                }, 300);
            });

            this.filterObserver.observe(window.parent.document.body, {
                childList: true,
                subtree: true,
                characterData: true,
                attributes: true,
                attributeFilter: ['aria-selected', 'data-value']
            });

        } catch (e) {
            console.warn('⚠️ Não foi possível instalar observer:', e.message);
        }
    }

    // Lidar com mudanças de filtros
    handleFiltersChange(filters) {
        this.capturedFilters = filters;

        console.log('🔄 Filtros capturados:', filters);

        this.filterChangeCallbacks.forEach(callback => {
            try {
                callback(filters);
            } catch (error) {
                console.error('Erro em callback de filtros:', error);
            }
        });
    }

    // Registrar callback para mudanças de filtros
    onFilterChange(callback) {
        if (typeof callback === 'function') {
            this.filterChangeCallbacks.push(callback);
        }
    }

    // Remover callback de mudanças de filtros
    offFilterChange(callback) {
        const index = this.filterChangeCallbacks.indexOf(callback);
        if (index > -1) {
            this.filterChangeCallbacks.splice(index, 1);
        }
    }

    // Formatar dados da resposta
    formatData(result) {
        if (!result.data || !result.data.rows || !result.data.cols) {
            console.warn('⚠️ Estrutura de dados inválida:', result);
            return [];
        }

        const columns = result.data.cols;
        const rows = result.data.rows;

        return rows.map((row, rowIndex) => {
            const obj = {};
            columns.forEach((col, colIndex) => {
                const colName = col.display_name || col.name;
                obj[colName] = row[colIndex];
            });
            return obj;
        });
    }

    // Buscar dados com filtros capturados
    async getDataWithCapturedFilters(questionId) {
        return this.getFilteredData(questionId, this.capturedFilters);
    }

    // Limpar recursos
    cleanup() {
        this.stopFilterMonitoring();
        this.questionCache = {};
        this.filterChangeCallbacks = [];
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MetabaseAPI;
}

if (typeof window !== 'undefined') {
    window.MetabaseAPI = MetabaseAPI;

    // Criar instância global
    window.metabaseAPI = new MetabaseAPI();
    console.log('✅ window.metabaseAPI criada (Modo Seguro com Formato Correto)');
}