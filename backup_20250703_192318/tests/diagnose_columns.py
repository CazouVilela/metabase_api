#!/usr/bin/env python3
"""
Script para diagnosticar colunas e valores exatos
Execute com: python diagnose_columns.py
"""

import requests
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from api.metabase_api import get_metabase_session, METABASE_BASE_URL

def diagnose_columns():
    print("🔍 DIAGNÓSTICO DE COLUNAS E VALORES\n")
    
    token = get_metabase_session()
    question_id = 51
    
    # 1. Busca uma amostra de dados
    print("1️⃣ Buscando amostra de dados com filtros...")
    print("-" * 50)
    
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
            print(f"✅ Encontradas {len(data)} linhas")
            
            # Lista TODAS as colunas
            print("\n📋 TODAS as colunas disponíveis:")
            for i, col in enumerate(data[0].keys()):
                print(f"  {i+1}. {col}")
            
            # Procura por colunas relacionadas a adset
            print("\n🔍 Colunas relacionadas a 'adset':")
            adset_columns = {}
            for col in data[0].keys():
                if 'adset' in col.lower() or 'ad_set' in col.lower():
                    # Pega valor da primeira linha
                    sample_value = data[0].get(col)
                    adset_columns[col] = sample_value
                    print(f"  • {col}: '{sample_value}'")
            
            # Mostra primeira linha completa
            print("\n📊 Primeira linha completa (para referência):")
            print(json.dumps(data[0], indent=2, ensure_ascii=False))
            
            # Verifica valores únicos para cada coluna de adset
            print("\n🔍 Valores únicos para colunas de adset:")
            for col_name in adset_columns.keys():
                unique_values = set()
                for row in data:
                    val = row.get(col_name)
                    if val:
                        unique_values.add(str(val))
                
                print(f"\n  Coluna '{col_name}':")
                print(f"  Total de valores únicos: {len(unique_values)}")
                
                # Mostra até 5 valores
                for i, val in enumerate(list(unique_values)[:5]):
                    print(f"    {i+1}. '{val}'")
                    
                # Verifica se contém "Remarketing"
                remarketing_values = [v for v in unique_values if 'Remarketing' in v]
                if remarketing_values:
                    print(f"\n  ✅ Valores com 'Remarketing' encontrados em '{col_name}':")
                    for val in remarketing_values:
                        print(f"    - '{val}'")
    
    # 2. Testa o valor exato encontrado
    print("\n\n2️⃣ Testando filtro com valor exato...")
    print("-" * 50)
    
    # Se encontramos o valor, vamos testá-lo
    adset_value = "Remarketing + Semelhantes | Engajamento | Degusta Burger 2025 | 26/05"
    
    test_with_all = test_params + [
        {
            "type": "string/=",
            "target": ["dimension", ["template-tag", "adset"]],
            "value": [adset_value]
        }
    ]
    
    print("Payload do teste:")
    print(json.dumps({"parameters": test_with_all}, indent=2, ensure_ascii=False))
    
    resp2 = requests.post(
        f"{METABASE_BASE_URL}/api/card/{question_id}/query/json",
        headers={
            "X-Metabase-Session": token,
            "Content-Type": "application/json"
        },
        json={"parameters": test_with_all},
        timeout=30
    )
    
    if resp2.status_code == 200:
        data2 = resp2.json()
        rows = len(data2) if isinstance(data2, list) else 0
        print(f"\n✅ Resultado: {rows} linhas")
        
        if rows > 0 and isinstance(data2, list):
            # Verifica qual coluna tem o valor de adset
            for col in data2[0].keys():
                if 'adset' in col.lower():
                    val = data2[0].get(col)
                    print(f"  {col}: '{val}'")
    else:
        print(f"\n❌ Erro: {resp2.status_code}")
        print(resp2.text[:300])


if __name__ == "__main__":
    diagnose_columns()
