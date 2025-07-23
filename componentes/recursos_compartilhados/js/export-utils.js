// componentes/recursos_compartilhados/js/export-utils.js
/**
 * Utilitários de exportação compartilhados
 */

const ExportUtils = {
  /**
   * Exporta dados para CSV
   * @param {Array} data - Array de objetos para exportar
   * @param {string} filename - Nome do arquivo (sem extensão)
   * @param {Object} options - Opções de exportação
   */
  exportToCSV(data, filename = 'export', options = {}) {
    if (!data || !Array.isArray(data) || data.length === 0) {
      console.warn('⚠️ Nenhum dado para exportar');
      return false;
    }
    
    const {
      delimiter = ',',
      includeHeaders = true,
      encoding = 'utf-8',
      lineBreak = '\n'
    } = options;
    
    try {
      // Obtém todas as colunas únicas
      const columns = this.getAllColumns(data);
      
      let csv = '';
      
      // Adiciona BOM para UTF-8 (melhora compatibilidade com Excel)
      if (encoding === 'utf-8') {
        csv = '\ufeff';
      }
      
      // Headers
      if (includeHeaders) {
        csv += columns.map(col => this.escapeCSVValue(col, delimiter)).join(delimiter) + lineBreak;
      }
      
      // Dados
      data.forEach(row => {
        const values = columns.map(col => {
          const value = row[col];
          return this.escapeCSVValue(value, delimiter);
        });
        
        csv += values.join(delimiter) + lineBreak;
      });
      
      // Download
      this.downloadFile(csv, `${filename}.csv`, 'text/csv;charset=utf-8');
      
      console.log(`✅ Exportados ${data.length} registros para CSV`);
      return true;
      
    } catch (error) {
      console.error('❌ Erro ao exportar CSV:', error);
      return false;
    }
  },
  
  /**
   * Exporta dados para JSON
   * @param {Array|Object} data - Dados para exportar
   * @param {string} filename - Nome do arquivo (sem extensão)
   * @param {boolean} pretty - Se deve formatar o JSON
   */
  exportToJSON(data, filename = 'export', pretty = true) {
    try {
      const json = pretty 
        ? JSON.stringify(data, null, 2)
        : JSON.stringify(data);
      
      this.downloadFile(json, `${filename}.json`, 'application/json');
      
      console.log('✅ Dados exportados para JSON');
      return true;
      
    } catch (error) {
      console.error('❌ Erro ao exportar JSON:', error);
      return false;
    }
  },
  
  /**
   * Exporta dados para Excel (formato CSV compatível)
   * @param {Array} data - Array de objetos
   * @param {string} filename - Nome do arquivo
   */
  exportToExcel(data, filename = 'export') {
    // Para Excel, usamos ponto-e-vírgula como delimitador
    // e vírgula como separador decimal
    const excelData = data.map(row => {
      const newRow = {};
      
      Object.entries(row).forEach(([key, value]) => {
        // Converte números para formato brasileiro
        if (typeof value === 'number') {
          newRow[key] = value.toString().replace('.', ',');
        } else {
          newRow[key] = value;
        }
      });
      
      return newRow;
    });
    
    return this.exportToCSV(excelData, filename, {
      delimiter: ';',
      encoding: 'utf-8'
    });
  },
  
  /**
   * Escapa valor para CSV
   * @private
   */
  escapeCSVValue(value, delimiter = ',') {
    if (value === null || value === undefined) {
      return '';
    }
    
    const stringValue = String(value);
    
    // Verifica se precisa escapar
    if (
      stringValue.includes(delimiter) ||
      stringValue.includes('"') ||
      stringValue.includes('\n') ||
      stringValue.includes('\r')
    ) {
      // Escapa aspas duplas dobrando elas
      const escaped = stringValue.replace(/"/g, '""');
      return `"${escaped}"`;
    }
    
    return stringValue;
  },
  
  /**
   * Obtém todas as colunas únicas dos dados
   * @private
   */
  getAllColumns(data) {
    const columnsSet = new Set();
    
    data.forEach(row => {
      Object.keys(row).forEach(key => {
        columnsSet.add(key);
      });
    });
    
    return Array.from(columnsSet);
  },
  
  /**
   * Faz download de arquivo
   * @private
   */
  downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }, 100);
  },
  
  /**
   * Copia dados para clipboard em formato de tabela
   * @param {Array} data - Dados para copiar
   * @param {boolean} includeHeaders - Se deve incluir headers
   */
  copyToClipboard(data, includeHeaders = true) {
    if (!data || !Array.isArray(data) || data.length === 0) {
      console.warn('⚠️ Nenhum dado para copiar');
      return false;
    }
    
    try {
      const columns = this.getAllColumns(data);
      let text = '';
      
      // Headers
      if (includeHeaders) {
        text += columns.join('\t') + '\n';
      }
      
      // Dados
      data.forEach(row => {
        const values = columns.map(col => row[col] || '');
        text += values.join('\t') + '\n';
      });
      
      // Copia para clipboard
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
          console.log('✅ Dados copiados para área de transferência');
        }).catch(err => {
          console.error('❌ Erro ao copiar:', err);
          this.fallbackCopy(text);
        });
      } else {
        this.fallbackCopy(text);
      }
      
      return true;
      
    } catch (error) {
      console.error('❌ Erro ao copiar dados:', error);
      return false;
    }
  },
  
  /**
   * Fallback para copiar quando clipboard API não está disponível
   * @private
   */
  fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
      document.execCommand('copy');
      console.log('✅ Dados copiados (fallback)');
    } catch (err) {
      console.error('❌ Erro no fallback de cópia:', err);
    }
    
    document.body.removeChild(textarea);
  },
  
  /**
   * Exporta dados em formato HTML (tabela)
   * @param {Array} data - Dados para exportar
   * @param {string} filename - Nome do arquivo
   * @param {Object} options - Opções de estilo
   */
  exportToHTML(data, filename = 'export', options = {}) {
    const {
      title = 'Dados Exportados',
      includeStyles = true
    } = options;
    
    if (!data || !Array.isArray(data) || data.length === 0) {
      console.warn('⚠️ Nenhum dado para exportar');
      return false;
    }
    
    try {
      const columns = this.getAllColumns(data);
      
      let html = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>${title}</title>`;
      
      if (includeStyles) {
        html += `
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; font-weight: bold; }
    tr:nth-child(even) { background-color: #f9f9f9; }
    h1 { color: #333; }
    .info { color: #666; font-size: 0.9em; margin-bottom: 10px; }
  </style>`;
      }
      
      html += `
</head>
<body>
  <h1>${title}</h1>
  <div class="info">Exportado em: ${new Date().toLocaleString('pt-BR')}</div>
  <div class="info">Total de registros: ${data.length}</div>
  
  <table>
    <thead>
      <tr>`;
      
      // Headers
      columns.forEach(col => {
        html += `<th>${this.escapeHTML(col)}</th>`;
      });
      
      html += `
      </tr>
    </thead>
    <tbody>`;
      
      // Dados
      data.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
          const value = row[col] || '';
          html += `<td>${this.escapeHTML(value)}</td>`;
        });
        html += '</tr>';
      });
      
      html += `
    </tbody>
  </table>
</body>
</html>`;
      
      this.downloadFile(html, `${filename}.html`, 'text/html;charset=utf-8');
      
      console.log('✅ Dados exportados para HTML');
      return true;
      
    } catch (error) {
      console.error('❌ Erro ao exportar HTML:', error);
      return false;
    }
  },
  
  /**
   * Escapa HTML para evitar XSS
   * @private
   */
  escapeHTML(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    
    return String(text).replace(/[&<>"']/g, m => map[m]);
  }
};

// Exporta para diferentes ambientes
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ExportUtils;
} else if (typeof define === 'function' && define.amd) {
  define([], function() { return ExportUtils; });
} else {
  window.ExportUtils = ExportUtils;
}
