# Solução de Caracteres Especiais nos Filtros

## Problema Identificado

Quando parâmetros de filtro contêm caracteres especiais (como `+`, `&`, `%`, `#`, etc.), eles não eram decodificados corretamente ao passar do dashboard do Metabase para o iframe, causando 0 resultados na query.

### Exemplo do Problema

- **Valor no banco:** `Remarketing + Semelhantes | Engajamento | Degusta Burger 2025 | 26/05`
- **Valor capturado (incorreto):** `Remarketing   Semelhantes | Engajamento | Degusta Burger 2025 | 26/05`
- **Resultado:** 0 linhas retornadas (filtro não encontra match)

## Causa Raiz

O problema ocorria em duas etapas:

1. **URL Encoding:** Quando o Metabase cria a URL do dashboard, ele codifica:
   - Espaços como `+` ou `%20`
   - O caractere `+` como `%2B`
   - Outros caracteres especiais com seus códigos %XX

2. **Decodificação no Flask:** O Flask/Werkzeug às vezes decodifica incorretamente:
   - `+` é interpretado como espaço
   - `%2B` deveria virar `+`, mas às vezes vira múltiplos espaços

## Solução Implementada

### 1. Parse Manual da Query String (proxy_server.py)

```python
def get_raw_parameters():
    """
    Obtém parâmetros diretamente da query string raw
    """
    raw_query = request.query_string.decode('utf-8')
    params = {}
    
    for param in raw_query.split('&'):
        if '=' in param:
            key, value = param.split('=', 1)
            key = urllib.parse.unquote(key)
            value = urllib.parse.unquote(value)  # unquote preserva melhor que unquote_plus
            params[key] = value
    
    return params
```

### 2. Encoding Controlado no JavaScript (dashboard-iframe.js)

```javascript
// Monta URL manualmente para ter controle sobre encoding
let proxyUrl = `${basePath}/query?question_id=${questionId}`;

Object.entries(filtroParams).forEach(([key, value]) => {
  const encodedKey = encodeURIComponent(key);
  const encodedValue = encodeURIComponent(value);
  proxyUrl += `&${encodedKey}=${encodedValue}`;
});
```

## Caracteres Especiais Suportados

A solução agora suporta TODOS os caracteres especiais em QUALQUER campo de filtro:

- `+` (plus/mais)
- `|` (pipe)
- `&` (ampersand)
- `%` (percent)
- `#` (hash)
- `*` (asterisk)
- `()` (parentheses)
- `[]` (brackets)
- `{}` (braces)
- `/` (slash)
- `\` (backslash)
- `@`, `!`, `$`, `^`, etc.

## Como Testar

### 1. Teste Manual via Browser
Aplique filtros no dashboard com valores contendo caracteres especiais e verifique se o iframe mostra os mesmos resultados.

### 2. Script de Teste
```bash
python test_special_chars.py
```

### 3. Endpoint de Debug
```bash
curl "http://localhost:3500/debug/decode?teste=Valor+%2B+Especial"
```

## Arquivos Modificados

1. **proxy_server/proxy_server.py**
   - Adicionada função `get_raw_parameters()`
   - Modificado endpoint `/query` para usar parse manual
   - Adicionado endpoint `/debug/decode`

2. **componentes/dashboard_tabela/dashboard-iframe.js**
   - Modificada função `getParentUrlParams()` para parse manual
   - Controle manual do encoding na construção da URL

## Notas Importantes

1. **Não use `urllib.parse.unquote_plus()`** - ele converte `+` em espaço
2. **Use `urllib.parse.unquote()`** - preserva caracteres especiais corretamente
3. **No JavaScript, use `encodeURIComponent()`** - mais seguro que `encodeURI()`
4. **Sempre faça parse manual** quando precisar controle total sobre decodificação

## Troubleshooting

### Problema: Ainda retorna 0 linhas
1. Verifique o log do proxy_server - ele mostra os valores recebidos
2. Use o endpoint `/debug/decode` para ver como está sendo decodificado
3. Compare o valor decodificado com o valor no banco de dados

### Problema: Caractere específico não funciona
1. Adicione o caractere no script `test_special_chars.py`
2. Verifique se precisa de escape especial
3. Teste diferentes métodos de encoding/decoding
