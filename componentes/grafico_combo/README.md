# Componente Gráfico Combinado v1.1

Componente de visualização de dados em gráfico combinado (colunas empilhadas + linhas) para dashboards do Metabase.

## Características

- **Gráfico Multi-Eixos**: 3 eixos Y independentes para diferentes métricas
- **Agregação Automática**: Dados agrupados por mês/ano com performance otimizada
- **Filtros Sincronizados**: Captura automática dos filtros do dashboard
- **Contador de Linhas**: Exibe total de linhas processadas antes da agregação (v1.1)
- **Debug Aprimorado**: Comandos avançados para diagnóstico de filtros (v1.1)
- **Responsivo**: Adapta-se a diferentes tamanhos de tela
- **Exportação**: CSV, PNG, JPG, SVG
- **Tela Cheia**: Modo de visualização expandida
- **Performance**: Otimizado para grandes volumes de dados (600k+ linhas)
- **Altura Fixa**: Previne crescimento vertical infinito

## Estrutura de Visualização

- **Eixo X**: Meses (formato Mês/Ano)
- **Eixo Y Principal (esquerda)**: Impressões - Colunas empilhadas por conta
- **Eixo Y Secundário 1 (direita)**: Clicks totais - Linha vermelha
- **Eixo Y Secundário 2 (direita)**: Investimento total - Linha verde pontilhada
- **Cabeçalho**: Total de linhas | Contas | Período | Última atualização (v1.1)

## Como Usar no Metabase

### 1. Adicionar ao Dashboard

Adicione um iframe com o seguinte formato:
```html
<iframe 
    src="https://metabasedashboards.ngrok.io/metabase_customizacoes/componentes/grafico_combo/?question_id=51" 
    width="100%" 
    height="600"
    frameborder="0"
    sandbox="allow-scripts allow-same-origin">
</iframe>
```

### 2. Parâmetro Obrigatório
- `question_id`: ID da pergunta no Metabase (ex: `?question_id=51`)
- O componente mostrará erro se o parâmetro não for fornecido

### 3. Filtros Suportados
- Data (date)
- Conta (account_name)
- Campanha (campaign_name)
- Conjunto de anúncios (adset_name)
- Anúncio (ad_name)
- Plataforma (publisher_platform)
- Posição (platform_position)
- Dispositivo (impression_device)
- Objetivo (objective)
- Meta de otimização (optimization_goal)
- Tipo de compra (buying_type)

### 4. Verificação Visual de Filtros (v1.1)
O contador de linhas no cabeçalho permite verificar se os filtros estão funcionando:
- **Sem filtros**: Ex: "41.285 linhas"
- **Com filtro de data**: Número deve diminuir (Ex: "3.000 linhas")
- **Com múltiplos filtros**: Número reduz ainda mais (Ex: "500 linhas")

## Como Obter o Question ID

1. Abra a pergunta no Metabase
2. Olhe a URL: `https://seu-metabase.com/question/51-nome-da-pergunta`
3. O número após `/question/` é o ID (no exemplo: 51)

## Configuração de Colunas

O componente espera que a query retorne as seguintes colunas:

- **date**: Data dos registros
- **account_name**: Nome da conta
- **impressions**: Número de impressões
- **clicks**: Número de clicks
- **spend**: Valor gasto/investido

Se suas colunas têm nomes diferentes, edite o arquivo `js/config.js`:

```javascript
columnMapping: {
    date: 'sua_coluna_data',
    account: 'sua_coluna_conta',
    impressions: 'sua_coluna_impressoes',
    clicks: 'sua_coluna_clicks',
    spend: 'sua_coluna_investimento'
}
```

## Performance e Otimizações

### Agregação em Lotes
- Processa dados em lotes de 1000 linhas
- Logs de progresso a cada 25%
- Parse otimizado de datas

### Medição de Performance
O componente mede e exibe o tempo de cada etapa:
- **API Time**: Tempo para buscar dados
- **Transform Time**: Tempo para agregar por mês
- **Chart Time**: Tempo para renderizar gráfico

