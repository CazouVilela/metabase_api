#!/usr/bin/env python3
"""
Script de debug para diagnosticar erro 500
"""

import sys
import traceback

# Adiciona o diretório ao path
sys.path.insert(0, '.')

def teste_1_conexao_postgres():
    """Testa conexão básica ao PostgreSQL"""
    print("\n🔧 TESTE 1: Conexão PostgreSQL")
    print("-" * 40)
    
    try:
        from api.postgres_client import postgres_client
        
        if postgres_client.testar_conexao():
            print("✅ Conexão OK")
            return True
        else:
            print("❌ Falha na conexão")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        traceback.print_exc()
        return False

def teste_2_metabase_api():
    """Testa conexão com API do Metabase"""
    print("\n🔧 TESTE 2: API Metabase")
    print("-" * 40)
    
    try:
        from api.metabase_client import metabase_client
        
        # Tenta obter token
        token = metabase_client.get_session_token()
        print(f"✅ Token obtido: {token[:20]}...")
        
        # Testa obter info de uma pergunta
        info = metabase_client.get_question_info(51)
        print(f"✅ Pergunta 51: {info.get('name', 'Sem nome')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        traceback.print_exc()
        return False

def teste_3_extracao_query():
    """Testa extração de query"""
    print("\n🔧 TESTE 3: Extração de Query")
    print("-" * 40)
    
    try:
        from api.query_extractor import query_extractor
        
        query, tags = query_extractor.extrair_query_sql(51)
        print(f"✅ Query extraída: {len(query)} caracteres")
        print(f"✅ Template tags: {tags}")
        
        # Mostra início da query
        print(f"\n📄 Início da query:")
        print(query[:200] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        traceback.print_exc()
        return False

def teste_4_consulta_simples():
    """Testa consulta simples sem filtros"""
    print("\n🔧 TESTE 4: Consulta Simples")
    print("-" * 40)
    
    try:
        from api.consulta_direta import consulta_direta
        
        # Configura schema
        consulta_direta.postgres.configurar_schema('road')
        
        # Query simples
        query = "SELECT COUNT(*) as total FROM view_metaads_insights_alldata LIMIT 1"
        
        with consulta_direta.postgres.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                print(f"✅ Total de registros na view: {result['total']:,}")
                
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        traceback.print_exc()
        return False

def teste_5_filtros():
    """Testa processamento de filtros"""
    print("\n🔧 TESTE 5: Processamento de Filtros")
    print("-" * 40)
    
    try:
        from api.query_extractor import query_extractor
        
        # Query de exemplo com template tags
        query_exemplo = """
        SELECT * FROM view_metaads_insights_alldata
        WHERE 1=1
        [[AND {{data}}]]
        [[AND {{campanha}}]]
        """
        
        # Filtros de teste
        filtros = {
            'data': '2024-01-01~2024-12-31',
            'campanha': ['Campanha A', 'Campanha B']
        }
        
        # Processa
        query_processada = query_extractor.substituir_template_tags(query_exemplo, filtros)
        
        print("✅ Query processada:")
        print(query_processada)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        traceback.print_exc()
        return False

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    print("\n🔧 VERIFICANDO DEPENDÊNCIAS")
    print("-" * 40)
    
    dependencias = {
        'psycopg2': 'psycopg2-binary',
        'flask': 'Flask',
        'flask_cors': 'flask-cors'
    }
    
    todas_ok = True
    
    for modulo, pacote in dependencias.items():
        try:
            __import__(modulo)
            print(f"✅ {modulo}")
        except ImportError:
            print(f"❌ {modulo} - Instale com: pip install {pacote}")
            todas_ok = False
    
    return todas_ok

def corrigir_problema_comum():
    """Sugere correções para problemas comuns"""
    print("\n🔧 CORREÇÕES SUGERIDAS")
    print("-" * 40)
    
    print("""
1. **Instalar psycopg2-binary:**
   ```bash
   pip install psycopg2-binary
   ```

2. **Verificar configuração do PostgreSQL:**
   - Host: localhost
   - Porta: 5432
   - Database: agencias
   - User: cazouvilela
   - Password: $Riprip001

3. **Verificar se o PostgreSQL está rodando:**
   ```bash
   sudo systemctl status postgresql
   ```

4. **Testar conexão manual:**
   ```bash
   psql -h localhost -U cazouvilela -d agencias
   ```

5. **Verificar logs do servidor Flask:**
   - Reinicie o servidor
   - Observe os logs de erro no terminal

6. **Verificar permissões no PostgreSQL:**
   ```sql
   GRANT SELECT ON SCHEMA road TO cazouvilela;
   GRANT SELECT ON ALL TABLES IN SCHEMA road TO cazouvilela;
   ```

7. **Se a pergunta 51 não existe ou não é SQL nativo:**
   - Use outro ID de pergunta
   - Verifique no Metabase se é uma "Native Query"
""")

if __name__ == "__main__":
    print("\n🔍 DIAGNÓSTICO DE ERRO 500")
    print("=" * 60)
    
    # Verifica dependências primeiro
    if not verificar_dependencias():
        print("\n⚠️  Instale as dependências faltantes primeiro!")
        sys.exit(1)
    
    # Executa testes
    testes = [
        teste_1_conexao_postgres,
        teste_2_metabase_api,
        teste_3_extracao_query,
        teste_4_consulta_simples,
        teste_5_filtros
    ]
    
    resultados = []
    for teste in testes:
        try:
            resultado = teste()
            resultados.append(resultado)
        except Exception as e:
            print(f"\n❌ Erro não tratado: {str(e)}")
            resultados.append(False)
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    total_ok = sum(resultados)
    total = len(resultados)
    
    print(f"\n✅ Testes OK: {total_ok}/{total}")
    print(f"❌ Testes com falha: {total - total_ok}/{total}")
    
    if total_ok < total:
        print("\n⚠️  Alguns testes falharam!")
        corrigir_problema_comum()
    else:
        print("\n✅ Todos os testes passaram!")
        print("   O erro 500 pode ser causado por:")
        print("   - ID de pergunta inválido")
        print("   - Filtros mal formatados")
        print("   - Timeout em queries muito grandes")
        print("\n   Verifique os logs do servidor Flask para mais detalhes.")
