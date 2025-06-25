#!/bin/bash
# Script adicional para mover documentações criadas
# Execute após o cleanup_project.sh

echo "📚 Movendo documentações adicionais..."

# Criar pasta docs se não existir
mkdir -p docs

# Mover documentações se existirem
[ -f "CARACTERES_ESPECIAIS.md" ] && mv CARACTERES_ESPECIAIS.md docs/
[ -f "MULTIPLOS_VALORES.md" ] && mv MULTIPLOS_VALORES.md docs/

# Mover testes criados recentemente se não foram movidos
[ -f "test_multi_values.py" ] && mv test_multi_values.py tests/
[ -f "test_plus_spaces.py" ] && mv test_plus_spaces.py tests/
[ -f "test_exact_url.py" ] && mv test_exact_url.py tests/
[ -f "debug_proxy_request.sh" ] && mv debug_proxy_request.sh tests/

# Criar pasta scripts se houver scripts bash de teste
mkdir -p tests/scripts
[ -f "test_curl.sh" ] && mv test_curl.sh tests/scripts/
[ -f "tests/debug_proxy_request.sh" ] && mv tests/debug_proxy_request.sh tests/scripts/

echo "✅ Documentações movidas para docs/"
echo "✅ Testes adicionais movidos para tests/"