### Volumes Suportados
| Volume de Dados | Tempo Total | Memória | Linhas Exibidas |
|----------------|-------------|---------|-----------------|
| 10k linhas | < 0.5s | ~50MB | 10.000 linhas |
| 100k linhas | < 1s | ~75MB | 100.000 linhas |
| 600k linhas | < 1.5s | ~100MB | 600.000 linhas |

## Exemplos de Uso

### Dashboard com Filtro de Data
```html
<iframe 
    src="https://metabasedashboards.ngrok.io/metabase_customizacoes/componentes/grafico_combo/?question_id=51" 
    width="100%" 
    height="600"
    frameborder="0">
</iframe>
```

### Múltiplos Gráficos no Mesmo Dashboard
```html
<!-- Gráfico 1: Visão Geral -->
<iframe 
    src=".../grafico_combo/?question_id=51" 
    width="50%" 
    height="500">
</iframe>

<!-- Gráfico 2: Análise Detalhada -->
<iframe 
    src=".../grafico_combo/?question_id=52" 
    width="50%" 
    height="500">
</iframe>
```

## Comandos de Debug (Console) - v1.1

### Comandos Básicos
```javascript
// Estatísticas gerais (inclui totalLinhas)
chartApp.getStats()

// Ver question_id configurado
chartApp.getQuestionId()

// Ver dados atuais
chartApp.getData()

// Debug detalhado dos dados
chartApp.debugData()

// Ver filtros ativos
chartApp.getFilters()

// Recarregar manualmente
chartApp.refresh()
```

### Comandos de Filtros (v1.1)
```javascript
// Debug completo de filtros
chartApp.debugFilters()

// Forçar recaptura e recarga de filtros
chartApp.forceReloadWithFilters()

// Ver URL e parâmetros
console.log('URL:', window.location.href)
```

### Comandos de Controle
```javascript
// Parar monitoramento de filtros
chartApp.stopMonitoring()

// Reiniciar monitoramento
chartApp.startMonitoring()

// Forçar altura fixa (corrige crescimento vertical)
chartApp.fixHeight()

// Exportar dados agregados
chartApp.exportData()
```

### Diagnóstico de Performance
```javascript
// Recarregar com medição detalhada
chartApp.refresh()
// Observe no console:
// [ChartApp] Tempo total: 1234ms (API: 650ms, Transform: 487ms, Chart: 97ms)
```

### Diagnóstico de Filtros (v1.1)
```javascript
// Verificar se filtros estão sendo aplicados
console.clear()
const antes = chartApp.getStats().totalLinhas
console.log('Linhas antes:', antes)

// Aplique um filtro no dashboard

const depois = chartApp.getStats().totalLinhas
console.log('Linhas depois:', depois)
console.log('Filtros aplicados?', antes !== depois)
```

## Personalização

### Cores das Contas

Edite em `js/config.js` ou `data-transformer.js`:
```javascript
accountColors: [
    '#2E86DE', '#5F27CD', '#00B894', // Azul, Roxo, Verde
    '#FDCB6E', '#E74C3C', '#0984E3', // Amarelo, Vermelho, Azul claro
    // Adicione mais cores conforme necessário
]
```

### Formato de Data

Edite em `data-transformer.js`:
```javascript
this.monthNames = {
    'pt': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
           'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
    'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
};
```

### Altura do Gráfico

Edite em `js/config.js`:
```javascript
visual: {
    minHeight: 400,  // Altura mínima
    defaultHeight: 450  // Altura padrão
}
```

### Métricas Exibidas

Para mudar as métricas ou adicionar novos eixos, edite `prepareChartData()` em `data-transformer.js`.

## Troubleshooting

### "Configuração Incorreta" aparece
1. Verifique se a URL contém `?question_id=XX`
2. Confirme que o ID é um número válido
3. Exemplo correto: `.../grafico_combo/?question_id=51`

### Gráfico não aparece mas dados são carregados
1. Execute `chartApp.debugData()` para ver mapeamento
2. Verifique se os nomes das colunas correspondem ao config.js
3. Ajuste o `columnMapping` se necessário
4. Execute `chartApp.refresh()` após ajustar

