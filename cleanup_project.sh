#!/bin/bash
# Script para limpar e organizar o projeto metabase_customizacoes
# Execute com: bash cleanup_project.sh

echo "🧹 LIMPEZA E ORGANIZAÇÃO DO PROJETO"
echo "===================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para confirmar ação
confirm() {
    read -p "$1 (s/N): " response
    case "$response" in
        [sS]) return 0 ;;
        *) return 1 ;;
    esac
}

# 1. Criar estrutura de pastas organizadas
echo -e "${YELLOW}📁 Criando estrutura de pastas organizadas...${NC}"
mkdir -p tests
mkdir -p docs
mkdir -p backup/old_files
mkdir -p config/nginx
mkdir -p config/docker

# 2. Mover arquivos de teste
echo -e "\n${YELLOW}🧪 Movendo arquivos de teste...${NC}"
TEST_FILES=(
    "debug_adset.py"
    "diagnose_columns.py"
    "diagnose_filters.py"
    "test_adset_values.py"
    "test_filters.py"
    "test_iframe_simulation.py"
    "test_special_chars.py"
    "test_target_formats.py"
)

for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" tests/
        echo -e "${GREEN}✓${NC} Movido: $file → tests/"
    fi
done

# 3. Mover arquivos Docker (se não estiver usando Docker)
echo -e "\n${YELLOW}🐳 Arquivos Docker encontrados:${NC}"
if confirm "Você ainda usa Docker neste projeto?"; then
    echo "Movendo para config/docker..."
    [ -f "docker-compose.yml" ] && mv docker-compose.yml config/docker/
    [ -f "docker-compose-fixed.yml" ] && mv docker-compose-fixed.yml config/docker/
    [ -f "docker-compose-final.yml" ] && mv docker-compose-final.yml config/docker/
else
    echo "Movendo para backup..."
    [ -f "docker-compose.yml" ] && mv docker-compose.yml backup/old_files/
    [ -f "docker-compose-fixed.yml" ] && mv docker-compose-fixed.yml backup/old_files/
    [ -f "docker-compose-final.yml" ] && mv docker-compose-final.yml backup/old_files/
fi

# 4. Mover arquivos nginx
echo -e "\n${YELLOW}📄 Movendo arquivos nginx...${NC}"
[ -f "nginx-metabase.pp" ] && mv nginx-metabase.pp config/nginx/
[ -f "nginx-metabase.te" ] && mv nginx-metabase.te config/nginx/
echo -e "${GREEN}✓${NC} Arquivos nginx movidos para config/nginx/"

# 5. Lidar com old_aplication
if [ -d "old_aplication" ]; then
    echo -e "\n${YELLOW}📦 Pasta 'old_aplication' encontrada${NC}"
    if confirm "Deseja mover 'old_aplication' para backup? (recomendado)"; then
        mv old_aplication backup/
        echo -e "${GREEN}✓${NC} Movido para backup/"
    fi
fi

# 6. Lidar com pasta data
if [ -d "data" ]; then
    echo -e "\n${YELLOW}💾 Pasta 'data' encontrada${NC}"
    if confirm "A pasta 'data' contém dados importantes?"; then
        echo "Mantendo pasta 'data'..."
    else
        mv data backup/old_files/
        echo -e "${GREEN}✓${NC} Movido para backup/"
    fi
fi

# 7. Criar novos arquivos de documentação
echo -e "\n${YELLOW}📝 Criando documentação adicional...${NC}"

# Criar .gitignore se não existir
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# Project specific
backup/
config/nginx/*.pp
config/nginx/*.te
data/
EOF
    echo -e "${GREEN}✓${NC} Criado .gitignore"
fi

# Criar run.sh para facilitar execução
cat > run.sh << 'EOF'
#!/bin/bash
# Script para iniciar o servidor proxy

echo "🚀 Iniciando servidor proxy do Metabase..."
cd "$(dirname "$0")"
python proxy_server/proxy_server.py
EOF
chmod +x run.sh
echo -e "${GREEN}✓${NC} Criado run.sh (script de inicialização)"

# Criar test.sh para executar testes
cat > test.sh << 'EOF'
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
EOF
chmod +x test.sh
echo -e "${GREEN}✓${NC} Criado test.sh (script de testes)"

# 8. Mostrar estrutura final
echo -e "\n${YELLOW}📊 Estrutura final do projeto:${NC}"
echo ""
tree -L 2 -I '__pycache__|*.pyc' 2>/dev/null || {
    echo "📁 metabase_customizacoes/"
    echo "├── api/                    # API do Metabase"
    echo "├── componentes/            # Frontend (iframe)"
    echo "├── proxy_server/           # Servidor proxy"
    echo "├── tests/                  # Scripts de teste"
    echo "├── docs/                   # Documentação"
    echo "├── config/                 # Configurações"
    echo "│   ├── nginx/             # Configs nginx"
    echo "│   └── docker/            # Configs Docker (se usado)"
    echo "├── backup/                 # Arquivos antigos"
    echo "├── README.md              # Documentação principal"
    echo "├── requirements.txt       # Dependências Python"
    echo "├── run.sh                 # Script para iniciar servidor"
    echo "├── test.sh                # Script para executar testes"
    echo "└── .gitignore            # Arquivos ignorados pelo git"
}

# 9. Criar README dos testes
cat > tests/README.md << 'EOF'
# Scripts de Teste

Esta pasta contém scripts de teste e debug usados durante o desenvolvimento.

## Testes Disponíveis

- `test_filters.py` - Testa filtros básicos do Metabase
- `test_special_chars.py` - Testa caracteres especiais nos filtros
- `test_adset_values.py` - Testa valores específicos de adset
- `test_iframe_simulation.py` - Simula comportamento do iframe
- `debug_adset.py` - Debug específico do filtro adset
- `diagnose_columns.py` - Diagnóstico de colunas
- `diagnose_filters.py` - Diagnóstico geral de filtros
- `test_target_formats.py` - Testa formatos de target

## Como executar

Use o script `test.sh` na raiz do projeto ou execute diretamente:

```bash
python tests/nome_do_teste.py
```
EOF

echo -e "\n${GREEN}✅ Limpeza concluída!${NC}"
echo ""
echo "Resumo:"
echo "- Arquivos de teste movidos para: tests/"
echo "- Configurações movidas para: config/"
echo "- Arquivos antigos em: backup/"
echo "- Criados scripts auxiliares: run.sh e test.sh"
echo ""
echo "Para iniciar o servidor: ./run.sh"
echo "Para executar testes: ./test.sh"
