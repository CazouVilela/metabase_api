#!/usr/bin/env python3
"""
Script para testar filtros com múltiplos valores
Execute com: python test_multi_values.py
"""

import requests
import urllib.parse
import json

def test_multiple_values():
    print("🧪 TESTE DE FILTROS COM MÚLTIPLOS VALORES\n")
    
    base_url = "http://localhost:3500"
    
    # 1. Teste do endpoint de debug
    print("1️⃣ Testando endpoint de debug com múltiplos valores...")
    print("-" * 50)
    
    # URL com múltiplos valores para campanha
    debug_url = f"{base_url}/debug/decode?campanha=Valor1&campanha=Valor2&campanha=Valor3&conta=ContaUnica"
    
    try:
        resp = requests.get(debug_url)
        if resp.status_code == 200:
            data = resp.json()
            print("Parâmetros parseados:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('multi_value_parameters'):
                print(f"\n✅ Múltiplos valores detectados para: {', '.join(data['multi_value_parameters'])}")
            else:
                print("\n❌ Nenhum parâmetro com múltiplos valores detectado!")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    # 2. Teste com valores reais do Metabase
    print("\n\n2️⃣ Testando com valores reais do Metabase...")
    print("-" * 50)
    
    # Valores exatos do problema
    campanhas = [
        "Barra Shopping | Road | Tráfego | Always On | MultiVocê | 07.02",
        "Barra Shopping | ROAD | Tráfego | Always On | Institucional / Acesso Multi | 24.10",
        "Barra Shopping | Road | Reconhecimento | Always On | MultiVocê | 07.02"
    ]
    conta = "ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA"
    
    # Constrói URL com múltiplos valores
    params = [('question_id', '51'), ('conta', conta)]
    for campanha in campanhas:
        params.append(('campanha', campanha))
    
    # URL com encoding correto
    query_string = urllib.parse.urlencode(params)
    query_url = f"{base_url}/query?{query_string}"
    
    print("URL construída (truncada):")
    print(f"{query_url[:150]}...")
    print(f"\nNúmero de valores de campanha: {len(campanhas)}")
    
    try:
        resp = requests.get(query_url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                print(f"\n✅ Resultado: {len(data)} linhas")
                print(f"   Esperado: ~4878 linhas (como no dashboard)")
                
                if len(data) < 4000:
                    print("\n⚠️  Menos linhas que o esperado!")
                    print("   Possível problema: O servidor pode não estar processando múltiplos valores corretamente")
            else:
                print(f"\n❌ Resposta inesperada: {type(data)}")
    except Exception as e:
        print(f"\n❌ Erro na requisição: {str(e)}")
    
    # 3. Teste do endpoint /test
    print("\n\n3️⃣ Testando endpoint /test com múltiplos valores...")
    print("-" * 50)
    
    try:
        resp = requests.get(f"{base_url}/test")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Resultado do teste:")
            print(f"  Linhas retornadas: {data.get('rows_returned', 0)}")
            print(f"  Filtros: {json.dumps(data.get('filters', {}), indent=4)}")
            
            if data.get('rows_returned', 0) > 4000:
                print("\n✅ Teste com múltiplos valores funcionando!")
            else:
                print("\n⚠️  Teste retornou menos linhas que o esperado")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
    
    # 4. Comparação: valor único vs múltiplos valores
    print("\n\n4️⃣ Comparação: filtro único vs múltiplos valores...")
    print("-" * 50)
    
    # Teste com apenas uma campanha
    single_url = f"{base_url}/query?question_id=51&conta={urllib.parse.quote(conta)}&campanha={urllib.parse.quote(campanhas[0])}"
    
    try:
        resp_single = requests.get(single_url)
        if resp_single.status_code == 200:
            data_single = resp_single.json()
            rows_single = len(data_single) if isinstance(data_single, list) else 0
            print(f"Com 1 campanha: {rows_single} linhas")
        
        # Teste com todas as campanhas
        resp_multi = requests.get(query_url)
        if resp_multi.status_code == 200:
            data_multi = resp_multi.json()
            rows_multi = len(data_multi) if isinstance(data_multi, list) else 0
            print(f"Com 3 campanhas: {rows_multi} linhas")
            
            if rows_multi > rows_single:
                print(f"\n✅ Múltiplos valores estão funcionando! ({rows_multi} > {rows_single})")
            else:
                print(f"\n❌ Problema detectado! Múltiplos valores não aumentaram o resultado")
    except Exception as e:
        print(f"\n❌ Erro na comparação: {str(e)}")


if __name__ == "__main__":
    print("⚠️  Certifique-se de que o proxy_server está rodando na porta 3500\n")
    test_multiple_values()
