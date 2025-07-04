#!/usr/bin/env python3
"""
Script para debugar o problema com o filtro adset
Execute com: python debug_adset.py
"""

import requests
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from api.metabase_api import get_metabase_session, METABASE_BASE_URL

def debug_adset_filter():
    print("🔍 DEBUG DO FILTRO ADSET\n")
    
    token = get_metabase_session()
    question_id = 51
    
    # Valores dos filtros
    campanha_value = "Road | Engajamento | Degusta Burger 2025 | 26/05"
    conta_value = "ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA"
    adset_value = "Remarketing + Semelhantes | Engajamento | Degusta Burger 2025 | 26/05"
    
    # 1. Verifica informações da questão
    print("1️⃣ Verificando parâmetros da questão...")
    print("-" * 50)
    
    resp = requests.get(
        f"{METABASE_BASE_URL}/api/card/{question_id}",
        headers={"X-Metabase-Session": token},
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        template_tags = data.get('dataset_query', {}).get('native', {}).get('template-tags', {})
        
        print("Parâmetros disponíveis na query:")
        for tag_name in template_tags.keys():
            print(f"  • {tag_name}")
        
        # Verifica se 'adset' existe
        if 'adset' in template_tags:
            print(f"\n✅ Parâmetro 'adset' encontrado:")
            print(f"   Tipo: {template_tags['adset'].get('type')}")
            print(f"   Widget: {template_tags['adset'].get('widget-type')}")
        else:
            print("\n❌ Parâmetro 'adset' NÃO encontrado!")
    
    # 2. Testa diferentes combinações
    print("\n\n2️⃣ Testando diferentes combinações de filtros...")
    print("-" * 50)
    
    test_cases = [
        {
            "name": "Apenas campanha + conta (sem adset)",
            "params": [
                {
                    "type": "string/=",
                    "target": ["dimension", ["template-tag", "campanha"]],
                    "value": [campanha_value]
                },
                {
                    "type": "string/=",
                    "target": ["dimension", ["template-tag", "conta"]],
                    "value": [conta_value]
                }
            ]
        },
        {
            "name": "Todos os 3 filtros (campanha + conta + adset)",
            "params": [
                {
                    "type": "string/=",
                    "target": ["dimension", ["template-tag", "campanha"]],
                    "value": [campanha_value]
                },
                {
                    "type": "string/=",
                    "target": ["dimension", ["template-tag", "conta"]],
                    "value": [conta_value]
                },
                {
                    "type": "string/=",
                    "target": ["dimension", ["template-tag", "adset"]],
                    "value": [adset_value]
                }
            ]
        },
        {
            "name": "Apenas adset",
            "params": [
                {
                    "type": "string/=",
                    "target": ["dimension", ["template-tag", "adset"]],
                    "value": [adset_value]
                }
            ]
        }
    ]
    
    for test in test_cases:
        print(f"\n🧪 {test['name']}")
        print("Payload:")
        print(json.dumps({"parameters": test['params']}, indent=2, ensure_ascii=False))
        
        try:
            resp = requests.post(
                f"{METABASE_BASE_URL}/api/card/{question_id}/query/json",
                headers={
                    "X-Metabase-Session": token,
                    "Content-Type": "application/json"
                },
                json={"parameters": test['params']},
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                rows = len(data) if isinstance(data, list) else 0
                print(f"✅ Resultado: {rows} linhas")
                
                # Se retornou dados, verifica o valor do adset
                if rows > 0 and isinstance(data, list):
                    adset_values = set()
                    for row in data[:10]:  # Primeiras 10 linhas
                        if 'adset_name' in row:
                            adset_values.add(row['adset_name'])
                    
                    if adset_values:
                        print(f"   Valores de adset encontrados:")
                        for val in list(adset_values)[:5]:
                            print(f"   - {val}")
            else:
                print(f"❌ Erro: {resp.status_code}")
                print(f"   {resp.text[:200]}")
                
        except Exception as e:
            print(f"❌ Exceção: {str(e)}")
    
    # 3. Busca valores únicos de adset
    print("\n\n3️⃣ Buscando valores únicos de adset no banco...")
    print("-" * 50)
    
    # Query sem filtros para ver todos os valores
    resp = requests.post(
        f"{METABASE_BASE_URL}/api/card/{question_id}/query/json",
        headers={"X-Metabase-Session": token},
        json={"parameters": []},
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            # Coleta valores únicos de adset
            adset_column = None
            for col in data[0].keys():
                if 'adset' in col.lower():
                    adset_column = col
                    break
            
            if adset_column:
                unique_adsets = set()
                for row in data:
                    val = row.get(adset_column)
                    if val:
                        unique_adsets.add(val)
                
                print(f"Coluna de adset encontrada: '{adset_column}'")
                print(f"Total de valores únicos: {len(unique_adsets)}")
                
                # Procura pelo valor específico
                matching = [a for a in unique_adsets if 'Remarketing' in a and 'Semelhantes' in a]
                if matching:
                    print(f"\n✅ Valores semelhantes encontrados:")
                    for m in matching[:5]:
                        print(f"   - '{m}'")
                        if m == adset_value:
                            print("     ^ MATCH EXATO!")
                else:
                    print(f"\n⚠️  Nenhum valor contendo 'Remarketing' e 'Semelhantes' foi encontrado")
                    
                # Mostra alguns exemplos
                print(f"\nExemplos de valores de adset:")
                for val in list(unique_adsets)[:10]:
                    print(f"   - '{val}'")


if __name__ == "__main__":
    debug_adset_filter()
