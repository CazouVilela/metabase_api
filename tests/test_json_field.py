#!/usr/bin/env python3
"""
Teste específico para o problema do campo JSON
"""

import psycopg2
import psycopg2.extras
import json

def teste_campo_json():
    """Testa especificamente o campo conversions que pode ser JSON/JSONB"""
    
    print("\n🔍 TESTE DO CAMPO JSON/JSONB")
    print("=" * 60)
    
    config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'agencias',
        'user': 'cazouvilela',
        'password': '$Riprip001'
    }
    
    try:
        conn = psycopg2.connect(**config)
        
        # Registra handlers JSON
        psycopg2.extras.register_default_json(loads=json.loads)
        psycopg2.extras.register_default_jsonb(loads=json.loads)
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Configura schema
            cursor.execute("SET search_path TO road, public")
            
            # Teste 1: Verifica tipo do campo conversions
            print("\n1️⃣ Verificando tipo do campo conversions...")
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    udt_name
                FROM information_schema.columns
                WHERE table_schema = 'road'
                AND table_name = 'view_metaads_insights_alldata'
                AND column_name LIKE '%conversion%'
            """)
            
            colunas = cursor.fetchall()
            for col in colunas:
                print(f"   • {col['column_name']}: {col['data_type']} ({col['udt_name']})")
            
            # Teste 2: Query com campo conversions
            print("\n2️⃣ Testando query com campo conversions...")
            cursor.execute("""
                SELECT 
                    conversions,
                    pg_typeof(conversions) as tipo
                FROM road.view_metaads_insights_alldata
                WHERE account_name = 'ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA'
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if result:
                print(f"   Tipo do campo: {result['tipo']}")
                print(f"   Tipo Python: {type(result['conversions'])}")
                print(f"   Valor (primeiros 100 chars): {str(result['conversions'])[:100]}...")
            
            # Teste 3: Tentativa de serialização
            print("\n3️⃣ Testando serialização JSON...")
            cursor.execute("""
                SELECT 
                    date,
                    account_name,
                    conversions
                FROM road.view_metaads_insights_alldata
                WHERE account_name = 'ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA'
                LIMIT 5
            """)
            
            rows = cursor.fetchall()
            
            # Tenta serializar
            for i, row in enumerate(rows):
                try:
                    # Converte para dict normal
                    row_dict = dict(row)
                    
                    # Tenta serializar
                    json_str = json.dumps(row_dict, default=str)
                    print(f"   ✅ Linha {i+1} serializada OK")
                    
                except Exception as e:
                    print(f"   ❌ Erro na linha {i+1}: {str(e)}")
                    
                    # Tenta identificar o campo problemático
                    for key, value in row.items():
                        try:
                            json.dumps({key: value}, default=str)
                        except:
                            print(f"      Campo problemático: {key} (tipo: {type(value)})")
            
            # Teste 4: Query sem campo conversions
            print("\n4️⃣ Testando query SEM campo conversions...")
            cursor.execute("""
                SELECT 
                    date,
                    account_name,
                    campaign_name,
                    impressions,
                    clicks,
                    spend
                FROM road.view_metaads_insights_alldata
                WHERE account_name = 'ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA'
                LIMIT 10
            """)
            
            rows_sem_json = cursor.fetchall()
            
            try:
                json_str = json.dumps([dict(r) for r in rows_sem_json], default=str)
                print(f"   ✅ Query sem conversions serializa OK! ({len(rows_sem_json)} linhas)")
            except Exception as e:
                print(f"   ❌ Erro mesmo sem conversions: {str(e)}")
        
        conn.close()
        
        print("\n💡 RECOMENDAÇÕES:")
        print("   1. Se conversions é JSONB, já deveria ser dict Python")
        print("   2. Pode ser necessário cast ou processamento especial")
        print("   3. Considere remover temporariamente o campo da query")
        
    except Exception as e:
        print(f"\n❌ Erro: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    teste_campo_json()
