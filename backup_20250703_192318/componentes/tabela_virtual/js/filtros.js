// componentes/tabela_virtual/js/filtros.js
/**
 * Módulo de gerenciamento de filtros
 */

class FiltrosManager {
  constructor() {
    this.filtrosAtuais = {};
    this.ultimoEstado = '';
    this.observers = [];
    
    // Mapa de normalização
    this.normalizacao = {
      'posição': 'posicao',
      'posicao': 'posicao',
      'anúncio': 'anuncio',
      'anuncio': 'anuncio',
      'conversões_consideradas': 'conversoes_consideradas',
      'conversoes_consideradas': 'conversoes_consideradas',
      'objetivo': 'objective',
      'objective': 'objective'
    };
  }

  /**
   * Captura filtros da URL do parent (dashboard)
   */
  capturarFiltrosParent() {
    try {
      // Verifica se está em iframe
      if (!Utils.isInIframe()) {
        Utils.log('⚠️ Não está em iframe, usando filtros da URL atual');
        return this.capturarFiltrosUrl(window.location.href);
      }

      const parentUrl = window.parent.location.href;
      return this.capturarFiltrosUrl(parentUrl);
      
    } catch (e) {
      Utils.log('❌ Erro ao acessar parent URL:', e);
      return {};
    }
  }

  /**
   * Captura filtros de uma URL
   */
  capturarFiltrosUrl(url) {
    const urlParts = url.split('?');
    if (urlParts.length < 2) return {};
    
    const queryString = urlParts[1];
    const params = {};
    
    // Parse manual para suportar múltiplos valores
    queryString.split('&').forEach(param => {
      if (!param.includes('=')) return;
      
      let [key, ...valueParts] = param.split('=');
      let value = valueParts.join('=');
      
      // Decodifica chave
      key = this.decodificarParametro(key);
      key = this.normalizarNome(key);
      
      // Decodifica valor
      value = this.decodificarParametro(value);
      
      if (value && value.trim() !== '') {
        this.adicionarParametro(params, key, value);
      }
    });
    
    Utils.log('📋 Filtros capturados:', params);
    return params;
  }

  /**
   * Decodifica parâmetro (trata dupla codificação)
   */
  decodificarParametro(str) {
    try {
      // Substitui + por espaço
      str = str.replace(/\+/g, ' ');
      
      // Primeira decodificação
      str = decodeURIComponent(str);
      
      // Se ainda tem %, tenta decodificar novamente
      if (str.includes('%')) {
        try {
          str = decodeURIComponent(str);
        } catch (e) {
          // Mantém como está se falhar
        }
      }
      
      return str;
    } catch (e) {
      Utils.log('⚠️ Erro ao decodificar:', str);
      return str;
    }
  }

  /**
   * Normaliza nome do parâmetro
   */
  normalizarNome(nome) {
    return this.normalizacao[nome] || nome;
  }

  /**
   * Adiciona parâmetro (suporta múltiplos valores)
   */
  adicionarParametro(params, key, value) {
    if (params[key]) {
      // Já existe - converte para array ou adiciona
      if (Array.isArray(params[key])) {
        params[key].push(value);
      } else {
        params[key] = [params[key], value];
      }
    } else {
      params[key] = value;
    }
  }

  /**
   * Verifica se filtros mudaram
   */
  filtrosMudaram(novosFiltros) {
    const novoEstado = JSON.stringify(novosFiltros);
    const mudou = novoEstado !== this.ultimoEstado;
    
    if (mudou) {
      this.ultimoEstado = novoEstado;
      this.filtrosAtuais = novosFiltros;
    }
    
    return mudou;
  }

  /**
   * Adiciona observer para mudanças de filtros
   */
  onChange(callback) {
    this.observers.push(callback);
  }

  /**
   * Notifica observers sobre mudanças
   */
  notificarMudanca() {
    this.observers.forEach(callback => {
      try {
        callback(this.filtrosAtuais);
      } catch (e) {
        Utils.log('❌ Erro em observer:', e);
      }
    });
  }

  /**
   * Gera informações de debug
   */
  gerarDebugInfo() {
    const info = {
      total: Object.keys(this.filtrosAtuais).length,
      filtros: this.filtrosAtuais,
      multiplos: [],
      especiais: []
    };
    
    // Identifica filtros com múltiplos valores
    Object.entries(this.filtrosAtuais).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        info.multiplos.push({
          nome: key,
          quantidade: value.length,
          valores: value
        });
      }
      
      // Verifica caracteres especiais
      const valores = Array.isArray(value) ? value : [value];
      valores.forEach(v => {
        const especiais = this.verificarCaracteresEspeciais(v);
        if (especiais.length > 0) {
          info.especiais.push({
            filtro: key,
            valor: v,
            caracteres: especiais
          });
        }
      });
    });
    
    return info;
  }

  /**
   * Verifica caracteres especiais em valor
   */
  verificarCaracteresEspeciais(valor) {
    const especiais = ['+', '&', '%', '=', '?', '#', '|', '/', '*', '@', '!', '$', '^', '(', ')', '[', ']', '{', '}'];
    return especiais.filter(char => valor.includes(char));
  }

  /**
   * Converte filtros para query string
   */
  paraQueryString() {
    const params = new URLSearchParams();
    
    Object.entries(this.filtrosAtuais).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach(v => params.append(key, v));
      } else {
        params.append(key, value);
      }
    });
    
    return params.toString();
  }

  /**
   * Renderiza debug visual
   */
  renderizarDebug(container) {
    const debugInfo = this.gerarDebugInfo();
    
    let html = `
      <details ${debugInfo.total > 0 ? 'open' : ''}>
        <summary>
          🔍 Debug de Filtros 
          <span class="text-small text-muted">(${debugInfo.total} ativos)</span>
        </summary>
        <div class="debug-info">
    `;
    
    if (debugInfo.multiplos.length > 0) {
      html += '<div class="mt-2"><strong>🔹 Filtros com Múltiplos Valores:</strong></div>';
      debugInfo.multiplos.forEach(f => {
        html += `
          <div class="mt-1 text-small">
            <strong>${f.nome}:</strong> ${f.quantidade} valores
            <ul style="margin: 5px 0 0 20px;">
              ${f.valores.map(v => `<li>${Utils.escapeHtml(v)}</li>`).join('')}
            </ul>
          </div>
        `;
      });
    }
    
    if (debugInfo.especiais.length > 0) {
      html += '<div class="mt-2"><strong>⚠️ Caracteres Especiais:</strong></div>';
      debugInfo.especiais.forEach(f => {
        html += `
          <div class="mt-1 text-small">
            <strong>${f.filtro}:</strong> ${f.caracteres.map(c => `<code>${c}</code>`).join(', ')}
          </div>
        `;
      });
    }
    
    html += `
          <details class="mt-2">
            <summary>JSON completo</summary>
            <pre>${JSON.stringify(debugInfo.filtros, null, 2)}</pre>
          </details>
        </div>
      </details>
    `;
    
    container.innerHTML = html;
  }
}

// Instância global
const filtrosManager = new FiltrosManager();
