#!/usr/bin/env python3
"""
Teste rápido para identificar o problema
"""

import psycopg2
import sys

print("🔍 TESTE RÁPIDO DE CONEXÃO\n")

# Configurações
config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'agencias',
    'user': 'cazouvilela',
    'password': '$Riprip001'
}

try:
    print("1. Tentando conectar ao PostgreSQL...")
    conn = psycopg2.connect(**config)
    print("✅ Conexão estabelecida!")
    
    cursor = conn.cursor()
    
    # Testa schema
    print("\n2. Configurando schema...")
    cursor.execute("SET search_path TO road, public")
    print("✅ Schema configurado!")
    
    # Testa query simples
    print("\n3. Testando query na view...")
    cursor.execute("""
        SELECT COUNT(*) as total 
        FROM road.view_metaads_insights_alldata 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    print(f"✅ View acessível! Total de registros: {result[0]:,}")
    
    # Testa com alguns dados
    print("\n4. Testando query com dados...")
    cursor.execute("""
        SELECT date, account_name, campaign_name, spend
        FROM road.view_metaads_insights_alldata 
        LIMIT 5
    """)
    
    rows = cursor.fetchall()
    print(f"✅ Query executada! {len(rows)} linhas retornadas")
    
    cursor.close()
    conn.close()
    
    print("\n✅ TODOS OS TESTES PASSARAM!")
    print("\nO problema pode estar em:")
    print("- ID da pergunta 51 não existe ou não é SQL nativo")
    print("- Erro na substituição de template tags")
    print("- Timeout na query completa")
    
except psycopg2.OperationalError as e:
    print(f"\n❌ ERRO DE CONEXÃO:")
    print(f"   {str(e)}")
    print("\nVerifique:")
    print("- PostgreSQL está rodando: sudo systemctl status postgresql")
    print("- Credenciais estão corretas")
    print("- Firewall permite conexão local")
    
except psycopg2.ProgrammingError as e:
    print(f"\n❌ ERRO DE SQL:")
    print(f"   {str(e)}")
    print("\nVerifique:")
    print("- Schema 'road' existe")
    print("- View 'view_metaads_insights_alldata' existe")
    print("- Usuário tem permissões de SELECT")
    
except Exception as e:
    print(f"\n❌ ERRO INESPERADO:")
    print(f"   {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
