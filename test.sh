#!/bin/bash
# Script para executar testes

echo "🧪 Executando testes..."
cd "$(dirname "$0")"

# Lista todos os testes disponíveis
echo "Testes disponíveis:"
for test in tests/*.py; do
    echo "  - $(basename $test)"
done

# Pergunta qual teste executar
echo ""
read -p "Digite o nome do teste (ou 'all' para todos): " test_name

if [ "$test_name" = "all" ]; then
    for test in tests/*.py; do
        echo -e "\n📋 Executando $(basename $test)..."
        python "$test"
    done
else
    if [ -f "tests/$test_name" ]; then
        python "tests/$test_name"
    else
        echo "❌ Teste não encontrado: $test_name"
    fi
fi
