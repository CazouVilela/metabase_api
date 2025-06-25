#!/usr/bin/env python3
"""
Script para testar se todos os caracteres especiais funcionam
Execute com: python tests/test_special_chars.py
"""

import requests
import urllib.parse
import json
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_special_characters():
    print("🧪 TESTE DE CARACTERES ESPECIAIS\n")
    
    base_url = "http://localhost:3500"
    
    # 1. Teste do endpoint de debug
    print("1️⃣ Testando endpoint de debug com vários caracteres...")
    print("-" * 50)
    
    test_values = {
        "plus": "Valor + Com + Plus",
        "pipe": "Valor | Com | Pipe",
        "ampersand": "Valor & Com & Ampersand",
        "percent": "Valor % Com % Percent",
        "hash": "Valor # Com # Hash",
        "asterisk": "Valor * Com * Asterisk",
        "parentheses": "Valor (Com) Parenteses",
        "brackets": "Valor [Com] Colchetes",
        "special_mix": "Mix + de | vários & caracteres % especiais # juntos!",
        "real_example": "Remarketing + Semelhantes | Engajamento | Degusta Burger 2025 | 26/05"
    }
    
    for name, value in test_values.items():
        encoded = urllib.parse.quote(value)
        url = f"{base_url}/debug/decode?{name}={encoded}"
        
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                data = resp.json()
                
                # Verifica no formato novo do endpoint
                if 'parsed_parameters' in data and name in data['parsed_parameters']:
                    param_data = data['parsed_parameters'][name]
                    received_value = param_data.get('value', '')
                    
                    if received_value == value:
                        print(f"✅ {name}: Preservado corretamente")
                        print(f"   Original: '{value}'")
                        print(f"   Recebido: '{received_value}'")
                    else:
                        print(f"❌ {name}: ERRO na decodificação")
                        print(f"   Original: '{value}'")
                        print(f"   Recebido: '{received_value}'")
                else:
                    print(f"⚠️  {name}: Parâmetro não encontrado na resposta")
                print()
        except Exception as e:
            print(f"❌ Erro ao testar {name}: {str(e)}\n")
    
    # 2. Teste com query real do Metabase
    print("\n2️⃣ Teste com query real usando caracteres especiais...")
    print("-" * 50)
    
    # Testes práticos
    test_queries = [
        {
            "name": "Plus no adset",
            "params": {
                "question_id": "51",
                "campanha": "Road | Engajamento | Degusta Burger 2025 | 26/05",
                "conta": "ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA",
                "adset": "Remarketing + Semelhantes | Engajamento | Degusta Burger 2025 | 26/05"
            }
        },
        {
            "name": "Ampersand na campanha",
            "params": {
                "question_id": "51",
                "campanha": "Road & Engajamento | Marketing & Vendas",
                "conta": "EMPRESA & ASSOCIADOS LTDA"
            }
        },
        {
            "name": "Múltiplos caracteres especiais",
            "params": {
                "question_id": "51",
                "campanha": "Promoção: 50% OFF + Frete Grátis!",
                "conta": "LOJA #1 - Shopping & Mall"
            }
        }
    ]
    
    for test in test_queries:
        print(f"\n🔸 {test['name']}")
        
        # Constrói URL manualmente
        query_parts = []
        for key, value in test['params'].items():
            encoded_key = urllib.parse.quote(key)
            encoded_value = urllib.parse.quote(value)
            query_parts.append(f"{encoded_key}={encoded_value}")
        
        url = f"{base_url}/query?{'&'.join(query_parts)}"
        print(f"   URL: {url[:100]}...")
        
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    print(f"   ✅ Resposta: {len(data)} linhas")
                else:
                    print(f"   ℹ️  Resposta: {type(data)}")
            else:
                print(f"   ❌ Erro HTTP: {resp.status_code}")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
    
    # 3. Teste simples e direto
    print("\n\n3️⃣ Teste simples de encoding/decoding...")
    print("-" * 50)
    
    # Testa o endpoint de debug com formato mais simples
    simple_test = "Teste + Com & Caracteres | Especiais % #"
    debug_url = f"{base_url}/debug/decode?teste={urllib.parse.quote(simple_test)}"
    
    try:
        resp = requests.get(debug_url)
        if resp.status_code == 200:
            data = resp.json()
            print(f"Valor enviado: '{simple_test}'")
            
            if 'parsed_parameters' in data and 'teste' in data['parsed_parameters']:
                received = data['parsed_parameters']['teste'].get('value', '')
                print(f"Valor recebido: '{received}'")
                
                if received == simple_test:
                    print("\n✅ Caracteres especiais funcionando corretamente!")
                else:
                    print("\n❌ Problema na decodificação de caracteres")
    except Exception as e:
        print(f"❌ Erro no teste simples: {str(e)}")
    
    print("\n✅ Teste concluído!")


if __name__ == "__main__":
    test_special_characters()
