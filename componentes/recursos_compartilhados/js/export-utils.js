/**
 * Utilitários de exportação compartilhados
 * @module export-utils
 */

class ExportUtils {
    constructor() {
        this.defaultFilename = 'export';
    }
    
    /**
     * Exporta dados para CSV
     * @param {Array} data - Dados para exportar
     * @param {Object} options - Opções de exportação
     * @returns {void}
     */
    exportToCSV(data, options = {}) {
        if (!data || data.length === 0) {
            console.warn('Nenhum dado para exportar');
            return;
        }
        
        const {
            filename = this.getFilename('csv'),
            columns = Object.keys(data[0]),
            headers = columns,
            delimiter = ',',
            encoding = 'utf-8'
        } = options;
        
        // Cria CSV
        let csv = this.createCSVHeader(headers, delimiter);
        
        // Adiciona dados
        data.forEach(row => {
            const values = columns.map(col => {
                const value = row[col] || '';
                return this.escapeCSVValue(value, delimiter);
            });
            csv += values.join(delimiter) + '\n';
        });
        
        // Adiciona BOM para UTF-8
        if (encoding === 'utf-8') {
            csv = '\ufeff' + csv;
        }
        
        // Download
        this.downloadFile(csv, filename, 'text/csv;charset=utf-8');
    }
    
    /**
     * Exporta dados para JSON
     * @param {Array|Object} data - Dados para exportar
     * @param {Object} options - Opções de exportação
     * @returns {void}
     */
    exportToJSON(data, options = {}) {
        const {
            filename = this.getFilename('json'),
            pretty = true,
            includeMetadata = false
        } = options;
        
        let exportData = data;
        
        if (includeMetadata) {
            exportData = {
                exportDate: new Date().toISOString(),
                recordCount: Array.isArray(data) ? data.length : 1,
                data: data
            };
        }
        
        const json = pretty 
            ? JSON.stringify(exportData, null, 2)
            : JSON.stringify(exportData);
        
        this.downloadFile(json, filename, 'application/json');
    }
    
    /**
     * Exporta dados para Excel (formato CSV compatível)
     * @param {Array} data - Dados para exportar
     * @param {Object} options - Opções de exportação
     * @returns {void}
     */
    exportToExcel(data, options = {}) {
        // Por enquanto, usa CSV com separador de tabulação
        // Para Excel real, seria necessário uma biblioteca como xlsx
        this.exportToCSV(data, {
            ...options,
            delimiter: '\t',
            filename: options.filename || this.getFilename('xls')
        });
    }
    
    /**
     * Cria cabeçalho CSV
     * @private
     */
    createCSVHeader(headers, delimiter) {
        return headers.map(h => this.escapeCSVValue(h, delimiter)).join(delimiter) + '\n';
    }
    
    /**
     * Escapa valor para CSV
     * @private
     */
    escapeCSVValue(value, delimiter) {
        if (value === null || value === undefined) {
            return '';
        }
        
        const stringValue = value.toString();
        
        // Verifica se precisa de aspas
        if (stringValue.includes(delimiter) || 
            stringValue.includes('\n') || 
            stringValue.includes('\r') ||
            stringValue.includes('"')) {
            return `"${stringValue.replace(/"/g, '""')}"`;
        }
        
        return stringValue;
    }
    
    /**
     * Gera nome de arquivo com timestamp
     * @private
     */
    getFilename(extension) {
        const date = new Date().toISOString().split('T')[0];
        return `${this.defaultFilename}_${date}.${extension}`;
    }
    
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
        document.body.removeChild(link);
        
        // Limpa URL
        setTimeout(() => URL.revokeObjectURL(url), 100);
        
        console.log(`✅ Arquivo exportado: ${filename}`);
    }
    
    /**
     * Copia dados para clipboard
     * @param {any} data - Dados para copiar
     * @param {string} format - Formato (text, json, csv)
     * @returns {Promise<void>}
     */
    async copyToClipboard(data, format = 'text') {
        try {
            let text = '';
            
            switch (format) {
                case 'json':
                    text = JSON.stringify(data, null, 2);
                    break;
                    
                case 'csv':
                    if (Array.isArray(data) && data.length > 0) {
                        const headers = Object.keys(data[0]);
                        text = headers.join(',') + '\n';
                        data.forEach(row => {
                            text += headers.map(h => row[h] || '').join(',') + '\n';
                        });
                    }
                    break;
                    
                default:
                    text = data.toString();
            }
            
            await navigator.clipboard.writeText(text);
            console.log('✅ Copiado para clipboard');
            
        } catch (error) {
            console.error('❌ Erro ao copiar:', error);
            throw error;
        }
    }
    
    /**
     * Prepara dados para impressão
     * @param {Array} data - Dados para imprimir
     * @param {Object} options - Opções de impressão
     * @returns {string} HTML para impressão
     */
    preparePrintHTML(data, options = {}) {
        const {
            title = 'Relatório',
            columns = Object.keys(data[0] || {}),
            headers = columns,
            includeDate = true
        } = options;
        
        let html = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>${title}</title>
                <style>
                    body { font-family: Arial, sans-serif; }
                    h1 { text-align: center; }
                    table { 
                        width: 100%; 
                        border-collapse: collapse; 
                        margin-top: 20px;
                    }
                    th, td { 
                        border: 1px solid #ddd; 
                        padding: 8px; 
                        text-align: left;
                    }
                    th { 
                        background-color: #f5f5f5; 
                        font-weight: bold;
                    }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                    .date { 
                        text-align: right; 
                        color: #666; 
                        margin-bottom: 20px;
                    }
                    @media print {
                        body { margin: 0; }
                        th { background-color: #ddd !important; }
                    }
                </style>
            </head>
            <body>
                <h1>${title}</h1>
        `;
        
        if (includeDate) {
            html += `<div class="date">Data: ${new Date().toLocaleDateString('pt-BR')}</div>`;
        }
        
        html += '<table><thead><tr>';
        headers.forEach(header => {
            html += `<th>${header}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        data.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                html += `<td>${row[col] || ''}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table></body></html>';
        
        return html;
    }
    
    /**
     * Imprime dados
     * @param {Array} data - Dados para imprimir
     * @param {Object} options - Opções de impressão
     */
    print(data, options = {}) {
        const html = this.preparePrintHTML(data, options);
        
        const printWindow = window.open('', '_blank');
        printWindow.document.write(html);
        printWindow.document.close();
        
        printWindow.onload = () => {
            printWindow.print();
            printWindow.close();
        };
    }
}

// Exporta instância única
const exportUtils = new ExportUtils();

// Exporta para diferentes ambientes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = exportUtils;
} else if (typeof define === 'function' && define.amd) {
    define([], function() { return exportUtils; });
} else {
    window.exportUtils = exportUtils;
}
