#!/usr/bin/env python3
"""
Script de teste para verificar que não há limites de linhas
e que o sistema retorna todos os dados
"""

import requests
import json
import time
from urllib.parse import quote

# Configuração
BASE_URL = "https://metabasedashboards.ngrok.io/metabase_customizacoes"

def test_no_row_limits():
    """Testa se o sistema retorna todas as linhas sem limites"""
    
    print("🧪 TESTE DE AUSÊNCIA DE LIMITES DE LINHAS")
    print("=" * 60)
    
    # Teste 1: Query sem filtros (deve retornar MUITAS linhas)
    print("\n📌 Teste 1: Query sem filtros (máximo de dados)")
    print("   ⚠️  Aviso: Pode demorar alguns segundos...")
    
    url = f"{BASE_URL}/query?question_id=51"
    
    start_time = time.time()
    
    try:
        response = requests.get(url, timeout=300)  # 5 minutos
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                row_count = len(data)
                print(f"\n✅ Sucesso! {row_count:,} linhas retornadas")
                print(f"   ⏱️  Tempo de resposta: {elapsed_time:.2f} segundos")
                print(f"   📊 Média: {(elapsed_time/row_count*1000):.2f} ms por mil linhas")
                
                # Verifica se não há limite artificial
                common_limits = [1000, 2000, 5000, 10000, 50000, 100000]
                if row_count in common_limits:
                    print(f"\n⚠️  ATENÇÃO: Retornou exatamente {row_count:,} linhas")
                    print("   Isso pode indicar um limite artificial.")
                else:
                    print("\n✅ Não parece haver limite artificial!")
                    print(f"   O número {row_count:,} não é um limite comum.")
                
                # Estatísticas de memória (aproximada)
                approx_size_mb = (len(json.dumps(data)) / 1024 / 1024)
                print(f"\n📦 Tamanho aproximado dos dados: {approx_size_mb:.1f} MB")
                
            else:
                print(f"❌ Resposta inesperada: {type(data)}")
                
        elif response.status_code == 504:
            print(f"⏱️  Timeout após {elapsed_time:.2f} segundos")
            print("   A query é muito grande. Use filtros.")
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout do cliente após 300 segundos")
        print("   A query é extremamente grande.")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    # Teste 2: Query com um filtro (menos dados)
    print("\n\n📌 Teste 2: Query com filtro de conta")
    
    params = {
        'conta': 'ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA'
    }
    
    url = f"{BASE_URL}/query?question_id=51&conta={quote(params['conta'])}"
    
    start_time = time.time()
    
    try:
        response = requests.get(url, timeout=300)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                filtered_count = len(data)
                print(f"\n✅ Com filtro: {filtered_count:,} linhas retornadas")
                print(f"   ⏱️  Tempo: {elapsed_time:.2f} segundos")
                
                # Comparação de performance
                if 'row_count' in locals():
                    reduction = ((row_count - filtered_count) / row_count * 100)
                    print(f"   📉 Redução: {reduction:.1f}% menos dados")
                    
            else:
                print(f"❌ Resposta inesperada: {type(data)}")
                
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
    
    # Teste 3: Verificar endpoint de debug
    print("\n\n📌 Teste 3: Verificando configurações")
    
    debug_url = f"{BASE_URL}/debug/decode?test=true"
    
    try:
        response = requests.get(debug_url, timeout=30)
        
        if response.status_code == 200:
            print("✅ Endpoint de debug funcionando")
        
    except Exception as e:
        print(f"⚠️  Debug endpoint não acessível: {str(e)}")
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DO TESTE:")
    print("=" * 60)
    
    if 'row_count' in locals():
        print(f"• Total de linhas sem filtro: {row_count:,}")
        
        if row_count > 50000:
            print("• ✅ Sistema capaz de retornar >50k linhas")
            print("• ⚠️  Para melhor performance, use filtros quando possível")
        elif row_count > 10000:
            print("• ✅ Sistema retorna dados substanciais")
        else:
            print("• ℹ️  Dataset relativamente pequeno")
    
    print("\n💡 DICAS:")
    print("• Para datasets grandes, sempre use filtros")
    print("• Monitore o uso de memória do navegador")
    print("• Considere criar views agregadas para dashboards")

def test_performance_with_sizes():
    """Testa a performance com diferentes tamanhos de resultado"""
    
    print("\n\n🚀 TESTE DE PERFORMANCE POR TAMANHO")
    print("=" * 60)
    
    # Testa com diferentes filtros que retornam diferentes quantidades
    test_filters = [
        {
            "name": "Sem filtros",
            "params": {}
        },
        {
            "name": "Uma conta",
            "params": {"conta": "ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA"}
        },
        {
            "name": "Uma campanha",
            "params": {"campanha": "Barra Shopping | Road | Tráfego | Always On | MultiVocê | 07.02"}
        },
        {
            "name": "Conta + Plataforma",
            "params": {
                "conta": "ASSOCIACAO DOS LOJISTAS DO SHOPPING CENTER DA BARRA",
                "plataforma": "facebook"
            }
        }
    ]
    
    results = []
    
    for test in test_filters:
        print(f"\n🔹 Testando: {test['name']}")
        
        # Constrói URL
        url = f"{BASE_URL}/query?question_id=51"
        for key, value in test['params'].items():
            url += f"&{key}={quote(value)}"
        
        start_time = time.time()
        
        try:
            response = requests.get(url, timeout=300)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    results.append({
                        "filter": test['name'],
                        "rows": len(data),
                        "time": elapsed_time,
                        "rows_per_sec": len(data) / elapsed_time if elapsed_time > 0 else 0
                    })
                    print(f"   ✅ {len(data):,} linhas em {elapsed_time:.2f}s")
        except:
            print(f"   ❌ Erro no teste")
    
    # Mostra resumo de performance
    if results:
        print("\n\n📊 RESUMO DE PERFORMANCE:")
        print("-" * 60)
        print(f"{'Filtro':<30} {'Linhas':>10} {'Tempo':>10} {'Linhas/s':>15}")
        print("-" * 60)
        
        for r in results:
            print(f"{r['filter']:<30} {r['rows']:>10,} {r['time']:>9.2f}s {r['rows_per_sec']:>15,.0f}")

if __name__ == "__main__":
    test_no_row_limits()
    test_performance_with_sizes()
    
    print("\n\n✅ Testes concluídos!")
    print("Se você viu números grandes (>50k), o sistema está funcionando sem limites! 🎉")
