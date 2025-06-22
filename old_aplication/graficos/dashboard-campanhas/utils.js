// Função corrigida para formatar parâmetros do Metabase
function formatMetabaseParameters(urlParams) {
    const parameters = {};
    
    // Para cada parâmetro da URL
    Object.keys(urlParams).forEach(key => {
        const value = urlParams[key];
        
        // Ignorar parâmetros vazios ou undefined
        if (!value || value === 'undefined' || value === '') {
            return;
        }
        
        // Mapear nomes dos parâmetros do iframe para os da query
        let paramName = key;
        if (key === 'peca') paramName = 'ad_name';
        if (key === 'objetivo') paramName = 'objective';
        if (key === 'conversoes_consideradas') paramName = 'action_type_filter';
        
        // Tratamento especial para data
        if (paramName === 'data') {
            // Para template tags de data no Metabase, use formato simples
            // O Metabase converte internamente para o formato SQL apropriado
            if (value.includes('~')) {
                // Range de datas
                const [start, end] = value.split('~');
                parameters[paramName] = `${start} to ${end}`;
            } else if (value.includes('past') || value.includes('last')) {
                // Datas relativas
                parameters[paramName] = value;
            } else {
                // Data única
                parameters[paramName] = value;
            }
        } else {
            // Para outros parâmetros, passar o valor diretamente
            parameters[paramName] = value;
        }
    });
    
    return parameters;
}

// Alternativa: Usar o endpoint de embedding público
async function fetchDataUsingPublicEmbedding(questionId, parameters) {
    // Gerar token JWT para embedding (isso deve ser feito no backend)
    const token = await generateEmbeddingToken(questionId, parameters);
    
    const url = `${METABASE_URL}/api/public/card/${token}/query`;
    
    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    });
    
    return response.json();
}

// Alternativa: Usar query direta no banco
async function fetchDataUsingDirectQuery(filters) {
    // Construir a query SQL dinamicamente com os filtros
    let sql = `
        WITH base_data AS (
            SELECT *
            FROM road.view_metaads_insights_alldata
            WHERE 1=1
    `;
    
    // Adicionar filtros dinamicamente
    if (filters.data) {
        const [start, end] = filters.data.split('~');
        sql += ` AND date BETWEEN '${start}' AND '${end}'`;
    }
    if (filters.conta) {
        sql += ` AND account_name = '${filters.conta}'`;
    }
    if (filters.campanha) {
        sql += ` AND campaign_name = '${filters.campanha}'`;
    }
    // ... adicionar outros filtros ...
    
    sql += `
        )
        -- Resto da query...
    `;
    
    // Executar via API do Metabase
    const response = await fetch(`${METABASE_URL}/api/dataset`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        },
        body: JSON.stringify({
            database: DATABASE_ID,
            native: { query: sql }
        })
    });
    
    return response.json();
}
