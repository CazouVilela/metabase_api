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

  // Captura parâmetros da URL do parent
  function getParentUrlParams() {
    try {
      const parentUrl = window.parent.location.href;
      const queryString = parentUrl.split('?')[1];
      if (!queryString) return {};

      const rawParams = new URLSearchParams(queryString);
      const filteredParams = {};

      for (const [key, value] of rawParams.entries()) {
        const decodedKey = decodeURIComponent(key);
        const decodedValue = decodeURIComponent(value);
        
        if (decodedValue && decodedValue.trim() !== "") {
          filteredParams[decodedKey] = decodedValue;
        }
      }

      return filteredParams;
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
    
    // Monta query string
    const queryParams = new URLSearchParams({ 
      question_id: questionId, 
      ...filtroParams 
    });

    // Caminho base
    const basePath = window.location.pathname.split("/componentes")[0];
    const proxyUrl = `${basePath}/query?${queryParams.toString()}`;

    // Atualiza debug info
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
          <details style="margin-top: 10px;">
            <summary>Parâmetros detalhados</summary>
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
        container.innerHTML = `
          <div class="empty-state">
            <p class="empty-icon">🔍</p>
            <p>Nenhum dado encontrado com os filtros aplicados.</p>
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

  // Observa mudanças no DOM do parent (se possível)
  try {
    const parentDoc = window.parent.document;
    const observer = new MutationObserver(() => {
      console.log("🔄 Mudança detectada no parent DOM");
      loadData("mudança no DOM");
    });
    
    // Observa mudanças nos elementos de filtro do Metabase
    const filterElements = parentDoc.querySelectorAll('[data-testid*="filter"], .FilterWidget, .DashCard');
    filterElements.forEach(el => {
      observer.observe(el, { 
        attributes: true, 
        childList: true, 
        subtree: true 
      });
    });
  } catch (e) {
    console.log("ℹ️ Não foi possível observar o parent DOM (cross-origin)");
  }

  // Escuta eventos de mudança
  ['popstate', 'hashchange'].forEach(eventName => {
    try {
      window.parent.addEventListener(eventName, () => {
        console.log(`🔄 Evento ${eventName} detectado`);
        loadData(`evento ${eventName}`);
      });
    } catch (e) {
      console.log(`ℹ️ Não foi possível escutar evento ${eventName} no parent`);
    }
  });

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
