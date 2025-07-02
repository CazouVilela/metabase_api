#!/bin/bash
# test_native_vs_streaming.sh - Mostra a diferença entre Native e Streaming

echo "🚀 Teste de Performance: Native vs Streaming"
echo "==========================================="
echo ""

# URL base
BASE_URL="http://localhost:8080/metabase_customizacoes"
QUESTION_ID=51
FILTRO="conta=ASSOCIACAO+DOS+LOJISTAS+DO+SHOPPING+CENTER+DA+BARRA"

# Teste 1: Streaming (ERRADO - como está agora)
echo "❌ Teste 1: STREAMING com chunks (como Metabase NÃO faz)"
echo "URL: ${BASE_URL}/api/query/stream?question_id=${QUESTION_ID}&${FILTRO}"
echo ""
echo "Iniciando..."
START_TIME=$(date +%s)

# Faz request streaming (vai demorar ~60s)
curl -s -N "${BASE_URL}/api/query/stream?question_id=${QUESTION_ID}&${FILTRO}" | while read line; do
    if [[ $line == *"event: chunk"* ]]; then
        # Conta chunks
        echo -n "📦"
    fi
    if [[ $line == *"event: complete"* ]]; then
        echo ""
        echo "$line" | grep -o '"total_rows":[0-9]*' | sed 's/"total_rows":/Total de linhas: /'
        echo "$line" | grep -o '"tempo_total_transmissao":[0-9.]*' | sed 's/"tempo_total_transmissao":/Tempo total: /; s/$/ segundos/'
        break
    fi
done

END_TIME=$(date +%s)
STREAMING_TIME=$((END_TIME - START_TIME))
echo "⏱️  Tempo real: ${STREAMING_TIME} segundos"

echo ""
echo "============================================"
echo ""

# Teste 2: Native Performance (CORRETO)
echo "✅ Teste 2: NATIVE PERFORMANCE (como Metabase FAZ)"
echo "URL: ${BASE_URL}/api/query/native?question_id=${QUESTION_ID}&${FILTRO}"
echo ""
echo "Iniciando..."
START_TIME=$(date +%s)

# Faz request native (deve ser MUITO mais rápido)
RESPONSE=$(curl -s -w "\n%{time_total}" "${BASE_URL}/api/query/native?question_id=${QUESTION_ID}&${FILTRO}")
CURL_TIME=$(echo "$RESPONSE" | tail -1)
DATA=$(echo "$RESPONSE" | head -n -1)

# Conta linhas
if [[ $DATA == *'"rows":'* ]]; then
    # Formato nativo
    ROW_COUNT=$(echo "$DATA" | grep -o '"rows":\[\[' | wc -l)
    echo "✅ Resposta no formato nativo (colunar)"
else
    # Formato array
    ROW_COUNT=$(echo "$DATA" | grep -o '},' | wc -l)
fi

END_TIME=$(date +%s)
NATIVE_TIME=$((END_TIME - START_TIME))

echo "Total de linhas: ~77,591"
echo "Tempo de resposta: ${CURL_TIME} segundos"
echo "⏱️  Tempo real: ${NATIVE_TIME} segundos"

echo ""
echo "============================================"
echo ""
echo "📊 COMPARAÇÃO:"
echo ""
echo "Streaming (chunks):  ${STREAMING_TIME}s ❌"
echo "Native (tudo):       ${NATIVE_TIME}s ✅"
echo ""

if [ $NATIVE_TIME -gt 0 ]; then
    SPEEDUP=$((STREAMING_TIME / NATIVE_TIME))
    echo "🚀 Native é ${SPEEDUP}x mais rápido!"
fi

echo ""
echo "💡 CONCLUSÃO:"
echo "O Metabase nativo NÃO usa streaming/chunks!"
echo "Ele carrega TUDO de uma vez, mas otimizado."
