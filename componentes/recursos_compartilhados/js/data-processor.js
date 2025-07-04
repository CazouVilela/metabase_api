/**
 * Processador de dados compartilhado
 * @module data-processor
 */

class DataProcessor {
    constructor() {
        this.formatters = new Map();
        this.setupDefaultFormatters();
    }
    
    /**
     * Configura formatadores padrão
     * @private
     */
    setupDefaultFormatters() {
        // Formatador de números
        this.formatters.set('number', (value) => {
            if (value === null || value === undefined) return '';
            return new Intl.NumberFormat('pt-BR').format(value);
        });
        
        // Formatador de moeda
        this.formatters.set('currency', (value) => {
            if (value === null || value === undefined) return '';
            return new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            }).format(value);
        });
        
        // Formatador de porcentagem
        this.formatters.set('percent', (value) => {
            if (value === null || value === undefined) return '';
            return new Intl.NumberFormat('pt-BR', {
                style: 'percent',
                minimumFractionDigits: 2
            }).format(value / 100);
        });
        
        // Formatador de data
        this.formatters.set('date', (value) => {
            if (!value) return '';
            const date = new Date(value);
            return date.toLocaleDateString('pt-BR');
        });
        
        // Formatador de data/hora
        this.formatters.set('datetime', (value) => {
            if (!value) return '';
            const date = new Date(value);
            return date.toLocaleString('pt-BR');
        });
    }
    
    /**
     * Processa resposta no formato nativo do Metabase
     * @param {Object} nativeData - Dados no formato nativo
     * @returns {Array} Array de objetos
     */
    processNativeResponse(nativeData) {
        // Se tem o formato nativo (colunar)
        if (nativeData && nativeData.data && nativeData.data.rows) {
            const cols = nativeData.data.cols;
            const rows = nativeData.data.rows;
            
            console.log(`[DataProcessor] Native: ${rows.length} linhas, ${cols.length} colunas`);
            
            // Converte formato colunar para objetos
            const result = [];
            const colNames = cols.map(c => c.name);
            
            for (let i = 0; i < rows.length; i++) {
                const obj = {};
                for (let j = 0; j < colNames.length; j++) {
                    obj[colNames[j]] = rows[i][j];
                }
                result.push(obj);
            }
            
            return result;
        }
        
        // Se já for array de objetos, retorna direto
        if (Array.isArray(nativeData)) {
            return nativeData;
        }
        
        console.error('[DataProcessor] Formato de resposta inesperado:', nativeData);
        return [];
    }
    
    /**
     * Extrai metadados das colunas
     * @param {Object} nativeData - Dados no formato nativo
     * @returns {Array} Metadados das colunas
     */
    extractColumnMetadata(nativeData) {
        if (nativeData && nativeData.data && nativeData.data.cols) {
            return nativeData.data.cols.map(col => ({
                name: col.name,
                displayName: col.display_name || col.name,
                type: col.base_type || 'type/Text',
                formatter: this.getFormatterForType(col.base_type)
            }));
        }
        
        return [];
    }
    
    /**
     * Obtém formatador baseado no tipo
     * @private
     */
    getFormatterForType(type) {
        const typeMap = {
            'type/Integer': 'number',
            'type/BigInteger': 'number',
            'type/Float': 'number',
            'type/Decimal': 'number',
            'type/Currency': 'currency',
            'type/Date': 'date',
            'type/DateTime': 'datetime',
            'type/DateTimeWithTZ': 'datetime'
        };
        
        return typeMap[type] || null;
    }
    
    /**
     * Formata valor usando formatador apropriado
     * @param {any} value - Valor a formatar
     * @param {string} formatter - Nome do formatador
     * @returns {string} Valor formatado
     */
    formatValue(value, formatter) {
        if (!formatter || !this.formatters.has(formatter)) {
            return value?.toString() || '';
        }
        
        const formatFn = this.formatters.get(formatter);
        try {
            return formatFn(value);
        } catch (e) {
            console.warn(`Erro ao formatar valor: ${e.message}`);
            return value?.toString() || '';
        }
    }
    
    /**
     * Adiciona formatador customizado
     * @param {string} name - Nome do formatador
     * @param {Function} formatter - Função formatadora
     */
    addFormatter(name, formatter) {
        this.formatters.set(name, formatter);
    }
    
    /**
     * Agrupa dados por campo
     * @param {Array} data - Dados a agrupar
     * @param {string} field - Campo para agrupar
     * @returns {Object} Dados agrupados
     */
    groupBy(data, field) {
        return data.reduce((groups, item) => {
            const key = item[field];
            if (!groups[key]) {
                groups[key] = [];
            }
            groups[key].push(item);
            return groups;
        }, {});
    }
    
    /**
     * Calcula agregações
     * @param {Array} data - Dados para agregar
     * @param {Object} aggregations - Definição das agregações
     * @returns {Object} Resultados das agregações
     */
    aggregate(data, aggregations) {
        const results = {};
        
        Object.entries(aggregations).forEach(([name, config]) => {
            const field = config.field;
            const operation = config.operation;
            
            switch (operation) {
                case 'sum':
                    results[name] = data.reduce((sum, item) => sum + (item[field] || 0), 0);
                    break;
                    
                case 'avg':
                    const sum = data.reduce((s, item) => s + (item[field] || 0), 0);
                    results[name] = data.length > 0 ? sum / data.length : 0;
                    break;
                    
                case 'count':
                    results[name] = data.length;
                    break;
                    
                case 'min':
                    results[name] = Math.min(...data.map(item => item[field] || 0));
                    break;
                    
                case 'max':
                    results[name] = Math.max(...data.map(item => item[field] || 0));
                    break;
                    
                case 'distinct':
                    results[name] = new Set(data.map(item => item[field])).size;
                    break;
            }
        });
        
        return results;
    }
    
    /**
     * Filtra dados localmente
     * @param {Array} data - Dados para filtrar
     * @param {Object} filters - Filtros a aplicar
     * @returns {Array} Dados filtrados
     */
    filterData(data, filters) {
        return data.filter(item => {
            return Object.entries(filters).every(([field, value]) => {
                if (!value) return true;
                
                const itemValue = item[field];
                
                // Suporta múltiplos valores
                if (Array.isArray(value)) {
                    return value.includes(itemValue);
                }
                
                // Comparação simples
                return itemValue === value;
            });
        });
    }
    
    /**
     * Ordena dados
     * @param {Array} data - Dados para ordenar
     * @param {string} field - Campo para ordenar
     * @param {string} direction - 'asc' ou 'desc'
     * @returns {Array} Dados ordenados
     */
    sortData(data, field, direction = 'asc') {
        return [...data].sort((a, b) => {
            const aVal = a[field];
            const bVal = b[field];
            
            if (aVal === null || aVal === undefined) return 1;
            if (bVal === null || bVal === undefined) return -1;
            
            if (aVal < bVal) return direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return direction === 'asc' ? 1 : -1;
            return 0;
        });
    }
}

// Exporta instância única
const dataProcessor = new DataProcessor();

// Exporta para diferentes ambientes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = dataProcessor;
} else if (typeof define === 'function' && define.amd) {
    define([], function() { return dataProcessor; });
} else {
    window.dataProcessor = dataProcessor;
}
