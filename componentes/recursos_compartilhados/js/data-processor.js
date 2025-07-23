// componentes/recursos_compartilhados/js/data-processor.js
/**
 * Processador de dados compartilhado
 * Converte formatos e aplica formatações
 */

class DataProcessor {
  constructor() {
    // Formatadores por tipo de dados
    this.formatters = {
      // Números
      number: new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      }),
      
      // Moeda
      currency: new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
      }),
      
      // Percentual
      percent: new Intl.NumberFormat('pt-BR', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }),
      
      // Data
      date: new Intl.DateTimeFormat('pt-BR'),
      
      // Data e hora
      datetime: new Intl.DateTimeFormat('pt-BR', {
        dateStyle: 'short',
        timeStyle: 'short'
      })
    };
  }
  
  /**
   * Processa resposta no formato nativo do Metabase (colunar)
   * @param {Object} nativeData - Resposta com {data: {cols, rows}}
   * @returns {Array} Array de objetos
   */
  processNativeResponse(nativeData) {
    // Se tem o formato nativo (colunar)
    if (nativeData && nativeData.data && nativeData.data.rows) {
      const { cols, rows } = nativeData.data;
      
      console.log(`📊 Processando formato nativo: ${rows.length} linhas, ${cols.length} colunas`);
      
      // Extrai nomes das colunas e tipos
      const colNames = cols.map(col => col.name);
      const colTypes = cols.map(col => col.base_type);
      
      // Converte formato colunar para array de objetos
      const result = rows.map(row => {
        const obj = {};
        
        for (let i = 0; i < colNames.length; i++) {
          const colName = colNames[i];
          const colType = colTypes[i];
          let value = row[i];
          
          // Aplica conversões básicas por tipo
          if (value !== null && value !== undefined) {
            if (colType === 'type/Date' || colType === 'type/DateTime') {
              // Mantém como string ISO se já for, ou converte
              if (value instanceof Date) {
                value = value.toISOString();
              }
            } else if (colType === 'type/Decimal' || colType === 'type/Float') {
              // Garante que seja número
              value = parseFloat(value);
            } else if (colType === 'type/Integer' || colType === 'type/BigInteger') {
              value = parseInt(value);
            }
          }
          
          obj[colName] = value;
        }
        
        return obj;
      });
      
      return result;
    }
    
    // Se já for array de objetos, retorna direto
    if (Array.isArray(nativeData)) {
      return nativeData;
    }
    
    console.error('❌ Formato de resposta não reconhecido:', nativeData);
    return [];
  }
  
  /**
   * Formata valor baseado no tipo
   * @param {any} value - Valor a formatar
   * @param {string} type - Tipo de formatação
   * @returns {string} Valor formatado
   */
  formatValue(value, type) {
    if (value === null || value === undefined || value === '') {
      return '';
    }
    
    try {
      switch(type) {
        case 'number':
          return this.formatters.number.format(value);
          
        case 'currency':
        case 'money':
        case 'brl':
          return this.formatters.currency.format(value);
          
        case 'percent':
        case 'percentage':
          // Se o valor já estiver em percentual (ex: 95.5), divide por 100
          const percentValue = value > 1 ? value / 100 : value;
          return this.formatters.percent.format(percentValue);
          
        case 'date':
          return this.formatDate(value);
          
        case 'datetime':
          return this.formatDateTime(value);
          
        default:
          return String(value);
      }
    } catch (error) {
      console.warn('⚠️ Erro ao formatar valor:', error);
      return String(value);
    }
  }
  
  /**
   * Formata data
   * @private
   */
  formatDate(value) {
    if (!value) return '';
    
    const date = value instanceof Date ? value : new Date(value);
    
    if (isNaN(date.getTime())) {
      return String(value);
    }
    
    return this.formatters.date.format(date);
  }
  
  /**
   * Formata data e hora
   * @private
   */
  formatDateTime(value) {
    if (!value) return '';
    
    const date = value instanceof Date ? value : new Date(value);
    
    if (isNaN(date.getTime())) {
      return String(value);
    }
    
    return this.formatters.datetime.format(date);
  }
  
  /**
   * Detecta tipo de dados automaticamente
   * @param {any} value - Valor para análise
   * @returns {string} Tipo detectado
   */
  detectType(value) {
    if (value === null || value === undefined) {
      return 'null';
    }
    
    // Verifica se é data
    if (value instanceof Date || (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}/.test(value))) {
      return 'date';
    }
    
    // Verifica se é número
    if (typeof value === 'number') {
      // Se tem casa decimal e está entre 0 e 1, provavelmente é percentual
      if (value > 0 && value < 1 && value.toString().includes('.')) {
        return 'percent';
      }
      
      // Se for maior que 1000, pode ser moeda
      if (value > 1000) {
        return 'currency';
      }
      
      return 'number';
    }
    
    return 'string';
  }
  
  /**
   * Processa metadados das colunas
   * @param {Array} cols - Array de metadados de colunas
   * @returns {Object} Mapa de coluna -> formatação
   */
  processColumnMetadata(cols) {
    const metadata = {};
    
    cols.forEach(col => {
      const formatting = {
        name: col.name,
        displayName: col.display_name || col.name,
        type: col.base_type,
        formatter: null
      };
      
      // Define formatador baseado no tipo ou nome
      if (col.base_type === 'type/Decimal' || col.base_type === 'type/Float') {
        // Verifica se é moeda pelo nome
        if (/spend|cost|revenue|valor|price|preco/i.test(col.name)) {
          formatting.formatter = 'currency';
        } else if (/rate|percent|taxa|ctr|cpm|roas/i.test(col.name)) {
          formatting.formatter = 'percent';
        } else {
          formatting.formatter = 'number';
        }
      } else if (col.base_type === 'type/Date') {
        formatting.formatter = 'date';
      } else if (col.base_type === 'type/DateTime') {
        formatting.formatter = 'datetime';
      }
      
      metadata[col.name] = formatting;
    });
    
    return metadata;
  }
  
  /**
   * Agrupa dados por campo
   * @param {Array} data - Dados a agrupar
   * @param {string} field - Campo para agrupamento
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
   * Ordena dados
   * @param {Array} data - Dados a ordenar
   * @param {string} field - Campo para ordenação
   * @param {string} direction - 'asc' ou 'desc'
   * @returns {Array} Dados ordenados
   */
  sortBy(data, field, direction = 'asc') {
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

// Exporta para diferentes ambientes
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DataProcessor;
} else if (typeof define === 'function' && define.amd) {
  define([], function() { return DataProcessor; });
} else {
  window.DataProcessor = DataProcessor;
}
