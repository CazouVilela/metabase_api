document.addEventListener("DOMContentLoaded", async () => {
  const container = document.getElementById("table-container");
  const debug = document.getElementById("debug");
  const updateIndicator = document.getElementById("update-indicator");
  
  // Estado da aplicação
  let lastFilterState = "";
  let isLoading = false;
  let updateCount = 0;

  // Função para mostrar indicador de atualização
  function showUpdateIndicator() {
    updateIndicator.classList.add('show');
    setTimeout(() => {
      updateIndicator.classList.remove('show');
    }, 2000);
  }

  // Captura parâmetros da URL do parent com suporte a múltiplos valores
  function getParentUrlParams() {
    try {
      const parentUrl = window.parent.location.href;
      const urlParts = parentUrl.split('?');
      
      if (urlParts.length < 2) return {};
      
      // Pega a query string raw
      const queryString = urlParts[1];
      const params = {};
      
      // Parse manual para capturar MÚLTIPLOS valores do mesmo parâmetro
      queryString.split('&').forEach(param => {
        if (param.includes('=')) {
          let [key, ...valueParts] = param.split('=');
          let value = valueParts.join('='); // Caso o valor tenha '='
          
          // Decodifica a chave
          try {
            key = decodeURIComponent(key);
          } catch (e) {
            console.warn(`Erro ao decodificar chave: ${key}`, e);
            return;
          }
          
          // Decodifica o valor
          try {
            // Primeiro substitui + por espaço (padrão de URL encoding)
            value = value.replace(/\+/g, ' ');
            // Depois decodifica outros caracteres especiais
            value = decodeURIComponent(value);
          } catch (e) {
            console.warn(`Erro ao decodificar valor: ${value}`, e);
            return;
          }
          
          // Só adiciona se tiver valor
          if (value && value.trim() !== "") {
            // IMPORTANTE: Suporta múltiplos valores para a mesma chave
            if (params[key]) {
              // Se já existe, converte para array ou adiciona ao array
              if (Array.isArray(params[key])) {
                params[key].push(value);
              } else {
                params[key] = [params[key], value];
              }
            } else {
              // Primeira ocorrência
              params[key] = value;
            }
          }
        }
      });
      
      console.log("📋 Parâmetros capturados (com suporte a múltiplos valores):", params);
      
      // Log especial para parâmetros com múltiplos valores
      Object.entries(params).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          console.log(`🔹 Parâmetro '${key}' tem ${value.length} valores:`, value);
        }
      });
      
      return params;
      
    } catch (e) {
      console.warn("❌ Não foi possível acessar parâmetros do parent:", e);
      return {};
    }
  }

  // Carrega os dados
  async function loadData(reason = "manual") {
    if (isLoading) return;
    
    const filtroParams = getParentUrlParams();
    const currentFilterState = JSON.stringify(filtroParams);
    
    // Verifica se os filtros mudaram
    if (currentFilterState === lastFilterState && lastFilterState !== "") {
      return; // Sem mudanças
    }
    
    isLoading = true;
    lastFilterState = currentFilterState;
    updateCount++;

    console.log(`🔄 Atualizando dados (${reason})...`);
    console.log("📋 Filtros:", filtroParams);

    // Mostra indicador se não for o primeiro carregamento
    if (updateCount > 1) {
      showUpdateIndicator();
    }

    // Captura parâmetros do iframe
    const iframeParams = new URLSearchParams(window.location.search);
    const questionId = iframeParams.get("question_id") || "51";
    
    // Monta URL manualmente para ter controle sobre encoding
    const basePath = window.location.pathname.split("/componentes")[0];
    const urlParams = new URLSearchParams();
    urlParams.append('question_id', questionId);
    
    // Adiciona cada parâmetro com encoding controlado
    // IMPORTANTE: Suporta múltiplos valores
    Object.entries(filtroParams).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        // Múltiplos valores - adiciona cada um
        value.forEach(v => {
          urlParams.append(key, v);
        });
      } else {
        // Valor único
        urlParams.append(key, value);
      }
    });
    
    const proxyUrl = `${basePath}/query?${urlParams.toString()}`;
    console.log("🔗 URL do proxy:", proxyUrl);

    // Atualiza debug info com suporte a múltiplos valores
    debug.innerHTML = `
      <details ${updateCount === 1 ? 'open' : ''}>
        <summary>
          🔍 Debug Info 
          <span style="color: green; font-size: 12px;">(Update #${updateCount})</span>
        </summary>
        <div style="margin-top: 10px;">
          <p><strong>Question ID:</strong> ${questionId}</p>
          <p><strong>Filtros ativos:</strong> ${Object.keys(filtroParams).length}</p>
          <p><strong>Última atualização:</strong> ${new Date().toLocaleTimeString('pt-BR')} - ${reason}</p>
          <p><strong>Auto-update:</strong> <span style="color: green;">✓ Ativado</span></p>
          
          <details style="margin-top: 10px; background: #e3f2fd; padding: 10px; border-radius: 4px;">
            <summary><strong>🔹 Filtros com Múltiplos Valores</strong></summary>
            <div style="margin-top: 10px; font-size: 12px;">
              ${Object.entries(filtroParams).map(([key, value]) => {
                if (Array.isArray(value)) {
                  return `
                    <div style="margin: 5px 0; padding: 8px; background: white; border-radius: 3px; border: 1px solid #2196F3;">
                      <strong>${key}:</strong> ${value.length} valores selecionados
                      <ul style="margin: 5px 0 0 20px;">
                        ${value.map(v => `<li>"${v}"</li>`).join('')}
                      </ul>
                    </div>
                  `;
                }
                return '';
              }).join('')}
              
              ${Object.entries(filtroParams).every(([k, v]) => !Array.isArray(v)) ? 
                '<p style="color: #666;">Nenhum filtro com múltiplos valores detectado.</p>' : ''
              }
            </div>
          </details>
          
          <details style="margin-top: 10px;">
            <summary>Parâmetros com caracteres especiais</summary>
            <div style="margin-top: 5px; font-size: 12px;">
              ${Object.entries(filtroParams).map(([key, value]) => {
                const specialChars = ['+', '&', '%', '=', '?', '#', '|', '/', '*', '@', '!', '$', '^', '(', ')', '[', ']', '{', '}'];
                
                // Trata arrays
                const values = Array.isArray(value) ? value : [value];
                const results = [];
                
                values.forEach((v, index) => {
                  const foundChars = specialChars.filter(char => v.includes(char));
                  if (foundChars.length > 0) {
                    results.push(`
                      <div style="margin: 5px 0; padding: 5px; background: #f0f0f0; border-radius: 3px;">
                        <strong>${key}${Array.isArray(value) ? ` [${index + 1}]` : ''}:</strong><br>
                        Valor: "${v}"<br>
                        Caracteres especiais: ${foundChars.map(c => `<code>${c}</code>`).join(', ')}
                      </div>
                    `);
                  }
                });
                
                return results.join('');
              }).join('')}
            </div>
          </details>
          
          <details style="margin-top: 10px;">
            <summary>Todos os parâmetros</summary>
            <pre>${JSON.stringify(filtroParams, null, 2)}</pre>
          </details>
        </div>
      </details>
    `;

    // Loading
    container.innerHTML = `
      <div class="loading-container">
        <div class="spinner"></div>
        <p>⏳ Carregando dados...</p>
      </div>
    `;

    try {
      const response = await fetch(proxyUrl);
      const data = await response.json();

      if (Array.isArray(data) && data.length > 0) {
        renderTable(data);
      } else if (data.error) {
        container.innerHTML = `
          <div class="error-message">
            <strong>❌ Erro:</strong> ${data.error}
          </div>
        `;
      } else {
        // Se não achou dados, mostra informação sobre múltiplos valores
        const hasMultipleValues = Object.values(filtroParams).some(v => Array.isArray(v));
        
        container.innerHTML = `
          <div class="empty-state">
            <p class="empty-icon">🔍</p>
            <p>Nenhum dado encontrado com os filtros aplicados.</p>
            
            ${hasMultipleValues ? `
              <div style="margin-top: 20px; padding: 15px; background: #e3f2fd; border: 1px solid #2196F3; border-radius: 4px;">
                <p style="color: #1976D2; font-weight: bold;">ℹ️ Filtros com múltiplos valores detectados</p>
                <p style="font-size: 14px; margin-top: 10px;">
                  Alguns filtros têm múltiplos valores selecionados. Verifique se o servidor
                  está processando corretamente filtros com múltiplas seleções.
                </p>
              </div>
            ` : ''}
            
            <details style="margin-top: 20px; font-size: 14px;">
              <summary>Debug: Parâmetros enviados</summary>
              <pre style="margin-top: 10px; text-align: left;">${JSON.stringify(filtroParams, null, 2)}</pre>
            </details>
          </div>
        `;
      }
      
    } catch (err) {
      console.error("❌ Erro:", err);
      container.innerHTML = `
        <div class="error-message">
          <strong>❌ Erro ao buscar dados:</strong>
          <pre>${err.message}</pre>
        </div>
      `;
    } finally {
      isLoading = false;
    }
  }

  // Renderiza a tabela
  function renderTable(data) {
    const table = document.createElement("table");
    
    // Header
    const header = table.insertRow();
    
    Object.keys(data[0]).forEach((col) => {
      const th = document.createElement("th");
      th.textContent = col;
      header.appendChild(th);
    });

    // Dados
    data.forEach((row) => {
      const tr = table.insertRow();
      
      Object.values(row).forEach((val) => {
        const td = tr.insertCell();
        td.textContent = val !== null && val !== undefined ? val : "";
      });
    });

    // Container com informações
    container.innerHTML = `
      <div class="table-info">
        <div class="record-count">📊 Total de registros: ${data.length}</div>
        <div>
          <span class="update-time">✅ Atualizado: ${new Date().toLocaleTimeString('pt-BR')}</span>
          <span class="update-count">(Update #${updateCount})</span>
        </div>
      </div>
      <div class="table-scroll-container"></div>
    `;
    
    // Adiciona tabela no container com scroll
    container.querySelector('.table-scroll-container').appendChild(table);
  }

  // Estratégia de verificação inteligente
  let checkInterval = 1000; // Começa verificando a cada 1 segundo
  let noChangeCount = 0;

  async function smartCheck() {
    const oldState = lastFilterState;
    await loadData("verificação periódica");
    
    if (oldState === lastFilterState) {
      noChangeCount++;
      // Aumenta o intervalo se não houver mudanças (até 5 segundos)
      checkInterval = Math.min(5000, checkInterval + 500);
    } else {
      noChangeCount = 0;
      checkInterval = 1000; // Volta para 1 segundo após mudança
    }
    
    setTimeout(smartCheck, checkInterval);
  }

  // Verifica quando a janela volta ao foco
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      console.log("🔄 Janela voltou ao foco");
      loadData("retorno ao foco");
    }
  });

  // Carrega dados inicialmente
  await loadData("carregamento inicial");
  
  // Inicia verificação inteligente
  setTimeout(smartCheck, checkInterval);
});
