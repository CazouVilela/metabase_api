#!/usr/bin/env python3
"""
Script para simular exatamente o que o iframe faz
Execute com: python test_iframe_simulation.py
"""

import requests
import urllib.parse

def test_iframe_simulation():
    print("🔍 SIMULAÇÃO DO COMPORTAMENTO DO IFRAME\n")
    
    # URL exata que você compartilhou
    dashboard_url = "https://metabasedashboards.ngrok.io/dashboard/4-dashboard?adset=Remarketing+%2B+Semelhantes+%7C+Engajamento+%7C+Degusta+Burger+2025+%7C+26%2F05&an%25C3%25BAncio=&buying_type=&campanha=Road+%7C+Engajamento+%7C+Degusta+Burger+2025+%7C+26%2F05&conta=ASSOCIACAO+DOS+LOJISTAS+DO+SHOPPING+CENTER+DA+BARRA&convers%25C3%25B5es_consideradas=&data=&device=&keyword=&objetivo=&optimization_goal=&plataforma=&posi%25C3%25A7%25C3%25A3o="
    
    # Extrai query string
    query_string = dashboard_url.split('?')[1]
    params = urllib.parse.parse_qs(query_string)
    
    print("1️⃣ Parâmetros extraídos da URL do dashboard:")
    print("-" * 50)
    
    # Processa cada parâmetro
    clean_params = {}
    for key, values in params.items():
        decoded_key = urllib.parse.unquote(key)
        if values and values[0]:
            decoded_value = urllib.parse.unquote_plus(values[0])
            clean_params[decoded_key] = decoded_value
            print(f"  • {decoded_key}: '{decoded_value}'")
    
    # Filtra apenas parâmetros com valor
    filtered_params = {k: v for k, v in clean_params.items() if v}
    
    print(f"\n2️⃣ Parâmetros com valor ({len(filtered_params)}):")
    print("-" * 50)
    for key, value in filtered_params.items():
        print(f"  • {key}: '{value}'")
    
    # Simula chamada ao proxy
    print("\n3️⃣ Simulando chamada ao proxy server...")
    print("-" * 50)
    
    proxy_url = "http://localhost:3500/query"
    query_params = {"question_id": "51", **filtered_params}
    
    print("URL do proxy:")
    print(f"  {proxy_url}?{urllib.parse.urlencode(query_params)}")
    
    print("\nParâmetros enviados:")
    for k, v in query_params.items():
        print(f"  • {k}: {v}")
    
    try:
        # Faz a requisição
        resp = requests.get(proxy_url, params=query_params, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                print(f"\n✅ Resposta: {len(data)} linhas")
                
                if len(data) == 0:
                    print("\n⚠️  PROBLEMA CONFIRMADO: 0 linhas retornadas!")
                    print("\nPossíveis causas:")
                    print("1. O '+' em 'Remarketing + Semelhantes' pode estar sendo mal interpretado")
                    print("2. Caracteres especiais podem estar sendo codificados incorretamente")
                    
                    # Testa com valor hardcoded
                    print("\n4️⃣ Testando com parâmetros hardcoded...")
                    print("-" * 50)
                    
                    hardcoded_params = {
                        "question_id": "51",
                        "campanha": "Road | Engajamento | Degusta Burger 2025 | 26/05",
                        "conta": "ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA",
                        "adset": "Remarketing + Semelhantes | Engajamento | Degusta Burger 2025 | 26/05"
                    }
                    
                    resp2 = requests.get(proxy_url, params=hardcoded_params, timeout=30)
                    if resp2.status_code == 200:
                        data2 = resp2.json()
                        rows2 = len(data2) if isinstance(data2, list) else 0
                        print(f"Resultado com params hardcoded: {rows2} linhas")
            else:
                print(f"\n❌ Resposta inesperada: {type(data)}")
                if 'error' in data:
                    print(f"Erro: {data['error']}")
        else:
            print(f"\n❌ Erro HTTP: {resp.status_code}")
            print(resp.text[:500])
            
    except Exception as e:
        print(f"\n❌ Erro ao conectar: {str(e)}")
        print("\nCertifique-se de que o proxy_server está rodando na porta 3500")
    
    # Teste direto de encoding
    print("\n5️⃣ Teste de encoding do valor 'adset':")
    print("-" * 50)
    
    original = "Remarketing + Semelhantes | Engajamento | Degusta Burger 2025 | 26/05"
    
    # Diferentes formas de encoding
    encodings = {
        "Original": original,
        "URL encode": urllib.parse.quote(original),
        "URL encode plus": urllib.parse.quote_plus(original),
        "Unquote da URL": urllib.parse.unquote_plus("Remarketing+%2B+Semelhantes+%7C+Engajamento+%7C+Degusta+Burger+2025+%7C+26%2F05"),
    }
    
    for name, encoded in encodings.items():
        print(f"  {name}: '{encoded}'")


if __name__ == "__main__":
    test_iframe_simulation()
