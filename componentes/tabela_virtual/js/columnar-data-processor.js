// componentes/tabela_virtual/js/columnar-data-processor.js
/**
 * Processador para formato colunar nativo do Metabase
 * Converte dados colunares em formato de linha para renderização
 */

class ColumnarDataProcessor {
  constructor() {
    this.compressionEnabled = true;
  }

  /**
   * Processa resposta no formato nativo do Metabase
   */
  processNativeResponse(response) {
    // Se a resposta tem o formato do Metabase nativo
    if (response.data && response.data.cols && response.data.rows) {
      const startTime = performance.now();
      
      const cols = response.data.cols;
      const rows = response.data.rows;
      
      console.log(`📊 Processando formato nativo: ${rows.length} linhas, ${cols.length} colunas`);
      
      // Converte para formato de objetos (necessário para ClusterizeJS)
      const processedData = this.columnarToObjects(cols, rows);
      
      const processingTime = (performance.now() - startTime) / 1000;
      console.log(`✅ Conversão completa em ${processingTime.toFixed(3)}s`);
      
      // Retorna com metadados
      return {
        data: processedData,
        metadata: {
          format: 'native',
          originalFormat: 'columnar',
          rowCount: rows.length,
          columnCount: cols.length,
          processingTime: processingTime,
          serverTime: response.running_time / 1000,
          compressed: response.compressed || false
        }
      };
    }
    
    // Se já está no formato de array de objetos
    return {
      data: response,
      metadata: {
        format: 'legacy',
        originalFormat: 'objects'
      }
    };
  }

  /**
   * Converte formato colunar para objetos
   * Otimizado para performance com muitas linhas
   */
  columnarToObjects(cols, rows) {
    // Extrai nomes das colunas uma vez
    const columnNames = cols.map(col => col.name);
    const columnCount = columnNames.length;
    
    // Pré-aloca array do tamanho correto
    const result = new Array(rows.length);
    
    // Usa loop otimizado
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const obj = {};
      
      // Cria objeto para cada linha
      for (let j = 0; j < columnCount; j++) {
        obj[columnNames[j]] = row[j];
      }
      
      result[i] = obj;
    }
    
    return result;
  }

  /**
   * Converte objetos para formato colunar (para envio)
   * Usado quando precisamos enviar dados de volta
   */
  objectsToColumnar(data) {
    if (!data || data.length === 0) {
      return { cols: [], rows: [] };
    }
    
    // Extrai colunas
    const firstRow = data[0];
    const cols = Object.keys(firstRow).map(key => ({
      name: key,
      display_name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      base_type: this.guessType(firstRow[key])
    }));
    
    // Converte linhas
    const rows = data.map(obj => 
      cols.map(col => obj[col.name])
    );
    
    return { cols, rows };
  }

  /**
   * Detecta tipo de dado
   */
  guessType(value) {
    if (value === null || value === undefined) return 'type/Text';
    if (typeof value === 'number') {
      return Number.isInteger(value) ? 'type/Integer' : 'type/Float';
    }
    if (typeof value === 'boolean') return 'type/Boolean';
    if (value instanceof Date) return 'type/DateTime';
    if (typeof value === 'string') {
      // Tenta detectar datas
      if (/^\d{4}-\d{2}-\d{2}/.test(value)) {
        return value.includes('T') ? 'type/DateTime' : 'type/Date';
      }
    }
    return 'type/Text';
  }

  /**
   * Otimiza dados para renderização
   * Remove campos desnecessários, formata valores
   */
  optimizeForRendering(data, options = {}) {
    const {
      excludeColumns = [],
      formatNumbers = true,
      formatDates = true,
      maxDecimals = 2
    } = options;
    
    return data.map(row => {
      const optimized = {};
      
      for (const [key, value] of Object.entries(row)) {
        // Pula colunas excluídas
        if (excludeColumns.includes(key)) continue;
        
        // Formata valores
        if (formatNumbers && typeof value === 'number') {
          optimized[key] = Number.isInteger(value) ? 
            value : 
            parseFloat(value.toFixed(maxDecimals));
        } else if (formatDates && typeof value === 'string' && /^\d{4}-\d{2}-\d{2}/.test(value)) {
          // Formato brasileiro
          const date = new Date(value);
          optimized[key] = date.toLocaleDateString('pt-BR');
        } else {
          optimized[key] = value;
        }
      }
      
      return optimized;
    });
  }

  /**
   * Estima tamanho em memória
   */
  estimateMemoryUsage(data) {
    if (!data || data.length === 0) return 0;
    
    // Amostra primeira linha
    const sampleRow = JSON.stringify(data[0]);
    const rowSize = new Blob([sampleRow]).size;
    
    // Estima total
    const totalBytes = rowSize * data.length;
    const totalMB = totalBytes / (1024 * 1024);
    
    return {
      bytes: totalBytes,
      mb: totalMB,
      formatted: `${totalMB.toFixed(2)} MB`
    };
  }

  /**
   * Compara performance entre formatos
   */
  compareFormats(data) {
    const results = {};
    
    // Testa conversão para colunar
    let start = performance.now();
    const columnar = this.objectsToColumnar(data);
    results.toColumnar = (performance.now() - start) / 1000;
    
    // Testa conversão de colunar
    start = performance.now();
    const objects = this.columnarToObjects(columnar.cols, columnar.rows);
    results.fromColumnar = (performance.now() - start) / 1000;
    
    // Tamanhos
    const objectSize = new Blob([JSON.stringify(data)]).size;
    const columnarSize = new Blob([JSON.stringify(columnar)]).size;
    
    results.sizes = {
      objects: objectSize,
      columnar: columnarSize,
      reduction: ((1 - columnarSize / objectSize) * 100).toFixed(1) + '%'
    };
    
    console.log('📊 Comparação de formatos:', results);
    return results;
  }
}

// Instância global
const columnarProcessor = new ColumnarDataProcessor();

// Exporta se estiver em ambiente de módulos
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ColumnarDataProcessor;
}
