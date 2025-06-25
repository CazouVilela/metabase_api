#!/usr/bin/env python3
"""
Script para testar valores específicos de adset
Execute com: python test_adset_values.py
"""

import requests
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from api.metabase_api import get_metabase_session, METABASE_BASE_URL

def test_adset_values():
    print("🔍 TESTE DE VALORES DE ADSET\n")
    
    token = get_metabase_session()
    question_id = 51
    
    # Primeiro, busca todos os valores únicos de adset
    print("1️⃣ Buscando valores únicos de adset...")
    print("-" * 50)
    
    # Query apenas com campanha e conta para ver os adsets disponíveis
    test_params = [
        {
            "type": "string/=",
            "target": ["dimension", ["template-tag", "campanha"]],
            "value": ["Road | Engajamento | Degusta Burger 2025 | 26/05"]
        },
        {
            "type": "string/=",
            "target": ["dimension", ["template-tag", "conta"]],
            "value": ["ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA"]
        }
    ]
    
    resp = requests.post(
        f"{METABASE_BASE_URL}/api/card/{question_id}/query/json",
        headers={
            "X-Metabase-Session": token,
            "Content-Type": "application/json"
        },
        json={"parameters": test_params},
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            print(f"✅ Encontradas {len(data)} linhas com campanha + conta")
            
            # Encontra a coluna de adset
            adset_column = None
            for col in data[0].keys():
                if 'adset' in col.lower():
                    adset_column = col
                    break
            
            if adset_column:
                print(f"\nColuna de adset: '{adset_column}'")
                
                # Coleta valores únicos
                unique_adsets = {}
                for row in data:
                    val = row.get(adset_column)
                    if val:
                        unique_adsets[val] = unique_adsets.get(val, 0) + 1
                
                print(f"\nValores únicos de {adset_column} ({len(unique_adsets)} valores):")
                for adset_val, count in sorted(unique_adsets.items()):
                    print(f"  • '{adset_val}' ({count} linhas)")
                
                # Procura especificamente por "Remarketing"
                remarketing_found = False
                for adset_val in unique_adsets.keys():
                    if 'Remarketing' in adset_val:
                        remarketing_found = True
                        print(f"\n✅ Valor com 'Remarketing' encontrado: '{adset_val}'")
                        
                        # Testa este valor específico
                        print("\n2️⃣ Testando filtro com este valor...")
                        test_with_adset = test_params + [
                            {
                                "type": "string/=",
                                "target": ["dimension", ["template-tag", "adset"]],
                                "value": [adset_val]
                            }
                        ]
                        
                        resp2 = requests.post(
                            f"{METABASE_BASE_URL}/api/card/{question_id}/query/json",
                            headers={
                                "X-Metabase-Session": token,
                                "Content-Type": "application/json"
                            },
                            json={"parameters": test_with_adset},
                            timeout=30
                        )
                        
                        if resp2.status_code == 200:
                            data2 = resp2.json()
                            rows = len(data2) if isinstance(data2, list) else 0
                            print(f"   Resultado: {rows} linhas")
                
                if not remarketing_found:
                    print("\n⚠️  Nenhum valor contendo 'Remarketing' foi encontrado!")
                    print("\nTalvez o valor esperado seja diferente?")
                    print("Valor tentado: 'Remarketing + Semelhantes | Engajamento | Degusta Burger 2025 | 26/05'")
    else:
        print(f"❌ Erro ao buscar dados: {resp.status_code}")


if __name__ == "__main__":
    test_adset_values()
