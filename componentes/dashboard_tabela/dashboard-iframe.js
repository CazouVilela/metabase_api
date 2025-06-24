document.addEventListener("DOMContentLoaded", async () => {
  const container = document.getElementById("table-container");
  const debug = document.getElementById("debug");

  function getParentUrlParams() {
    try {
      const parentUrl = window.parent.location.href;
      const queryString = parentUrl.split('?')[1];
      if (!queryString) return {};

      const rawParams = new URLSearchParams(queryString);
      const filteredParams = {};

      for (const [key, value] of rawParams.entries()) {
        if (value && value.trim() !== "") {
          filteredParams[key] = value;
        }
      }

      return filteredParams;
    } catch (e) {
      console.warn("Não foi possível acessar parâmetros do parent:", e);
      return {};
    }
  }

  const iframeParams = new URLSearchParams(window.location.search);
  const questionId = iframeParams.get("question_id") || "51";

  const filtroParams = getParentUrlParams();
  const queryParams = new URLSearchParams({ question_id: questionId, ...filtroParams });

  // 🚨 Corrige caminho base para ambientes com subpath (como ngrok com pasta)
  const basePath = window.location.pathname.split("/componentes")[0];
  const proxyUrl = `${basePath}/query?${queryParams.toString()}`;

  debug.innerHTML = `<small>🔗 Proxy URL: <code>${proxyUrl}</code></small>`;

  try {
    const response = await fetch(proxyUrl);
    const data = await response.json();

    if (Array.isArray(data) && data.length > 0) {
      const table = document.createElement("table");
      table.border = "1";
      const header = table.insertRow();
      Object.keys(data[0]).forEach((col) => {
        const th = document.createElement("th");
        th.textContent = col;
        header.appendChild(th);
      });

      data.forEach((row) => {
        const tr = table.insertRow();
        Object.values(row).forEach((val) => {
          const td = tr.insertCell();
          td.textContent = val;
        });
      });

      container.innerHTML = "";
      container.appendChild(table);
    } else {
      container.innerHTML = "<p>🔍 Nenhum dado encontrado.</p>";
    }
  } catch (err) {
    container.innerHTML = `<pre>Erro ao buscar dados: ${err}</pre>`;
    console.error(err);
  }
});
