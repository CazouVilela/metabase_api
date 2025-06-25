# Metabase Customizações - API de Filtros para Dashboard

Este projeto implementa uma API proxy que permite que iframes dentro de dashboards do Metabase herdem os filtros aplicados no dashboard principal.

## 🚀 Funcionalidades

- ✅ Captura automática de filtros do dashboard parent
- ✅ Suporte completo a caracteres especiais (+, &, %, |, etc.)
- ✅ Suporte a múltiplos valores no mesmo filtro
- ✅ Auto-update quando filtros mudam
- ✅ Interface de debug integrada

## 📋 Pré-requisitos

- Python 3.7+
- Metabase (instalação local ou remota)
- Nginx (para proxy reverso)

## 🔧 Instalação

1. Clone o repositório:
```bash
cd ~/metabase_customizacoes
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as credenciais do Metabase:
```bash
nano api/config.py
```

4. Configure o Nginx:
```bash
sudo cp config/nginx/metabase.conf /etc/nginx/conf.d/
sudo systemctl reload nginx
```

## ▶️ Uso

### Iniciar o servidor

```bash
./run.sh
# ou
python proxy_server/proxy_server.py
```

O servidor rodará em `http://localhost:3500`

### Adicionar iframe no dashboard

No Metabase, adicione um Text Card com o seguinte conteúdo:

```html
<iframe src="https://seu-dominio/metabase_customizacoes/componentes/dashboard_tabela/dashboard-iframe.html?question_id=51" 
        width="100%" 
        height="800">
</iframe>
```

Substitua:
- `seu-dominio` pelo seu domínio
- `51` pelo ID da sua pergunta no Metabase

## 🧪 Testes

Execute todos os testes:
```bash
./test.sh
# Escolha 'all' quando solicitado
```

Ou execute um teste específico:
```bash
python tests/test_special_chars.py
```

## 📁 Estrutura do Projeto

```
metabase_customizacoes/
├── api/                    # API do Metabase
├── componentes/            # Frontend (iframe)
├── proxy_server/           # Servidor proxy
├── tests/                  # Scripts de teste
├── docs/                   # Documentação adicional
└── config/                 # Arquivos de configuração
```

## 🔍 Debug

O iframe inclui uma interface de debug que mostra:
- Filtros capturados
- Parâmetros com caracteres especiais
- Múltiplos valores detectados
- Status de atualização

Para ver logs detalhados do servidor:
```bash
# Os logs aparecem no terminal onde o servidor está rodando
```

## 📚 Documentação Adicional

- [Solução de Caracteres Especiais](docs/CARACTERES_ESPECIAIS.md)
- [Suporte a Múltiplos Valores](docs/MULTIPLOS_VALORES.md)

## ⚙️ Configuração Avançada

### Parâmetros Suportados

Todos os filtros do tipo texto suportam múltiplos valores:
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

### Endpoints da API

- `GET /query` - Executa query com filtros
- `GET /test` - Teste manual com valores predefinidos
- `GET /debug/decode` - Debug de decodificação de parâmetros
- `GET /debug/parameters/<id>` - Mostra parâmetros disponíveis

## 🐛 Solução de Problemas

### Iframe mostra 0 linhas
1. Verifique se os valores dos filtros existem exatamente como no banco
2. Confirme que o proxy_server está rodando
3. Verifique os logs do servidor para erros

### Caracteres especiais não funcionam
1. Verifique se está usando a versão mais recente dos arquivos
2. Confirme que o JavaScript está substituindo + por espaços
3. Use o endpoint `/debug/decode` para verificar decodificação

### Múltiplos valores não funcionam
1. Confirme que o filtro permite múltiplas seleções no Metabase
2. Verifique se o JavaScript está capturando arrays
3. Veja os logs do servidor para confirmar recebimento

## 📝 Licença

Este projeto é uma customização open source para o Metabase.

## 👥 Contribuindo

1. Faça backup antes de modificar
2. Teste em ambiente de desenvolvimento
3. Documente mudanças significativas

## 📞 Suporte

Para problemas específicos:
1. Verifique a documentação em `docs/`
2. Execute os scripts de teste em `tests/`
3. Analise os logs do servidor
