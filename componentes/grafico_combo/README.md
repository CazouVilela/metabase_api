# Componente Gráfico Combinado

Componente de visualização de dados em gráfico combinado (colunas empilhadas + linhas) para dashboards do Metabase.

## Características

- **Gráfico Multi-Eixos**: 3 eixos Y independentes para diferentes métricas
- **Agregação Automática**: Dados agrupados por mês/ano
- **Filtros Sincronizados**: Captura automática dos filtros do dashboard
- **Responsivo**: Adapta-se a diferentes tamanhos de tela
- **Exportação**: CSV, PNG, JPG, SVG
- **Tela Cheia**: Modo de visualização expandida
- **Performance**: Otimizado para grandes volumes de dados

## Estrutura de Visualização

- **Eixo X**: Meses (formato Mês/Ano)
- **Eixo Y Principal (esquerda)**: Impressões - Colunas empilhadas por conta
- **Eixo Y Secundário 1 (direita)**: Clicks totais - Linha vermelha
- **Eixo Y Secundário 2 (direita)**: Investimento total - Linha verde pontilhada

## Como Usar no Metabase

1. **Adicionar ao Dashboard**:
   
   Adicione um iframe com o seguinte formato:
   ```html
   <iframe 
       src="https://metabasedashboards.ngrok.io/metabase_customizacoes/componentes/grafico_combo/?question_id=51" 
       width="100%" 
       height="600">
   </iframe>
   ```

2. **Parâmetro Obrigatório**:
   - `question_id`: ID da pergunta no Metabase (ex: `?question_id=51`)
   - O componente mostrará erro se o parâmetro não for fornecido

3. **Filtros Suportados**:
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

## Como Obter o Question ID

1. Abra a pergunta no Metabase
2. Olhe a URL: `https://seu-metabase.com/question/51-nome-da-pergunta`
3. O número após `/question/` é o ID (no exemplo: 51)

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

## Comandos de Debug (Console)

```javascript
// Estatísticas gerais
chartApp.getStats()

// Ver question_id configurado
chartApp.getQuestionId()

// Ver dados atuais
chartApp.getData()

// Ver filtros ativos
chartApp.getFilters()

// Recarregar manualmente
chartApp.refresh()

// Parar monitoramento de filtros
chartApp.stopMonitoring()

// Exportar dados
chartApp.exportData()
```

## Personalização

### Cores das Contas

Edite em `data-transformer.js`:
```javascript
getColorForAccount(index) {
    const colors = [
        '#2E86DE', '#5F27CD', '#00B894', // suas cores aqui
    ];
    return colors[index % colors.length];
}
```

### Formato de Data

Edite em `data-transformer.js`:
```javascript
this.monthNames = {
    'pt': ['Jan', 'Fev', 'Mar', ...], // Português
    'en': ['Jan', 'Feb', 'Mar', ...]  // Inglês
};
```

### Métricas Exibidas

Para mudar as métricas, edite `prepareChartData()` em `data-transformer.js`.

## Troubleshooting

### "Configuração Incorreta" aparece
1. Verifique se a URL contém `?question_id=XX`
2. Confirme que o ID é um número válido
3. Exemplo correto: `.../grafico_combo/?question_id=51`

### Gráfico não aparece
1. Verifique o console para erros
2. Execute `chartApp.getStats()` para ver o status
3. Confirme que há dados: `chartApp.getData()`

### Filtros não funcionam
1. Execute `chartApp.getFilters()` para ver filtros ativos
2. Verifique se os nomes dos filtros correspondem ao mapeamento
3. Use `chartApp.stopMonitoring()` e `chartApp.refresh()` para recarregar

### Erro de memória com muitos dados
- O componente já agrega por mês, reduzindo significativamente o volume
- Se ainda houver problemas, considere limitar o período dos dados

## Estrutura de Arquivos

```
grafico_combo/
├── index.html              # HTML principal
├── css/
│   └── grafico.css        # Estilos específicos
├── js/
│   ├── main.js            # Controlador principal
│   ├── chart-builder.js   # Construtor do gráfico
│   └── data-transformer.js # Transformação de dados
└── README.md              # Esta documentação
```

## Dependências

- **Highcharts**: Biblioteca de gráficos (carregada via CDN)
- **Recursos Compartilhados**: 
  - filter-manager.js
  - api-client.js
  - data-processor.js

## Performance

- Agregação mensal reduz dados de 600k+ linhas para ~24-36 pontos
- Renderização < 1 segundo
- Memória: ~50-100MB típico

## Próximas Melhorias

- [ ] Seletor de métricas dinâmico
- [ ] Comparação período anterior
- [ ] Drill-down para dados diários
- [ ] Tema escuro
- [ ] Cache local de dados agregados

## Teste Local

Para testar localmente sem Metabase:
```bash
# Navegue até a pasta do componente
cd ~/metabase_customizacoes/componentes/grafico_combo/

# Abra no navegador com parâmetro
firefox "file://$(pwd)/index.html?question_id=51"
```
