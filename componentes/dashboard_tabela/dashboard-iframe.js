const debugEl = document.getElementById('debug');
const tableEl = document.getElementById('table-container');

const params = new URLSearchParams(window.location.search);
const questionId = params.get('question_id') || '51';

let lastFilterString = '';

function getFiltersFromDashboard() {
    if (typeof window.captureDashboardFilters === 'function') {
        return window.captureDashboardFilters();
    }
    return {};
}

async function fetchData(filters) {
    const query = new URLSearchParams({ question_id: questionId, ...filters });
    const url = `/proxy/query?${query.toString()}`;
    const res = await fetch(url);
    const data = await res.json();
    return { data, url, status: res.status };
}

function renderDebug(filters, url, status, data) {
    debugEl.innerHTML = `
        <pre>Filtros: ${JSON.stringify(filters)}</pre>
        <pre>Requisição: ${url}</pre>
        <pre>Status: ${status}</pre>
        <pre>Retorno: ${JSON.stringify(data).substring(0, 500)}...</pre>
        <pre>Total linhas: ${data.length}</pre>
    `;
}

function renderTable(data) {
    if (!Array.isArray(data) || data.length === 0) {
        tableEl.innerHTML = '<p>Nenhum dado retornado.</p>';
        return;
    }
    const headers = Object.keys(data[0]);
    let html = '<table class="table table-sm table-striped">';
    html += '<thead><tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr></thead>';
    html += '<tbody>' + data.map(row => {
        return '<tr>' + headers.map(h => `<td>${row[h]}</td>`).join('') + '</tr>';
    }).join('') + '</tbody></table>';
    tableEl.innerHTML = html;
}

async function update() {
    const filters = getFiltersFromDashboard();
    const filterString = JSON.stringify(filters);
    if (filterString !== lastFilterString) {
        lastFilterString = filterString;
        const { data, url, status } = await fetchData(filters);
        renderDebug(filters, url, status, data);
        renderTable(data);
    }
}

setInterval(update, 500);
update();