### Gráfico cresce verticalmente infinitamente
1. Execute `chartApp.fixHeight()` para forçar altura fixa
2. Verifique se o CSS foi aplicado corretamente
3. Pare o monitoramento temporariamente: `chartApp.stopMonitoring()`

### Performance lenta com muitos dados
1. Execute `chartApp.refresh()` e observe os tempos
2. Se "Transform time" > 1000ms:
   - Considere adicionar filtro de data padrão
   - Limite o período dos dados na query
3. Se "API time" > 2000ms:
   - Verifique índices no banco de dados
   - Considere cache no backend

### Filtros não funcionam (v1.1)
1. **Verifique o contador de linhas**: Deve mudar quando aplica filtros
2. Execute `chartApp.debugFilters()` para ver estado dos filtros
3. Use `chartApp.forceReloadWithFilters()` para forçar recaptura
4. Compare número de linhas antes/depois de aplicar filtros
5. Se o número não muda, verifique:
   - A query tem placeholders de filtros (`[[AND {{data}}]]`)
   - Os nomes dos filtros correspondem ao mapeamento
   - A URL do iframe contém os parâmetros de filtro

### Dados aparecem no console mas gráfico fica vazio
1. Verifique o mapeamento de colunas em config.js
2. Confirme que todas as colunas necessárias existem
3. Use `chartApp.debugData()` para ver estrutura dos dados
4. Verifique se há valores null nas datas

### Erro "Out of Memory"
1. Verifique o volume de dados com `chartApp.getStats()`
2. Adicione filtro de data para limitar período
3. Considere aumentar `batchSize` em data-transformer.js

### Contador de linhas não aparece (v1.1)
1. Verifique se o elemento existe: `document.getElementById('total-linhas')`
2. Confirme que tem a versão mais recente do HTML
3. Limpe o cache do navegador: Ctrl+Shift+R
4. Execute `chartApp.elements.totalLinhas` no console

## Estrutura de Arquivos

```
grafico_combo/
├── index.html              # HTML principal (v1.1: com contador)
├── css/
│   └── grafico.css        # Estilos específicos + altura fixa
├── js/
│   ├── main_grafico_combo.js # Controlador principal (v1.1: debug aprimorado)
│   ├── config.js          # Configurações e mapeamentos
│   ├── chart-builder.js   # Construtor do gráfico Highcharts
│   └── data-transformer.js # Transformação e agregação de dados
└── README.md              # Esta documentação
```

## Dependências

- **Highcharts 11.x**: Biblioteca de gráficos (carregada via CDN)
- **Recursos Compartilhados**: 
  - filter-manager.js (v3.4)
  - api-client.js (v3.4)
  - data-processor.js

## Performance Detalhada

### Agregação Mensal
- Reduz 600k+ linhas para ~24-36 pontos
- Processamento em lotes de 1000 linhas
- Logs de progresso (25%, 50%, 75%, 100%)

### Renderização
- Animação desabilitada na carga inicial
- Reabilitada após 100ms
- Altura fixa de 450px (previne reflow)

### Memória
- ~50-100MB típico
- Não cresce com scroll (diferente da tabela)
- Dados agregados ocupam pouco espaço

## Integração com Dashboard

### Sincronização de Filtros
O componente captura automaticamente todos os filtros aplicados no dashboard:
1. Aguarda 3 segundos após carregar
2. Monitora mudanças nos filtros
3. Aplica debounce de 500ms
4. Recarrega dados automaticamente
5. **Atualiza contador de linhas** (v1.1)

### Múltiplos Componentes
É possível ter vários gráficos no mesmo dashboard:
- Cada um com seu próprio `question_id`
- Filtros são aplicados em todos simultaneamente
- Performance otimizada para múltiplas instâncias
- Contadores individuais por componente

## Novidades v1.1

### Contador de Linhas
- Exibe total de linhas processadas no cabeçalho
- Formato: "X linhas | Y contas | Período | Atualização"
- Permite verificar visualmente se filtros estão funcionando
- Atualiza automaticamente quando filtros mudam

