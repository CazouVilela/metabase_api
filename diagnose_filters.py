#!/usr/bin/env python3
"""
Script de diagnóstico para descobrir o problema dos filtros
Execute com: python diagnose_filters.py
"""

import requests
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from api.metabase_api import get_metabase_session, METABASE_BASE_URL

def diagnose():
    print("🔍 DIAGNÓSTICO DE FILTROS DO METABASE\n")
    
    token = get_metabase_session()
    question_id = 51
    
    # 1. Teste sem filtros
    print("1️⃣ Teste SEM filtros:")
    print("-" * 40)
    
    resp = requests.post(
        f"{METABASE_BASE_URL}/api/card/{question_id}/query/json",
        headers={"X-Metabase-Session": token},
        json={"parameters": []},
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        total_rows = len(data) if isinstance(data, list) else 0
        print(f"✅ Total de registros sem filtro: {total_rows}")
    else:
        print(f"❌ Erro: {resp.status_code}")
    
    # 2. Teste com filtro que deveria retornar ~161 linhas
    print("\n2️⃣ Teste COM filtros (formato string simples):")
    print("-" * 40)
    
    test_params = {
        "parameters": [
            {
                "type": "string/=",
                "target": ["variable", ["template-tag", "campanha"]],
                "value": "Road | Engajamento | Degusta Burger 2025 | 26/05"
            },
            {
                "type": "string/=",
                "target": ["variable", ["template-tag", "conta"]],
                "value": "ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA"
            }
        ]
    }
    
    print("Payload:")
    print(json.dumps(test_params, indent=2, ensure_ascii=False))
    
    resp = requests.post(
        f"{METABASE_BASE_URL}/api/card/{question_id}/query/json",
        headers={
            "X-Metabase-Session": token,
            "Content-Type": "application/json"
        },
        json=test_params,
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list):
            filtered_rows = len(data)
            print(f"\n✅ Registros com filtro: {filtered_rows}")
            
            if filtered_rows < 5000:
                print("🎯 Filtro aplicado com sucesso!")
                
                # Verifica os dados
                if filtered_rows > 0:
                    sample = data[0]
                    print(f"\nAmostra do primeiro registro:")
                    print(f"  Campanha: {sample.get('campaign_name', 'N/A')}")
                    print(f"  Conta: {sample.get('account_name', 'N/A')}")
                    
                    # Verifica todos os registros
                    all_match = True
                    for row in data:
                        if ('Road | Engajamento | Degusta Burger 2025 | 26/05' not in str(row.get('campaign_name', '')) or
                            'ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA' not in str(row.get('account_name', ''))):
                            all_match = False
                            break
                    
                    if all_match:
                        print("\n✅ TODOS os registros correspondem aos filtros!")
                    else:
                        print("\n⚠️  Alguns registros NÃO correspondem aos filtros")
            else:
                print("⚠️  Retornou 5000 linhas - filtro não aplicado!")
    else:
        print(f"❌ Erro: {resp.status_code}")
        print(f"Detalhes: {resp.text[:500]}")
    
    # 3. Sugestão de solução
    print("\n3️⃣ SOLUÇÃO:")
    print("-" * 40)
    
    if filtered_rows == 5000:
        print("""
⚠️  O filtro não está sendo aplicado. Possíveis causas:

1. Os nomes dos parâmetros não correspondem aos template tags da query
2. O formato do valor precisa ser exato (case sensitive)
3. A query SQL pode ter algum problema

PRÓXIMOS PASSOS:
1. Execute: python test_target_formats.py
2. Verifique no Metabase UI se os filtros funcionam corretamente
3. Compare a requisição do dashboard (F12 > Network) com nosso formato
""")
    else:
        print(f"""
✅ Filtros funcionando! Retornou {filtered_rows} registros.

Para aplicar a correção:
1. Substitua proxy_server.py pelo arquivo proxy-server-fixed
2. Substitua metabase_api.py pelo arquivo metabase-api-simplified
3. Reinicie o servidor proxy
""")

if __name__ == "__main__":
    diagnose()
