#!/usr/bin/env python3
"""
Script para testar filtros do Metabase diretamente
Execute com: python test_filters.py
"""

import requests
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from api.metabase_api import get_metabase_session, METABASE_BASE_URL

def test_direct_api():
    """Testa a API do Metabase diretamente com diferentes formatos de parâmetros"""
    
    print("🧪 TESTE DE FILTROS DO METABASE\n")
    
    token = get_metabase_session()
    question_id = 51
    
    # Diferentes formatos de teste
    test_cases = [
        {
            "name": "Formato 1: string/= com array",
            "parameters": [
                {
                    "type": "string/=",
                    "target": ["variable", ["template-tag", "campanha"]],
                    "value": ["Road | Engajamento | Degusta Burger 2025 | 26/05"]
                },
                {
                    "type": "string/=",
                    "target": ["variable", ["template-tag", "conta"]],
                    "value": ["ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA"]
                }
            ]
        },
        {
            "name": "Formato 2: category",
            "parameters": [
                {
                    "type": "category",
                    "target": ["variable", ["template-tag", "campanha"]],
                    "value": ["Road | Engajamento | Degusta Burger 2025 | 26/05"]
                },
                {
                    "type": "category",
                    "target": ["variable", ["template-tag", "conta"]],
                    "value": ["ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA"]
                }
            ]
        },
        {
            "name": "Formato 3: string/= com string simples",
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
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Testando: {test['name']}")
        print(f"{'='*60}")
        
        payload = {"parameters": test["parameters"]}
        
        print("\nPayload enviado:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        
        try:
            resp = requests.post(
                f"{METABASE_BASE_URL}/api/card/{question_id}/query/json",
                headers={
                    "X-Metabase-Session": token,
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    print(f"\n✅ Sucesso! Retornou {len(data)} linhas")
                    
                    # Mostra primeira linha como exemplo
                    if len(data) > 0:
                        print("\nPrimeira linha de exemplo:")
                        print(json.dumps(data[0], indent=2, ensure_ascii=False)[:500] + "...")
                else:
                    print(f"\n⚠️  Resposta inesperada: {type(data)}")
            else:
                print(f"\n❌ Erro: Status {resp.status_code}")
                print(f"Resposta: {resp.text[:500]}")
                
        except Exception as e:
            print(f"\n❌ Exceção: {str(e)}")
            
    print(f"\n{'='*60}")
    print("Teste concluído!")


def test_question_info():
    """Busca informações sobre a questão 51"""
    print("\n📋 INFORMAÇÕES DA QUESTÃO 51\n")
    
    token = get_metabase_session()
    
    resp = requests.get(
        f"{METABASE_BASE_URL}/api/card/51",
        headers={"X-Metabase-Session": token},
        timeout=30
    )
    
    if resp.status_code == 200:
        data = resp.json()
        
        print(f"Nome: {data.get('name')}")
        print(f"Database ID: {data.get('database_id')}")
        
        # Template tags
        template_tags = data.get('dataset_query', {}).get('native', {}).get('template-tags', {})
        
        print(f"\nParâmetros disponíveis ({len(template_tags)}):")
        for tag_name, tag_info in template_tags.items():
            print(f"\n  • {tag_name}:")
            print(f"    - type: {tag_info.get('type')}")
            print(f"    - widget-type: {tag_info.get('widget-type')}")
            print(f"    - display-name: {tag_info.get('display-name')}")
            print(f"    - required: {tag_info.get('required', False)}")
            print(f"    - default: {tag_info.get('default')}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Testa filtros do Metabase')
    parser.add_argument('--info', action='store_true', help='Mostra informações da questão')
    parser.add_argument('--test', action='store_true', help='Executa testes de filtros')
    
    args = parser.parse_args()
    
    if args.info or (not args.info and not args.test):
        test_question_info()
    
    if args.test or (not args.info and not args.test):
        test_direct_api()