### Debug de Filtros Aprimorado
- `chartApp.debugFilters()`: Mostra estado completo dos filtros
- `chartApp.forceReloadWithFilters()`: Força recaptura e recarga
- Logs mais detalhados no console
- Diagnóstico visual através do contador

### Melhorias de Usabilidade
- Feedback imediato do impacto dos filtros
- Formatação de números com separadores de milhares
- Comandos de debug mais intuitivos

## Próximas Melhorias

- [ ] Seletor de métricas dinâmico
- [ ] Comparação com período anterior
- [ ] Drill-down para dados diários
- [ ] Tema escuro automático
- [ ] Cache local de dados agregados
- [ ] Exportação de imagem em alta resolução
- [ ] Animações de transição entre dados
- [x] Contador de linhas processadas (v1.1)
- [x] Debug aprimorado de filtros (v1.1)

## Teste Local

Para testar localmente sem Metabase:
```bash
# Navegue até a pasta do componente
cd ~/metabase_customizacoes/componentes/grafico_combo/

# Inicie um servidor local
python -m http.server 8000

# Abra no navegador
firefox "http://localhost:8000/index.html?question_id=51"
```

## API de Desenvolvimento

### Estrutura de Dados Esperada
```javascript
{
  data: {
    cols: [
      {name: "date", base_type: "type/Date"},
      {name: "account_name", base_type: "type/Text"},
      {name: "impressions", base_type: "type/Integer"},
      {name: "clicks", base_type: "type/Integer"},
      {name: "spend", base_type: "type/Decimal"}
    ],
    rows: [
      ["2024-01-01", "Conta A", 1000, 50, 100.50],
      ["2024-01-02", "Conta A", 1500, 75, 150.00],
      // ...
    ]
  },
  row_count: 41285  // v1.1: Total de linhas retornadas
}
```

### Estrutura de Dados Transformada
```javascript
{
  categories: ["Jan/2024", "Fev/2024", ...],
  series: [
    // Séries de impressões (uma por conta)
    {
      name: "Conta A",
      type: "column",
      yAxis: 0,
      data: [50000, 75000, ...],
      color: "#2E86DE"
    },
    // Série de clicks total
    {
      name: "Clicks Total",
      type: "spline",
      yAxis: 1,
      data: [2500, 3750, ...],
      color: "#FF6B6B"
    },
    // Série de investimento total
    {
      name: "Investimento Total",
      type: "spline",
      yAxis: 2,
      data: [5000.00, 7500.00, ...],
      color: "#4CAF50"
    }
  ],
  stats: {
    totalAccounts: 5,
    totalMonths: 12,
    totalImpressions: 1000000,
    totalClicks: 50000,
    totalSpend: 100000.00
  }
}
```

## Versão e Suporte

- **Versão**: 1.1.0
- **Última Atualização**: 29/07/2025
- **Compatibilidade**: Metabase 0.48+
- **Navegadores**: Chrome, Firefox, Safari, Edge
- **Requisitos**: JavaScript ES6+

## Contribuindo

Para contribuir com melhorias:
1. Teste em diferentes volumes de dados
2. Mantenha a documentação atualizada
3. Adicione comandos de debug úteis
4. Preserve a compatibilidade com recursos compartilhados
5. Otimize para performance com grandes volumes

## Changelog

### v1.1.0 (29/07/2025)
- Adicionado contador de linhas no cabeçalho
- Debug aprimorado de filtros
- Novos comandos: `debugFilters()` e `forceReloadWithFilters()`
- Formatação de números com separadores
- Logs mais detalhados para diagnóstico
- Verificação visual do impacto de filtros

### v1.0.0 (29/07/2025)
- Lançamento inicial
- Suporte a 3 eixos Y
- Agregação mensal otimizada
- Altura fixa para prevenir crescimento
- Performance otimizada para 600k+ linhas
- Comandos de debug completos
- Modo tela cheia
- Exportação múltiplos formatos

---

**Componente desenvolvido para o projeto Metabase Customizações**
