# Suporte a Múltiplos Valores nos Filtros

## Problema Identificado

Quando múltiplos valores são selecionados no mesmo filtro do dashboard Metabase, a URL contém o parâmetro repetido:

```
?campanha=valor1&campanha=valor2&campanha=valor3
```

Mas o sistema estava capturando apenas o **último valor**, resultando em menos linhas do que o esperado.

### Exemplo do Problema

- **Dashboard nativo:** 4878 linhas (com 3 campanhas selecionadas)
- **Iframe (antes):** 2386 linhas (apenas última campanha)

## Solução Implementada

### 1. JavaScript - Captura de Múltiplos Valores

O parsing manual da query string agora detecta e agrupa valores repetidos:

```javascript
// Quando encontra o mesmo parâmetro múltiplas vezes
if (params[key]) {
  // Converte para array ou adiciona ao array existente
  if (Array.isArray(params[key])) {
    params[key].push(value);
  } else {
    params[key] = [params[key], value];
  }
} else {
  params[key] = value;
}
```

### 2. Proxy Server - Processamento de Arrays

O servidor agora usa `request.args.getlist()` para capturar todos os valores:

```python
# Para parâmetros que podem ter múltiplos valores
values = request.args.getlist(param_name)
if len(values) > 1:
    params[param_name] = values  # Array
else:
    params[param_name] = values[0]  # Valor único
```

### 3. API Metabase - Formato Correto

Para múltiplos valores, o Metabase espera:

```json
{
  "type": "string/=",
  "target": ["dimension", ["template-tag", "campanha"]],
  "value": ["valor1", "valor2", "valor3"]  // Array de valores
}
```

## Como Funciona

### URL do Dashboard
```
?campanha=Valor1&campanha=Valor2&campanha=Valor3&conta=ContaUnica
```

### JavaScript Captura
```javascript
{
  "campanha": ["Valor1", "Valor2", "Valor3"],  // Array
  "conta": "ContaUnica"                         // String
}
```

### Proxy Envia para Metabase
```json
[
  {
    "type": "string/=",
    "target": ["dimension", ["template-tag", "campanha"]],
    "value": ["Valor1", "Valor2", "Valor3"]
  },
  {
    "type": "string/=",
    "target": ["dimension", ["template-tag", "conta"]],
    "value": ["ContaUnica"]
  }
]
```

## Interface de Debug

O iframe agora mostra uma seção especial quando detecta múltiplos valores:

```
🔹 Filtros com Múltiplos Valores
campanha: 3 valores selecionados
  • "Valor1"
  • "Valor2"
  • "Valor3"
```

## Testando

### 1. No Dashboard
- Selecione múltiplos valores em um filtro (ex: 3 campanhas)
- O iframe deve mostrar o mesmo número de linhas que a pergunta nativa

### 2. Via Script
```bash
python test_multi_values.py
```

### 3. Endpoint de Debug
```bash
curl "http://localhost:3500/debug/decode?param=valor1&param=valor2&param=valor3"
```

## Parâmetros Suportados

Todos os filtros de texto suportam múltiplos valores:
- `campanha`
- `conta`
- `adset`
- `ad_name`
- `plataforma`
- `posicao`
- `device`
- `objective`
- `optimization_goal`
- `buying_type`
- `action_type_filter`

## Limitações

1. **Filtros de data** não suportam múltiplos valores (usam range)
2. **Performance** pode ser impactada com muitos valores selecionados
3. **URL muito longa** pode causar problemas (limite de ~2000 caracteres)

## Troubleshooting

### Problema: Ainda mostra menos linhas
1. Verifique o log do proxy_server - deve mostrar arrays
2. Confirme que o JavaScript está capturando arrays (console F12)
3. Teste o endpoint `/test` que simula múltiplos valores

### Problema: Erro 414 (URI Too Long)
Se selecionar MUITOS valores, a URL pode ficar muito longa.
Solução: Implementar POST em vez de GET (futura melhoria)
